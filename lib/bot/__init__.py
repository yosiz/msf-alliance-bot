import asyncio
import os
from glob import glob

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord import DMChannel
from discord import Message
from discord.errors import Forbidden
from discord.ext.commands import Bot as BotBase, BotMissingPermissions, MissingPermissions
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown
from discord.ext.commands import Context, when_mentioned_or

from ..db import db

OWNER_IDS = []
BOT_MSG_CHANNEL = 543413299841073154
COGS = [path.split(os.path.sep)[-1][:-3] for path in glob("./lib/cogs/*.py")]
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument)


def get_guild_prefix(message: Message):
    prefix = db.field("SELECT Prefix FROM guilds WHERE GuildID = ?", message.guild.id)
    if prefix:
        return prefix
    else:
        db.execute("INSERT INTO guilds (GuildID,Prefix) VALUES (?, ?)", message.guild.id, "+")
        return "+"


def get_prefix(bot, message: Message):
    return when_mentioned_or(get_guild_prefix(message))(bot, message)


class Ready():
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"Cog '{cog}' is up")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])


class Bot(BotBase):
    def __init__(self):
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        self.scheduler = AsyncIOScheduler()
        self.VERSION = ''
        self.NAME = 'Bot'
        self.TOKEN = ''
        super().__init__(command_prefix=get_prefix, owner_ids=OWNER_IDS)
        self.bot_channel = self.get_channel(BOT_MSG_CHANNEL)
        db.autosave(self.scheduler)

    async def notify(self, msg):
        if self.bot_channel:
            await self.bot_channel.send(msg)
        else:
            print(f"Notify: {msg}")

    def setup(self):
        for cog in COGS:
            print(f"loading cog: {cog}")
            self.load_extension(f"lib.cogs.{cog}")

    def update_db(self):
        db.multiexec("INSERT OR IGNORE INTO guilds (GuildID) VALUES (?)",
                     ((guild.id,) for guild in self.guilds))

        db.multiexec("INSERT OR IGNORE INTO exp (UserID, GuildID) VALUES(?, ?)",
                     ((member.id, member.guild.id) for guild in self.guilds for member in guild.members if
                      not member.bot))

        # remove members that left - not in any guild
        to_remove = []
        stored_members = db.column("SELECT UserID from exp")
        for id_ in stored_members:
            if not any((guild.get_member(id_) for guild in self.guilds)):
                to_remove.append(id_)
        if len(to_remove):
            db.multiexec("DELETE FROM exp WHERE UserID = ?",
                         ((id_ for id_ in to_remove)))

        db.commit()

    def run(self, name, version):
        self.VERSION = version
        self.NAME = name
        self.setup()
        if os.path.exists('./lib/bot/token.0'):
            with open("./lib/bot/token.0", "r", encoding="utf-8") as tkn:
                self.TOKEN = tkn.read()
        else:
            self.TOKEN = os.environ['TOKEN']
        print("running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def rules_reminder(self):
        await self.notify("this is a timed message to remind you the rules")

    async def on_connect(self):
        print("bot connected")

    async def on_disconnect(self):
        print("bot disconnected")

    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("a command error occurred")
        else:
            await self.notify("a command error happened")
        raise

    async def on_command_error(self, ctx, exc):
        if isinstance(exc, IGNORE_EXCEPTIONS):
            pass
        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("one of more of the required arguments is missing")
        elif isinstance(exc, CommandOnCooldown):
            await ctx.send(
                f"Command on {str(exc.cooldown.type).split('.')[-1]} cooldown, try again in {exc.retry_after:,.2f}s.")
        elif isinstance(exc, BotMissingPermissions):
            await ctx.send(str(exc))
        elif isinstance(exc, MissingPermissions):
            await ctx.send(str(exc))
        elif hasattr(exc, "original"):
            # if isinstance(exception.original, HTTPException):
            #     await ctx.send("unable to send message")
            if isinstance(exc.original, Forbidden):
                await ctx.send("no permission to perform the action")
            else:
                raise exc.original
        elif isinstance(exc, ValueError):
            await ctx.send(f"invalid value provided for '{ctx.command.name}' command.")
        else:
            raise exc

    async def on_ready(self):
        if not self.ready:
            self.guild = self.get_guild(543413299841073152)
            self.scheduler.add_job(self.rules_reminder, CronTrigger(day_of_week=0, hour=12, minute=0, second=0))
            self.scheduler.start()
            self.update_db()

            # await channel.send(file=File("./data/images/hedionism_bot.png"))
            while not self.cogs_ready.all_ready():
                await asyncio.sleep(0.1)
            self.ready = True
            await self.notify(f"Bot '{self.NAME}' is online (version: {self.VERSION})")
            print("bot ready")
            await self.get_cog("Log").log_msg(f"{self.VERSION} I'm Alive! servicing {len(self.guilds):,} guild(s).")
            await self.get_cog("Meta").set()

        else:
            print("bot reconnected")

    async def process_commands(self, message):
        ctx: Context = await self.get_context(message, cls=Context)
        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)
            else:
                await ctx.send("bot is not ready to recieved commands yet.")

    async def on_message(self, message: Message):
        if not message.author.bot:  # and message.author != message.guild.me:
            if isinstance(message.channel, DMChannel):
                if len(message.content) < 20:
                    await message.channel.send("Your message should be at least 50 characters long.")
                else:
                    await self.get_cog('Log').log_member_message(message.author.id,
                                                                 title="ModMail",
                                                                 text=message.content)
                    await message.channel.send("Message relayed to moderators")

            else:
                await self.process_commands(message)


bot = Bot()
