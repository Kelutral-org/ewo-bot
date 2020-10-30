import json
import os
from collections import OrderedDict

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
    # Open selfie_leaderboard
    with open("cogs/fun/selfie_leaderboard.json", encoding='utf-8') as f:
        selfie_leaderboard = json.load(f)

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
    @commands.command(name='scream')
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
        await ctx.send(embed=discord.Embed(title="Random Words:", description=random_words, colour=899718))

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

    # Say command
    @commands.command(name='say', aliases=['speak', 'plltxe'])
    async def say(self, ctx, *msg):
        msg = ' '.join(msg)

        # Send the message
        await ctx.send(msg)

        if bot.bot_options['delete_?say_context'] == "True":
            # Delete the command message
            await ctx.message.delete()

    # Selfie command
    @commands.command(name='selfie', aliases=['picture', 'rel'])
    async def selfie(self, ctx):

        # Create a list of every file name from the selfie directory
        selfie_list = os.listdir("cogs/fun/selfies")

        # Choose a random selection from that list
        selfie = random.choice(selfie_list)

        # Open the chosen image and send it as a file.
        with open('cogs/fun/selfies/' + selfie, 'rb') as f:
            picture = discord.File(f)
            await ctx.send(file=picture)

        # Try to do the following:
        if str(ctx.author.id) in self.selfie_leaderboard:
            # If the chosen image is not in the command sender's list of images found
            if not selfie in self.selfie_leaderboard[str(ctx.author.id)]:

                # Add the current image and command sender to the current leaderboard
                self.selfie_leaderboard[str(ctx.author.id)].append(selfie)

                # Open the leaderboard file and write the new leaderboard
                with open('cogs/fun/selfie_leaderboard.json', 'w') as f:
                    json.dump(self.selfie_leaderboard, f)

        # If a KeyError occurs, add a new player to the leaderboard
        else:

            # Add the current image and command sender to the current leaderboard
            self.selfie_leaderboard[str(ctx.author.id)] = []
            self.selfie_leaderboard[str(ctx.author.id)].append(selfie)

            # Open the leaderboard file and write the new leaderboard
            with open('cogs/fun/selfie_leaderboard.json', 'w') as f:
                json.dump(self.selfie_leaderboard, f)

    # Selfiesfound command
    @commands.command(name='selfiesfound', aliases=['selfies', 'pictures', 'ayral', 'picturesfound', 'ayralarusun'])
    async def selfiesfound(self, ctx):
        # Variables
        name = ""
        total_count = 0
        selfies_found = {}
        sorted_selfies_found = {}
        selfies_found_string = ""
        my_selfies_found = 0
        
        # For every user ID in the leadeboard
        for user in self.selfie_leaderboard:
            
            # Integerize the user ID
            user = int(user)
            # Get the member from the user ID
            name = bot.discord.Guild.get_member(ctx.guild, user)
            # Get their server nickname and surround it in "!"
            # (To be able to remove the 's later without removing tìftangs)
            name = str(name.nick)
            # If the player has no nickname
            if name == "None":
                # Get the user from the user ID
                name = bot.bot.get_user(user)
                # Get the user's display name
                name = str(name.name)
            
            # Make a new section in the variable for the user's name
            selfies_found[name] = 0
            
            # For every enumerated image in the selfies directory
            for count, image in enumerate(os.listdir("cogs/fun/selfies")):
                
                # If the name of the image is in the user's list of found images
                if image in self.selfie_leaderboard[str(user)]:
                    
                    # Add 1 to the user's selfies found
                    selfies_found[name] += 1
                
                # Set the amount of total images (counting starts at 0 so a 1 must be added)
                total_count = count + 1
            
        # Sort the dictionary numerically and store the sorted version in a new variable
        for key, value in sorted(selfies_found.items(), key=lambda x: int(x[1]), reverse=True):
            sorted_selfies_found[key] = value

        # For ever user in the sorted dictionary
        for user in sorted_selfies_found:

            # Add the user and their score to the string to be displayed
            selfies_found_string += str(user + ": " + str(sorted_selfies_found.get(user))) + "/" + str(total_count)

            # Add a new line to the string
            selfies_found_string += "\n"

        # For every enumerated image in the selfies directory
        for count, image in enumerate(os.listdir("cogs/fun/selfies")):

            # Try
            try:

                # If the image is in the user's selfies found
                if image in self.selfie_leaderboard[str(ctx.author.id)]:

                    # Add 1 to the command sender's selfies found count
                    my_selfies_found += 1

            # If this user is not in the leaderboard
            except KeyError:
                # Do nothing, their count is 0
                pass

            # Set the amount of total images (counting starts at 0 so a 1 must be added)
            total_count = count + 1

        # Send the leaderboard and user's count
        await ctx.send(embed=discord.Embed(title="Selfies Found:", description=selfies_found_string + "\n\n" + 'You have found ' + str(my_selfies_found) + ' selfies out of ' + str(total_count), colour=899718))


# Set up cog
def setup(bot):
    # Add the cog
    bot.add_cog(Fun(bot))
    # Print some info
    print('Added new Cog: ' + str(Fun))
