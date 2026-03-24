import discord
from discord.ext import commands
import json
import os
import random
import math
import time

XP_FILE = "data/xp.json"
XP_GAIN_RANGE = (15, 30)
LEVEL_LOG_CHANNEL = 1452292197105012789

ROLE_REWARDS = {
    5:  [1467083282892984493, 1466614746911342722, 1467083861421723792],
    15: [1467083348823248997, 1466614064896671835],
    25: [1467084163114074419, 1467526357696122941],
    35: [1467084360879706270, 1467526859842388050]
}

class XP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {}
        self.load_data()

    def load_data(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.isfile(XP_FILE):
            with open(XP_FILE, "w") as f:
                json.dump({}, f)
        with open(XP_FILE, "r") as f:
            self.data = json.load(f)

    def save_data(self):
        with open(XP_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_user(self, guild_id: int, user_id: int):
        guild = str(guild_id)
        user = str(user_id)
        if guild not in self.data:
            self.data[guild] = {}
        if user not in self.data[guild]:
            self.data[guild][user] = {"xp": 0, "level": 0}
        return self.data[guild][user]

    def xp_needed(self, level: int) -> int:
        return math.floor(75 * (level ** 1.25) * (1 + 0.015 * level))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        now = time.time()
        last = self.cooldowns.get(message.author.id, 0)
        if now - last < 60:
            return
        self.cooldowns[message.author.id] = now
        user = self.get_user(message.guild.id, message.author.id)
        gain = random.randint(*XP_GAIN_RANGE)
        user["xp"] += gain
        if user["xp"] >= self.xp_needed(user["level"]):
            user["level"] += 1
            user["xp"] = 0
            level = user["level"]
            await message.channel.send(f"{message.author.mention} congratulations! You are now level **{level}**")
            if level in ROLE_REWARDS:
                granted = []
                for role_id in ROLE_REWARDS[level]:
                    role = message.guild.get_role(role_id)
                    if role:
                        try:
                            await message.author.add_roles(role)
                            granted.append(role.name)
                        except discord.Forbidden:
                            pass
                if granted:
                    await message.channel.send("Gave " + ", ".join(granted) + " role.")
            log_channel = message.guild.get_channel(LEVEL_LOG_CHANNEL)
            if log_channel:
                await log_channel.send(f"{message.author.mention} congratulations! You are now level **{level}**")
        self.save_data()
        
    @commands.command(name="xp", aliases=["level"])
    async def xp(self, ctx, member: discord.Member | None = None):
        member = member or ctx.author
        user = self.get_user(ctx.guild.id, member.id)
        embed = discord.Embed(title="Experience Points", color=0x6C3BAA)
        embed.add_field(name="Current Level", value=str(user["level"]), inline=False)
        embed.add_field(name="Current XP", value=str(user["xp"]), inline=False)
        embed.add_field(name="XP Needed", value=str(self.xp_needed(user["level"])), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="perks")
    async def perks(self, ctx):
        embed = discord.Embed(title="Level Perks", color=0x6C3BAA)
        embed.add_field(name="Level 5", value="Reaction Permission, Change Nickname", inline=False)
        embed.add_field(name="Level 15", value="Image/Attachment Permission, Exclusive Channels", inline=False)
        embed.add_field(name="Level 25", value="External Emoji, Sticker, Soundboard Permission", inline=False)
        embed.add_field(name="Level 35", value="Polls Permission, Exclusive Channels", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.data:
            await ctx.send("No XP data for this server yet.")
            return
        users_data = self.data[guild_id]
        sorted_users = sorted(users_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
        embed = discord.Embed(title=f"{ctx.guild.name} Leaderboard", color=0x6C3BAA)
        for i, (user_id, info) in enumerate(sorted_users[:10], start=1):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"User ID {user_id}"
            embed.add_field(name=f"#{i} {name}", value=f"Level: {info['level']} | XP: {info['xp']}", inline=False)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(XP(bot))