import discord
from discord.ext import commands
import json
import os
import datetime

TAGS_FILE = "data/tags.json"

class Tags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)
        if not os.path.isfile(TAGS_FILE):
            with open(TAGS_FILE, "w") as f:
                json.dump({}, f)
        with open(TAGS_FILE, "r") as f:
            self.tags = json.load(f)

    def save_tags(self):
        with open(TAGS_FILE, "w") as f:
            json.dump(self.tags, f, indent=4)

    @commands.group(name="tag", invoke_without_command=True)
    async def tag(self, ctx, *, name: str):
        guild_id = str(ctx.guild.id)
        tag_name = name.lower()
        if guild_id in self.tags and tag_name in self.tags[guild_id]:
            await ctx.send(self.tags[guild_id][tag_name]["content"])
        else:
            await ctx.send(f"Tag `{name}` does not exist.")

    @tag.command(name="create")
    async def create(self, ctx, name: str, *, content: str):
        guild_id = str(ctx.guild.id)
        tag_name = name.lower()
        self.tags.setdefault(guild_id, {})
        if tag_name in self.tags[guild_id]:
            await ctx.send(f"Tag `{name}` already exists.")
            return
        self.tags[guild_id][tag_name] = {
            "content": content,
            "owner": ctx.author.id,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        self.save_tags()
        await ctx.send(f"Tag `{name}` created with you as owner.")

    @tag.command(name="edit")
    async def edit(self, ctx, name: str, *, content: str):
        guild_id = str(ctx.guild.id)
        tag_name = name.lower()
        if guild_id not in self.tags or tag_name not in self.tags[guild_id]:
            await ctx.send(f"Tag `{name}` does not exist.")
            return
        if self.tags[guild_id][tag_name]["owner"] != ctx.author.id:
            await ctx.send("Only the tag owner can edit this tag.")
            return
        self.tags[guild_id][tag_name]["content"] = content
        self.save_tags()
        await ctx.send(f"Tag `{name}` updated.")

    @tag.command(name="delete")
    async def delete(self, ctx, name: str):
        guild_id = str(ctx.guild.id)
        tag_name = name.lower()
        if guild_id in self.tags and tag_name in self.tags[guild_id]:
            if self.tags[guild_id][tag_name]["owner"] != ctx.author.id:
                await ctx.send("Only the tag owner can delete this tag.")
                return
            del self.tags[guild_id][tag_name]
            self.save_tags()
            await ctx.send(f"Tag `{name}` deleted.")
        else:
            await ctx.send(f"Tag `{name}` does not exist.")

    @tag.command(name="list")
    async def list_tags(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.tags or not self.tags[guild_id]:
            await ctx.send("No tags exist in this server.")
            return
        tag_list = ", ".join(sorted(self.tags[guild_id].keys()))
        await ctx.send(f"Tags in this server: {tag_list}")

    @tag.command(name="transfer")
    async def transfer(self, ctx, name: str, member: discord.Member):
        guild_id = str(ctx.guild.id)
        tag_name = name.lower()
        if guild_id not in self.tags or tag_name not in self.tags[guild_id]:
            await ctx.send(f"Tag `{name}` does not exist.")
            return
        if self.tags[guild_id][tag_name]["owner"] != ctx.author.id:
            await ctx.send("Only the tag owner can transfer this tag.")
            return
        self.tags[guild_id][tag_name]["owner"] = member.id
        self.save_tags()
        await ctx.send(f"Tag `{name}` has been transferred to {member.display_name}.")

    @tag.command(name="raw")
    async def raw(self, ctx, *, name: str):
        guild_id = str(ctx.guild.id)
        tag_name = name.lower()
        if guild_id in self.tags and tag_name in self.tags[guild_id]:
            content = discord.utils.escape_markdown(self.tags[guild_id][tag_name]["content"])
            await ctx.send(f"```\n{content}\n```")
        else:
            await ctx.send(f"Tag `{name}` does not exist.")

    @tag.command(name="info")
    async def info(self, ctx, *, name: str):
        guild_id = str(ctx.guild.id)
        tag_name = name.lower()
        if guild_id in self.tags and tag_name in self.tags[guild_id]:
            tag = self.tags[guild_id][tag_name]
            owner = ctx.guild.get_member(tag["owner"])
            owner_name = owner.display_name if owner else f"User ID {tag['owner']}"
            created_at = datetime.datetime.fromisoformat(tag["created_at"])
            embed = discord.Embed(
                title=f"Tag Info: {name}",
                color=0x6C3BAA
            )
            embed.add_field(name="Owner", value=owner_name, inline=False)
            embed.add_field(name="Created At (UTC)", value=created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Tag `{name}` does not exist.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Tags(bot))