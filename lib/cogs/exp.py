from typing import Optional

from discord import Message, Member, Embed
from discord.ext.commands import Cog, command, Context
from discord.ext.menus import MenuPages, ListPageSource

from ..db import db
from datetime import datetime, timedelta
from random import randint

cog_name = "exp"


class LeaderboardMenu(ListPageSource):
    def __init__(self, ctx: Context, data):
        self.ctx = ctx
        super().__init__(data, per_page=2)

    async def write_page(self, menu, offset, fields=[]):
        len_data = len(self.entries)

        embed = Embed(title="XP Leaderboard",
                      color=self.ctx.author.color)
        embed.set_thumbnail(url=self.ctx.guild.icon_url)
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset + self.per_page - 1):,} of {len_data:,} members.")
        for cmd_name, value in fields:
            embed.add_field(name=cmd_name, value=value, inline=False)
        return embed

    async def format_page(self, menu, entries):
        offset = (menu.current_page * self.per_page) + 1
        fields = []
        table = ("\n".join(
            f"{idx + offset}. {self.ctx.guild.get_member(entry[0]).display_name} (XP:{entry[1]} | Level: {entry[2]})"
            for idx, entry in enumerate(entries)))
        fields.append(("Ranks", table))

        return await self.write_page(menu, offset, fields)


class Exp(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = None

    async def process_xp(self, message: Message):
        xp, lvl, xplock = db.record("SELECT XP,Level,XPLock FROM exp WHERE UserID = ?", message.author.id)
        if xp >= 0:
            if datetime.fromisoformat(xplock) < datetime.utcnow():
                await self.add_xp(message, xp, lvl)

    async def add_xp(self, message, xp, lvl):
        xp_to_add = randint(10, 20)

        if (new_lvl := int(((xp + xp_to_add) // 42) ** 0.55)) > lvl:
            await message.channel.send(f"{message.author.mention} has reached level {new_lvl}. Congrats.")
        db.execute(f"UPDATE exp SET XP = XP + ?, Level = ?,XPLock = ? WHERE UserID =?",
                   xp_to_add,
                   new_lvl,
                   (datetime.utcnow() + timedelta(seconds=60)).isoformat(),
                   message.author.id)

    @command(name="level", aliases=["rank", "xp"])
    async def display_level(self, ctx: Context, target: Optional[Member]):
        target = target or ctx.author
        if target.bot:
            await ctx.send("bots have no level or rank, nor would it gain any xp :).")
        else:
            xp, lvl = db.record("SELECT XP,Level FROM exp WHERE UserID = ?", target.id) or (None, None)
            if lvl:
                # get rank
                ids = db.column("SELECT UserID FROM exp ORDER BY XP DESC")

                await ctx.send(f"{target.display_name} is on level {lvl} with {xp}xp"
                               f" and rank {ids.index(target.id) + 1} of {len(ids)}.")
            else:
                await ctx.send("that member does not have a level or xp.")

    @command(name="leaderboard", aliases=["lb"])
    async def display_leaderboard(self, ctx: Context):
        records = db.records("SELECT UserID, XP, Level FROM exp WHERE GuildID = ? ORDER BY XP DESC ",
                             ctx.guild.id)
        menu = MenuPages(source=LeaderboardMenu(ctx, records),
                         clear_reactions_after=True, timeout=60.0)
        await menu.start(ctx)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.log = self.log = self.bot.get_cog('Log')
            self.bot.cogs_ready.ready_up(cog_name)

    @Cog.listener()
    async def on_message(self, message: Message):
        if not message.author.bot:
            await self.process_xp(message)


def setup(bot):
    bot.add_cog(Exp(bot))
