from discord.ext.commands import Cog, Context
from discord.ext.commands import command
from discord.ext.commands import CheckFailure, has_permissions

from ..db import db

name = "misc"


class Misc(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="prefix")
    @has_permissions(manage_guild=True)
    async def change_prefix(self, ctx: Context, new: str):
        if len(new) > 5:
            await ctx.send("Prefix cannot be more than 5 characters")
        else:
            db.execute("UPDATE guilds SET Prefix = ? WHERE GuildID = ?", new, ctx.guild.id)
            await ctx.send(f"prefix set to {new}.")

    @change_prefix.error
    async def change_prefix_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send("you need the manage server permission")



    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(name)


def setup(bot):
    bot.add_cog(Misc(bot))
