import json
import random
import sqlite3
from sqlite3 import Error

import disnake
from disnake.ext import commands
import bot

with open('cogs/wordgame/forbidden_words.json', 'r', encoding='utf-8') as f:
    forbidden_words = json.load(f)

with open('cogs/wordgame/exception_words.json', 'r', encoding='utf-8') as f:
    exception_words = json.load(f)


# Set up databases and create tables
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


players_db = create_connection('cogs/wordgame/players.db')
channels_db = create_connection('cogs/wordgame/channels.db')


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
    except Error as e:
        if str(e) != 'UNIQUE constraint failed: words.word':
            print(f"The error '{e}' occurred")


def execute_read_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")


execute_query(players_db, """
CREATE TABLE IF NOT EXISTS players (
  player_id TEXT NOT NULL, 
  points INTEGER NOT NULL, 
  guild_id TEXT NOT NULL, 
  UNIQUE (player_id, points, guild_id)
);
""")


execute_query(channels_db, """
CREATE TABLE IF NOT EXISTS channels (
  channel_id TEXT NOT NULL, 
  guild_id TEXT NOT NULL, 
  PRIMARY KEY (channel_id)
);
""")


def convert_back(word):
    return_word = word.replace('á', 'aw').replace('à', 'ay').replace('é', 'ew').replace('è', 'ey') \
        .replace('j', 'll').replace('ʀ', 'rr') \
        .replace('b', 'px').replace('d', 'tx').replace('g', 'kx') \
        .replace('ŋ', 'ng').replace('c', 'ts')
    return return_word


