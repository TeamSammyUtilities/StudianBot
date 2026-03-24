import discord
from discord.ext import commands, tasks
import os
import asyncio

with open("key.txt") as f:
    TOKEN = f.read().strip()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    update_status.start()

@tasks.loop(minutes=5)
async def update_status():
    total_members = sum(guild.member_count for guild in bot.guilds)
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{total_members} members • +help"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="Bot Commands", color=0x6C3BAA)

    embed.add_field(name="XP Commands", value=(
        "+xp / +level → Check your XP and level\n"
        "+perks → See server level perks\n"
        "+leaderboard / +lb → Show top 10 users by level & XP"
    ), inline=False)

    embed.add_field(name="Tag Commands", value=(
        "+tag create <name> <content> → Create a new tag\n"
        "+tag delete <name> → Delete your tag\n"
        "+tag info <name> → Show tag owner and creation date\n"
        "+tag transfer <name> <member> → Transfer tag ownership"
    ), inline=False)

    await ctx.send(embed=embed)

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    await load_cogs()
    await bot.start(TOKEN)

asyncio.run(main())