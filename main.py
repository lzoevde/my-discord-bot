import os
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def get_roblox_thumbnail(user_id: int):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = data.get("data", [])
                if results:
                    item = results[0]
                    if item.get("state") == "Completed":
                        return item.get("imageUrl")
    return None

async def check_roblox_user(username: str):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": True}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                users = data.get("data", [])
                if users:
                    user_info = users[0]
                    user_id = user_info["id"]
                    thumb_url = await get_roblox_thumbnail(user_id)
                    user_info["avatarUrl"] = thumb_url
                    return user_info
    return None

class VerificationModal(discord.ui.Modal, title="로블록스 계정 인증"):
    roblox_username = discord.ui.TextInput(
        label="로블록스 아이디를 입력하세요",
        placeholder="예: Builderman",
        max_length=50,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        username = self.roblox_username.value.strip()

        r_user = await check_roblox_user(username)
        if not r_user:
            return await interaction.followup.send(
                f"❌ **'{username}'**은(는) 존재하지 않는 로블록스 계정이거나 밴된 계정입니다. 정확한 아이디를 입력해주세요.",
                ephemeral=True
            )

        guild = interaction.guild
        member = interaction.user
        roblox_id = r_user["id"]
        roblox_display = r_user["displayName"]
        roblox_name = r_user["name"]
        avatar_url = r_user.get("avatarUrl")

        role = discord.utils.get(guild.roles, name="Verified")
        if not role:
            return await interaction.followup.send(
                "❌ 서버에 **'Verified'** 이름의 역할이 없습니다. 서버 설정 -> 역할에서 'Verified' 역할을 먼저 만들어주세요!",
                ephemeral=True
            )

        try:
            await member.add_roles(role)
        except discord.Forbidden:
            return await interaction.followup.send(
                "❌ 봇의 권한이 부족합니다. 봇 역할을 'Verified' 역할보다 위쪽으로 올려주세요.",
                ephemeral=True
            )

        # '#한국인-플레이어' 채널에 보기 좋은 프로필 전송
        target_channel = discord.utils.get(guild.text_channels, name="한국인-플레이어")
        if target_channel:
            embed = discord.Embed(
                title="✨ 로블록스 연동 플레이어 등록",
                color=discord.Color.from_rgb(0, 162, 255)
            )
            embed.add_field(name="📌 디스코드 유저", value=f"**{member.display_name}** (`@{member.name}`)", inline=False)
            embed.add_field(name="🏷️ 로블록스 닉네임", value=f"**{roblox_display}**", inline=True)
            embed.add_field(name="🆔 로블록스 아이디", value=f"`@{roblox_name}`", inline=True)
            embed.add_field(name="🔢 로블록스 숫자 ID", value=f"`{roblox_id}`", inline=False)
            
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
                
            icon_url = guild.icon.url if guild.icon else None
            embed.set_footer(text="Roblox Verification System", icon_url=icon_url)
            embed.timestamp = discord.utils.utcnow()
            
            await target_channel.send(embed=embed)

        await interaction.followup.send(
            f"✅ 인증이 완료되었습니다! **Verified** 역할을 지급받으셨습니다.",
            ephemeral=True
        )

class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="로블록스 인증하기", style=discord.ButtonStyle.green, custom_id="verify_button_persistent")
    async def verify_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerificationModal())

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"✅ 로그인 성공: {bot.user} (ID: {bot.user.id})")
    print(f"🚀 디스코드 봇이 정상적으로 가동되었습니다.")
    print(f"========================================")
    
    bot.add_view(VerificationView())
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ 슬래시 명령어 총 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"❌ 명령어 동기화 실패: {e}")

@bot.tree.command(name="인증판넬설정", description="인증-탭에 로블록스 인증 버튼을 설치합니다.")
@app_commands.default_permissions(administrator=True)
async def setup_verify_panel(interaction: discord.Interaction): # <--- 올바르게 수정 완료!
    embed = discord.Embed(
        title="🎮 로블록스 계정 인증 안내",
        description="아래 **[로블록스 인증하기]** 버튼을 눌러 본인의 로블록스 **아이디**를 입력해 주세요.\n정상 확인되면 자동으로 **Verified** 역할과 프로필이 등록됩니다.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message("✅ 인증 패널을 설치했습니다!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=VerificationView())

if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("❌ 토큰이 설정되지 않았습니다!")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ 봇 실행 중 오류 발생: {e}")