class WordgameCog(commands.Cog):
    def __init__(self, bot):
        with open('cogs/wordgame/permitted_words.txt', 'r', encoding='utf-8') as f:
            self.permitted_words = []
            for line in f:
                self.permitted_words.append(line.strip())

        with open('cogs/wordgame/permitted_words.txt', 'r', encoding='utf-8') as f:
            self.total_permitted_words = []
            for line in f:
                self.total_permitted_words.append(line.strip())
        
        self.bot = bot

        # A variable to hold the currently active games
        self.games = {}

        # A variable to hold the previous 5 words of each game for each active channel
        self.recent_words = {}

        # A variable to hold the previous player to say a word for each active channel
        self.previous_player = {}

        # A variable to store the previous word spoken for each active channel
        self.previous_word = {}

        self.points = {}

    def random_word(self, id):
        global available_words
        available_words = []
        for word in self.permitted_words:
            if word[0] == self.previous_word.get(id)[-1]:
                available_words.append(word)

        if available_words:
            return_word = random.choice(available_words)
        else:
            return_word = None

        if (return_word not in self.recent_words.get(id)) and (self.previous_word.get(id) != return_word) and (return_word is not None):
            return return_word
        elif return_word is None:
            return return_word
        else:
            self.random_word(id)

    async def win(self, channel_id, player_id):
        channel = bot.bot.get_channel(channel_id)

        # Get user id
        user = player_id
        # Get the member from the user ID
        winner_name = bot.disnake.Guild.get_member(channel.guild, user)
        # Get their server nickname
        winner_name = str(winner_name.nick)

        # If the player has no nickname
        if winner_name == "None":
            # Get the user from the user ID
            winner_name = bot.bot.get_user(user)
            # Get the user's display name
            winner_name = str(winner_name.name)

        # Replace values in self.permitted_words
        with open('cogs/wordgame/permitted_words.txt', 'r', encoding='utf-8') as f:
            self.permitted_words = []
            for line in f:
                self.permitted_words.append(line.strip())
        if self.games.get(channel_id).get('playermode') == 'solo':
            await channel.send(embed=disnake.Embed(
                description=bot.lang.get(str(channel.guild.id)).get('wordgame_win').replace('&1', winner_name),
                colour=899718))
        else:
            return_string = "**" + bot.lang.get(str(channel.guild.id)).get('wordgame_round_points') + "**:\n"
            sort_dict = sorted(self.points.get(channel_id).items(), key=lambda x: x[1], reverse=True)
            sorted_dict = {}
            for i in sort_dict:
                sorted_dict[i[0]] = i[1]
            for player in sorted_dict:
                # Get user id
                user = player
                # Get the member from the user ID
                name = bot.disnake.Guild.get_member(channel.guild, user)
                # Get their server nickname
                name = str(name.nick)

                # If the player has no nickname
                if name == "None":
                    # Get the user from the user ID
                    name = bot.bot.get_user(user)
                    # Get the user's display name
                    name = str(name.name)
                return_string += "- " + name + ": " + str(self.points.get(channel_id).get(player)) + "\n"

                points = execute_read_query(players_db,"SELECT [player_id], [points], [guild_id] FROM players WHERE ([guild_id] = '" + str(channel.guild.id) + "') AND ([player_id] = '" + str(player) + "')")
                if not points:
                    execute_query(players_db, "INSERT INTO players (player_id, points, guild_id) VALUES ('" + str(player) + "','" + str(self.points.get(channel_id).get(player)) + "','" + str(channel.guild.id) + "');")
                else:
                    execute_query(players_db, "UPDATE players SET [points] = '" + str(int(execute_read_query(players_db,"SELECT [player_id], [points], [guild_id] FROM players WHERE ([guild_id] = '" + str(channel.guild.id) + "') AND ([player_id] = '" + str(player) + "')")[0][1]) + self.points.get(channel_id).get(player)) + "' WHERE ([guild_id] = '" + str(channel.guild.id) + "') AND ([player_id] = '" + str(player) + "')")

            await channel.send(embed=disnake.Embed(
                title=bot.lang.get(str(channel.guild.id)).get('wordgame_win').replace('&1', winner_name),
                description=return_string,
                colour=899718))

        # Remove this channel from the database and send a confirmation message
        self.games.pop(channel_id)
        # Remove this channel from the recent word list
        self.recent_words.pop(channel_id)
        # Remove this channel from the previous player list
        self.previous_player.pop(channel_id)
        # Remove this channel from the points list
        self.points.pop(channel_id)

    def remove_word(self, word, id):
        if self.games.get(id).get('gamemode') == 'casual':
            self.recent_words[id].append(word)
        if self.games.get(id).get('gamemode') == 'competitive':
            self.permitted_words.remove(word)

        if len(self.recent_words[id]) > 5:
            self.recent_words[id].pop(0)

    @commands.command(name='wordgame', aliases=['uvanlì\'uyä','wortspiel'])
    async def wordgame(self, ctx, *args):
        args = list(args)
        # Variable to record whether or not the user has operator permissions
        is_op = False

        # Variables to temporarily record the game types for a new game
        gamemode_record = ""
        playermode_record = ""

        # Set the operator perms variable
        for perm in ctx.author.permissions_in(ctx.channel):
            if (perm == ('manage_guild', True)) or (perm == ('administrator', True)) or (ctx.author.id in bot.config.operators):
                is_op = True

        if "addchannel" in args:
            if is_op:
                # Get all of the channels that match the current channel
                channels = execute_read_query(channels_db, "SELECT * FROM channels WHERE ([channel_id] = '" + str(ctx.channel.id) + "')")

                # If the previous line does not return anything (this channel is not a wordgame channel),
                # add this channel to the database and send a confirmation message
                if not channels:
                    execute_query(channels_db, """
                                                INSERT INTO
                                                  channels (channel_id, guild_id)
                                                VALUES
                                                  ('""" + str(ctx.channel.id) + """','""" + str(ctx.guild.id) + """');
                                                """)
                    await ctx.send(embed=disnake.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_added').replace('&1', ctx.channel.name), colour=899718))

                # If this channel is already in the database, send an error
                else:
                    await ctx.send(embed=disnake.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_exists'), colour=0xff0000))

            # If the user does not have operator permissions, send an error
            else:
                await ctx.send(embed=disnake.Embed(title=bot.lang.get(str(ctx.guild.id)).get('denied'),
                                                   description=bot.lang.get(str(ctx.guild.id)).get('no_access'),
                                                   colour=0xff0000))

        if "removechannel" in args:
            if is_op:
                # Get all of the channels that match the current channel
                channels = execute_read_query(channels_db, "SELECT * FROM channels WHERE ([channel_id] = '" + str(ctx.channel.id) + "')")

                # If the previous line DOES return something (this channel IS a wordgame channel),
                # remove this channel from the database and send a confirmation message
                if channels:
                    execute_query(channels_db, """
                                                DELETE FROM channels
                                                WHERE (channel_id = """ + str(ctx.channel.id) + """);
                                                """)
                    await ctx.send(embed=disnake.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_removed').replace('&1', ctx.channel.name), colour=899718))

                # If this channel is NOT already in the database, send an error
                else:
                    await ctx.send(embed=disnake.Embed(description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_nonexistent'), colour=0xff0000))

            # If the user does not have operator permissions, send an error
            else:
                await ctx.send(embed=disnake.Embed(title=bot.lang.get(str(ctx.guild.id)).get('denied'),
                                                   description=bot.lang.get(str(ctx.guild.id)).get('no_access'),
                                                   colour=0xff0000))

        # Set game type args
        if ("solo" in args) or ("Solo" in args):
            playermode_record = 'solo'

        if ("multiplayer" in args) or ("Multiplayer" in args):
            playermode_record = 'multiplayer'

        if ("casual" in args) or ("Casual" in args):
            gamemode_record = 'casual'

        if ("competitive" in args) or ("Wettstreit" in args):
            gamemode_record = 'competitive'

        if ("start" in args) or ("begin" in args) or ("Start" in args):
            # If this channel is NOT currently active
            if not ctx.channel.id in self.games:
                # Add the required info to the database and send a startup message
                self.games[ctx.channel.id] = {}
                if playermode_record:
                    self.games[ctx.channel.id]['playermode'] = playermode_record
                else:
                    self.games[ctx.channel.id]['playermode'] = 'multiplayer'
                if gamemode_record:
                    self.games[ctx.channel.id]['gamemode'] = gamemode_record
                else:
                    self.games[ctx.channel.id]['gamemode'] = 'casual'

                # Select a random word to start
                word = random.choice(self.permitted_words)
                self.permitted_words.remove(word)

                # Add this channel as a slot in the recent word list
                self.recent_words[ctx.channel.id] = []

                # Add this channel as a slot in the previous player list
                self.previous_player[ctx.channel.id] = bot.bot.user.id

                # Add this channel as a slot in the points list
                self.points[ctx.channel.id] = {}

                # Set the previous word
                self.previous_word[ctx.channel.id] = word

                return_string = "**" + bot.lang.get(str(ctx.guild.id)).get('solo') + "**: "

                if playermode_record == 'solo':
                    return_string += bot.lang.get(str(ctx.guild.id)).get('true')
                else:
                    return_string += bot.lang.get(str(ctx.guild.id)).get('false')

                return_string += "\n**" + bot.lang.get(str(ctx.guild.id)).get('competitive') + "**: "

                if gamemode_record == 'competitive':
                    return_string += bot.lang.get(str(ctx.guild.id)).get('true')
                else:
                    return_string += bot.lang.get(str(ctx.guild.id)).get('false')

                await ctx.send(embed=disnake.Embed(
                    title=bot.lang.get(str(ctx.guild.id)).get('wordgame_starting'),
                    description=return_string,
                    colour=899718))
                await ctx.send(embed=disnake.Embed(
                    description=bot.lang.get(str(ctx.guild.id)).get('wordgame_first_word').replace('&1', convert_back(word)),
                    colour=899718))
            # If the channel IS currently active, send an error
            else:
                await ctx.send(embed=disnake.Embed(
                    description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_active'),
                    colour=0xff0000))

        if ("stop" in args) or ("end" in args) or ("Ende" in args):
            # If this channel IS currently active
            if ctx.channel.id in self.games:
                
                # Replace values in self.permitted_words
                with open('cogs/wordgame/permitted_words.txt', 'r', encoding='utf-8') as f:
                    self.permitted_words = []
                    for line in f:
                        self.permitted_words.append(line.strip())

                if self.games.get(ctx.channel.id).get('playermode') == 'solo':
                    await ctx.send(embed=disnake.Embed(
                        description=bot.lang.get(str(ctx.guild.id)).get('wordgame_stopping'),
                        colour=899718))
                else:
                    return_string = "**" + bot.lang.get(str(ctx.guild.id)).get('wordgame_round_points') + "**:\n"
                    sort_dict = sorted(self.points.get(ctx.channel.id).items(), key=lambda x: x[1], reverse=True)
                    sorted_dict = {}
                    for i in sort_dict:
                        sorted_dict[i[0]] = i[1]
                    for player in sorted_dict:
                        # Get user id
                        user = player
                        # Get the member from the user ID
                        name = bot.disnake.Guild.get_member(ctx.guild, user)
                        # Get their server nickname
                        name = str(name.nick)

                        # If the player has no nickname
                        if name == "None":
                            # Get the user from the user ID
                            name = bot.bot.get_user(user)
                            # Get the user's display name
                            name = str(name.name)
                        return_string += "- " + name + ": " + str(self.points.get(ctx.channel.id).get(player)) + "\n"

                        points = execute_read_query(players_db, "SELECT [player_id], [points], [guild_id] FROM players WHERE ([guild_id] = '" + str(ctx.guild.id) + "') AND ([player_id] = '" + str(player) + "')")
                        if not points:
                            execute_query(players_db, "INSERT INTO players (player_id, points, guild_id) VALUES ('" + str(player) + "','" + str(self.points.get(ctx.channel.id).get(player)) + "','" + str(ctx.guild.id) + "');")
                        else:
                            execute_query(players_db, "UPDATE players SET [points] = '" + str(int(execute_read_query(players_db, "SELECT [player_id], [points], [guild_id] FROM players WHERE ([guild_id] = '" + str(ctx.guild.id) + "') AND ([player_id] = '" + str(player) + "')")[0][1]) + self.points.get(ctx.channel.id).get(player)) + "' WHERE ([guild_id] = '" + str(ctx.guild.id) + "') AND ([player_id] = '" + str(player) + "')")

                    await ctx.channel.send(embed=disnake.Embed(
                        title=bot.lang.get(str(ctx.guild.id)).get('wordgame_stopping'),
                        description=return_string,
                        colour=899718))

                # Remove this channel from the database and send a confirmation message
                self.games.pop(ctx.channel.id)
                # Remove this channel from the recent word list
                self.recent_words.pop(ctx.channel.id)
                # Remove this channel from the previous player list
                self.previous_player.pop(ctx.channel.id)
                # Remove this channel from the points list
                self.points.pop(ctx.channel.id)
            # If the channel is NOT currently active, send an error
            else:
                await ctx.send(embed=disnake.Embed(
                    description=bot.lang.get(str(ctx.guild.id)).get('wordgame_channel_inactive'),
                    colour=0xff0000))

        # Reset the permissions variable
        is_op = False

    @commands.Cog.listener()
    async def on_message(self, message):
        lowered_msg = message.content.lower()
        global converted_msg
        global word

        if lowered_msg in exception_words:
            converted_msg = exception_words.get(lowered_msg)
        else:
            converted_msg = lowered_msg.replace('aw', 'á').replace('ay', 'à').replace('ew', 'é').replace('ey', 'è')\
                .replace('ll', 'j').replace('rr', 'ʀ')\
                .replace('ng', 'ŋ').replace('ts', 'c')\
                .replace('px', 'b').replace('tx', 'd').replace('kx', 'g')

        if message.channel.id in self.games:
            if message.author != bot.bot.user:
                if not message.content.startswith('?'):
                    if converted_msg in forbidden_words.get('aw'):
                        await message.channel.send(embed=disnake.Embed(
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_aw'),
                            colour=0xff0000))
                    elif converted_msg in forbidden_words.get('ew'):
                        await message.channel.send(embed=disnake.Embed(
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ew'),
                            colour=0xff0000))
                    elif converted_msg in forbidden_words.get('rr'):
                        await message.channel.send(embed=disnake.Embed(
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_rr'),
                            colour=0xff0000))
                    elif converted_msg in forbidden_words.get('ll'):
                        await message.channel.send(embed=disnake.Embed(
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ll'),
                            colour=0xff0000))
                    elif converted_msg in forbidden_words.get('space'):
                        await message.channel.send(embed=disnake.Embed(
                            description=bot.lang.get(str(message.guild.id)).get('wordgame_no_spaces'),
                            colour=0xff0000))
                    else:
                        if converted_msg in self.total_permitted_words:
                            word = converted_msg
                            if word[0] == self.previous_word.get(message.channel.id)[-1]:
                                if ((self.games.get(message.channel.id).get('playermode') == 'multiplayer') and self.previous_player.get(message.channel.id) != message.author.id) or (self.games.get(message.channel.id).get('playermode') == 'solo'):
                                    if word not in self.recent_words.get(message.channel.id):
                                        if ((self.games.get(message.channel.id).get('gamemode') == 'competitive') and (word in self.permitted_words)) or (self.games.get(message.channel.id).get('gamemode') == 'casual'):
                                            # Get user id
                                            user = message.author.id
                                            # Get the member from the user ID
                                            name = bot.disnake.Guild.get_member(message.guild, user)
                                            # Get their server nickname
                                            name = str(name.nick)

                                            # If the player has no nickname
                                            if name == "None":
                                                # Get the user from the user ID
                                                name = bot.bot.get_user(user)
                                                # Get the user's display name
                                                name = str(name.name)

                                            await message.channel.send(embed=disnake.Embed(
                                                description=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_word_said').replace('&1', name).replace('&2',
                                                                                                      convert_back(
                                                                                                          word)),
                                                colour=899718))

                                            self.previous_player[message.channel.id] = message.author.id
                                            self.previous_word[message.channel.id] = word
                                            self.remove_word(self.previous_word.get(message.channel.id),
                                                             message.channel.id)
                                            if self.games.get(message.channel.id).get('playermode') == 'solo':
                                                self.previous_player[message.channel.id] = bot.bot.user.id
                                                self.previous_word[message.channel.id] = self.random_word(
                                                    message.channel.id)
                                                if self.previous_word.get(message.channel.id) is not None:
                                                    self.remove_word(self.previous_word.get(message.channel.id),
                                                                     message.channel.id)
                                                    self.previous_player[message.channel.id] = bot.bot.user.id
                                                    await message.channel.send(embed=disnake.Embed(
                                                        description=bot.lang.get(str(message.guild.id)).get(
                                                            'wordgame_word_said').replace('&1',
                                                                                          bot.bot.user.display_name).replace(
                                                            '&2',
                                                            convert_back(self.previous_word.get(message.channel.id))),
                                                        colour=899718))

                                                    global available
                                                    available = False
                                                    for word in self.permitted_words:
                                                        if word[0] == self.previous_word.get(message.channel.id)[-1]:
                                                            available = True
                                                    if not available:
                                                        await self.win(message.channel.id, bot.bot.user.id)

                                                else:
                                                    await self.win(message.channel.id, message.author.id)

                                            # If playermode is multiplayer
                                            else:
                                                if message.author.id in self.points.get(message.channel.id):
                                                    self.points.get(message.channel.id)[message.author.id] += 1
                                                else:
                                                    self.points.get(message.channel.id)[message.author.id] = 1

                                                available = False
                                                for word in self.permitted_words:
                                                    if word[0] == self.previous_word.get(message.channel.id)[-1]:
                                                        available = True
                                                if not available:
                                                    if message.author.id in self.points.get(message.channel.id):
                                                        self.points.get(message.channel.id)[message.author.id] += 10
                                                    else:
                                                        self.points.get(message.channel.id)[message.author.id] = 10
                                                    await self.win(message.channel.id, message.author.id)

                                        elif (self.games.get(message.channel.id).get('gamemode') == 'competitive') and (word in self.total_permitted_words):
                                            await message.channel.send(embed=disnake.Embed(
                                                description=bot.lang.get(str(message.guild.id)).get('wordgame_already_used'),
                                                colour=0xff0000))
                                    elif self.games.get(message.channel.id).get('gamemode') != 'competitive':
                                        await message.channel.send(embed=disnake.Embed(
                                            description=bot.lang.get(str(message.guild.id)).get('wordgame_used_recently'),
                                            colour=0xff0000))
                                else:
                                    await message.channel.send(embed=disnake.Embed(
                                        description=bot.lang.get(str(message.guild.id)).get('wordgame_already_said'),
                                        colour=0xff0000))
                            else:
                                await message.channel.send(embed=disnake.Embed(
                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_incorrect_word_end'),
                                    colour=0xff0000))

    @commands.command(name='points', aliases=['punkte'])
    async def points(self, ctx, *args):
        point_list = execute_read_query(players_db, "SELECT player_id, points FROM players WHERE guild_id = '" + str(ctx.guild.id) + "' ORDER BY points DESC;")
        return_string = ""
        user_stats = ""
        for num, player in enumerate(point_list):
            if str(player[0]) == str(ctx.author.id):
                user_stats = (num + 1, player[1])

            # Get user id
            user = int(player[0])
            # Get the member from the user ID
            name = bot.disnake.Guild.get_member(ctx.guild, user)
            # Get their server nickname
            name = str(name.nick)

            # If the player has no nickname
            if name == "None":
                # Get the user from the user ID
                name = bot.bot.get_user(user)
                # Get the user's display name
                name = str(name.name)

            return_string += "- " + name + ": " + str(player[1]) + "\n"

        return_string += "\n\n"
        if user_stats[0] == 1:
            return_string += bot.lang.get(str(ctx.guild.id)).get('points_first_place').replace('&1', str(user_stats[0])).replace('&2', str(user_stats[1]))
        if user_stats[0] == 2:
            return_string += bot.lang.get(str(ctx.guild.id)).get('points_second_place').replace('&1', str(user_stats[0])).replace('&2', str(user_stats[1]))
        if user_stats[0] == 3:
            return_string += bot.lang.get(str(ctx.guild.id)).get('points_third_place').replace('&1', str(user_stats[0])).replace('&2', str(user_stats[1]))
        if int(user_stats[0]) > 3:
            return_string += bot.lang.get(str(ctx.guild.id)).get('points_general_place').replace('&1', str(user_stats[0])).replace('&2', str(user_stats[1]))

        await ctx.channel.send(embed=disnake.Embed(
            title=bot.lang.get(str(ctx.guild.id)).get('points_title') + ":",
            description=return_string,
            colour=899718))


def setup(bot):
    bot.add_cog(WordgameCog(bot))
    print('Added new Cog: ' + str(WordgameCog))
