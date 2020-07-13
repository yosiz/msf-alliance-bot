from datetime import datetime

from discord import Embed, Member, Message
from discord.message import Attachment
from discord.ext.commands import Cog, command

cog_name = "log"


def build_bfa_fields(before, after,
                     before_label=None, after_label=None, inline=False):
    return [(before_label or "Before", before, inline),
            (after_label or "After", after, inline)]


class Log(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None

    async def log_msg(self, msg=None, embed=None):
        if embed:
            await self.log_channel.send(embed=embed)
        if msg:
            await self.log_channel.send(msg)

    async def log_action_on_member(self, author: Member, member: Member, title, color=None, description=None,
                                   thumbnail=None, fields=None):
        embed = Embed(title=title,
                      description=description,
                      color=color or member.color,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=thumbnail or member.avatar_url)
        if fields is None:
            fields = []
        fields.insert(0, ("Actioned By", author.display_name, False))
        fields.insert(0, ("Member", member.display_name, False))
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        await self.log_channel.send(embed=embed)

    async def log_action(self, title, member_id, color=None, description=None, thumbnail=None, fields=None):
        member: Member = self.log_channel.guild.get_member(member_id)
        embed = Embed(title=title,
                      description=description,
                      color=color or member.color,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=thumbnail or member.avatar_url)
        if fields is not None:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        await self.log_channel.send(embed=embed)

    async def log_member_message(self, member_id, title, text):
        member = self.bot.guild.get_member(member_id)
        embed = Embed(title=title,
                      color=member.color,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=member.avatar_url)
        fields = [("Member", member.display_name, False),
                  ("Message", text, False)]
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        await self.log_channel.send(embed=embed)

    def create_member_embed(self, member, title, color=None, description=None, thumbnail=None, fields=None):
        descr = description or f"member: ***{member.display_name}***"
        embed = Embed(title=title,
                      description=descr,
                      color=color or member.color,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=thumbnail or member.avatar_url)
        if fields is not None:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        return embed

    def create_log_embed(self, title, member_id, color=None, description=None, thumbnail=None, fields=None):
        member: Member = self.log_channel.guild.get_member(member_id)
        embed = Embed(title=title,
                      description=f"member: ***{member.display_name}***\n" + (description or ""),
                      color=color or member.color,
                      timestamp=datetime.utcnow())

        embed.set_thumbnail(url=thumbnail or self.bot.guild.me.avatar_url)
        if fields is not None:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        return embed

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.log_channel = self.bot.get_channel(730867749357879398)
            self.bot.cogs_ready.ready_up(cog_name)

    @Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar_url != after.avatar_url:
            embed = self.create_log_embed("Avatar change",
                                          after.id,
                                          color=after.color,
                                          thumbnail=before.avatar_url)
            embed.set_image(url=after.avatar_url)
            await self.log_channel.send(Embed=embed)
        if before.name != after.name:
            embed = self.create_log_embed("Username Update",
                                          after.id,
                                          color=after.color,
                                          fields=build_bfa_fields(before.name,
                                                                  after.name,
                                                                  inline=True))
            await self.log_channel.send(embed=embed)
        if before.discriminator != after.discriminator:
            embed = self.create_log_embed("Discriminator change",
                                          after.id,
                                          fields=build_bfa_fields(before.discriminator,
                                                                  after.discriminator,
                                                                  inline=True))
            await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_member_update(self, before, after):
        if before.display_name is not after.display_name:
            embed = self.create_log_embed("Nickname Update",
                                          after.id,
                                          color=after.color,
                                          fields=build_bfa_fields(before.display_name,
                                                                  after.display_name,
                                                                  inline=True))
            await self.log_channel.send(embed=embed)
        if before.roles != after.roles:
            broles = [r.mention for r in before.roles]
            aroles = [r.mention for r in after.roles]
            added = set(aroles) - set(broles) or set('---')
            removed = set(broles) - set(aroles) or set('---')

            embed = self.create_log_embed("Roles Update",
                                          after.id,
                                          color=after.color,
                                          fields=build_bfa_fields(', '.join(added),
                                                                  ','.join(removed),
                                                                  after_label="Removed",
                                                                  before_label="Added"))
            await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.author.bot:
            if before.content != after.content:
                embed = self.create_log_embed("Message Edit",
                                              after.author.id,
                                              color=after.author.color,
                                              fields=build_bfa_fields(before.content,
                                                                      after.content))
                await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_message_delete(self, message: Message):
        if not message.author.bot:
            fields = []
            if message.content and len(message.content):
                fields.append(("Message Content", message.content, False))
            if len(message.attachments):
                images = []
                files = []
                for a in message.attachments:
                    if hasattr(a, "width"):
                        images.append(f"{a.filename} ({a.width}x{a.height})")
                    else:
                        files.append(f"{a.filename} ({a.size:,}bytes)")
                if len(images):
                    fields.append(("Images", "\n".join(images), False))
                if len(files):
                    fields.append(("Files", "\n".join(files), False))
            await self.log_action(title="Message Deleted",
                                  member_id=message.author.id,
                                  fields=fields)


def setup(bot):
    bot.add_cog(Log(bot))
