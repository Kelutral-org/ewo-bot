import json
import random
import sqlite3
from sqlite3 import Error
import copy

import disnake
import requests
from disnake.ext import commands
import bot


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
word_frequency_db = create_connection('cogs/frequency/word_frequency.db')


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
    except Error as e:
        if str(e) != 'UNIQUE constraint failed: words.word_info':
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
  player_id INTEGER NOT NULL, 
  points INTEGER NOT NULL, 
  guild_id INTEGER NOT NULL, 
  UNIQUE (player_id, points, guild_id)
);
""")

execute_query(channels_db, """
CREATE TABLE IF NOT EXISTS channels (
  channel_id INTEGER NOT NULL, 
  guild_id INTEGER NOT NULL, 
  PRIMARY KEY (channel_id)
);
""")


# Some boiler plate variables that multiple classes need to access
active_channels = {}
full_word_initial_lookup = {}
valid_words = {}
navi_letters = ['\'', 'a', 'ä', 'à', 'e', 'é', 'è', 'f', 'h', 'i', 'ì', 'k', 'g', 'l', 'm', 'n', 'ŋ', 'o', 'p', 'b', 'r', 's', 't', 'c', 'd', 'u', 'v', 'w', 'y', 'z']


# Takes a word_info and changes the letters to monographic representations
def convert_to_monographic(word):
    return word.replace('ng', 'ŋ').replace('ay', 'à').replace('ey', 'è').replace('aw', 'á').replace('ew', 'é') \
        .replace('ll', 'ʟ').replace('rr', 'ʀ').replace('ts', 'c').replace('px', 'b').replace('tx', 'd') \
        .replace('kx', 'g')


# Chooses a random word_info from the list of valid words and returns it
# (returns only the name, to get the data use valid_words.get(word_info))
def choose_first_word(channel_id: int, sound: str):
    word = random.choice(full_word_initial_lookup.get(sound))
    return word


# Chooses a random word_info from the list of valid words and returns it
# (returns only the name, to get the data use valid_words.get(word_info))
def choose_word(channel_id: int, sound: str):
    if active_channels.get(str(channel_id)).get("gamemode") == "casual":
        word = random.choice(active_channels.get(str(channel_id)).get("word_initial_lookup").get(sound))

        if word in active_channels.get(str(channel_id)).get("recent_words"):
            choose_word(channel_id, sound)
        else:
            return word
    if active_channels.get(str(channel_id)).get("gamemode") == "competitive":
        if active_channels.get(str(channel_id)).get("word_initial_lookup").get(sound):
            word = random.choice(active_channels.get(str(channel_id)).get("word_initial_lookup").get(sound))

            if word in active_channels.get(str(channel_id)).get("recent_words"):
                choose_word(channel_id, sound)
            else:
                return word
        else:
            return None
    if active_channels.get(str(channel_id)).get("gamemode") == "deathmatch":
        pass


# Ends the game in the given channel. Does not check if a game is active.
async def end_game(channel_id: int, inter: disnake.Interaction):
    channel = await bot.bot.fetch_channel(channel_id)

    embed = disnake.Embed(title=bot.lang.get(str(channel.guild.id)).get('wordgame_title'),
                                        description=bot.lang.get(str(channel.guild.id)).get('wordgame_stopping'),
                                        colour=899718)

    if active_channels.get(str(channel_id)).get("playmode") == "multiplayer":

        points = ""
        sorted_points = sorted(active_channels.get(str(channel_id)).get("points").items(), key=lambda x: x[1], reverse=True)
        for player in sorted_points:
            points += "・" + bot.get_name(int(player[0]), channel.guild) + ": " + str(player[1]) + "\n"

            players = execute_read_query(players_db, "SELECT * FROM players WHERE player_id = " + player[0] + " AND guild_id = " + str(channel.guild.id))
            if not players:
                execute_query(players_db, """
                                            INSERT INTO
                                              players (player_id, points, guild_id)
                                            VALUES
                                              ('""" + player[0] + """', '""" + str(player[1]) + """', '""" + str(channel.guild.id) + """');
                                            """)
            else:
                execute_query(players_db, "UPDATE players SET points = " + str(players[0][1] + player[1]) + " WHERE player_id = " + player[0] + " AND guild_id = " + str(channel.guild.id))

        if active_channels.get(str(channel_id)).get("gamemode") == "casual":
            embed.add_field(name=bot.lang.get(str(channel.guild.id)).get('points') + ":", value=points)

    await inter.response.send_message(embed=embed)

    active_channels.pop(str(channel_id))


async def win(winner_id: int, channel_id: int):
    active_channels[str(channel_id)]["points"][str(winner_id)] += 10

    channel = await bot.bot.fetch_channel(channel_id)

    embed = disnake.Embed(title=bot.lang.get(str(channel.guild.id)).get('wordgame_title'),
                          description=bot.lang.get(str(channel.guild.id)).get('wordgame_win').replace('&1', bot.get_name(winner_id, channel.guild)),
                          colour=899718)

    if active_channels.get(str(channel_id)).get("playmode") == "multiplayer":

        points = ""
        sorted_points = sorted(active_channels.get(str(channel_id)).get("points").items(), key=lambda x: x[1],
                               reverse=True)
        for player in sorted_points:
            points += "・" + bot.get_name(int(player[0]), channel.guild) + ": " + str(player[1]) + "\n"

            players = execute_read_query(players_db, "SELECT * FROM players WHERE player_id = " + player[
                0] + " AND guild_id = " + str(channel.guild.id))
            if not players:
                execute_query(players_db, """
                                                INSERT INTO
                                                  players (player_id, points, guild_id)
                                                VALUES
                                                  ('""" + player[0] + """', '""" + str(player[1]) + """', '""" + str(
                    channel.guild.id) + """');
                                                """)
            else:
                execute_query(players_db,
                              "UPDATE players SET points = " + str(players[0][1] + player[1]) + " WHERE player_id = " +
                              player[0] + " AND guild_id = " + str(channel.guild.id))

        embed.add_field(name=bot.lang.get(str(channel.guild.id)).get('points') + ":", value=points)

    await channel.send(embed=embed)

    active_channels.pop(str(channel_id))


