from discord.ext.commands import Cog, command, Context

cog_name = "cog"


class SkelCog(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = None

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.log = self.log = self.bot.get_cog('Log')
            self.bot.cogs_ready.ready_up(cog_name)


def setup(bot):
    bot.add_cog(SkelCog(bot))
