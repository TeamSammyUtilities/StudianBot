import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os

ROLES_FILE = "data/roles.json"

class RoleView(View):
    def __init__(self, roles: dict, message_id: int):
        super().__init__(timeout=None)

        for label, role_id in roles.items():
            button = Button(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id=f"role:{message_id}:{role_id}"
            )
            button.callback = self.make_callback(role_id)
            self.add_item(button)

    def make_callback(self, role_id: int):
        async def callback(interaction: discord.Interaction):
            role = interaction.guild.get_role(role_id)
            member = interaction.user

            if not role:
                await interaction.response.send_message(
                    "Role no longer exists.",
                    ephemeral=True
                )
                return

            if role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(
                    f"Removed **{role.name}**",
                    ephemeral=True
                )
            else:
                await member.add_roles(role)
                await interaction.response.send_message(
                    f"Gave **{role.name}**",
                    ephemeral=True
                )
        return callback


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)

        if not os.path.isfile(ROLES_FILE):
            with open(ROLES_FILE, "w") as f:
                json.dump({}, f)

        with open(ROLES_FILE, "r") as f:
            self.data = json.load(f)

    async def cog_load(self):
        for message_id, entry in self.data.items():
            view = RoleView(entry["roles"], int(message_id))
            self.bot.add_view(view, message_id=int(message_id))

    def save(self):
        with open(ROLES_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def admin():
        async def check(ctx):
            return ctx.author.guild_permissions.manage_roles
        return commands.check(check)

    @commands.command(name="role_message")
    @admin()
    async def role_message(self, ctx, title: str, *, description: str):
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x6C3BAA
        )

        view = RoleView({}, 0)
        msg = await ctx.send(embed=embed, view=view)

        self.data[str(msg.id)] = {
            "title": title,
            "description": description,
            "roles": {}
        }
        self.save()

    @commands.command(name="add_button")
    @admin()
    async def add_button(self, ctx, message_id: int, role_id: int, *, label: str):
        mid = str(message_id)
        if mid not in self.data:
            return

        self.data[mid]["roles"][label] = role_id
        self.save()

        msg = await ctx.channel.fetch_message(message_id)
        entry = self.data[mid]

        embed = discord.Embed(
            title=entry["title"],
            description=entry["description"],
            color=0x6C3BAA
        )

        view = RoleView(entry["roles"], message_id)
        await msg.edit(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))