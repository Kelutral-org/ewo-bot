import discord
from discord.ext import commands

class MembersCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name='scream2', aliases=['zawng2'])
    async def hello(self,ctx):
        await ctx.send("SKREEEEEEEE")

def setup(bot):
    bot.add_cog(MembersCog(bot))