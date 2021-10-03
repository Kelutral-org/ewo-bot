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
navi_letters = ['\'', 'a', 'ä', 'á', 'à', 'e', 'é', 'è', 'f', 'h', 'i', 'ì', 'k', 'g', 'l', 'ʟ', 'm', 'n', 'ŋ', 'o', 'p', 'b', 'r', 'ʀ', 's', 't', 'c', 'd', 'u', 'v', 'w', 'y', 'z']


# Takes a word and changes the letters to monographic representations
def convert_to_monographic(word):
    return word.replace('ng', 'ŋ').replace('ay', 'à').replace('ey', 'è').replace('aw', 'á').replace('ew', 'é') \
        .replace('ll', 'ʟ').replace('rr', 'ʀ').replace('ts', 'c').replace('px', 'b').replace('tx', 'd') \
        .replace('kx', 'g')


# Chooses a random word from the list of valid words and returns it
# (returns only the name, to get the data use valid_words.get(word))
def choose_word(word_initial_lookup: dict, sound: str):
    word = random.choice(word_initial_lookup.get(sound))

    return word


# Ends the game in the given channel. Does not check if a game is active.
def end_game(channel_id: int):
    active_channels.pop(str(channel_id))


# The class for the playermode dropdown in the wordgame start ui.
class PlaymodeDropdown(disnake.ui.Select):
    def __init__(self):
        playmode_options = [
            disnake.SelectOption(label='Multiplayer',
                                 description='The bot will not respond, more than one player required.',
                                 emoji='👨‍👩‍👧‍👦'),
            disnake.SelectOption(label='Solo',
                                 description='The bot will automatically respond, anyone can still play.',
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
        ]

        super().__init__(placeholder='Please select the playmode...', min_values=1, max_values=1, options=gamemode_options)


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
            self.playmode = self.playmode_dropdown.values[0]
            self.gamemode = self.gamemode_dropdown.values[0]

            # This sets the list of usable words for THE CURRENT GAME
            word_initial_lookup = full_word_initial_lookup

            # Chose the first word by randomly choosing a sound from the list of possible sounds
            first_word = choose_word(word_initial_lookup, random.choice(navi_letters))
            # Get the first word's data
            first_word_data = valid_words.get(first_word)

            # Set all of the necessary data in the list of active channels
            active_channels[str(inter.channel_id)] = {}
            active_channels[str(inter.channel_id)]["playmode"] = self.playmode
            active_channels[str(inter.channel_id)]["gamemode"] = self.gamemode
            active_channels[str(inter.channel_id)]["points"] = {}
            active_channels[str(inter.channel_id)]["word_initial_lookup"] = word_initial_lookup
            active_channels[str(inter.channel_id)]["previous_player_id"] = bot.bot.user.id
            active_channels[str(inter.channel_id)]["previous_word_end"] = first_word_data.get("last_sound")

            # Create an embed to send information about the game
            embed = disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                  description=bot.lang.get(str(inter.guild_id)).get('wordgame_starting'),
                                  colour=899718)

            # Add info to above embed
            embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_playmode'), value=self.playmode.capitalize())
            embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_gamemode'), value=self.gamemode.capitalize())

            # Send above embed publicly
            await inter.response.send_message(embed=embed)

            # Get the channel from the id
            channel = await bot.bot.fetch_channel(inter.channel_id)

            # Create an embed to hold data about the first word
            embed = disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                  description=bot.lang.get(str(inter.guild_id)).get('wordgame_first_word').replace('&1', "**" + first_word + "**"),
                                  colour=899718)

            # Get language data from the current guild
            lang_value = bot.execute_read_query(
                "SELECT [value] FROM options WHERE ([option] = 'language') AND ([guild_id] = '" + str(
                    inter.guild_id) + "')")[0][0]
            if lang_value == "English":
                # If language is English, set the Meaning entry to be the English translation
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_meaning'), value=first_word_data.get("translations").get("en"))
            elif lang_value == "German":
                # If language is German, set the Meaning entry to be the German translation
                embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_meaning'), value=first_word_data.get("translations").get("de"))

            # Set the rest of the fields for the first word data
            embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_pronunciation'), value=first_word_data.get("pronunciation"))
            embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_pos'), value=first_word_data.get("pos"))
            embed.add_field(name=bot.lang.get(str(inter.guild_id)).get('wordgame_frequency'), value=str(first_word_data.get("frequency")) + "%")

            # Send above embed publicly
            await channel.send(embed=embed)

            # Some stuff I don't really understand for buttons
            self.value = True
            self.stop()

    # Cancel button
    @disnake.ui.button(label='Cancel', style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Do nothing
        await interaction.response.defer()

        # More weird stuff
        self.value = False
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

        # Get the total words process for the word frequency list (to use in calculating frequency percentage)
        word_frequency_total_processed = 0
        words = execute_read_query(word_frequency_db, "SELECT * FROM words")
        for word in words:
            word_frequency_total_processed += word[1]

        print("WORDGAME: Compiling valid word list...")
        # List of unusable words, soon to be filled
        self.invalid_words = {"aw": [], "ew": [], "ll": [], "rr": [], "space": []}
        # Get the list of every word in Na'vi from reykunyu
        reykunyu_all = requests.get("https://reykunyu.wimiso.nl/api/frau").json()

        # For every word in above list
        for word in reykunyu_all:
            # If the word ends in aw, add it to unusable words. Not enough words start with it.
            if (reykunyu_all.get(word).get("na'vi").lower().endswith('aw')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["aw"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word ends in ew, add it to unusable words. Not enough words start with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ew')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["ew"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word ends in ll, add it to unusable words. No words end with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ll')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["ll"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word ends in r, add it to unusable words. No words end with it.
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('rr')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["rr"].append(reykunyu_all.get(word).get("na'vi").lower())
            # If the word contains a space, add it to unusable words. They're usually just multiple other words or si verbs.
            elif ' ' in reykunyu_all.get(word).get("na'vi").lower():
                self.invalid_words["space"].append(reykunyu_all.get(word).get("na'vi").lower())

            # If all above tests pass, we know the word is valid and can add it to the list
            else:
                # Add the word to the list alongside some daya
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

                    # Set the placeholder string to the new, joined monographic word
                    monographic = ''.join(monographic_syllables)

                    # Add the word's pronunciation to the data
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = word_pronunciation

                # If either of these exeptions are thrown,
                # the list doesn't contain any pronunciation info for this word, and this entire step can be skipped.
                except TypeError:
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = "N/A"
                except IndexError:
                    valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = "N/A"

                # Add the part of speech to the data
                valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pos"] = reykunyu_all.get(word).get(
                    "type")

                # Get the frequency of this word from the word frequency list
                word_frequency = execute_read_query(word_frequency_db,
                                                    "SELECT count FROM words WHERE (word = '" + reykunyu_all.get(
                                                        word).get("na'vi").lower().replace('\'', '’') + "')")
                try:
                    # Calculate the frequency percentage
                    frequency_percentage = round(word_frequency[0][0] / word_frequency_total_processed * 100, 2)
                # If this exception is thrown, the word is not in the list, and the percentage is then zero
                except IndexError:
                    frequency_percentage = 0

                # Add the frequency to the data
                valid_words[reykunyu_all.get(word).get("na'vi").lower()]["frequency"] = frequency_percentage

                # If there is no monographic form (pronunciation information was not available),
                # simply use the word and hope for the best
                if not monographic:
                    monographic = convert_to_monographic(reykunyu_all.get(word).get("na'vi").lower())

                # Add the first and last sounds of the word to the data
                valid_words[reykunyu_all.get(word).get("na'vi").lower()]["first_sound"] = monographic[0]
                valid_words[reykunyu_all.get(word).get("na'vi").lower()]["last_sound"] = monographic[-1]

                # Append the word into the correct entry in the lookup table, using the monographic info used above
                full_word_initial_lookup[monographic[0]].append(reykunyu_all.get(word).get("na'vi").lower())

        # with open("cogs/wordgame/tempjson.json", 'w', encoding='utf-8') as f:
        #     json.dump(valid_words, f, indent=4, ensure_ascii=False)
        # with open("cogs/wordgame/forbidden_words.json", 'w', encoding='utf-8') as f:
        #     json.dump(self.invalid_words, f, indent=4, ensure_ascii=False)

        print("WORDGAME: Complete!")

    # Update the list of channels, used when it is changed with addchannel and removechannel
    def update_channels(self):
        self.channels = execute_read_query(channels_db, "SELECT * FROM channels")

    # This does nothing, it just holds the subcommands
    @commands.slash_command(name="wordgame", description="A basic word game to help learn vocabulary!", default_permission=True, guild_ids=bot.test_guilds)
    async def wordgame(self, inter):
        pass

    # Start command :D
    @wordgame.sub_command(name="start", description="Start a word game in the current channel.")
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
    @wordgame.sub_command(name="stop", description="End the current word game.")
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
                end_game(inter.channel_id)
                # Send a public confirmation message
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_starting'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_stopping'),
                                        colour=899718))
        # If this channel is not a wordgame channel, send an error
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                    description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_nonexistent'),
                                    colour=0xff0000), ephemeral=True)

    @wordgame.sub_command(name="addchannel", description="Add this channel to the list of word game channels.")
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

    @wordgame.sub_command(name="removechannel", description="Remove this channel from the list of word game channels.")
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

    # DOES NOTHING, REALLY NEED TO FLESH THIS OUT
    @wordgame.sub_command(name="info", description="Show some basic info about the game.")
    async def points(self, inter):
        pass

    @wordgame.sub_command(name="points", description="Show the leaderboard of word game points.")
    async def points(self, inter):
        pass


def setup(bot):
    bot.add_cog(WordgameCog(bot))
    print('Added new Cog: ' + str(WordgameCog))
