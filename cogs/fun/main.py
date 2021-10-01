import json
import os
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


# Cog
async def random_word():
    # Choose random word from search_database
    word = random.choices(search_database)
    # Select object
    word = word[0]
    # Get word, part of speech, and definition
    word = (word['name'], word['pos'], word['definition'].replace('\n', '; '))

    # Return word
    return word


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
    @commands.command(name='sarcasm', aliases=['sarkasmus'])
    async def sarcasm(self, ctx, *args):
        string = ' '.join(args)
        display = ""
        for letter in string:
            caps = random.choice([True, False])
            if caps:
                display += letter.upper()
            else:
                display += letter.lower()

        await ctx.send(display)

    # Boop
    @commands.command(name='boop', aliases=['stups'])
    async def boop(self, ctx):
        await ctx.send('*' + bot.lang.get(str(ctx.guild.id)).get('boop') + '*')

    # Scream command
    @commands.command(name='scream', aliases=['schrei'])
    async def scream(self, ctx, args):

        # Base string
        msg = "SKR"
        # Convert args to integer
        length = int(args)

        # If length is bigger than 100, set it to 100
        if length > 100:
            length = 100

        # While length is greater than zero, add an 'E' to the end of the string and subtract 1 from length
        while length > 0:
            msg = msg + "E"
            length -= 1

        # Send the msg
        await ctx.send(msg)

    @commands.command(name='zawng')
    async def zawng(self, ctx, args):

        # Base string
        msg = "S"
        # Convert args to integer
        length = int(args)

        # If length is bigger than 100, set it to 100
        if length > 100:
            length = 100

        # While length is greater than zero, add an 'A' to the end of the string and subtract 1 from length
        while length > 0:
            msg = msg + "A"
            length -= 1

        # Send the msg
        await ctx.send(msg)

    @commands.command(name='hiss', aliases=['oìsss', 'fauch'])
    async def hiss(self, ctx, args):
        # Base string
        msg = "OÌ"
        # Convert args to integer
        length = int(args)

        # If length is bigger than 100, set it to 100
        if length > 100:
            length = 100

        # While length is greater than zero, add an 'S' to the end of the string and subtract 1 from length
        while length > 0:
            msg = msg + "S"
            length -= 1

        # Send the msg
        await ctx.send(msg)

    # Random word command
    @commands.command(name='random', aliases=['renulke', 'zufall'])
    async def random(self, ctx, args):

        embed = disnake.Embed(title=bot.lang.get(str(ctx.guild.id)).get('random_title'), colour=899718)

        # Convert args to integer
        number = int(args)

        # Set minimum and maximum
        if number > 30:
            number = 30
        if number < 1:
            number = 1

        # While number is greater than 0
        while number > 0:
            # Generate random word
            rand_word = await random_word()

            # Append random word to the end of the list
            embed.add_field(name=rand_word[0] + " `" + rand_word[1]
                            .replace('substantive (noun)', 'n.')
                            .replace('verb, transitive', 'vtr.')
                            .replace('verb, intransitiv', 'vin.')
                            .replace('adposition', 'adp.')
                            .replace('adverb', 'adv.')
                            .replace('adjective', 'adj.')
                            .replace('proper noun', 'pr.')
                            .replace('interjection', 'interj.')
                            .replace('numeral', 'num.')
                            .replace('interrogation pronouns', 'inter.')
                            + "`:\n", value=rand_word[2])

            # Subtract 1 from number
            number -= 1

        # Send the message
        await ctx.send(embed=embed)

    # Swear command
    @commands.command(name='swear', aliases=['räptum', 'fluch'])
    async def swear(self, ctx):

        # Generate random swear
        random_swear = await self.random_swear()

        # Send the swear
        await ctx.send(random_swear)

    # Say command
    @commands.command(name='say', aliases=['speak', 'plltxe', 'sprich'])
    async def say(self, ctx, *msg):
        msg = ' '.join(msg)

        # Send the message
        await ctx.send(msg)

        # If delete_?say_context is true for this server
        if bot.execute_read_query("SELECT [value] FROM options WHERE ([option] = 'delete_?say_context') AND ([guild_id] = '" + str(ctx.guild.id) + "')")[0][0] == "True":
            # Delete the command message
            await ctx.message.delete()


# Set up cog
def setup(bot):
    # Add the cog
    bot.add_cog(Fun(bot))
    # Print some info
    print('Added new Cog: ' + str(Fun))
