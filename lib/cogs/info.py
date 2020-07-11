from datetime import datetime
from typing import Optional

from discord import Embed, Member
from discord.ext.commands import Cog, command, Context

cog_name = "info"


class Info(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="userinfo", aliases=["memberinfo", "ui", "mi"])
    async def user_info(self, ctx: Context, target: Optional[Member]):
        target = target or ctx.author
        embed = Embed(title="User Info",
                      description="",
                      color=target.color,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=target.avatar_url)
        # to get the guild/server icon
        # embed.set_thumbnail(url=ctx.guild.icon_url)
        if target.activity:
            activity_name = target.activity.name
            activity_type = str(getattr(target.activity, 'type')).split(".")[-1].title()
        else:
            activity_name = "Nothing"
            activity_type = "Doing"
        fields = [("Name", str(target), False),
                  ("ID", target.id, True),
                  ("Bot?", target.bot, True),
                  ("Top Role", target.top_role.mention, True),
                  ("Status", str(target.status).title(), True),
                  ("Activity", f"{activity_type} {activity_name}", True),
                  ("Boosted", bool(target.premium_since), True),
                  ("Created at", target.created_at.strftime("%d/%m/%Y %H:%M:%S"), False),
                  ("Joined at", target.joined_at.strftime("%d/%m/%Y %H:%M:%S"), False),
                  ]
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        await ctx.send(embed=embed)

    @command(name="serverinfo", aliases=["si", "gi"])
    async def server_info(self, ctx: Context):
        embed = Embed(title="Server Info",
                      description="",
                      color=ctx.guild.owner.color,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=ctx.guild.icon_url)

        statuses = [
            len(list(filter(lambda m: str(m.status) == "online", ctx.guild.members))),
            len(list(filter(lambda m: str(m.status) == "idle", ctx.guild.members))),
            len(list(filter(lambda m: str(m.status) == "dnd", ctx.guild.members))),
            len(list(filter(lambda m: str(m.status) == "offline", ctx.guild.members)))
        ]
        fields = [
            ("Name", ctx.guild.name, False),
            ("ID", ctx.guild.id, True),
            ("Owner", ctx.guild.owner, True),
            ("Region", ctx.guild.region, True),
            ("Created at", ctx.guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), False),
            ("Members", len(ctx.guild.members), True),
            ("Humans", len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
            ("Bots", len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
            # ("Banned Members", len(await ctx.guild.bans()), True),
            ("Statuses",
             f":green_circle:{statuses[0]} :orange_circle:{statuses[1]} :red_circle:{statuses[2]} :white_circle:{statuses[3]}",
             False),
            ("Text Channels", len(ctx.guild.text_channels), True),
            ("Voice Channels", len(ctx.guild.voice_channels), True),
            ("Categories", len(ctx.guild.categories), True),
            ("Premium Tier", ctx.guild.premium_tier, True),
            ("Premium Subs", ctx.guild.premium_subscription_count, True),
            ("Roles", len(ctx.guild.roles), True),
            ("Invites", len(await ctx.guild.invites()), True),
            ("\u200b", "\u200b", True),
        ]
        if self.bot.guild.me.guild_permissions.ban_members:
            fields.insert(8, ("Banned Members", len(await ctx.guild.bans()), True))
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        await ctx.send(embed=embed)

    # ctx.guild.premium_tier
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(cog_name)


def setup(bot):
    bot.add_cog(Info(bot))
