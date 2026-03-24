import discord
from discord.ext import commands, tasks
import json
import os
import random
import time

GIVEAWAY_FILE = "data/giveaways.json"

def parse_duration(duration: str):
    unit = duration[-1]
    value = int(duration[:-1])
    if unit == "s":
        return value
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400
    return None

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)
        if not os.path.isfile(GIVEAWAY_FILE):
            with open(GIVEAWAY_FILE, "w") as f:
                json.dump({"counter": 0, "giveaways": {}}, f)
        with open(GIVEAWAY_FILE, "r") as f:
            self.data = json.load(f)
        self.check_giveaways.start()

    def save(self):
        with open(GIVEAWAY_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    @commands.group(name="giveaway", invoke_without_command=True)
    async def giveaway(self, ctx):
        await ctx.send("Subcommands: start, info, reroll")

    @giveaway.command(name="start")
    @commands.has_permissions(administrator=True)
    async def start(self, ctx, channel: discord.TextChannel, duration: str, winners: int, *, prize: str):
        await ctx.message.delete()

        seconds = parse_duration(duration)
        if not seconds:
            return

        self.data["counter"] += 1
        giveaway_id = str(self.data["counter"])

        end_time = int(time.time()) + seconds

        embed = discord.Embed(
            title="🎉 Giveaway 🎉",
            description=f"**ID:** {giveaway_id}\n**Prize:** {prize}\n\nReact with 🎉 to enter!\n\nEnds <t:{end_time}:R>\nWinners: {winners}",
            color=0x6C3BAA
        )
        embed.set_footer(text=f"Hosted by {ctx.author}")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("🎉")

        self.data["giveaways"][giveaway_id] = {
            "message_id": msg.id,
            "channel_id": channel.id,
            "end_time": end_time,
            "winners_count": winners,
            "prize": prize,
            "winners": [],
            "ended": False
        }

        self.save()

    @giveaway.command(name="info")
    async def info(self, ctx, giveaway_id: int):
        giveaway_id = str(giveaway_id)
        data = self.data["giveaways"].get(giveaway_id)
        if not data:
            return await ctx.send("Giveaway not found.")

        channel = self.bot.get_channel(data["channel_id"])
        try:
            msg = await channel.fetch_message(data["message_id"])
        except:
            return await ctx.send("Giveaway message not found.")

        participants = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        participants.append(user.mention)

        embed = discord.Embed(
            title=f"Giveaway Info - ID {giveaway_id}",
            color=0x6C3BAA
        )
        embed.add_field(name="Prize", value=data["prize"], inline=False)
        embed.add_field(name="Winners Needed", value=data["winners_count"], inline=True)
        embed.add_field(name="Ended", value=str(data["ended"]), inline=True)
        embed.add_field(name="Total Entries", value=str(len(participants)), inline=False)

        if participants:
            embed.add_field(name="Participants", value="\n".join(participants[:20]), inline=False)
        else:
            embed.add_field(name="Participants", value="No entries yet.", inline=False)

        if data["winners"]:
            winner_mentions = [f"<@{w}>" for w in data["winners"]]
            embed.add_field(name="Winners", value=", ".join(winner_mentions), inline=False)

        await ctx.send(embed=embed)

    @giveaway.command(name="reroll")
    @commands.has_permissions(administrator=True)
    async def reroll(self, ctx, giveaway_id: int, amount: int):
        giveaway_id = str(giveaway_id)
        data = self.data["giveaways"].get(giveaway_id)
        if not data:
            return await ctx.send("Giveaway not found.")

        channel = self.bot.get_channel(data["channel_id"])
        try:
            msg = await channel.fetch_message(data["message_id"])
        except:
            return await ctx.send("Giveaway message not found.")

        participants = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot and user.id not in data["winners"]:
                        participants.append(user)

        if not participants:
            return await ctx.send("No eligible users to reroll.")

        selected = random.sample(participants, min(len(participants), amount))

        for user in selected:
            data["winners"].append(user.id)

        self.save()

        winner_mentions = ", ".join(user.mention for user in selected)
        await channel.send(f"🎉 Reroll Winners (ID {giveaway_id}): {winner_mentions} | Prize: **{data['prize']}**")

    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        now = int(time.time())
        for giveaway_id, data in self.data["giveaways"].items():
            if not data["ended"] and now >= data["end_time"]:
                channel = self.bot.get_channel(data["channel_id"])
                if not channel:
                    continue

                try:
                    msg = await channel.fetch_message(data["message_id"])
                except:
                    continue

                participants = []
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "🎉":
                        async for user in reaction.users():
                            if not user.bot:
                                participants.append(user)

                if participants:
                    winners = random.sample(participants, min(len(participants), data["winners_count"]))
                    data["winners"] = [user.id for user in winners]
                    winner_mentions = ", ".join(user.mention for user in winners)
                    await channel.send(f"🎉 Congratulations {winner_mentions}! You won **{data['prize']}**!")
                else:
                    await channel.send("No valid entries. Giveaway cancelled.")

                embed = msg.embeds[0]
                embed.color = 0x2F3136
                embed.set_footer(text="Giveaway Ended")
                await msg.edit(embed=embed)

                data["ended"] = True
                self.save()

    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Giveaway(bot))