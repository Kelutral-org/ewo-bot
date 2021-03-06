import json
import yaml
import random
from collections import OrderedDict

import discord
from discord.ext import commands
import bot

# Open wordgame_words database
with open("cogs/wordgame/wordgame_words.json", encoding='utf-8') as f:
    wordgame_words = json.load(f)

# Open wordgame_channels database
with open("cogs/wordgame/wordgame_channels.json", encoding='utf-8') as f:
    wordgame_channels = json.load(f)

# Open wordgame_players database
with open("cogs/wordgame/wordgame_players.yaml", encoding='utf-8') as f:
    wordgame_players = yaml.load(f, Loader=yaml.FullLoader)

# Open unusable_words database
with open("cogs/wordgame/unusable_words.json", encoding='utf-8') as f:
    unusable_words = json.load(f)

# Sort wordgame_players database numerically
players = {}
for key, value in sorted(wordgame_players.items(), key=lambda x: int(x[1]), reverse=True):
    players[key] = value
with open("cogs/wordgame/wordgame_players.yaml", 'w') as f:
    yaml.safe_dump(players, f, default_flow_style=False, sort_keys=False)
    f.close()
wordgame_players = players


# Cog
class Wordgame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Add global variables
    recent_words = []
    players = OrderedDict(wordgame_players)
    last_word = ''
    last_word_end = ''
    last_player = 0
    options = []
    wordgame_activechannels = []
    solo = False
    soloplayer = 0
    competitivehistory = []
    competitive = False
    session_points = OrderedDict({})

    # Select a random possible word for solo gameplay
    async def solorandom(self):

        # Empty list to be referenced later
        possible_words = []

        # If current game is competitive
        if self.competitive:

            # For every word in wordgame_words that starts with the last_word's ending letter
            # and is not in the competitive-mode history,
            # add it to the list of possible words
            for word in wordgame_words:
                if word.startswith(self.last_word_end) and word not in self.competitivehistory:
                    possible_words.append(word)

            # Try to select a random choice from possible_words
            try:
                word = random.choices(possible_words)
                word = word[0]
                self.last_word_end = word[-1]
                self.last_word = word

            # If there were no possible words, return None
            except IndexError:
                return None

        # If current game is not competitive
        else:

            # For every word in wordgame_words that starts with the last_word's ending letter
            # and is not in the list of recent words,
            # add it to the list of possible words
            for word in wordgame_words:
                if word.startswith(self.last_word_end) and word not in self.recent_words:
                    possible_words.append(word)

            # Select a random choice from possible_words
            word = random.choices(possible_words)
            word = word[0]
            self.last_word_end = word[-1]
            self.last_word = word

        # Return the chosen word
        return word

    # Select a random word to use when starting a new wordgame
    async def firstword(self):

        # Select a random choice from wordgame_words
        word = random.choices(wordgame_words)
        word = word[0]
        self.last_word = word
        self.last_word_end = self.last_word[-1]

        # Return the chosen word
        return word

    # Points command
    @commands.command(name='points', aliases=['punkte'])
    async def points(self, ctx):

        # Empty dict to reference later
        player_list = []

        # For every user ID in wordgame_players, add them and their amount of points to the list of players
        for id in self.players:

            # Get user id
            user = int(id)
            # Get the member from the user ID
            name = bot.discord.Guild.get_member(ctx.guild, user)
            # Get their server nickname
            name = str(name.nick)
            # If the player has no nickname
            if name == "None":
                # Get the user from the user ID
                name = bot.bot.get_user(user)
                # Get the user's display name
                name = str(name.name)

            # Add the player's name to the list and set their value to be the value from wordgame_players
            player_list.append(str(name) + ": " + str(self.players.get(id)))

        # Turn the list into a string
        player_list = '\n'.join(player_list)

        # Remove the brackets, as well as the string markers with the exclamation marks
        player_list = player_list.strip('{}')

        # Replace comma separator with a new line
        player_list = player_list.replace(', ', '\n')

        # An empty int to reference later
        x = 0
        # For every entry in the player list
        for id in self.players:
            # Add one to the amount of places
            x += 1
            # If the sender of the command has a place in the player list
            if id == str(ctx.author.id):
                # Add a section at the end of the string stating the sender's place and amount of points.
                if x == 1:
                    player_list += "\n\n" + bot.lang.get(str(ctx.guild.id)).get('points_first_place').replace('&1', str(
                        x)).replace('&2', str(self.players.get(str(ctx.author.id))))
                    break
                if x == 2:
                    player_list += "\n\n" + bot.lang.get(str(ctx.guild.id)).get('points_second_place').replace('&1',
                                                                                                               str(
                                                                                                                   x)).replace(
                        '&2', str(self.players.get(str(ctx.author.id))))
                    break
                if x == 3:
                    player_list += "\n\n" + bot.lang.get(str(ctx.guild.id)).get('points_third_place').replace('&1', str(
                        x)).replace('&2', str(self.players.get(str(ctx.author.id))))
                    break
                if x > 3:
                    player_list += "\n\n" + bot.lang.get(str(ctx.guild.id)).get('points_general_place').replace('&1',
                                                                                                                str(
                                                                                                                    x)).replace(
                        '&2', str(self.players.get(str(ctx.author.id))))
                    break

        # Send the player list.
        await ctx.send(embed=discord.Embed(title=bot.lang.get(str(ctx.guild.id)).get('points_title') + ":",
                                           description=player_list, colour=899718))

    # Main command
    @commands.command(name='wordgame', aliases=['uvanlì\'uyä', 'wortspiel'])
    async def wordgame(self, ctx, *args):

        # Convert args into a list
        options = list(args)
        # Print some info
        print('?wordgame run with following args: ' + str(options) + '\n')
        # Set local variable
        channels = wordgame_channels

        # If the options contains 'solo'
        if ('solo' in options or 'Solo' in options) and not ('multiplayer' in options or 'Multiplayer' in options):

            # If the current channel is in the list of active wordgame channels
            if ctx.channel.id in self.wordgame_activechannels:
                # Send a message informing players of the change
                await ctx.channel.send(
                    embed=discord.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_solo'),
                                        colour=899718))

            # Set solo boolean to true
            self.solo = True
            # Print some info
            print('Solo = True')

        # If the options contains 'multiplayer'
        if ('multiplayer' in options or 'Multiplayer' in options) and not ('solo' in options or 'Solo' in options):

            # If the current channel is in the list of active wordgame channels
            if ctx.channel.id in self.wordgame_activechannels:
                # Send a message informing players of the change
                await ctx.channel.send(
                    embed=discord.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_multiplayer'),
                                        colour=899718))

            # Set solo boolean to false
            self.solo = False
            # Print some info
            print('Solo = False')

        # If the options contains 'casual'
        if ('casual' in options or 'Casual' in options) and not ('competitive' in options or 'Wettstreit' in options):

            # If the current channel is in the list of active wordgame channels
            if ctx.channel.id in self.wordgame_activechannels:
                # Send a message informing players of the change
                await ctx.channel.send(
                    embed=discord.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_casual'),
                                        colour=899718))

            # Set competitive boolean to false
            self.competitive = False
            # Print some info
            print('Competitive = False')

        # If the options contains 'competitive'
        if ('competitive' in options or 'Wettstreit' in options) and not ('casual' in options or 'Casual' in options):

            # If the current channel is in the list of active wordgame channels
            if ctx.channel.id in self.wordgame_activechannels:
                # Send a message informing players of the change
                await ctx.channel.send(
                    embed=discord.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_competitive'),
                                        colour=899718))

            # Set the competitive boolean to true
            self.competitive = True
            # Print some info
            print('Competitive = True')

        # If the only option is 'add' or 'new'
        if options == ['add'] or options == ['new'] and not options == ['remove'] or options == ['delete']:

            # If the sender of the command is an Ewo' operator
            if ctx.message.author.id in bot.config.operators:

                # If the current channel is NOT already a wordgame channel
                if ctx.channel.id not in channels:

                    # Print some info
                    print("Creating new wordgame channel: " + str(ctx.channel.id))

                    # Add current channel to list of wordgame_channels
                    channels.append(ctx.channel.id)

                    # Open the wordgame_channels database
                    with open("cogs/wordgame/wordgame_channels.json", 'w') as file:

                        # Update the file and close it
                        json.dump(channels, file)
                        file.close()

                    # Send a confirmation message
                    await ctx.send(embed=discord.Embed(
                        description=bot.lang.get(str(ctx.guild.id)).get('wordgame_added').replace('&1',
                                                                                                  str(ctx.channel.id)),
                        colour=899718))

                # If the current channel is already a wordgame channel
                else:

                    # Send a warning message
                    await ctx.send(
                        embed=discord.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_exists'),
                                            colour=0xff0000))
                    # Print some info
                    print('Current channel is already a wordgame channel.')

        # If the only option is 'remove' or 'delete'
        if options == ['remove'] or options == ['delete'] and not options == ['add'] or options == ['new']:

            # If the sender of the command is an Ewo' operator
            if ctx.message.author.id in bot.config.operators:

                # If the current channel is currently a wordgame channel
                if ctx.channel.id in channels:

                    # Print some info
                    print("Removing current wordgame channel: " + str(ctx.channel.id))

                    # Remove the current channel from the list of wordgame channels
                    channels.remove(ctx.channel.id)

                    # Open the wordgame_channels database
                    with open("cogs/wordgame/wordgame_channels.json", 'w') as file:

                        # Update the file and close it
                        json.dump(channels, file)
                        file.close()

                    # Send a confirmation message
                    await ctx.send(embed=discord.Embed(
                        description=bot.lang.get(str(ctx.guild.id)).get('wordgame_removed').replace('&1', str(
                            ctx.channel.id)),
                        colour=899718))

                # If the current channel is NOT currently a wordgame channel
                else:

                    # Send a warning message
                    await ctx.send(
                        embed=discord.Embed(
                            description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_nonexistent'),
                            colour=0xff0000))
                    # Print some info
                    print('Current channel is not a wordgame channel.')

        # If the options contains 'start' or 'begin'
        if ('start' in options or 'begin' in options or 'Start' in options) and not ('stop' in options or 'end' in options or 'Ende' in options):

            # If current channel is a wordgame channel
            if ctx.channel.id in channels:

                # If the current channel is NOT already active
                if ctx.channel.id not in self.wordgame_activechannels:
                    # Print some info
                    print('Found current channel in wordgame_channels: ' + str(ctx.channel.id) + ", activating it...")

                    # Add current channel to list of active channels
                    self.wordgame_activechannels.append(ctx.channel.id)
                    # Print some info
                    print('Current active channels: ' + str(self.wordgame_activechannels))

                    # Choose the first word
                    await self.firstword()

                    # If the gamemode is competitive
                    if self.competitive:

                        # Add first word to competitive-mode history
                        self.competitivehistory.append(self.last_word)

                    # If the gamemode is NOT competitive
                    else:

                        # Add first word to list of recently used words
                        self.recent_words.append(self.last_word)

                    # Replace individualized characters with digraphs and set it in a new variable
                    display_word = self.last_word.replace('d', 'tx').replace('g', 'kx').replace('b', 'px').replace(
                        'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à', 'ay').replace(
                        'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')

                    # Send a startup message
                    await ctx.send(embed=discord.Embed(
                        description=bot.lang.get(str(ctx.guild.id)).get('wordgame_starting') + "\n" +
                                    bot.lang.get(str(ctx.guild.id)).get('solo') + ": " + str(self.solo) + "\n" +
                                    bot.lang.get(str(ctx.guild.id)).get('competitive') + ": " + str(
                            self.competitive) + "\n\n" +
                                    bot.lang.get(str(ctx.guild.id)).get('wordgame_first_word').replace('&1',
                                                                                                       display_word),
                        colour=899718))

                # If the current channel is already active
                else:

                    # Send a warning message
                    await ctx.send(
                        embed=discord.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_active'),
                                            colour=0xff0000))

        # If the options contain 'stop' or 'end'
        if ('stop' in options or 'end' in options or 'Ende' in options) and not ('start' in options or 'begin' in options or 'Start' in options):

            # If current channel is a wordgame channel
            if ctx.channel.id in channels:

                # If current channel is currently active
                if ctx.channel.id in self.wordgame_activechannels:
                    # Print some info
                    print('Found current channel in wordgame_activechannels: ' + str(
                        ctx.channel.id) + ", deactivating it...")

                    # Remove current channel from list of active channels
                    self.wordgame_activechannels.remove(ctx.channel.id)
                    # Print some info
                    print('Current active channels: ' + str(self.wordgame_activechannels))

                    # If gamemode is NOT solo
                    if not self.solo:

                        # Empty dict to reference later
                        player_list = []

                        # For every user ID in wordgame_players,
                        # add them and their amount of points to the list of players
                        for id in self.session_points:

                            # Get user id
                            user = int(id)
                            # Get the member from the user ID
                            name = bot.discord.Guild.get_member(ctx.guild, user)
                            # Get their server nickname
                            name = str(name.nick)

                            # If the player has no nickname
                            if name == "None":
                                # Get the user from the user ID
                                name = bot.bot.get_user(user)
                                # Get the user's display name
                                name = str(name.name)

                            # Add the player's name to the list and set their value to be the value from wordgame_players
                            player_list.append(str(name) + ": " + str(self.players.get(id)))

                        # Turn the list into a string
                        player_list = '\n'.join(player_list)

                        # Remove the brackets, as well as the string markers with the exclamation marks
                        player_list = player_list.strip('{}')
                        player_list = player_list.replace('!\'', '')
                        player_list = player_list.replace('\'!', '')

                        # Replace comma separator with a new line
                        player_list = player_list.replace(', ', '\n')

                        # Send stop message with player_list
                        await ctx.channel.send(embed=discord.Embed(
                            description=bot.lang.get(str(ctx.guild.id)).get('wordgame_stopping') + "\n" +
                                        bot.lang.get(str(ctx.guild.id)).get(
                                            'wordgame_round_points') + ":\n" + player_list,
                            colour=899718))

                    # If gamemode is solo
                    else:

                        # Send stop message without player_list
                        await ctx.channel.send(
                            embed=discord.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_stopping'),
                                                colour=899718))

                    # Set variables back to default
                    self.last_player = 0
                    self.solo = False
                    self.competitive = False
                    self.competitivehistory = []
                    self.session_points = {}
                    self.recent_words = []

                # If current channel is NOT currently active
                else:

                    # Send a warning message
                    await ctx.send(
                        embed=discord.Embed(
                            description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_inactive'),
                            colour=0xff0000))
        # Print a separator
        print('---------------------')

    @commands.Cog.listener()
    async def on_message(self, message):

        # If there is a wonky tìftang in the message, replace it with a normal tìftang
        if '’' in message.content:
            message.content = message.content.replace('’', '\'')

        # Make new variable for lowercase message
        msg = message.content.lower()

        # Replace digraphs in msg with individualized characters
        msg = msg.replace('ng', 'ŋ').replace('tx', 'd').replace('kx', 'g').replace(
            'px', 'b').replace('aw', 'á').replace('ew', 'é').replace('ay', 'à').replace(
            'ey', 'è').replace('rr', 'ʀ').replace('ll', 'j')

        # If the current channel is an active wordgame channel
        # and the author is not a bot
        # and the message does not start with a command prefix,
        if message.channel.id in self.wordgame_activechannels and not message.author.bot and not msg.startswith(
                '?') and not msg.startswith('!'):

            # Replace individualized characters with digraphs and set it in a new variable
            display_word = msg.replace('d', 'tx').replace('g', 'kx').replace('b',
                                                                             'px').replace(
                'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à',
                                                                         'ay').replace(
                'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')

            # If the message is not in the list of valid wordgame words
            if msg not in wordgame_words:

                # If msg ends with aw
                if msg in unusable_words['aw']:
                    # Send a warning message
                    await message.channel.send(
                        embed=discord.Embed(
                            title=bot.lang.get(str(message.guild.id)).get('wordgame_unusable') + ": " + display_word,
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_aw'),
                            colour=0xff0000))

                # If message ends with ew
                if msg in unusable_words['ew']:
                    # Send a warning message
                    await message.channel.send(
                        embed=discord.Embed(
                            title=bot.lang.get(str(message.guild.id)).get('wordgame_unusable') + ": " + display_word,
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ew'),
                            colour=0xff0000))

                # If message ends with rr
                if msg in unusable_words['rr']:
                    # Send a warning message
                    await message.channel.send(
                        embed=discord.Embed(
                            title=bot.lang.get(str(message.guild.id)).get('wordgame_unusable') + ": " + display_word,
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_rr'),
                            colour=0xff0000))

                # If message ends with ll
                if msg in unusable_words['ll']:
                    # Send a warning message
                    await message.channel.send(
                        embed=discord.Embed(
                            title=bot.lang.get(str(message.guild.id)).get('wordgame_unusable') + ": " + display_word,
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ll'),
                            colour=0xff0000))

            # If there are no spaces in the message
            if ' ' not in msg:

                # If msg is NOT in the list of recent words
                if msg not in self.recent_words:

                    # If msg starts with the final letter of the last word and msg is a valid word
                    if msg.startswith(self.last_word_end) and msg in wordgame_words:

                        # If the author is the last player to say a word
                        if not message.author.id == self.last_player:

                            # If gamemode is NOT solo
                            if not self.solo:

                                # If msg is a valid word
                                if msg in wordgame_words:

                                    # If the gamemode is competitive and msg is in the competitive-mode history
                                    if self.competitive and msg in self.competitivehistory:
                                        # Send a warning message
                                        await message.channel.send(
                                            embed=discord.Embed(description=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_already_used'),
                                                colour=0xff0000))

                                    # If the gamemode is competitive and msg is NOT in the competitive-mode history,
                                    # or the gamemode is NOT competitive
                                    if (
                                            self.competitive and msg not in self.competitivehistory) or not self.competitive:

                                        # Set local variable
                                        new_word = msg

                                        # Replace individualized characters with digraphs and set it in a new variable
                                        display_word = msg.replace('d', 'tx').replace('g', 'kx').replace('b',
                                                                                                         'px').replace(
                                            'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à',
                                                                                                     'ay').replace(
                                            'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')

                                        # Set last word to current word
                                        self.last_word_end = new_word[-1]
                                        self.last_word = new_word

                                        # Get the member of the message author
                                        name = bot.discord.Guild.get_member(message.guild, message.author.id)
                                        # Get their nickname
                                        name = str(name.nick)

                                        # If the user has no nickname
                                        if name == 'None':
                                            # Get the user of the message author
                                            name = bot.bot.get_user(message.author.id)
                                            # Get their display name
                                            name = str(name.name)

                                        # Record the new player and word
                                        await message.channel.send(
                                            embed=discord.Embed(description=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_word_said').replace('&1', str(name)).replace('&2',
                                                                                                       display_word),
                                                                colour=899718))

                                        # Get message author's id
                                        session_author = str(message.author.id)

                                        # If the message author is in the session points list
                                        if session_author in self.session_points:

                                            # Add 1 to their points
                                            self.session_points[session_author] += 1

                                        # If the message author is NOT in the session points list
                                        else:

                                            # Create a new key for the author and set their score to 1
                                            self.session_points[
                                                self.session_points.get(session_author, session_author)] = 1

                                        # Empty dict to reference later
                                        session_player_data = {}

                                        # Sort session points list numerically and set game_player_points to it
                                        for key, value in sorted(self.session_points.items(), key=lambda x: int(x[1]),
                                                                 reverse=True):
                                            session_player_data[key] = value

                                        # Set the global variable to the sorted version
                                        self.session_points = session_player_data

                                        # Get message author's id
                                        author = str(message.author.id)

                                        # If the message author is in the player list
                                        if author in self.players:

                                            # Add 1 to their points
                                            self.players[author] += 1

                                        # If the message author is NOT in the player list
                                        else:

                                            # Create a new key for the author and set their score to 1
                                            self.players[
                                                self.players.get(author, author)] = 1

                                        # Empty dict to reference later
                                        player_data = {}

                                        # Sort player list numerically and set game_player_points to it
                                        for key, value in sorted(self.players.items(), key=lambda x: int(x[1]),
                                                                 reverse=True):
                                            player_data[key] = value

                                        # Open wordgame_players database
                                        with open("cogs/wordgame/wordgame_players.yaml", 'w') as f:

                                            # Update file and close it
                                            yaml.safe_dump(player_data, f, default_flow_style=False, sort_keys=False)
                                            f.close()

                                        # Set the global variable to the sorted version
                                        self.players = player_data

                                        # Set the last player to the message author
                                        self.last_player = message.author.id

                                        # If gamemode is competitive
                                        if self.competitive:
                                            # Add the new word to the competitive-mode history
                                            self.competitivehistory.append(new_word)

                                            # Empty list to reference later
                                            valid_words = []

                                            # For every word in the wordgame_words database
                                            for word in wordgame_words:

                                                # If the word is not in the competitive-mode history
                                                # and the word starts with the final letter of the new word,
                                                # add it to the list of valid words
                                                if word not in self.competitivehistory and word.startswith(
                                                        new_word[-1]):
                                                    valid_words.append(word)

                                            # If there are no more valid words
                                            if not valid_words:

                                                # Get message author's id
                                                session_author = str(message.author.id)

                                                # If the message author is in the session points list
                                                if session_author in self.session_points:

                                                    # Add 5 to their points
                                                    self.session_points[session_author] += 5

                                                # If the message author is NOT in the session points list
                                                else:

                                                    # Create a new key for the author and set their score to 5
                                                    self.session_points[
                                                        self.session_points.get(session_author, session_author)] = 5

                                                # Empty dict to reference later
                                                session_player_data = {}

                                                # Sort session points list numerically and set game_player_points to it
                                                for key, value in sorted(self.session_points.items(),
                                                                         key=lambda x: int(x[1]),
                                                                         reverse=True):
                                                    session_player_data[key] = value

                                                # Set the global variable to the sorted version
                                                self.session_points = session_player_data

                                                # Get message author's id
                                                author = str(message.author.id)

                                                # If the message author is in the player list
                                                if author in self.players:

                                                    # Add 5 to their points
                                                    self.players[author] += 5

                                                # If the message author is NOT in the player list
                                                else:

                                                    # Create a new key for the author and set their score to 5
                                                    self.players[
                                                        self.players.get(author, author)] = 5

                                                # Empty dict to reference later
                                                player_data = {}

                                                # Sort player list numerically and set game_player_points to it
                                                for key, value in sorted(self.players.items(), key=lambda x: int(x[1]),
                                                                         reverse=True):
                                                    player_data[key] = value

                                                # Open wordgame_players database
                                                with open("cogs/wordgame/wordgame_players.yaml", 'w') as f:

                                                    # Update file and close it
                                                    yaml.safe_dump(player_data, f, default_flow_style=False,
                                                                   sort_keys=False)
                                                    f.close()

                                                # Set the global variable to the sorted version
                                                self.players = player_data

                                                # End the game with the message author as the winner
                                                await self.endcompetitive(message, name)

                                        # If gamemode is NOT competitive
                                        else:
                                            # Add new word to list of recent words
                                            self.recent_words.append(new_word)

                                            # If the list of recent words has 6 or more entries
                                            # (after the new word has been added),
                                            # Remove the first entry in the history
                                            # (No more than 5 entries should be present)
                                            if len(self.recent_words) >= 6:
                                                self.recent_words.remove(self.recent_words[0])

                            # If gamemode is solo
                            else:

                                # If the gamemode is NOT competitive
                                if not self.competitive:
                                    # Set the last word to the msg
                                    self.last_word = msg
                                    self.last_word_end = msg[-1]

                                    # Add msg to list of recent words
                                    self.recent_words.append(msg)

                                    # Generate new word
                                    new_word = await self.solorandom()

                                    # Add new word to list of recent words
                                    self.recent_words.append(new_word)

                                    # If the list of recent words has 7 or more entries
                                    # (after the new word has been added),
                                    # Remove the first two entries in the history
                                    # (No more than 5 entries should be present)
                                    if len(self.recent_words) >= 7:
                                        self.recent_words.remove(self.recent_words[0])
                                        self.recent_words.remove(self.recent_words[0])

                                    # Try to set display_word to the digraph version of the new word
                                    try:
                                        display_word = new_word.replace('d', 'tx').replace('g', 'kx').replace('b',
                                                                                                              'px').replace(
                                            'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à', 'ay').replace(
                                            'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')

                                    # If new_word is None
                                    except AttributeError:
                                        # Do nothing
                                        pass

                                    # Say the new word
                                    await message.channel.send(
                                        embed=discord.Embed(description=display_word + "!", colour=899718))

                                # If gamemode is competitive and msg is in competitive-mode history
                                if self.competitive and msg in self.competitivehistory:
                                    # Send a warning message
                                    await message.channel.send(
                                        embed=discord.Embed(description=bot.lang.get(str(message.guild.id)).get(
                                            'wordgame_already_used'),
                                            colour=0xff0000))

                                # If gamemode is competitive and msg is not in competitive-mode history
                                if self.competitive and msg not in self.competitivehistory:
                                    # Set last word to msg
                                    self.last_word = msg
                                    self.last_word_end = msg[-1]

                                    # Generate new word
                                    new_word = await self.solorandom()

                                    # Try to set display_word to the digraph version of the new word
                                    try:
                                        display_word = new_word.replace('d', 'tx').replace('g', 'kx').replace('b',
                                                                                                              'px').replace(
                                            'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à',
                                                                                                     'ay').replace(
                                            'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                                    # If display_word is None
                                    except AttributeError:
                                        # Do nothing
                                        pass

                                    # If gamemode is competitive
                                    if self.competitive:

                                        # Add new word AND msg to competitive-mode history
                                        self.competitivehistory.append(new_word)
                                        self.competitivehistory.append(msg)

                                        # Empty list to reference later
                                        valid_words = []

                                        # For every word in wordgame_words database
                                        for word in wordgame_words:

                                            # Try to add the current word to the list of valid words
                                            # if word is not in competitive-mode history
                                            # and word starts with the final letter of the new word
                                            # and word is not in the list of recent words
                                            try:
                                                if word not in self.competitivehistory and word.startswith(
                                                        new_word[-1]) and word not in self.recent_words:
                                                    valid_words.append(word)

                                            # If no valid word could be found
                                            except TypeError:
                                                # Do nothing
                                                continue

                                        # Get ID of message author
                                        user = message.author.id
                                        # Get member of message author
                                        name = bot.discord.Guild.get_member(message.guild, user)
                                        # Get server nickame of message author
                                        name = name.nick

                                        # If message author has no nickname
                                        if name == 'None':
                                            # Get user of message author
                                            name = bot.bot.get_user(user)
                                            # Get display name of message author
                                            name = str(name.name)

                                        # If new word is None (a valid word could not be generated)
                                        if new_word is None:
                                            # End competitive game with message author as the winner
                                            await self.endcompetitive(message, name)

                                        # If new word is NOT None
                                        if new_word is not None:
                                            # Say the new word
                                            await message.channel.send(
                                                embed=discord.Embed(description=display_word + "!", colour=899718))

                                        # If no new valid words can be said
                                        if not valid_words:
                                            # End competitive game with Ewo' as the winner
                                            await self.endcompetitive(message, bot.bot.user.name)

                        # If the author is the last player to say a word
                        else:

                            # Send a warning message
                            await message.channel.send(
                                embed=discord.Embed(
                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_already_said'),
                                    colour=0xff0000))

                # If msg is in the list of recent words
                else:

                    # Send a warning message
                    await message.channel.send(
                        embed=discord.Embed(
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_used_recently'),
                            colour=0xff0000))

            # If there are spaces in msg
            else:

                # If the message is in the list of words with spaces
                if msg in unusable_words['space']:
                    # Send a warning message
                    await message.channel.send(
                        embed=discord.Embed(
                            title=bot.lang.get(str(message.guild.id)).get('wordgame_unusable') + ": " + display_word,
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_no_spaces'),
                            colour=0xff0000))

    # End a competitive game with a defined winner
    async def endcompetitive(self, message, winner):

        # If the current channel is an active wordgame channel
        if message.channel.id in self.wordgame_activechannels:

            # Print some info
            print(str(winner) + ' won the game!')
            print(
                'Found current channel in wordgame_activechannels: ' + str(message.channel.id) + ', deactivating it...')

            # Remove current channel from list of active wordgame channels
            self.wordgame_activechannels.remove(message.channel.id)

            # Print some info
            print('Current active channels: ' + str(self.wordgame_activechannels))

            # Empty dict to reference later
            player_list = []

            # For every user ID in list of session points
            for id in self.session_points:

                # Get player ID
                user = int(id)
                # Get member of player
                name = bot.discord.Guild.get_member(message.guild, user)
                # Get the server nickname of player
                name = str(name.nick)

                # If player has no nickname
                if name == "None":
                    # Get user of player
                    name = bot.bot.get_user(user)
                    # Get display name of player and surround it in "!"
                    # (To be able to remove the 's later without removing tìftangs)
                    name = str(name.name)

                # Add the player's name to the list and set their value to be the value from wordgame_players
                player_list.append(str(name) + ": " + str(self.players.get(id)))

            # Turn the list into a string
            player_list = '\n'.join(player_list)

            # Remove the brackets, as well as the string markers with the exclamation marks
            player_list = player_list.strip('{}')
            player_list = player_list.replace('!\'', '')
            player_list = player_list.replace('\'!', '')

            # Replace comma separators to new lines
            player_list = player_list.replace(', ', '\n')

            # If gamemode is NOT solo
            if not self.solo:

                # Send win message with list of session points
                await message.channel.send(embed=discord.Embed(
                    title=bot.lang.get(str(message.guild.id)).get('wordgame_win').replace('&1', str(winner)),
                    description=bot.lang.get(str(message.guild.id)).get('wordgame_round_points') + ":\n" + player_list,
                    colour=899718))

            # If gamemode is solo
            else:

                # Send win message without list of session points
                await message.channel.send(embed=discord.Embed(
                    description=bot.lang.get(str(message.guild.id)).get('wordgame_win').replace('&1', str(winner)),
                    colour=899718))

            # Set variables back to defaults
            self.last_player = 0
            self.solo = False
            self.competitive = False
            self.competitivehistory = []
            self.session_points = {}
            self.recent_words = []


# Set up cog
def setup(bot):
    # Add the cog
    bot.add_cog(Wordgame(bot))
    # Print some info
    print('Added new Cog: ' + str(Wordgame))
