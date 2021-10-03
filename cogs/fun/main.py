import json
import random

import disnake
from disnake.ext import commands

import bot

# Open swear_database
with open("cogs/fun/swears.txt", encoding='utf-8') as f:
    swears = []
    for line in f:
        swears.append(line.strip())

# Open search_database
with open("cogs/fun/word_database.json", encoding='utf-8') as f:
    search_database = json.load(f)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Generate random Na'vi swear
    @staticmethod
    async def random_swear():
        # Choose random word from swears and add exclamation mark
        word = random.choice(swears) + '!'
        # Return word
        return word

    # Sarcasm
    @commands.slash_command(name="sarcasm", description="thIs IS a saRcAsTIC DEsCRipTioN.", default_permission=True, guild_ids=bot.test_guilds)
    async def sarcasm(self, inter, string: str):
        display = ""
        for letter in string:
            caps = random.choice([True, False])
            if caps:
                display += letter.upper()
            else:
                display += letter.lower()

        await inter.response.send_message(display)

    # Boop
    @commands.slash_command(name="boop", description="Boop me I'm into it.", default_permission=True, guild_ids=bot.test_guilds)
    async def boop(self, inter):
        await inter.response.send_message('*' + bot.lang.get(str(inter.guild_id)).get('boop') + '*')

    # Scream command
    @commands.slash_command(name="scream", description="Make me scream. One number = one 'E'.", default_permission=True, guild_ids=bot.test_guilds)
    async def scream(self, inter, length: int):

        # Base string
        msg = "SKR"

        # If length is bigger than 100, set it to 100
        if length > 100:
            length = 100

        # While length is greater than zero, add an 'E' to the end of the string and subtract 1 from length
        while length > 0:
            msg += "E"
            length -= 1

        # Send the msg
        await inter.response.send_message(msg)

    # Swear command
    @commands.slash_command(name="swear", description="Do you feel like swearing? Keep yourself clean, I can do it for you.", default_permission=True, guild_ids=bot.test_guilds)
    async def swear(self, inter):

        # Generate random swear
        random_swear = await self.random_swear()

        # Send the swear
        await inter.response.send_message(random_swear)

    # Say command
    @commands.slash_command(name="say", description="Makes me speak for you.", default_permission=True, guild_ids=bot.test_guilds)
    async def say(self, inter, msg: str):

        # Send the message
        await inter.response.send_message(msg)


# Set up cog
def setup(bot):
    # Add the cog
    bot.add_cog(Fun(bot))
    # Print some info
    print('Added new Cog: ' + str(Fun))
