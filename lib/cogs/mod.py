from datetime import datetime, timedelta
from typing import Optional

from asyncio import sleep
from discord import Member, Embed, Message
from discord.ext.commands import Cog, CheckFailure, Context, Greedy
from discord.ext.commands import command, has_permissions, bot_has_permissions
from better_profanity import profanity
import aiofiles
from re import search

cog_name = "mod"

from ..db import db

profanity.load_censor_words_from_file("./data/profanity.txt")


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = None
        self.mute_role = None
        self.profanity_file = "./data/profanity.txt"
        self.no_links_channels = []
        self.no_images_channels = []
        self.url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        self.mute_duration = 1

    async def kick_or_ban_members(self, message: Message, targets, reason, mode="kick", ctx=None):
        mode_msg = "kicked" if mode == "kick" else "banned" if mode == "ban" else mode
        for target in targets:
            if (message.guild.me.top_role.position > target.top_role.position and
                    not target.guild_permissions.administrator):
                if mode == 'kick':
                    await target.kick(reason=reason)
                elif mode == 'ban':
                    await target.ban(reason=reason)
                await self.log.log_action_on_member(message.author,
                                                    target,
                                                    title=f"Member {mode_msg.capitalize()}",
                                                    color=0xDD2222,
                                                    fields=[("Reason", reason, False)])
            elif ctx is not None:
                await ctx.send(f"{target.display_name} could not be {mode_msg}.")

    @command(name="kick")
    @bot_has_permissions(kick_members=True)
    @has_permissions(kick_members=True)
    async def kick_command(self, ctx: Context, targets: Greedy[Member], *,
                           reason: Optional[str] = "No reason provided"):
        if not len(targets):
            await ctx.send("One or more requires arguments is missing.")
        else:
            await self.kick_or_ban_members(ctx.message, targets, reason, mode="kick", ctx=ctx)
            await ctx.send("Action complete.")

    @command(name="ban")
    @bot_has_permissions(ban_members=True)
    @has_permissions(ban_members=True)
    async def ban_command(self, ctx: Context, targets: Greedy[Member], *,
                          reason: Optional[str] = "No reason provided"):
        if not len(targets):
            await ctx.send("One or more requires arguments is missing.")
        else:
            await self.kick_or_ban_members(ctx.message, targets, reason, mode="ban", ctx=ctx)
            await ctx.send("Action complete.")

    # @ban_command.error
    # async def ban_command_error(self, ctx, exc):
    #     if isinstance(exc, CheckFailure):
    #         await ctx.send("Insufficient permissions to perform that task.")

    @bot_has_permissions(manage_messages=True)
    @has_permissions(manage_messages=True)
    @command(name="clear", aliases=["purge"])
    async def clear_command(self, ctx: Context, targets: Greedy[Member], limit: Optional[int] = 1):
        def _check(message: Message):
            # if the message author is a bot - purge the message
            # return ctx.author.bot
            # purge messages for given targets only
            return not len(targets) or message.author in targets

        if 0 < limit <= 100:
            with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit,
                                                  after=datetime.utcnow() - timedelta(days=14),
                                                  check=_check)
                await ctx.send(f"Deleted {len(deleted):,} messages.", delete_after=5)
                await self.log.log_msg(f"{len(deleted)} messages were purged by {ctx.author.display_name}")
        else:
            await ctx.send("The limit provided is not within the acceptable range.")

    async def mute_members(self, message: Message, targets, minutes, reason, ctx: Context = None):
        unmutes = []
        for target in targets:
            if self.mute_role not in target.roles:
                if message.guild.me.top_role.position > target.top_role.position:
                    role_ids = ",".join(str(r.id) for r in target.roles)
                    end_time = datetime.utcnow() + timedelta(minutes=minutes) if minutes else None
                    db.execute("INSERT INTO mutes VALUES (?, ?, ?)",
                               target.id, role_ids, getattr(end_time, "isoformat", lambda: None)())
                    await target.edit(roles=[self.mute_role])
                    await self.log.log_action_on_member(message.author,
                                                        target,
                                                        title="Member Muted",
                                                        color=0xDD2222,
                                                        fields=[("Duration",
                                                                 f"{minutes:,} minutes(s)" if minutes else "Indefinite",
                                                                 False),
                                                                ("Reason", reason, False)])
                    if minutes:
                        unmutes.append(target)
                elif ctx is not None:
                    await ctx.send(f"{target.display_name} could not be muted.")
            elif ctx is not None:
                await ctx.send(f"{target.display_name} is already muted.")
        if len(unmutes):
            await sleep(minutes * 60)
            await self.unmute_members(message.guild, targets)
        return unmutes

    @command(name="mute")
    @bot_has_permissions(manage_roles=True)
    @has_permissions(manage_roles=True, manage_guild=True)
    async def mute_command(self, ctx: Context, targets: Greedy[Member], minutes: Optional[int],
                           *, reason: Optional[str] = "No Reason provided"):
        if not len(targets):
            await ctx.send("One or more requires arguments is missing.")
        else:
            await self.mute_members(ctx.message, targets, minutes, reason, ctx)
            await ctx.send("Action Complete.")


    async def unmute_members(self, guild, targets, *, reason="Muted time expired.", author=None, ctx: Context = None):
        for target in targets:
            if self.mute_role in target.roles:
                role_ids = db.field("SELECT RoleIDs FROM mutes WHERE UserID=?", target.id)
                if len(role_ids):
                    roles = [guild.get_role(int(id_)) for id_ in role_ids.split(",") if len(id_)]
                    await target.edit(roles=roles)
                    db.execute("DELETE FROM mutes WHERE UserID = ?", target.id)
                else:
                    await target.edit(roles=list(set(target.roles) - {self.mute_role}))

                await self.log.log_action_on_member(author or guild.me,
                                                    target,
                                                    title="Member Unmuted",
                                                    color=0xDD2222,
                                                    fields=[("Reason", reason, False)])
            elif ctx is not None:
                await ctx.send(f"{target.display_name} is not muted.")

    @command(name="unmute")
    @bot_has_permissions(manage_roles=True)
    @has_permissions(manage_roles=True, manage_guild=True)
    async def unmute_command(self, ctx: Context, targets: Greedy[Member],
                             *, reason: Optional[str] = "No Reason provided"):
        if not len(targets):
            await ctx.send("One or more requires arguments is missing.")
        else:
            await self.unmute_members(ctx.guild, targets, reason=reason, author=ctx.message.author, ctx=ctx)

    @command(name="addprofanity", aliases=["addswears", "addcurses"])
    @has_permissions(manage_guild=True)
    async def add_profanity(self, ctx: Context, *words):
        update_count = await self.update_profanity("add", *words)
        await ctx.send(f"Action complete. {update_count} Word(s) added")

    @command(name="delprofanity", aliases=["delswears", "delcurses"])
    @has_permissions(manage_guild=True)
    async def remove_profanity(self, ctx: Context, *words):
        update_count = await self.update_profanity("remove", *words)
        await ctx.send(f"Action complete. {update_count} Word(s) removed")

    async def update_profanity(self, mode, *words):
        async with aiofiles.open(self.profanity_file, "r", encoding="utf-8") as afp:
            stored = [w.strip() for w in await afp.readlines()]
        if mode == 'add':
            new_list = [w for w in words if w not in stored]
            if len(new_list):
                async with aiofiles.open(self.profanity_file, "a+", encoding="utf-8") as afp:
                    await afp.write("".join([f"{w}\n" for w in new_list]))
                profanity.add_censor_words(new_list)
            return len(new_list)
        elif mode == "remove":
            new_list = [w for w in stored if w not in words]
            async with aiofiles.open(self.profanity_file, "w", encoding="utf-8") as afp:
                await afp.write("".join([f"{w}\n" for w in new_list]))
            await self.load_profanity(new_list)
            return len(new_list)

    async def load_profanity(self, words=None):
        if words is None:
            profanity.load_censor_words_from_file(self.profanity_file)
        else:
            profanity.load_censor_words(words)
    @mute_command.error
    @kick_command.error
    @ban_command.error
    @clear_command.error
    async def generic_command_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send(f"Insufficient permissions to run the '{ctx.command.name}' command.")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.log = self.bot.get_cog('Log')
            self.mute_role = self.bot.guild.get_role(731364314824441878)

            unmutes = []
            active_mutes = db.records("SELECT UserID,EndTime FROM mutes")
            for userid, endtime in active_mutes:
                if endtime and datetime.utcnow() > (et := datetime.fromisoformat(endtime)):
                    unmutes.append(self.bot.guild.get_member(userid))
                else:
                    self.bot.scheduler.add_job(self.unmute_members, "date", run_date=et,
                                               args=[self.bot.guild,
                                                     [self.bot.guild.get_member(userid)]])
            if len(unmutes):
                await self.unmute_members(self.bot.guild, unmutes)
            self.no_links_channels.append(730654420647411734)
            self.no_images_channels.append(731449573171658883)
            self.bot.cogs_ready.ready_up(cog_name)

    @Cog.listener()
    async def on_message(self, message: Message):
        def _check(m: Message):
            return (m.author == message.author
                    and len(m.mentions)
                    and (datetime.utcnow() - m.created_at).seconds < 60)

        if not message.author.bot:
            # SPAM DETECTION - this method recommended for single server only, otherwise cpu+mem intensive
            if len(list(filter(lambda m: _check(m), self.bot.cached_messages))) >= 3:
                await message.channel.send(f"Mention span Detected ! \n" +
                                           f"{message.author.mention} is muted for {self.mute_duration} minute(s).")
                await self.mute_members(message, [message.author], self.mute_duration, "For spamming @mentions")
                # await self.kick_or_ban_members(message, [message.author], "For spamming @mentions", mode="kick")

            elif profanity.contains_profanity(message.content) and not message.content.find("delprofanity") == 1:
                await message.delete()
                await message.channel.send("You can't use this word here", delete_after=10)
            elif message.channel.id in self.no_links_channels \
                    and search(self.url_regex, message.content) \
                    and not message.author.guild_permissions.manage_guild:
                await message.delete()
                await message.channel.send("You can't send links to this channel", delete_after=10)
            elif message.channel.id in self.no_images_channels \
                    and any([hasattr(a, "width") for a in message.attachments]) \
                    and not message.author.guild_permissions.manage_guild:
                await message.delete()
                await message.channel.send("You cant post images in this channel", delete_after=10)


def setup(bot):
    bot.add_cog(Mod(bot))
