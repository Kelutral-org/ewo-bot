import discord
from discord.ext import commands
import re
import bot

# Replace RandomCog with something that describes the cog.  E.G. SearchCog for a search engine, sl.
class GameCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    # commands have this format instead.  For any variables from the main file, use bot.variable.
    @commands.command(name='wordgame', aliases=['lì\'uyä'])
    async def wordgame(self, ctx, *args):
        print(args)

        wordgame_channels = []

        # Checks for options
        options = list(args[-1])
        for channel in wordgame_channels:
            if re.fullmatch(ctx.channel, channel):
                print(channel)
            else:
                if options == "new":
                    print("new game")


def setup(bot):
    bot.add_cog(GameCog(bot))