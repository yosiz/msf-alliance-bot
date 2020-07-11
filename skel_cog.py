from discord.ext.commands import Cog, command

name = "cog"


class SkelCog(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(name)


def setup(bot):
    bot.add_cog(SkelCog(bot))
