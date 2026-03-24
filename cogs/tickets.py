import discord
from discord.ext import commands
import json
import os

PANEL_FILE = "data/ticket_panels.json"
TICKET_FILE = "data/tickets.json"
CATEGORY_NAME = "—————Tickets—————"
USER_LIMIT = 3
STAFF_ROLE_IDS = [1466613609852436492, 1471800024055808030]


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)

        if not os.path.isfile(PANEL_FILE):
            with open(PANEL_FILE, "w") as f:
                json.dump({}, f)

        with open(PANEL_FILE, "r") as f:
            self.panels = json.load(f)

        if not os.path.isfile(TICKET_FILE):
            with open(TICKET_FILE, "w") as f:
                json.dump({"counter": 0, "tickets": {}}, f)

        with open(TICKET_FILE, "r") as f:
            self.tickets = json.load(f)

    def save_panels(self):
        with open(PANEL_FILE, "w") as f:
            json.dump(self.panels, f, indent=4)

    def save_tickets(self):
        with open(TICKET_FILE, "w") as f:
            json.dump(self.tickets, f, indent=4)

    def user_open_tickets(self, user_id: int):
        return sum(
            1
            for t in self.tickets["tickets"].values()
            if t["owner"] == user_id and t["status"] == "open"
        )

    def build_view(self, panel_id: str):
        panel = self.panels.get(panel_id)
        if not panel:
            return None

        view = discord.ui.View(timeout=None)

        for name in panel["buttons"]:
            view.add_item(
                discord.ui.Button(
                    label=name,
                    custom_id=f"ticket:{panel_id}:{name}",
                    style=discord.ButtonStyle.primary,
                )
            )
        return view

    @commands.group(name="ticket", invoke_without_command=True)
    async def ticket(self, ctx):
        await ctx.send("Subcommands available.")

    @ticket.group(name="panel")
    async def panel(self, ctx):
        pass

    @panel.command(name="create")
    @commands.has_permissions(administrator=True)
    async def panel_create(
        self,
        ctx,
        channel: discord.TextChannel,
        panel_id: int,
        title: str,
        *,
        description: str,
    ):
        await ctx.message.delete()

        embed = discord.Embed(title=title, description=description, color=0x6C3BAA)
        msg = await channel.send(embed=embed)

        self.panels[str(panel_id)] = {
            "channel_id": channel.id,
            "message_id": msg.id,
            "title": title,
            "description": description,
            "buttons": {},
        }

        self.save_panels()
        await ctx.send(f"Panel {panel_id} created.", delete_after=5)

    @panel.command(name="edit")
    @commands.has_permissions(administrator=True)
    async def panel_edit(
        self,
        ctx,
        panel_id: int,
        title: str = None,
        *,
        description: str = None,
    ):
        await ctx.message.delete()

        panel = self.panels.get(str(panel_id))
        if not panel:
            return await ctx.send("Panel not found.", delete_after=5)

        if title:
            panel["title"] = title
        if description:
            panel["description"] = description

        self.save_panels()

        try:
            channel = self.bot.get_channel(panel["channel_id"])
            msg = await channel.fetch_message(panel["message_id"])

            embed = discord.Embed(
                title=panel["title"],
                description=panel["description"],
                color=0x6C3BAA,
            )

            await msg.edit(embed=embed, view=self.build_view(str(panel_id)))
        except:
            pass

        await ctx.send("Panel edited.", delete_after=5)

    @panel.command(name="delete")
    @commands.has_permissions(administrator=True)
    async def panel_delete(self, ctx, panel_id: int):
        await ctx.message.delete()

        panel = self.panels.pop(str(panel_id), None)
        if not panel:
            return await ctx.send("Panel not found.", delete_after=5)

        try:
            channel = self.bot.get_channel(panel["channel_id"])
            msg = await channel.fetch_message(panel["message_id"])
            await msg.delete()
        except:
            pass

        self.save_panels()
        await ctx.send("Panel deleted.", delete_after=5)

    @ticket.group(name="button")
    async def button(self, ctx):
        pass

    @button.command(name="add")
    @commands.has_permissions(administrator=True)
    async def button_add(
        self, ctx, panel_id: int, button_name: str, ticket_name: str
    ):
        await ctx.message.delete()

        panel = self.panels.get(str(panel_id))
        if not panel:
            return await ctx.send("Panel not found.", delete_after=5)

        panel["buttons"][button_name] = ticket_name
        self.save_panels()

        channel = self.bot.get_channel(panel["channel_id"])
        msg = await channel.fetch_message(panel["message_id"])
        await msg.edit(view=self.build_view(str(panel_id)))

        await ctx.send("Button added.", delete_after=5)

    @button.command(name="edit")
    @commands.has_permissions(administrator=True)
    async def button_edit(
        self,
        ctx,
        panel_id: int,
        button_name: str,
        new_label: str = None,
        new_ticket: str = None,
    ):
        await ctx.message.delete()

        panel = self.panels.get(str(panel_id))
        if not panel or button_name not in panel["buttons"]:
            return await ctx.send("Button not found.", delete_after=5)

        template = panel["buttons"].pop(button_name)

        if new_ticket:
            template = new_ticket
        if new_label:
            button_name = new_label

        panel["buttons"][button_name] = template
        self.save_panels()

        channel = self.bot.get_channel(panel["channel_id"])
        msg = await channel.fetch_message(panel["message_id"])
        await msg.edit(view=self.build_view(str(panel_id)))

        await ctx.send("Button edited.", delete_after=5)

    @button.command(name="delete")
    @commands.has_permissions(administrator=True)
    async def button_delete(self, ctx, panel_id: int, button_name: str):
        await ctx.message.delete()

        panel = self.panels.get(str(panel_id))
        if not panel or button_name not in panel["buttons"]:
            return await ctx.send("Button not found.", delete_after=5)

        panel["buttons"].pop(button_name)
        self.save_panels()

        channel = self.bot.get_channel(panel["channel_id"])
        msg = await channel.fetch_message(panel["message_id"])
        await msg.edit(view=self.build_view(str(panel_id)))

        await ctx.send("Button deleted.", delete_after=5)

    @ticket.command(name="close")
    async def ticket_close(self, ctx):
        await ctx.message.delete()

        ticket_id = None
        for tid, data in self.tickets["tickets"].items():
            if data["channel_id"] == ctx.channel.id:
                ticket_id = tid
                break

        if not ticket_id:
            return await ctx.send("Not a ticket channel.", delete_after=5)

        self.tickets["tickets"][ticket_id]["status"] = "closed"
        self.save_tickets()
        await ctx.channel.delete()

    @commands.Cog.listener()
    async def on_ready(self):
        for panel_id in self.panels:
            panel = self.panels[panel_id]
            try:
                channel = self.bot.get_channel(panel["channel_id"])
                msg = await channel.fetch_message(panel["message_id"])
                await msg.edit(view=self.build_view(panel_id))
            except:
                continue

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data:
            return

        custom_id = interaction.data.get("custom_id")
        if not custom_id or not custom_id.startswith("ticket:"):
            return

        _, panel_id, button_name = custom_id.split(":", 2)
        panel = self.panels.get(panel_id)
        if not panel:
            return

        if self.user_open_tickets(interaction.user.id) >= USER_LIMIT:
            return await interaction.response.send_message(
                f"You already have {USER_LIMIT} open tickets.", ephemeral=True
            )

        template = panel["buttons"].get(button_name)
        if not template:
            return

        self.tickets["counter"] += 1
        ticket_id = self.tickets["counter"]

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if not category:
            category = await guild.create_category(CATEGORY_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        }

        staff_roles = []
        for rid in STAFF_ROLE_IDS:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                )
                staff_roles.append(role)

        channel_name = template.replace("%ID%", str(ticket_id))
        channel = await guild.create_text_channel(
            channel_name, overwrites=overwrites, category=category
        )

        self.tickets["tickets"][str(ticket_id)] = {
            "channel_id": channel.id,
            "owner": interaction.user.id,
            "status": "open",
        }
        self.save_tickets()

        ping_message = interaction.user.mention
        if staff_roles:
            ping_message += f" {staff_roles[0].mention}"

        await channel.send(ping_message)

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Ticket(bot))