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


def convert_to_monographic(word):
    return word.replace('ng', 'ŋ').replace('ay', 'à').replace('ey', 'è').replace('aw', 'á').replace('ew', 'é') \
        .replace('ll', 'ʟ').replace('rr', 'ʀ').replace('ts', 'c').replace('px', 'b').replace('tx', 'd') \
        .replace('kx', 'g')


class WordgameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels = execute_read_query(channels_db, "SELECT * FROM channels")

        word_frequency_total_processed = 0
        words = execute_read_query(word_frequency_db, "SELECT * FROM words")
        for word in words:
            word_frequency_total_processed += word[1]

        self.valid_words = {}
        self.invalid_words = {"aw": [], "ew": [], "ll": [], "rr": [], "space": []}
        print("WORDGAME: Compiling valid word list...")
        reykunyu_all = requests.get("https://reykunyu.wimiso.nl/api/frau").json()
        for word in reykunyu_all:
            if (reykunyu_all.get(word).get("na'vi").lower().endswith('aw')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["aw"].append(reykunyu_all.get(word).get("na'vi").lower())
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ew')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["ew"].append(reykunyu_all.get(word).get("na'vi").lower())
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('ll')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["ll"].append(reykunyu_all.get(word).get("na'vi").lower())
            elif (reykunyu_all.get(word).get("na'vi").lower().endswith('rr')) and (not ' ' in reykunyu_all.get(word).get("na'vi").lower()):
                self.invalid_words["rr"].append(reykunyu_all.get(word).get("na'vi").lower())
            elif ' ' in reykunyu_all.get(word).get("na'vi").lower():
                self.invalid_words["space"].append(reykunyu_all.get(word).get("na'vi").lower())
            else:
                self.valid_words[reykunyu_all.get(word).get("na'vi").lower()] = {}
                self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["translations"] = \
                reykunyu_all.get(word).get("translations")[0]
                monographic = ""
                try:
                    pronunciation = reykunyu_all.get(word).get("pronunciation")[0].lower()
                    reykunyu_pronunciation = reykunyu_all.get(word).get("pronunciation")[1]
                    split_pronunciation = pronunciation.split('-')
                    stressed_pronunciation = copy.deepcopy(split_pronunciation)
                    stressed_pronunciation[reykunyu_pronunciation - 1] = split_pronunciation[reykunyu_pronunciation - 1].upper()
                    word_pronunciation = '-'.join(stressed_pronunciation)

                    monographic_syllables = copy.deepcopy(split_pronunciation)
                    for num, syllable in enumerate(split_pronunciation):
                        monographic_syllables[num] = convert_to_monographic(syllable)
                    monographic = ''.join(monographic_syllables)

                    self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = word_pronunciation
                except TypeError:
                    self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = "N/A"
                except IndexError:
                    self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pronunciation"] = "N/A"

                self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["pos"] = reykunyu_all.get(word).get(
                    "type")

                word_frequency = execute_read_query(word_frequency_db,
                                                    "SELECT count FROM words WHERE (word = '" + reykunyu_all.get(
                                                        word).get("na'vi").lower().replace('\'', '’') + "')")
                try:
                    frequency_percentage = round(word_frequency[0][0] / word_frequency_total_processed * 100, 2)
                except IndexError:
                    frequency_percentage = 0

                self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["frequency"] = frequency_percentage

                if not monographic:
                    monographic = convert_to_monographic(reykunyu_all.get(word).get("na'vi").lower())

                self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["first_sound"] = monographic[0]
                self.valid_words[reykunyu_all.get(word).get("na'vi").lower()]["last_sound"] = monographic[-1]

        # with open("cogs/wordgame/tempjson.json", 'w', encoding='utf-8') as f:
        #     json.dump(self.valid_words, f, indent=4, ensure_ascii=False)
        # with open("cogs/wordgame/forbidden_words.json", 'w', encoding='utf-8') as f:
        #     json.dump(self.invalid_words, f, indent=4, ensure_ascii=False)

        print("WORDGAME: Complete!")

    def update_channels(self):
        self.channels = execute_read_query(channels_db, "SELECT * FROM channels")

    @commands.slash_command(name="wordgame", description="A basic word game to help learn vocabulary!", default_permission=True, guild_ids=bot.test_guilds)
    async def wordgame(self, inter):
        pass

    @wordgame.sub_command(name="start", description="Start a word game in the current channel.")
    async def start(self, inter, args=""):
        pass

    @wordgame.sub_command(name="stop", description="End the current word game")
    async def stop(self, inter, args=""):
        pass

    @wordgame.sub_command(name="addchannel", description="Add this channel to the list of word game channels.")
    async def addchannel(self, inter):
        is_op = False
        for perm in inter.permissions:
            if (perm == ('manage_guild', True)) or (perm == ('administrator', True)) or (inter.author.id in bot.config.operators):
                is_op = True

        if is_op:
            if tuple([inter.channel_id, inter.guild_id]) in self.channels:
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_exists'),
                                        colour=0xff0000))
            else:
                execute_query(channels_db, """
                                            INSERT INTO
                                              channels (channel_id, guild_id)
                                            VALUES
                                              (""" + str(inter.channel_id) + """, """ + str(inter.guild_id) + """);
                                            """)

                channel = await self.bot.fetch_channel(inter.channel_id)
                name = channel.name

                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_added').replace('&1', name),
                                        colour=899718))
                self.update_channels()
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('denied'),
                                    description=bot.lang.get(str(inter.guild_id)).get('no_access'),
                                    colour=0xff0000))

    @wordgame.sub_command(name="removechannel", description="Remove this channel from the list of word game channels.")
    async def removechannel(self, inter):
        is_op = False
        for perm in inter.permissions:
            if (perm == ('manage_guild', True)) or (perm == ('administrator', True)) or (inter.author.id in bot.config.operators):
                is_op = True

        if is_op:
            if tuple([inter.channel_id, inter.guild_id]) not in self.channels:
                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_channel_nonexistent'),
                                        colour=0xff0000))
            else:
                execute_query(channels_db, "DELETE FROM channels WHERE channel_id = " + str(inter.channel_id) + " AND guild_id = " + str(inter.guild_id) + ";")

                channel = await self.bot.fetch_channel(inter.channel_id)
                name = channel.name

                await inter.response.send_message(
                    embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('wordgame_title'),
                                        description=bot.lang.get(str(inter.guild_id)).get('wordgame_removed').replace('&1', name),
                                        colour=899718))
                self.update_channels()
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title=bot.lang.get(str(inter.guild_id)).get('denied'),
                                    description=bot.lang.get(str(inter.guild_id)).get('no_access'),
                                    colour=0xff0000))

    @wordgame.sub_command(name="points", description="Show the leaderboard of word game points.")
    async def points(self, inter):
        pass


def setup(bot):
    bot.add_cog(WordgameCog(bot))
    print('Added new Cog: ' + str(WordgameCog))
