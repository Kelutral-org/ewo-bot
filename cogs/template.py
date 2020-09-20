import discord
from discord.ext import commands
import re
import bot

# Replace RandomCog with something that describes the cog.  E.G. SearchCog for a search engine, sl.
class RandomCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    # commands have this format instead.  For any variables from the main file, use bot.variable.
    @commands.command()
    async def wordgame(self, ctx, *args):
        print('do things')


def setup(bot):
    bot.add_cog(RandomCog(bot))
    print('Added new Cog: ' + str(RandomCog))
