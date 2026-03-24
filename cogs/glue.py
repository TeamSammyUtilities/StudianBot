import discord
from discord.ext import commands
import json
import os
import asyncio

GLUE_FILE = "data/glue.json"

class Glue(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)
        if not os.path.isfile(GLUE_FILE):
            with open(GLUE_FILE, "w") as f:
                json.dump({}, f)
        with open(GLUE_FILE, "r") as f:
            self.data = json.load(f)
        self.cooldowns = {}

    def save(self):
        with open(GLUE_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    async def repost_sticky(self, channel: discord.TextChannel):
        cid = str(channel.id)
        if cid not in self.data:
            return
        entries = self.data[cid]
        new_entries = []
        for entry in entries:
            try:
                old_id = entry.get("message_id")
                if old_id:
                    try:
                        old_msg = await channel.fetch_message(old_id)
                        await old_msg.delete()
                    except:
                        pass
                if entry["type"] == "text":
                    msg = await channel.send(entry["content"])
                else:
                    embed = discord.Embed(title=entry["title"], description=entry["description"], color=0x6C3BAA)
                    msg = await channel.send(embed=embed)
                entry["message_id"] = msg.id
                new_entries.append(entry)
            except discord.Forbidden:
                continue
        self.data[cid] = new_entries
        self.save()

    @commands.command(name="glue")
    @commands.has_permissions(administrator=True)
    async def glue(self, ctx, channel: discord.TextChannel, *, content: str):
        await ctx.message.delete()
        msg = await channel.send(content)
        cid = str(channel.id)
        if cid not in self.data:
            self.data[cid] = []
        self.data[cid].append({"message_id": msg.id, "type": "text", "content": content})
        self.save()
        await ctx.send(f"Sticky message created in {channel.mention}", delete_after=5)

    @commands.command(name="glue-embed")
    @commands.has_permissions(administrator=True)
    async def glue_embed(self, ctx, channel: discord.TextChannel, title: str, *, description: str):
        await ctx.message.delete()
        embed = discord.Embed(title=title, description=description, color=0x6C3BAA)
        msg = await channel.send(embed=embed)
        cid = str(channel.id)
        if cid not in self.data:
            self.data[cid] = []
        self.data[cid].append({"message_id": msg.id, "type": "embed", "title": title, "description": description})
        self.save()
        await ctx.send(f"Sticky embed created in {channel.mention}", delete_after=5)

    @commands.command(name="unglue")
    @commands.has_permissions(administrator=True)
    async def unglue(self, ctx, channel: discord.TextChannel):
        await ctx.message.delete()
        cid = str(channel.id)
        if cid not in self.data or not self.data[cid]:
            return await ctx.send("No sticky messages found for that channel.", delete_after=5)
        for entry in self.data[cid]:
            try:
                msg = await channel.fetch_message(entry["message_id"])
                await msg.delete()
            except:
                pass
        self.data.pop(cid)
        self.save()
        await ctx.send(f"Sticky messages removed from {channel.mention}", delete_after=5)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        cid = str(message.channel.id)
        if cid in self.data:
            for i, entry in enumerate(self.data[cid]):
                if entry["message_id"] == message.id:
                    await asyncio.sleep(0.5)
                    await self.repost_sticky(message.channel)
                    break

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        cid = str(message.channel.id)
        if cid not in self.data:
            return
        if message.author == self.bot.user:
            return
        now = asyncio.get_event_loop().time()
        last = self.cooldowns.get(cid, 0)
        if now - last < 2:
            return
        self.cooldowns[cid] = now
        await asyncio.sleep(1)
        await self.repost_sticky(message.channel)

async def setup(bot: commands.Bot):
    await bot.add_cog(Glue(bot))