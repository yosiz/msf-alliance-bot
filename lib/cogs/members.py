from discord import Member, Forbidden, TextChannel, Role
from discord.ext.commands import Cog, command, Context, has_permissions, Greedy
from ..db import db

name = "members"


class Members(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel: TextChannel = None
        self.default_roles = []

    def _set_welcome_channel(self):
        ch_id = db.field("SELECT WelcomeChannel FROM guilds WHERE GuildID = ?", self.bot.guild.id)
        if not ch_id:
            for channel in self.bot.get_all_channels():
                if channel.name.lower() == "welcome":
                    ch_id = channel.id
                    db.execute("UPDATE guilds SET WelcomeChannel = ? WHERE GuildID = ?", ch_id, self.bot.guild.id)
        self.welcome_channel = self.bot.get_channel(ch_id)

    def _set_default_roles(self):
        roles_ = db.field("SELECT DefaultMemberRoles FROM guilds WHERE GuildID = ?", self.bot.guild.id)
        if roles_:
            self.default_roles = [self.bot.guild.get_role(int(r)) for r in roles_.split(",")]

    async def welcome_channel_send(self, message_content=None, embed=None):
        if self.welcome_channel:
            await self.welcome_channel.send(message_content, embed=embed)

    @command(name="setdefaultroles", aliases=['set_def_roles'])
    @has_permissions(manage_guild=True)
    async def set_default_roles(self, ctx: Context, roles: Greedy[Role]):
        self.default_roles = roles
        db.execute("UPDATE guilds SET DefaultMemberRoles = ? WHERE GuildID = ?",
                   ",".join([str(r.id) for r in roles]),
                   self.bot.guild.id)
        await ctx.send("Default member roles set.")

    @command(name='welcome', aliases=["greet"])
    async def greet(self, ctx: Context, member: Member):
        await ctx.message.delete()
        await ctx.send(f"Welcome to our team {member.mention}. Please respect the rules.")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self._set_welcome_channel()
            self._set_default_roles()
            self.bot.cogs_ready.ready_up(name)

    @Cog.listener()
    async def on_member_join(self, member: Member):
        db.execute("INSERT INTO exp (UserID) VALUES (?)", member.id)
        await self.welcome_channel_send(f"Hi {member.mention}, welcome to **{member.guild.name}**. "
                                        f"you are the member number {len(member.guild.members)}.")
        # dm
        try:
            await member.send(f"welcome to {member.guild.name}")
        except Forbidden:
            pass
        # give role
        # TODO get new member roles from db
        if self.bot.guild.me.guild_permissions.manage_roles:
            await member.add_roles(*self.default_roles)
        # or, this is faster
        # await member.edit(roles=[*member.roles, *[member.guild.get_role(id_) for id_ in (560179541293662218,730682817461092403)]])

    async def on_member_remove(self, member: Member):
        db.execute("DELETE FROM exp WHERE UserID = ?", member.id)
        await self.get_welcome_channel().send(f"{member.display_name} has left **{member.guild.name}**.")


def setup(bot):
    bot.add_cog(Members(bot))
