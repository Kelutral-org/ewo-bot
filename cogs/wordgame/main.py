import json
import random
import sqlite3
from sqlite3 import Error
import copy

import disnake
import requests
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


def convert_to_monographic(word):
    return word.replace('ng', 'ŋ').replace('ay', 'à').replace('ey', 'è').replace('aw', 'á').replace('ew', 'é') \
        .replace('ll', 'ʟ').replace('rr', 'ʀ').replace('ts', 'c').replace('px', 'b').replace('tx', 'd') \
        .replace('kx', 'g')


class WordgameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invalid_words = {"aw": [], "ew": [], "ll": [], "rr": [], "space": []}

        word_frequency_total_processed = 0
        words = execute_read_query(word_frequency_db, "SELECT * FROM words")
        for word in words:
            word_frequency_total_processed += word[1]
        print(word_frequency_total_processed)

        self.valid_words = {}
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




def setup(bot):
    bot.add_cog(WordgameCog(bot))
    print('Added new Cog: ' + str(WordgameCog))