# The class for the playermode dropdown in the wordgame start ui.
class PlaymodeDropdown(disnake.ui.Select):
    def __init__(self):
        playmode_options = [
            disnake.SelectOption(label='Multiplayer',
                                 description='More info in /wordgame info!',
                                 emoji='👨‍👩‍👧‍👦'),
            disnake.SelectOption(label='Solo',
                                 description='More info in /wordgame info!',
                                 emoji='🧑')
        ]

        super().__init__(placeholder='Please select the playmode...', min_values=1, max_values=1, options=playmode_options)


# The class for the gamemode dropdown in the wordgame start ui.
class GamemodeDropdown(disnake.ui.Select):
    def __init__(self):
        gamemode_options = [
            disnake.SelectOption(label='Casual',
                                 description='More info in /wordgame info!',
                                 emoji='🚶'),
            disnake.SelectOption(label='Competitive',
                                 description='More info in /wordgame info!',
                                 emoji='🏃'),
            disnake.SelectOption(label='Deathmatch',
                                 description='More info in /wordgame info!',
                                 emoji='💀'),
        ]

        super().__init__(placeholder='Please select the gamemode...', min_values=1, max_values=1, options=gamemode_options)


# The class for the deathmatch start ui.
class DeathmatchStartView(disnake.ui.View):
    def __init__(self, playmode: str, gamemode: str, initiator: int):
        super().__init__()
        self.initiator = initiator
        self.playmode = playmode
        self.gamemode = gamemode
        self.players = []
        self.value = None
        self.timeout = None

    @disnake.ui.button(label='Join', style=disnake.ButtonStyle.blurple)
    async def join(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not inter.author.id in self.players:
            self.players.append(inter.author.id)

            # Get the channel from the id
            channel = await bot.bot.fetch_channel(inter.channel_id)

            await channel.send(embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                      description=bot.lang.get(str(inter.guild_id)).get('wordgame_joined').replace('&1', bot.get_name(inter.author.id, inter.guild)),
                                      colour=899718))

    @disnake.ui.button(label='Start', style=disnake.ButtonStyle.green)
    async def start(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        print(self.players)

        if not len(self.players) <= 1:
            self.playmode = "multiplayer"

            if inter.author.id == self.initiator:

                # This sets the list of usable words for THE CURRENT GAME
                word_initial_lookup = full_word_initial_lookup

                # Chose the first word_info by randomly choosing a sound from the list of possible sounds
                first_word = choose_first_word(inter.channel_id, random.choice(navi_letters))
                # Get the first word_info's data
                first_word_data = valid_words.get(first_word)

                # Set all of the necessary data in the list of active channels
                active_channels[str(inter.channel_id)] = {}
                active_channels[str(inter.channel_id)]["playmode"] = self.playmode
                active_channels[str(inter.channel_id)]["gamemode"] = self.gamemode
                active_channels[str(inter.channel_id)]["points"] = {}
                active_channels[str(inter.channel_id)]["word_initial_lookup"] = word_initial_lookup
                active_channels[str(inter.channel_id)]["previous_player_id"] = bot.bot.user.id
                active_channels[str(inter.channel_id)]["previous_word_end"] = first_word_data.get("last_sound")
                active_channels[str(inter.channel_id)]["used_words"] = [first_word]
                active_channels[str(inter.channel_id)]["players"] = self.players

                # Create an embed to send information about the game
                embed = disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                      description=bot.lang.get(str(inter.guild_id)).get('wordgame_starting'),
                                      colour=899718)

                # Add info to above embed
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_playmode') + ":",
                                value=self.playmode.capitalize())
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_gamemode') + ":",
                                value=self.gamemode.capitalize())

                # Send above embed publicly
                await inter.response.send_message(embed=embed)

                # Get the channel from the id
                channel = await bot.bot.fetch_channel(inter.channel_id)

                # Create an embed to hold data about the first word_info
                embed = disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                      description=bot.lang.get(str(inter.guild_id)).get('wordgame_first_word').replace('&1', "**" + first_word + "**"),
                                      colour=899718)

                # Get language data from the current guild
                lang_value = bot.execute_read_query(
                    "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                        inter.guild_id) + "')")[0][0]
                if lang_value == "English":
                    # If language is English, set the Meaning entry to be the English translation
                    embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_meaning') + ":",
                                    value=first_word_data.get("translations").get("en"))
                elif lang_value == "German":
                    # If language is German, set the Meaning entry to be the German translation
                    embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_meaning') + ":",
                                    value=first_word_data.get("translations").get("de"))

                # Set the rest of the fields for the first word_info data
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_pronunciation') + ":",
                                value=first_word_data.get("pronunciation"))
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_pos') + ":",
                                value=first_word_data.get("pos"))
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_frequency') + ":",
                                value=str(first_word_data.get("frequency")) + "%")

                # Send above embed publicly
                await channel.send(embed=embed)

                # Some stuff I don't really understand for buttons
                self.value = True
                self.stop()


