from datetime import datetime, timedelta

from discord import User, Reaction, RawReactionActionEvent, Role, Message, Embed, NotFound, TextChannel, Emoji
from discord.ext.commands import Cog, command, bot_has_permissions, Context, Greedy, CheckFailure

from ..db import db
from ..db import json_db
import json

cog_name = "reactions"

colors = {
    "❤️": 731625542490783814,  # red
    "💛": 731625689660522556,  # yellow
    "💚": 731625734338248775,  # green
    "💙": 731625764981702716,  # blue
    "💜": 731625799307755660,  # purple
}


def get_number_emoji(num):
    if 0 <= num <= 9:
        return f"{num}\N{COMBINING ENCLOSING KEYCAP}"
    if num == 10:
        return u"\U0001F51F"
    else:
        return "".join([get_number_emoji(x) for x in [int(d) for d in str(num)]])


class Reactions(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = None
        self.roles = {}
        self.reaction_roles = {}
        self.role_reaction = {}
        self.starboard_channel = None
        self.polls = {}

    async def starboard_channel_send(self, *args, **kwagrs):
        if self.starboard_channel:
            return await self.starboard_channel.send(*args, **kwagrs)

    # '"1\\ufe0f\\u20e3"'
    # '"\\ud83d\\udd1f"'
    @command(name="emojiname")
    async def emojiname(self, ctx: Context, emoji):
        if int(emoji) in range(0, 15):
            await ctx.send(get_number_emoji(int(emoji)))
        print(emoji)
        print(json.dumps(emoji))
        await ctx.send(emoji)

    @command(name='createpoll', aliases=['mkpoll'])
    @bot_has_permissions(manage_guild=True)
    async def create_poll(self, ctx: Context, minutes: int, question: str, *options):
        if len(options) > 10:
            await ctx.send("Polls can have up to 10 options.")
        else:
            embed = Embed(title="Poll",
                          description=question,
                          color=ctx.author.color,
                          timestamp=datetime.utcnow())
            fields = [("Options",
                       # "\n".join([f"{get_number_emoji(idx + 1)} {options[idx]}" for idx in range(0, len(options))]),
                       "\n".join([f"{get_number_emoji(idx + 1)} {option}" for idx, option in enumerate(options)]),
                       False),
                      ("Instructions", "React to cast a vote.", False)]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            message = await ctx.send(embed=embed)
            if ctx.guild.id not in self.polls:
                self.polls[ctx.guild.id] = [(message.channel.id, message.id)]
            else:
                self.polls[ctx.guild.id].append((message.channel.id, message.id))
            for emoji in [get_number_emoji(x + 1) for x in range(len(options))]:
                await message.add_reaction(emoji=emoji)
            self.bot.scheduler.add_job(self.complete_poll, "date",
                                       run_date=datetime.now() + timedelta(minutes=minutes),
                                       args=[message.channel.id, message.id])

    async def complete_poll(self, channel_id, message_id):
        message = await self.bot.get_channel(channel_id).fetch_message(message_id)
        most_voted = max(message.reactions, key=lambda r: r.count)
        await message.channel.send(
            f"Poll results: {most_voted.emoji} was the most popular with {most_voted.count - 1} votes")

    @command(name='setstarboard', aliases=['sb', 'set_sb'])
    @bot_has_permissions(manage_guild=True)
    async def set_starboard_channel(self, ctx: Context, channel: TextChannel):
        self.starboard_channel = channel
        db.execute("UPDATE guilds SET StarboardChannel= ? WHERE GuildID = ? ", channel.id, self.bot.guild.id)
        await ctx.send(f"Starboard channel set to {self.starboard_channel}")

    @command(name='unsetsetstarboard', aliases=['unset_sb'])
    @bot_has_permissions(manage_guild=True)
    async def set_starboard_channel(self, ctx: Context):
        self.starboard_channel = None
        db.execute("UPDATE guilds SET StarboardChannel= ? WHERE GuildID = ? ", None, self.bot.guild.id)
        await ctx.send(f"Cleared Starboard channel.")

    @command(name='setreactionrole', aliases=['setrr'])
    @bot_has_permissions(manage_roles=True)
    async def set_reaction_role(self, ctx: Context, message_id: int, roles: Greedy[Role]):
        message = await self.bot.get_channel(ctx.message.channel.id).fetch_message(message_id)
        if len(message.reactions) > len(roles):
            await ctx.send(f"missing {len(message.reactions) - len(roles)} roles")
        else:
            if ctx.guild.id not in self.reaction_roles:
                self.reaction_roles[ctx.guild.id] = {}
                self.role_reaction[ctx.guild.id] = {}
            self.reaction_roles[ctx.guild.id][int(message_id)] = {}
            self.role_reaction[ctx.guild.id][int(message_id)] = {}
            idx = 0
            for reaction in message.reactions:
                self.reaction_roles[ctx.guild.id][int(message_id)][reaction.emoji] = roles[idx]
                self.role_reaction[ctx.guild.id][int(message_id)][roles[idx].id] = reaction.emoji
                idx += 1
            await ctx.send(f"set reactionRole message to: {message.content[:20]}")
            # json_db.save_section(ctx.guild.id, "reaction_role", self.reaction_roles[ctx.guild.id])

    # @set_starboard_channel.error
    async def generic_command_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send(f"Insufficient permissions to run the '{ctx.command.name}' command.")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.log = self.log = self.bot.get_cog('Log')
            self.roles = {
                '_': {
                    "❤️": self.bot.guild.get_role(731625542490783814),  # red
                    "💛": self.bot.guild.get_role(731625689660522556),  # yellow
                    "💚": self.bot.guild.get_role(731625734338248775),  # green
                    "💙": self.bot.guild.get_role(731625764981702716),  # blue
                    "💜": self.bot.guild.get_role(731625799307755660),  # purple
                }
            }
            # self.starboard_channel = self.bot.get_channel(731806068296122378)
            ch = db.record("SELECT StarboardChannel from guilds WHERE GuildID = ?", self.bot.guild.id)
            if len(ch):
                self.starboard_channel = self.bot.get_channel(ch[0])
            # else:
            #     self.starboard_channel = self.bot.get_channel(731806068296122378)
            print("GUILD:", self.bot.guild)
            self.bot.cogs_ready.ready_up(cog_name)

    # @Cog.listener()
    # async def on_reaction_add(self, reaction: Reaction, user: User):
    #     print(f"{user.display_name} reacted with {reaction.emoji}")
    #
    # @Cog.listener()
    # async def on_reaction_remove(self, reaction, user):
    #     print(f"{user.display_name} removed their reaction of {reaction.emoji}")

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        # print(f"[RAW] {payload.member.display_name} reacted with {payload.emoji.name}")
        # if self.bot.ready and payload.message_id == self.reaction_message_id.get(payload.guild_id, 0):
        # print(f"[RAW] {payload.member.display_name} reacted with {payload.emoji.name}")
        # role = self.bot.guild.get_role(colors.get(payload.emoji.name))
        if self.bot.ready:
            message: Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if payload.guild_id in self.reaction_roles \
                    and payload.message_id in self.reaction_roles[payload.guild_id]:
                role = self.reaction_roles[payload.guild_id][payload.message_id][payload.emoji.name]
                # TODO for allowing single role, method1 - remove reaction immediately after selected
                # remove previous roles
                current_roles = list(
                    filter(lambda r: r in self.reaction_roles[payload.guild_id][payload.message_id].values(),
                           payload.member.roles))
                print("member_roles:", current_roles)
                # await payload.member.remove_roles(*current_roles, reason="Selected another")
                # remove previous role reactions related to this message
                for r in current_roles:
                    print('check ', r, r.id)
                    if r.id in self.role_reaction[payload.guild_id][int(payload.message_id)]:
                        print("removing reaction:", self.role_reaction[payload.guild_id][int(payload.message_id)][r.id])
                        await message.remove_reaction(
                            self.role_reaction[payload.guild_id][int(payload.message_id)][r.id],
                            payload.member)
                await payload.member.add_roles(role, reason="Role Added By Reaction")
            elif payload.emoji.name == "⭐" and self.starboard_channel:
                if not message.author.bot and payload.member.id != message.author.id:
                    msg_id, stars = db.record("SELECT StarMessageID,Stars FROM starboard WHERE RootMessageID = ?",
                                              message.id) or (None, 0)
                    embed = Embed(title="Starred Message",
                                  color=message.author.color,
                                  timestamp=datetime.utcnow()
                                  )
                    fields = [("Author", message.author.mention, False),
                              ("Content", message.content or None, False),
                              ("Stars", stars + 1, False)]

                    for name, value, inline in fields:
                        embed.add_field(name=name, value=value, inline=inline)
                    for a in message.attachments:
                        if hasattr(a, "width"):
                            embed.set_image(url=a.url)
                        else:
                            pass
                    if not stars:
                        star_message = await self.starboard_channel_send(embed=embed)
                        db.execute("INSERT INTO starboard (RootMessageID,StarMessageID) VALUES (?, ?)",
                                   message.id, star_message.id)
                    else:
                        try:
                            star_message = await self.starboard_channel.fetch_message(msg_id)
                            await star_message.edit(embed=embed)
                            db.execute("UPDATE starboard SET Stars = Stars + 1 WHERE RootMessageID = ?",
                                       message.id)
                        except NotFound:
                            print(f"message {msg_id} not found.")
                else:
                    # if wrong, remove the *
                    await message.remove_reaction(payload.emoji, payload.member)
            elif payload.message_id in (poll[1] for poll in self.polls.get(payload.guild_id, [(None, None)])):
                message: Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                for reaction in message.reactions:
                    if (not payload.member.bot
                            and payload.member in await reaction.users().flatten()
                            and reaction.emoji != payload.emoji.name):
                        await message.remove_reaction(reaction.emoji, payload.member)
                        # break

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):

        # print(f"[RAW] {member.display_name} removed their reaction of {payload.emoji.name} " +
        #       f"on msg {payload.message_id}")
        # if self.bot.ready and payload.message_id == self.reaction_message_id.get(payload.guild_id, 0):
        #     member = self.bot.guild.get_member(payload.user_id)
        #     role = self.bot.guild.get_role(colors.get(payload.emoji.name))
        #     await member.remove_roles(role, reason="Role Removed By Reaction")

        if self.bot.ready \
                and payload.guild_id in self.reaction_roles \
                and payload.message_id in self.reaction_roles[payload.guild_id]:
            member = self.bot.guild.get_member(payload.user_id)
            role = self.reaction_roles[payload.guild_id][payload.message_id][payload.emoji.name]
            await member.remove_roles(role, reason="Role Removed By Reaction")


def setup(bot):
    bot.add_cog(Reactions(bot))
