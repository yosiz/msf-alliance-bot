from datetime import datetime, timedelta
from discord.ext.commands import Cog, command, Context, CheckFailure, has_permissions
from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType, Embed
from time import time
# for the stats
from platform import python_version
from discord import __version__ as discord_version
from psutil import Process, virtual_memory
from ..db import db

cog_name = "meta"


class Meta(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = None
        self._message = "watching +help | {users:,} users in {guilds:,} servers"
        self.bot.scheduler.add_job(self.set, CronTrigger(second=0))

    @property
    def message(self):
        return self._message.format(users=len(self.bot.users), guilds=len(self.bot.guilds))

    @message.setter
    def message(self, value):
        if value.split(" ")[0] not in ('playing', 'watching', 'listening', 'streaming'):
            raise ValueError("Invalid activity type")
        self._message = value

    async def set(self):
        _type, _name = self.message.split(" ", maxsplit=1)
        await self.bot.change_presence(activity=Activity(
            name=_name,
            type=getattr(ActivityType, _type, ActivityType.watching)
        ))

    @command(name="setactivity", aliases=["set_activity"])
    async def set_activity_command(self, ctx: Context, *, text: str):
        self.message = text
        await self.set()

    @command(name="ping")
    async def ping_cmd(self, ctx):
        start = time()
        message = await ctx.send(f"Pong! DWSP latency: {self.bot.latency * 1000:,.0f}ms")
        end = time()
        await message.edit(content=f"{message.content} Response time: {(end - start) * 1000:,.0f}ms")

    @command(name="stats")
    @has_permissions(manage_guild=True)
    async def stats(self, ctx: Context):
        embed = Embed(title="Bot Stats",
                      color=ctx.author.color,
                      thumbnail=self.bot.user.avatar_url,
                      timestamp=datetime.utcnow()
                      )
        proc = Process()
        with proc.oneshot():
            uptime = timedelta(seconds=time() - proc.create_time())
            cpu_time = timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user)
            mem_total = virtual_memory().total / (1024 ** 2)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total * (mem_total / 100)
        fields = [
            ("Bot version", self.bot.VERSION, True),
            ("Python version", python_version(), True),
            ("discord.py Version", f"{discord_version}", True),
            ("Uptime", f"{uptime}", True),
            ("CPU time", f"{cpu_time}", True),
            ("Memory Usage", f"{mem_usage:,.3f} / {mem_total:,.0f} MiB ({mem_of_total:,.0f}%)", True),
            ("Users", f"{sum((guild.member_count for guild in self.bot.guilds)):,}", True),
        ]
        for cmd_name, value, inline in fields:
            embed.add_field(name=cmd_name, value=value, inline=inline)
        await ctx.send(embed=embed)

    @command(name="shutdown")
    @has_permissions(manage_guild=True)
    async def shutdown(self, ctx):
        await ctx.send("Shutting down...")
        await self.log.log_msg(f"Shutting down upon request from {ctx.author.mention}")
        db.commit()
        self.bot.scheduler.shutdown()
        await self.bot.logout()
        await self.bot.close()

    @set_activity_command.error
    async def generic_command_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send(f"Insufficient permissions to run the '{ctx.command.name}' command.")
        elif isinstance(exc, ValueError):
            await ctx.send(f"invalid value provided for '{ctx.command.name}' command.")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.log = self.log = self.bot.get_cog('Log')
            self.bot.cogs_ready.ready_up(cog_name)


def setup(bot):
    bot.add_cog(Meta(bot))