# The class for the wordgame start ui.
class StartGameView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.playmode = ""
        self.gamemode = ""
        self.value = None

        # Create variables for the dropdowns
        self.playmode_dropdown = PlaymodeDropdown()
        self.gamemode_dropdown = GamemodeDropdown()

        # Add the dropdowns
        self.add_item(self.playmode_dropdown)
        self.add_item(self.gamemode_dropdown)

    # Start button
    @disnake.ui.button(label='Start', style=disnake.ButtonStyle.green)
    async def start(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):

        # If both dropdowns have been selected
        if self.playmode_dropdown.values and self.gamemode_dropdown.values:

            # Get the data from the dropdowns
            self.playmode = self.playmode_dropdown.values[0].lower()
            self.gamemode = self.gamemode_dropdown.values[0].lower()

            if self.gamemode == "deathmatch":
                deathmatch_start_view = DeathmatchStartView(self.playmode, self.gamemode, inter.author.id)

                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_deathmatch_prompt'),
                                        colour=899718), view=deathmatch_start_view)
            else:
                # This sets the list of usable words for THE CURRENT GAME
                word_initial_lookup = full_word_initial_lookup

                # Chose the first word_info by randomly choosing a sound from the list of possible sounds
                first_word = choose_first_word(inter.channel_id, random.choice(navi_letters))
                # Get the first word_info's data
                first_word_data = valid_words.get(first_word)

                word_initial_lookup[first_word_data.get("first_sound")].remove(first_word)

                # Set all of the necessary data in the list of active channels
                active_channels[str(inter.channel_id)] = {}
                active_channels[str(inter.channel_id)]["playmode"] = self.playmode
                active_channels[str(inter.channel_id)]["gamemode"] = self.gamemode
                active_channels[str(inter.channel_id)]["points"] = {}
                active_channels[str(inter.channel_id)]["word_initial_lookup"] = word_initial_lookup
                active_channels[str(inter.channel_id)]["previous_player_id"] = bot.bot.user.id
                active_channels[str(inter.channel_id)]["previous_word_end"] = first_word_data.get("last_sound")
                active_channels[str(inter.channel_id)]["recent_words"] = []

                # Some mode specific data
                if self.playmode == "solo":
                    active_channels[str(inter.channel_id)]["player"] = inter.author.id
                if self.gamemode == "competitive":
                    active_channels[str(inter.channel_id)]["used_words"] = []

                # Create an embed to send information about the game
                embed = disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                      description=bot.lang.get(str(inter.guild_id)).get('wordgame_starting'),
                                      colour=899718)

                # Add info to above embed
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_playmode') + ":", value=self.playmode.capitalize())
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_gamemode') + ":", value=self.gamemode.capitalize())

                # Send above embed publicly
                await inter.response.send_message(embed=embed)

                # Get the channel from the id
                channel = await bot.bot.fetch_channel(inter.channel_id)

                # Create an embed to hold data about the first word_info
                embed = disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                      description=bot.lang.get(str(inter.guild_id)).get('wordgame_first_word').replace('&1', "**" + first_word + "**"),
                                      colour=899718)

                # Get language data from the current guild
                lang_value = bot.execute_read_query(
                    "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                        inter.guild_id) + "')")[0][0]
                if lang_value == "English":
                    # If language is English, set the Meaning entry to be the English translation
                    embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_meaning') + ":", value=first_word_data.get("translations").get("en"))
                elif lang_value == "German":
                    # If language is German, set the Meaning entry to be the German translation
                    embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_meaning') + ":", value=first_word_data.get("translations").get("de"))

                # Set the rest of the fields for the first word_info data
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_pronunciation') + ":", value=first_word_data.get("pronunciation"))
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_pos') + ":", value=first_word_data.get("pos"))
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_frequency') + ":", value=str(first_word_data.get("frequency")) + "%")

                # Send above embed publicly
                await channel.send(embed=embed)

                # Some stuff I don't really understand for buttons
                self.value = True
                self.stop()


# Wordgame Cog
class WordgameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Get the list of wordgame channels
        self.channels = execute_read_query(channels_db, "SELECT * FROM channels")

        # Add entries to the list of first-letter lookups for every letter in the language
        for letter in navi_letters:
            full_word_initial_lookup[letter] = []

        # Get the total words process for the word_info frequency list (to use in calculating frequency percentage)
        word_frequency_total_processed = 0
        words = execute_read_query(word_frequency_db, "SELECT * FROM words")
        for word in words:
            word_frequency_total_processed += word[1]

        print("WORDGAME: Compiling valid word_info list...")
        # List of unusable words, soon to be filled
        self.invalid_words = {"aw": [], "ew": [], "ay": [], "ey": [], "ll": [], "rr": [], "ì": [], "ä": [], "space": []}
        # Get the list of every word_info in Na'vi from reykunyu
        reykunyu_all = requests.get("https://reykunyu.wimiso.nl/api/frau").json()

        ignore_startswith = ['aw', 'ew', 'ay', 'ey', 'll', 'rr', 'ì', 'ä']

        # For every word_info in above list
        for word in reykunyu_all:
            # If the word_info ends in aw, add it to unusable words. Not enough words start with it.
            if (reykunyu_all.get(word).get("na'vi").lower().endswith('aw')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("aw"):
                    self.invalid_words["aw"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info ends in ew, add it to unusable words. Not enough words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ew')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("ew"):
                    self.invalid_words["ew"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info ends in ay, add it to unusable words. Not enough words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ay')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("ay"):
                    self.invalid_words["ay"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info ends in ey, add it to unusable words. Not enough words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ey')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("ey"):
                    self.invalid_words["ey"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info ends in ll, add it to unusable words. No words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ll')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("ll"):
                    self.invalid_words["ll"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info ends in rr, add it to unusable words. No words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('rr')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("rr"):
                    self.invalid_words["rr"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info ends in ì, add it to unusable words. Not enough words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ì')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("ì"):
                    self.invalid_words["ì"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info ends in ä, add it to unusable words. Not enough words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ä')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("ä"):
                    self.invalid_words["ä"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word_info contains a space, add it to unusable words.
            # They're usually just multiple other words or si verbs.
            elif ' ' in reykunyu_all.get(word).get("na'vi").lower():
                if reykunyu_all.get(word).get("na'vi").lower() not in self.invalid_words.get("space"):
                    self.invalid_words["space"].append(reykunyu_all.get(word).get("na'vi").lower())

            elif reykunyu_all.get(word).get("na'vi").lower().startswith(tuple(ignore_startswith)):
                pass

            # If all above tests pass, we know the word_info is valid and can add it to the list
            else:
                if reykunyu_all.get(word).get("na'vi").lower() not in valid_words:
                    # Add the word_info to the list alongside some data
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()] = {}
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["translations"] = reykunyu_all.get(word).get("translations")[0]

                    # Placeholder string, soon to be filled
                    monographic = ""
                    try:
                        # Get pronunciation and stress data if it exists
                        pronunciation = reykunyu_all.get(word).get("pronunciation")[0].lower()
                        reykunyu_stress = reykunyu_all.get(word).get("pronunciation")[1]

                        # Split the pronunciation data into syllables
                        split_pronunciation = pronunciation.split('-')

                        # Copy that to modify it (copied because more code uses the original)
                        stressed_pronunciation = copy.deepcopy(split_pronunciation)

                        # Indicate the stressed syllable by making it uppercase and join it back together
                        stressed_pronunciation[reykunyu_stress - 1] = split_pronunciation[reykunyu_stress - 1].upper()
                        word_pronunciation = '-'.join(stressed_pronunciation)

                        # Copy the pronunciation again
                        monographic_syllables = copy.deepcopy(split_pronunciation)

                        # For every syllable, convert it to monographic using the function
                        # (done to fix exceptions like eyawr)
                        for num, syllable in enumerate(split_pronunciation):
                            monographic_syllables[num] = convert_to_monographic(syllable)

                        # Set the placeholder string to the new, joined monographic word_info
                        monographic = ''.join(monographic_syllables)

                        # Add the word_info's pronunciation to the data
                        valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = word_pronunciation

                    # If either of these exeptions are thrown,
                    # the list doesn't contain any pronunciation info for this word_info, and this entire step can be skipped.
                    except TypeError:
                        valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = "N/A"
                    except IndexError:
                        valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = "N/A"

                    # Add the part of speech to the data
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pos"] = reykunyu_all.get(word).get(
                        "type")

                    # Get the frequency of this word_info from the word_info frequency list
                    word_frequency = execute_read_query(word_frequency_db,
                                                        "SELECT count FROM words WHERE (word = '" + reykunyu_all.get(
                                                            word).get("na'vi").lower().replace('\'', '’') + "')")
                    try:
                        # Calculate the frequency percentage
                        frequency_percentage = round(word_frequency[0][0] / word_frequency_total_processed * 100, 2)
                    # If this exception is thrown, the word_info is not in the list, and the percentage is then zero
                    except IndexError:
                        frequency_percentage = 0
                    except TypeError:
                        frequency_percentage = 0

                    # Add the frequency to the data
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["frequency"] = frequency_percentage

                    # If there is no monographic form (pronunciation information was not available),
                    # simply use the word_info and hope for the best
                    if not monographic:
                        monographic = convert_to_monographic(reykunyu_all.get(word).get("na'vi").lower())

                    # Add the first and last sounds of the word_info to the data
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["first_sound"] = monographic[0]
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["last_sound"] = monographic[-1]

                    if reykunyu_all.get(word).get("na'vi").lower() not in full_word_initial_lookup.get(monographic[0]):
                        # Append the word_info into the correct entry in the lookup table,
                        # using the monographic info used above
                        full_word_initial_lookup[monographic[0]].append(reykunyu_all.get(word).get("na'vi").lower())

        with open("cogs/wordgame/word_info/valid_words.json", 'w', encoding='utf-8') as f:
            json.dump(valid_words, f, indent=4, ensure_ascii=False)
        with open("cogs/wordgame/word_info/invalid_words.json", 'w', encoding='utf-8') as f:
            json.dump(self.invalid_words, f, indent=4, ensure_ascii=False)
        with open("cogs/wordgame/word_info/full_word_initial_lookup.json", 'w', encoding='utf-8') as f:
            json.dump(full_word_initial_lookup, f, indent=4, ensure_ascii=False)

        print("WORDGAME: Complete!")

    # Update the list of channels, used when it is changed with addchannel and removechannel
    def update_channels(self):
        self.channels = execute_read_query(channels_db, "SELECT * FROM channels")

    # This does nothing, it just holds the subcommands
    @commands.slash_command(name="wordgame", description="A basic wordgame to help learn vocabulary!", default_permission=True, guild_ids=bot.test_guilds)
    async def wordgame(self, inter):
        pass

    # Start command :D
    @wordgame.sub_command(name="start", description="Start a wordgame in the current channel.")
    async def start(self, inter):
        # If this channel is a wordgame channel
        if tuple([inter.channel_id, inter.guild_id]) in self.channels:
            # If the channel is already active, send an error
            if str(inter.channel_id) in active_channels:
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_active'),
                                        colour=0xff0000), ephemeral=True)
            else:
                # Get the start game ui
                view = StartGameView()
                # Send an embed to the user with a prompt for the start, alongside the ui
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_start_prompt'),
                                        colour=899718), ephemeral=True, view=view)
                # Wait until the ui has been used before continuing (all start code is handled in the ui class above)
                #await view.wait()
        # If this channel is not a wordgame channel, send an error
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                    description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_nonexistent'),
                                    colour=0xff0000), ephemeral=True)

    # Stop command
    @wordgame.sub_command(name="stop", description="End the current wordgame.")
    async def stop(self, inter):
        # If this channel is a wordgame channel
        if tuple([inter.channel_id, inter.guild_id]) in self.channels:
            # If the channel is not active, send an error
            if str(inter.channel_id) not in active_channels:
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_inactive'),
                                        colour=0xff0000), ephemeral=True)
            else:
                # End the game using the function
                await end_game(inter.channel_id, inter)
        # If this channel is not a wordgame channel, send an error
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                    description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_nonexistent'),
                                    colour=0xff0000), ephemeral=True)

    @wordgame.sub_command(name="addchannel", description="Add this channel to the list of wordgame channels.")
    async def addchannel(self, inter):
        # Permissions test
        is_op = False
        # Test if user is an Ewo' operator, or a mod/admin
        for perm in inter.permissions:
            if (perm == ('manage_guild', True)) or (perm == ('administrator', True)) or (inter.author.id in bot.config.operators):
                is_op = True

        # If user has permission
        if is_op:
            # If the channel is already a wordgame channel, send an error
            if tuple([inter.channel_id, inter.guild_id]) in self.channels:
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_exists'),
                                        colour=0xff0000), ephemeral=True)
            else:
                # Add the channel to the database
                execute_query(channels_db, """
                                            INSERT INTO
                                              channels (channel_id, guild_id)
                                            VALUES
                                              (""" + str(inter.channel_id) + """, """ + str(inter.guild_id) + """);
                                            """)
                # Get the channel from the id and gets its name
                channel = await self.bot.fetch_channel(inter.channel_id)
                name = channel.name

                # Send a private confirmation message, using the name above
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_added').replace('&1', name),
                                        colour=899718), ephemeral=True)
                # Update the local list of channels
                self.update_channels()
        # If user does not have permission, send an error
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('denied'),
                                    description=bot.lang.get(str(inter.guild_id)).get('no_access'),
                                    colour=0xff0000), ephemeral=True)

    @wordgame.sub_command(name="removechannel", description="Remove this channel from the list of wordgame channels.")
    async def removechannel(self, inter):
        # Permissions test
        is_op = False
        # Test if user is an Ewo' operator, or a mod/admin
        for perm in inter.permissions:
            if (perm == ('manage_guild', True)) or (perm == ('administrator', True)) or (inter.author.id in bot.config.operators):
                is_op = True

        # If user has permission
        if is_op:
            # If the channel is NOT a wordgame channel, send an error
            if tuple([inter.channel_id, inter.guild_id]) not in self.channels:
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_nonexistent'),
                                        colour=0xff0000), ephemeral=True)
            else:
                # Remove the channel from the database
                execute_query(channels_db, "DELETE FROM channels WHERE channel_id = " + str(inter.channel_id) + " AND guild_id = " + str(inter.guild_id) + ";")

                # Get the channel from the id and gets its name
                channel = await self.bot.fetch_channel(inter.channel_id)
                name = channel.name

                # Send a private confirmation message, using the name above
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_removed').replace('&1', name),
                                        colour=899718), ephemeral=True)
                # Update the local list of channels
                self.update_channels()
        # If user does not have permission, send an error
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('denied'),
                                    description=bot.lang.get(str(inter.guild_id)).get('no_access'),
                                    colour=0xff0000), ephemeral=True)

    # Info command
    @wordgame.sub_command(name="info", description="Show some basic info about the game.")
    async def info(self, inter):
        # Empty string, to be filled soon
        info = ""

        # Get language data from the current guild
        lang_value = bot.execute_read_query(
            "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                inter.guild_id) + "')")[0][0]
        if lang_value == "English":
            # If the language is English, get the English info file.
            with open('lang/wordgame_info_english.txt', 'r', encoding='utf-8') as f:
                info = f.read()
        if lang_value == "German":
            # If the language is German, get the German info file.
            with open('lang/wordgame_info_german.txt', 'r', encoding='utf-8') as f:
                info = f.read()

        # Send the info privately, using the name above
        await inter.response.send_message(
            embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                description=info,
                                colour=899718), ephemeral=True)

    @wordgame.sub_command(name="points", description="Show the leaderboard of wordgame points.")
    async def points(self, inter):
        players = execute_read_query(players_db, "SELECT * FROM players WHERE guild_id = " + str(inter.guild_id) + " ORDER BY points DESC")
        author_player = execute_read_query(players_db, "SELECT * FROM players WHERE player_id = " + str(inter.author.id) + " AND guild_id = " + str(inter.guild_id))

        string = ""
        for player in players:
            string += "・" + bot.get_name(int(player[0]), inter.guild) + ": " + str(player[1]) + "\n"
        author_place = 1
        for player in players:
            if int(player[0]) != inter.author.id:
                author_place += 1
            else:
                break
        try:
            if author_place == 1:
                string += "\n" + bot.lang.get(str(inter.guild_id)).get('points_first_place').replace('&1', str(author_player[0][1]))
            if author_place == 2:
                string += "\n" + bot.lang.get(str(inter.guild_id)).get('points_second_place').replace('&1', str(author_player[0][1]))
            if author_place == 3:
                string += "\n" + bot.lang.get(str(inter.guild_id)).get('points_third_place').replace('&1', str(author_player[0][1]))
            if author_place >= 4:
                string += "\n" + bot.lang.get(str(inter.guild_id)).get('points_general_place').replace('&1', str(author_place)).replace('&2', str(author_player[0][1]))
        except IndexError:
            pass
        print(players)

        embed = disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'), colour=899718)
        embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('points') + ":", value=string)

        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        # A bunch of tests to make sure the channel is active and its a real user not using a command.
        if not message.author.bot:
            if not message.type == disnake.MessageType.application_command:
                if tuple([message.channel.id, message.guild.id]) in self.channels:
                    if str(message.channel.id) in active_channels:
                        playmode = active_channels.get(str(message.channel.id)).get("playmode")
                        gamemode = active_channels.get(str(message.channel.id)).get("gamemode")

                        msg = message.content.lower()

                        # Now to test if the word_info is a Na'vi word_info, and is usable.
                        # Not gonna go into detail, but it sends some errors if they aren't usable
                        if (msg.endswith('aw')) and (not ' ' in msg) and (msg in self.invalid_words.get("aw")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_aw'),
                                                    colour=0xff0000))

                        elif (msg.endswith('ew')) and (not ' ' in msg) and (msg in self.invalid_words.get("ew")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ew'),
                                                    colour=0xff0000))

                        elif (msg.endswith('ay')) and (not ' ' in msg) and (msg in self.invalid_words.get("ay")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ay'),
                                                    colour=0xff0000))

                        elif (msg.endswith('ey')) and (not ' ' in msg) and (msg in self.invalid_words.get("ey")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ey'),
                                                    colour=0xff0000))

                        elif (msg.endswith('ll')) and (not ' ' in msg) and (msg in self.invalid_words.get("ll")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ll'),
                                                    colour=0xff0000))

                        elif (msg.endswith('rr')) and (not ' ' in msg) and (msg in self.invalid_words.get("rr")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_rr'),
                                                    colour=0xff0000))

                        elif (msg.endswith('ì')) and (not ' ' in msg) and (msg in self.invalid_words.get("ì")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ì'),
                                                    colour=0xff0000))

                        elif (msg.endswith('ä')) and (not ' ' in msg) and (msg in self.invalid_words.get("ä")):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_ä'),
                                                    colour=0xff0000))

                        elif (' ' in msg) and ((msg in self.invalid_words.get("space")) or msg.endswith(' si')):
                            await message.channel.send(
                                embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_unusable_space'),
                                                    colour=0xff0000))

                        # If above tests pass, we need to test if the word_info is actually Na'vi.
                        # We can do that by finding it in valid words, since we know from the above tests it must be valid.
                        elif msg in valid_words:
                            # This tests if the word_info does not begin with the correct sound.
                            if valid_words.get(msg).get("first_sound") != active_channels.get(str(message.channel.id)).get("previous_word_end"):
                                await message.channel.send(
                                    embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                        description=bot.lang.get(str(message.guild.id)).get('wordgame_incorrect_word_end'),
                                                        colour=0xff0000))
                            elif msg not in active_channels.get(str(message.channel.id)).get("word_initial_lookup").get(valid_words.get(msg).get("first_sound")):
                                await message.channel.send(
                                    embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                        description=bot.lang.get(str(message.guild.id)).get('wordgame_already_used'),
                                                        colour=0xff0000))
                            # If the user already said a word
                            elif message.author.id == active_channels.get(str(message.channel.id)).get("previous_player_id"):
                                await message.channel.send(
                                    embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                        description=bot.lang.get(str(message.guild.id)).get('wordgame_already_said'),
                                                        colour=0xff0000))
                            else:
                                # If we've gotten to this point, we know the word is a valid Na'vi word_info,
                                # and ends with the correct sound. Now we can branch into mode-specific tests.

                                # If the playmode is solo
                                if playmode == "solo":
                                    # If the player is not the player who started the game
                                    if message.author.id != active_channels.get(str(message.channel.id)).get("player"):
                                        await message.channel.send(
                                            embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                                description=bot.lang.get(str(message.guild.id)).get('wordgame_not_in'),
                                                                colour=0xff0000))
                                    else:

                                        # If the gamemode is casual
                                        if gamemode == "casual":
                                            # If the word was used recently
                                            if msg in active_channels.get(str(message.channel.id)).get("recent_words"):
                                                await message.channel.send(embed=disnake.Embed(title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                                                               description=bot.lang.get(str(message.guild.id)).get('wordgame_used_recently'),
                                                                                               colour=0xff0000))
                                            else:
                                                active_channels[str(message.channel.id)]["recent_words"].append(msg)
                                                if len(active_channels[str(message.channel.id)].get("recent_words")) >= 5:
                                                    active_channels[str(message.channel.id)]["recent_words"].pop(0)

                                                new_word = choose_word(message.channel.id, valid_words.get(msg).get("last_sound"))

                                                new_word_data = valid_words.get(new_word)

                                                active_channels[str(message.channel.id)]["previous_player_id"] = bot.bot.user.id
                                                active_channels[str(message.channel.id)]["previous_word_end"] = new_word_data.get("last_sound")
                                                active_channels[str(message.channel.id)]["recent_words"].append(new_word)

                                                # Create an embed to hold data about the new word_info
                                                embed = disnake.Embed(
                                                    title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_word_said').replace('&1', bot.get_name(bot.bot.user.id, message.guild)).replace('&2', "**" + new_word + "**"),
                                                    colour=899718)

                                                # Get language data from the current guild
                                                lang_value = bot.execute_read_query(
                                                    "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                                                        message.guild.id) + "')")[0][0]
                                                if lang_value == "English":
                                                    # If language is English, set the Meaning entry to be the English translation
                                                    embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                        'wordgame_meaning') + ":",
                                                                    value=new_word_data.get("translations").get(
                                                                        "en"))
                                                elif lang_value == "German":
                                                    # If language is German, set the Meaning entry to be the German translation
                                                    embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                        'wordgame_meaning') + ":",
                                                                    value=new_word_data.get("translations").get(
                                                                        "de"))

                                                # Set the rest of the fields for the new word_info data
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_pronunciation') + ":",
                                                                value=new_word_data.get("pronunciation"))
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_pos') + ":", value=new_word_data.get("pos"))
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_frequency') + ":",
                                                                value=str(new_word_data.get("frequency")) + "%")

                                                # Send above embed publicly
                                                await message.channel.send(embed=embed)

                                        # If the gamemode is competitive
                                        if gamemode == "competitive":

                                            active_channels[str(message.channel.id)]["recent_words"].append(msg)
                                            active_channels[str(message.channel.id)]["word_initial_lookup"][valid_words.get(msg).get("first_sound")].remove(msg)

                                            new_word = choose_word(message.channel.id, valid_words.get(msg).get("last_sound"))

                                            if new_word is None:
                                                await win(message.author.id, message.channel.id)
                                            else:
                                                new_word_data = valid_words.get(new_word)

                                                active_channels[str(message.channel.id)][
                                                    "previous_player_id"] = bot.bot.user.id
                                                active_channels[str(message.channel.id)][
                                                    "previous_word_end"] = new_word_data.get("last_sound")

                                                # Create an embed to hold data about the new word_info
                                                embed = disnake.Embed(
                                                    title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                    description=bot.lang.get(str(message.guild.id)).get('wordgame_word_said').replace('&1', bot.get_name(bot.bot.user.id, message.guild)).replace('&2', "**" + new_word + "**"),
                                                    colour=899718)

                                                # Get language data from the current guild
                                                lang_value = bot.execute_read_query(
                                                    "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(message.guild.id) + "')")[0][0]
                                                if lang_value == "English":
                                                    # If language is English, set the Meaning entry to be the English translation
                                                    embed.add_field(name=bot.lang.get(str(message.guild.id)).get('wordgame_meaning') + ":",
                                                                    value=new_word_data.get("translations").get("en"))
                                                elif lang_value == "German":
                                                    # If language is German, set the Meaning entry to be the German translation
                                                    embed.add_field(name=bot.lang.get(str(message.guild.id)).get('wordgame_meaning') + ":",
                                                                    value=new_word_data.get("translations").get("de"))

                                                # Set the rest of the fields for the new word_info data
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get('wordgame_pronunciation') + ":",
                                                                value=new_word_data.get("pronunciation"))
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get('wordgame_pos') + ":",
                                                                value=new_word_data.get("pos"))
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get('wordgame_frequency') + ":",
                                                                value=str(new_word_data.get("frequency")) + "%")

                                                # Send above embed publicly
                                                await message.channel.send(embed=embed)

                                                active_channels[str(message.channel.id)]["recent_words"].append(new_word)
                                                active_channels[str(message.channel.id)]["word_initial_lookup"][valid_words.get(new_word).get("first_sound")].remove(new_word)

                                                if not active_channels.get(str(message.channel.id)).get("word_initial_lookup").get(new_word_data.get("last_sound")):
                                                    await win(bot.bot.user.id, message.channel.id)

                                # If the playmode is multiplayer
                                if playmode == "multiplayer":

                                    # If gamemode is casual
                                    if gamemode == "casual":
                                        # If the word_info was used recently
                                        if msg in active_channels.get(str(message.channel.id)).get("recent_words"):
                                            await message.channel.send(embed=disnake.Embed(
                                                title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                description=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_used_recently'),
                                                colour=0xff0000))
                                        else:
                                            if len(active_channels[str(message.channel.id)].get("recent_words")) >= 5:
                                                active_channels[str(message.channel.id)]["recent_words"].pop(0)

                                            new_word = msg

                                            new_word_data = valid_words.get(msg)

                                            active_channels[str(message.channel.id)]["previous_player_id"] = message.author.id
                                            active_channels[str(message.channel.id)]["previous_word_end"] = new_word_data.get("last_sound")
                                            active_channels[str(message.channel.id)]["recent_words"].append(new_word)

                                            # Create an embed to hold data about the new word_info
                                            embed = disnake.Embed(
                                                title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                description=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_word_said').replace('&1', bot.get_name(message.author.id, message.guild)).replace('&2', "**" + new_word + "**"),
                                                colour=899718)

                                            # Get language data from the current guild
                                            lang_value = bot.execute_read_query(
                                                "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                                                    message.guild.id) + "')")[0][0]
                                            if lang_value == "English":
                                                # If language is English, set the Meaning entry to be the English translation
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_meaning') + ":",
                                                                value=new_word_data.get("translations").get(
                                                                    "en"))
                                            elif lang_value == "German":
                                                # If language is German, set the Meaning entry to be the German translation
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_meaning') + ":",
                                                                value=new_word_data.get("translations").get(
                                                                    "de"))

                                            # Set the rest of the fields for the new word_info data
                                            embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_pronunciation') + ":",
                                                            value=new_word_data.get("pronunciation"))
                                            embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_pos') + ":", value=new_word_data.get("pos"))
                                            embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_frequency') + ":",
                                                            value=str(new_word_data.get("frequency")) + "%")

                                            # Send above embed publicly
                                            await message.channel.send(embed=embed)

                                            if str(message.author.id) in active_channels[str(message.channel.id)].get("points"):
                                                active_channels[str(message.channel.id)]["points"][str(message.author.id)] += 1
                                            else:
                                                active_channels[str(message.channel.id)]["points"][str(message.author.id)] = 1

                                    # If the gamemode is competitive
                                    if gamemode == "competitive":

                                        new_word = msg
                                        new_word_data = valid_words.get(new_word)

                                        active_channels[str(message.channel.id)]["previous_player_id"] = message.author.id
                                        active_channels[str(message.channel.id)]["previous_word_end"] = new_word_data.get("last_sound")
                                        active_channels[str(message.channel.id)]["word_initial_lookup"][new_word_data.get("first_sound")].remove(new_word)

                                        # Create an embed to hold data about the new word_info
                                        embed = disnake.Embed(
                                            title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                            description=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_word_said').replace('&1', bot.get_name(message.author.id,
                                                                                                 message.guild)).replace(
                                                '&2', "**" + new_word + "**"),
                                            colour=899718)

                                        # Get language data from the current guild
                                        lang_value = bot.execute_read_query(
                                            "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                                                message.guild.id) + "')")[0][0]
                                        if lang_value == "English":
                                            # If language is English, set the Meaning entry to be the English translation
                                            embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_meaning') + ":",
                                                            value=new_word_data.get("translations").get("en"))
                                        elif lang_value == "German":
                                            # If language is German, set the Meaning entry to be the German translation
                                            embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_meaning') + ":",
                                                            value=new_word_data.get("translations").get("de"))

                                        # Set the rest of the fields for the new word_info data
                                        embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                            'wordgame_pronunciation') + ":",
                                                        value=new_word_data.get("pronunciation"))
                                        embed.add_field(
                                            name=bot.lang.get(str(message.guild.id)).get('wordgame_pos') + ":",
                                            value=new_word_data.get("pos"))
                                        embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                            'wordgame_frequency') + ":",
                                                        value=str(new_word_data.get("frequency")) + "%")

                                        # Send above embed publicly
                                        await message.channel.send(embed=embed)

                                        if str(message.author.id) in active_channels[str(message.channel.id)].get(
                                                "points"):
                                            active_channels[str(message.channel.id)]["points"][
                                                str(message.author.id)] += 1
                                        else:
                                            active_channels[str(message.channel.id)]["points"][
                                                str(message.author.id)] = 1

                                        if not active_channels.get(str(message.channel.id)).get("word_initial_lookup").get(new_word_data.get("last_sound")):
                                            await win(message.author.id, message.channel.id)

                                    if gamemode == "deathmatch":
                                        new_word = msg
                                        new_word_data = valid_words.get(new_word)

                                        if new_word not in active_channels.get(str(message.channel.id)).get("used_words"):
                                            active_channels[str(message.channel.id)][
                                                "previous_player_id"] = message.author.id
                                            active_channels[str(message.channel.id)][
                                                "previous_word_end"] = new_word_data.get("last_sound")
                                            active_channels[str(message.channel.id)]["used_words"].append(new_word)

                                            # Create an embed to hold data about the new word_info
                                            embed = disnake.Embed(
                                                title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                description=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_word_said').replace('&1', bot.get_name(message.author.id,
                                                                                                     message.guild)).replace(
                                                    '&2', "**" + new_word + "**"),
                                                colour=899718)

                                            # Get language data from the current guild
                                            lang_value = bot.execute_read_query(
                                                "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                                                    message.guild.id) + "')")[0][0]
                                            if lang_value == "English":
                                                # If language is English, set the Meaning entry to be the English translation
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_meaning') + ":",
                                                                value=new_word_data.get("translations").get("en"))
                                            elif lang_value == "German":
                                                # If language is German, set the Meaning entry to be the German translation
                                                embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_meaning') + ":",
                                                                value=new_word_data.get("translations").get("de"))

                                            # Set the rest of the fields for the new word_info data
                                            embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_pronunciation') + ":",
                                                            value=new_word_data.get("pronunciation"))
                                            embed.add_field(
                                                name=bot.lang.get(str(message.guild.id)).get('wordgame_pos') + ":",
                                                value=new_word_data.get("pos"))
                                            embed.add_field(name=bot.lang.get(str(message.guild.id)).get(
                                                'wordgame_frequency') + ":",
                                                            value=str(new_word_data.get("frequency")) + "%")

                                            # Send above embed publicly
                                            await message.channel.send(embed=embed)

                                            if str(message.author.id) in active_channels[str(message.channel.id)].get(
                                                    "points"):
                                                active_channels[str(message.channel.id)]["points"][
                                                    str(message.author.id)] += 1
                                            else:
                                                active_channels[str(message.channel.id)]["points"][
                                                    str(message.author.id)] = 1
                                        else:
                                            active_channels[str(message.channel.id)]["players"].remove(message.author.id)
                                            await message.channel.send(embed=disnake.Embed(
                                                title=bot.lang.get(str(message.guild.id)).get('wordgame_title'),
                                                description=bot.lang.get(str(message.guild.id)).get(
                                                    'wordgame_eliminated').replace('&1', bot.get_name(message.author.id, message.guild)),
                                                colour=0xff0000))

                                        if len(active_channels.get(str(message.channel.id)).get("players")) == 1:
                                            await win(active_channels.get(str(message.channel.id)).get("players")[0],
                                                      message.channel.id)


def setup(bot):
    bot.add_cog(WordgameCog(bot))
    print('Added new Cog: ' + str(WordgameCog))
