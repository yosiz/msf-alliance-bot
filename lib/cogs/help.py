from typing import Optional

from discord import Embed
from discord.utils import get

from discord.ext.commands import Cog, command, Context
from discord.ext.menus import MenuPages, ListPageSource

name = "help"


def syntax(cmd: command):
    cmd_and_aliases = "|".join([str(cmd), *cmd.aliases])
    params = []
    for key, value in cmd.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(value) else f"<{key}>")
    params = " ".join(params)
    return f"```{cmd_and_aliases} {params}```"


class HelpMenu(ListPageSource):
    def __init__(self, ctx: Context, data):
        self.ctx = ctx
        super().__init__(data, per_page=3)

    async def write_page(self, menu, fields=[]):
        offset = (menu.current_page * self.per_page)
        len_data = len(self.entries)

        embed = Embed(title="Help",
                      description="Welcome to the Help page",
                      color=self.ctx.author.color)
        embed.set_thumbnail(url=self.ctx.guild.me.avatar_url)
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset + self.per_page - 1):,} of {len_data:,} commands.")
        for cmd_name, value in fields:
            embed.add_field(name=cmd_name, value=value, inline=False)
        return embed

    async def format_page(self, menu, entries):
        fields = []
        for entry in entries:
            fields.append((entry.brief or "No description", syntax(entry)))
        return await self.write_page(menu, fields)


class Help(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    async def cmd_help(self, ctx: Context, cmd):
        embed = Embed(title=f"help for `{cmd}`",
                      description=syntax(cmd),
                      color=ctx.author.color)
        embed.add_field(name="Command description", value="command.help")
        await ctx.send(embed=embed)

    @command(name="help")
    async def show_help(self, ctx: Context, cmd: Optional[str]):
        """display help"""
        if cmd is None:
            menu = MenuPages(source=HelpMenu(ctx, list(self.bot.commands)),
                             clear_reactions_after=True,
                             delete_message_after=True,
                             timeout=60.0)
            await menu.start(ctx)
        else:
            if cmnd := get(self.bot.commands, name=cmd):
                await self.cmd_help(ctx, cmnd)
            else:
                await ctx.send("Command does not exist")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(name)
            print(f"{name} Cog ready")


def setup(bot):
    bot.add_cog(Help(bot))
