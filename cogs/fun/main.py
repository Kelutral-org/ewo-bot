import json

import discord
from discord.ext import commands
import bot

import random

# Open search_database
with open("cogs/compact_database.json", encoding ='utf-8') as f:
    search_database = json.load(f)

# Open swear_database
with open("cogs/fun/swear_database.json", encoding ='utf-8') as f:
    swear_database = json.load(f)


# Cog
class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Generate random Na'vi word
    async def random_word(self):
        # Choose random word from search_database
        word = random.choices(search_database)
        # Select object
        word = word[0]
        # Get word, part of speech, and definition
        word = word['name'] + ' ' + word['pos'] + ' = \n' + word['definition'].replace('\n', '; ')
        
        # Return word
        return word
    
    # Generate random Na'vi swear
    async def random_swear(self):
        # Choose random word from search_database
        word = random.choices(swear_database)
        # Select object
        word = word[0]
        # Get word and add exclamation mark
        word = word['name'] + '!'
        
        # Return word
        return word
    
    # Scream command
    @commands.command(name='msg')
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
    
    @commands.command(name='hiss', aliases=['oìsss'])
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
    @commands.command(name='random', aliases=['renulke'])
    async def random(self, ctx, args):

        # Empty list to be referenced later
        random_words = []

        # Convert args to integer
        number = int(args)

        # If number is bigger than 30, set it to 30
        if number > 30:
            number = 30

        # While number is greater than 0
        while number > 0:

            # Generate random word
            random_word = await self.random_word()

            # Append random word to the end of the list
            random_words.append(random_word)

            # Subtract 1 from number
            number -= 1

        # Join the list into a string
        random_words = '\n\n'.join(random_words)

        # Send the message
        await ctx.send(embed=discord.Embed(title="Random Words:", description=random_words))

    # React history command
    @commands.command()
    async def reacthistory(self, ctx,args,emojiname):

        # Convert args to integer
        amount = int(args)

        # Get the emoji that was entered
        emoji = '<' + emojiname + '>'

        # Get current channel
        channel = ctx.message.channel

        # If the sender of the command is an Ewo' operator
        if ctx.message.author.id in bot.config.operators:

            # Delete the command message
            await ctx.message.delete()

            # Get history of chat
            messages = await channel.history(limit=amount).flatten()

            # For each message in the history of the chat, react with the emoji specified
            for message in messages:
                await message.add_reaction(emoji)

    # React command
    @commands.command()
    async def react(self, ctx, msg, emojiname):

        # Delete the command message
        await ctx.message.delete()

        # Get the emoji that was entered
        emoji = '<' + emojiname + '>'

        # Get message from the ID specified
        message = await ctx.fetch_message(msg)

        # Add reaction of emoji to message
        await message.add_reaction(emoji)

    # Swear command
    @commands.command(name='swear', aliases=['räptum'])
    async def swear(self, ctx):

        # Generate random swear
        random_swear = await self.random_swear()

        # Send the swear
        await ctx.send(random_swear)


# Set up cog
def setup(bot):
    # Add the cog
    bot.add_cog(Fun(bot))
    # Print some info
    print('Added new Cog: ' + str(Fun))
