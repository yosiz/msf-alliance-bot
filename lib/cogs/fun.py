from discord.ext.commands import Cog, command, Context, BadArgument
from random import choice, randint
from discord import Member, Embed
from discord.errors import HTTPException
from typing import Optional
from aiohttp import request
from discord.ext.commands import cooldown, BucketType

name = "fun"


class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="hello", aliases=["hi"], hidden=False)
    async def say_hello(self, ctx: Context):
        await ctx.send(f"{choice(('Hello', 'Hi', 'Hey'))} {ctx.author.mention}")

    @command(name="echo", aliases=["say"], hidden=False)
    @cooldown(1, 15, BucketType.guild)
    async def echo_msg(self, ctx: Context, *, msg):
        await ctx.message.delete()
        await ctx.send(msg)

    @command(name="slap", aliases=["hit"])
    async def slap_member(self, ctx: Context, member: Member, *, reason: Optional[str] = "no reason"):
        await ctx.send(f"{ctx.author.display_name} slapped {member.mention} for {reason}")

    @command(name="dice", aliases=["roll"])
    @cooldown(1, 60, BucketType.user)  # 60 seconds
    async def roll_dice(self, ctx: Context, die_string: str):
        dice, value = (int(term) for term in die_string.split('d'))
        if dice <= 25:
            rolls = [randint(1, value) for i in range(dice)]
            await ctx.send(" + ".join([str(r) for r in rolls]) + f" = {sum(rolls)} ")
        else:
            await ctx.send("too many dice, use less")

    @roll_dice.error
    async def roll_dice_error(self, ctx: Context, exc):
        if isinstance(exc, HTTPException):
            await ctx.send("too many dice rolled, use less")

    @slap_member.error
    async def slap_member_error(self, ctx: Context, exc):
        if isinstance(exc, BadArgument):
            await ctx.send("i cant find that member")

    @command(name="fact")
    @cooldown(3, 60, BucketType.guild)
    async def animal_facts(self, ctx: Context, animal: str):
        animals = ("dog", "cat", "panda", "fox", "bird", "koala")
        if (animal := animal.lower()) in animals:
            url = f"https://some-random-api.ml/facts/{animal}"
            img_url = f"https://some-random-api.ml/img/{'birb' if animal == 'bird' else animal}"

            async with request("GET", img_url, headers={}) as response:
                if response.status == 200:
                    data = await response.json()
                    image_link = data['link']
                else:
                    image_link = None

            async with request("GET", url, headers={}) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = Embed(title=f"{animal.title()} fact",
                                  description=data['fact'],
                                  color=ctx.author.color)
                    if image_link is not None:
                        embed.set_image(url=image_link)
                    # await ctx.send(data["fact"])
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"API returned {response.status} status")
        else:
            await ctx.send(f"available animals: {animals}")

    @Cog.listener()
    async def on_ready(self):
        # await self.bot.bot_channel.send(f"cog ready")
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(name)
            print("fun Cog ready")


def setup(bot):
    bot.add_cog(Fun(bot))
    # bot.scheduler.add_job(...)
