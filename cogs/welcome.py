import discord
from discord.ext import commands
import json
import os

WELCOME_CHANNEL_ID = 1444533837219762308
DEFAULT_ROLE_ID = 1444730075449917602
STICKY_FILE = "data/sticky_roles.json"

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)
        if not os.path.isfile(STICKY_FILE):
            with open(STICKY_FILE, "w") as f:
                json.dump({}, f)
        with open(STICKY_FILE, "r") as f:
            self.sticky_data = json.load(f)

    def save_sticky(self):
        with open(STICKY_FILE, "w") as f:
            json.dump(self.sticky_data, f, indent=4)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        roles = [role.id for role in member.roles if role != member.guild.default_role]
        if roles:
            self.sticky_data[str(member.id)] = roles
            self.save_sticky()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        user_id = str(member.id)
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Welcome to Cozy Lab Studio",
                description=(
                    f"Greetings {member.mention}, welcome to Cozy Lab Studio.\n"
                    f"Check out <#1444534981069373622> and <#1444537287714275378>"
                ),
                color=0x6C3BAA
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Make sure to read the rules and enjoy your stay!")
            await channel.send(embed=embed)
        default_role = member.guild.get_role(DEFAULT_ROLE_ID)
        if default_role:
            try:
                await member.add_roles(default_role)
            except discord.Forbidden:
                pass
        if user_id in self.sticky_data:
            role_ids = self.sticky_data[user_id]
            roles_to_add = [member.guild.get_role(rid) for rid in role_ids if member.guild.get_role(rid)]
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add)
                except discord.Forbidden:
                    pass
            del self.sticky_data[user_id]
            self.save_sticky()

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))