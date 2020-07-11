from discord import Member, Forbidden
from discord.ext.commands import Cog, command, Context
from ..db import db

name = "members"


class Members(Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_welcome_channel(self):
        print("guild_id", self.bot.guild.id)
        ch_id = db.field("SELECT WelcomeChannel FROM guilds WHERE GuildID = ?", self.bot.guild.id)
        print(ch_id)
        if not ch_id:
            for channel in self.bot.get_all_channels():
                if channel.name.lower() == "welcome":
                    ch_id = channel.id
                    db.execute("UPDATE guilds SET WelcomeChannel = ? WHERE GuildID = ?", ch_id, self.bot.guild.id)
        if not ch_id:
            ch_id = 730654420647411734
        return self.bot.get_channel(ch_id)

    @command(name='welcome')
    async def greet(self, ctx: Context, member: Member):
        await self.get_welcome_channel().send(f"Hi {member.mention}, welcome to {member.guild.name}.")

        await ctx.send(f"Welcome to our team {member.mention}")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(name)

    @Cog.listener()
    async def on_member_join(self, member: Member):
        db.execute("INSERT INTO exp (UserID) VALUES (?)", member.id)
        await self.get_welcome_channel().send(f"Hi {member.mention}, welcome to **{member.guild.name}**.")
        # dm
        try:
            await member.send(f"welcome to {member.guild.name}")
        except Forbidden:
            pass
        # give role
        # TODO get new member roles from db
        if self.bot.guild.me.guild_permissions.manage_roles:
            await member.add_roles(member.guild.get_role(560179541293662218))
        # or, this is faster
        # await member.edit(roles=[*member.roles, *[member.guild.get_role(id_) for id_ in (560179541293662218,730682817461092403)]])

    async def on_member_remove(self, member: Member):
        db.execute("DELETE FROM exp WHERE UserID = ?", member.id)
        await self.get_welcome_channel().send(f"{member.display_name} has left **{member.guild.name}**.")


def setup(bot):
    bot.add_cog(Members(bot))
