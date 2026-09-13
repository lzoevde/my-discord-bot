import os
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"✅ 로그인 성공: {bot.user} (ID: {bot.user.id})")
    print(f"🚀 디스코드 봇이 정상적으로 가동되었습니다.")
    print(f"========================================")
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ 슬래시 명령어 총 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"❌ 명령어 동기화 실패: {e}")

@bot.tree.command(name="안녕", description="봇이 인사를 건넵니다.")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"안녕하세요 {interaction.user.mention}님! 봇이 정상 작동 중입니다 👋", ephemeral=True)

if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("❌ 토큰이 설정되지 않았습니다!")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ 봇 실행 중 오류 발생: {e}")
