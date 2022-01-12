import json
import re
import sqlite3
from sqlite3 import Error

import requests
from disnake.ext import commands


def create_connection(path):
    connection = None

    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


wordlist = create_connection('cogs/frequency/word_frequency.db')


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


execute_query(wordlist, """
CREATE TABLE IF NOT EXISTS words (
  word TEXT PRIMARY KEY,
  count INTEGER,
  meaning TEXT,
  type TEXT
);
""")


class FrequencyCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id in [715050499203661875, 856145252310188032]:
            if message.channel.id == 715050499203661875:
                message = message.content.lower().replace('>', '').replace('<', '').replace('!', '').replace(
                    '%', '').replace('&', '').replace('^', '').replace('(', '').replace(')', '').replace('$',
                                                                                                         '').replace(
                    '#', '').replace('@', '').replace('*', '').replace('{', '').replace('}', '').replace('/',
                                                                                                         '').replace(
                    '\\', '').replace('[', '').replace(']', '').replace('|', '').replace('.', '').replace(',',
                                                                                                          '').replace(
                    '?', '').replace(':', '').replace(';', '')
                try:
                    response = requests.get('https://reykunyu.wimiso.nl/api/fwew?t%C3%ACpawm=' + message).json()
                    for word in response:
                        try:
                            root_object = word.get('sì\'eyng')[0]
                            word = root_object.get('na\'vi').replace('\'', '’')

                            if not execute_read_query(wordlist, "SELECT * FROM words WHERE word = '" + word + "'"):
                                execute_query(wordlist, """
                                                INSERT INTO
                                                  words (word, count, meaning, type)
                                                VALUES
                                                ('""" + word + """', """ + str(1) + """, '""" + root_object.get('translations')[0].get('en').replace('\'', '’') + """', '""" + root_object.get('type') + """')
                                                """)
                            else:
                                execute_query(wordlist, """
                                                UPDATE
                                                  words
                                                SET
                                                  count = """ + str(execute_read_query(wordlist, "SELECT count FROM words WHERE word = '" + word + "'")[0][0] + 1) + """
                                                WHERE
                                                  word = '""" + str(word) + """'
                                                """)
                            try:
                                for affix in root_object.get('affixes'):
                                    affix = affix.get('affix')
                                    if 'adp' in affix.get('type'):
                                        affix_word = affix.get('na\'vi').replace('\'', '’')

                                        if not execute_read_query(wordlist, "SELECT * FROM words WHERE word = '" + affix_word + "'"):
                                            execute_query(wordlist, """
                                                            INSERT INTO
                                                              words (word, count, meaning, type)
                                                            VALUES
                                                            ('""" + affix_word + """', """ + str(1) + """, '""" + affix.get('translations')[0].get('en').replace('\'', '’') + """', '""" + affix.get('type') + """')
                                                            """)
                                        else:
                                            execute_query(wordlist, """
                                                            UPDATE
                                                              words
                                                            SET
                                                              count = """ + str(execute_read_query(wordlist,"SELECT count FROM words WHERE word = '" + affix_word + "'")[0][0] + 1) + """
                                                            WHERE
                                                              word = '""" + str(affix_word) + """'
                                                            """)
                            except TypeError:
                                pass
                        except IndexError:
                            pass
                except json.decoder.JSONDecodeError:
                    pass

            else:
                message = message.content.lower().replace('>', '').replace('<', '').replace('!', '').replace(
                    '%', '').replace('&', '').replace('^', '').replace('(', '').replace(')', '').replace('$',
                                                                                                         '').replace(
                    '#', '').replace('@', '').replace('*', '').replace('{', '').replace('}', '').replace('/',
                                                                                                         '').replace(
                    '\\', '').replace('[', '').replace(']', '').replace('.', '').replace(',',
                                                                                                          '').replace(
                    '?', '').replace(':', '').replace(';', '')

                message = re.sub(r'\|\|.*?\|\|', '', message)
                try:
                    response = requests.get('https://reykunyu.wimiso.nl/api/fwew?t%C3%ACpawm=' + message).json()
                    for word in response:
                        try:
                            root_object = word.get('sì\'eyng')[0]
                            word = root_object.get('na\'vi').replace('\'', '’').lower()

                            if not execute_read_query(wordlist, "SELECT * FROM words WHERE word = '" + word + "'"):
                                execute_query(wordlist, """
                                                                INSERT INTO
                                                                  words (word, count, meaning, type)
                                                                VALUES
                                                                ('""" + word + """', """ + str(1) + """, '""" +
                                              root_object.get('translations')[0].get('en').replace('\'',
                                                                                                   '’') + """', '""" + root_object.get(
                                    'type') + """')
                                                                """)
                            else:
                                execute_query(wordlist, """
                                                                UPDATE
                                                                  words
                                                                SET
                                                                  count = """ + str(
                                    execute_read_query(wordlist, "SELECT count FROM words WHERE word = '" + word + "'")[
                                        0][0] + 1) + """
                                                                WHERE
                                                                  word = '""" + str(word) + """'
                                                                """)
                            try:
                                for affix in root_object.get('affixes'):
                                    affix = affix.get('affix')
                                    if 'adp' in affix.get('type'):
                                        affix_word = affix.get('na\'vi').replace('\'', '’')

                                        if not execute_read_query(wordlist, "SELECT * FROM words WHERE word = '" + affix_word + "'"):
                                            execute_query(wordlist, """
                                                            INSERT INTO
                                                              words (word, count, meaning, type)
                                                            VALUES
                                                            ('""" + affix_word + """', """ + str(1) + """, '""" + affix.get('translations')[0].get('en').replace('\'', '’') + """', '""" + affix.get('type') + """')
                                                            """)
                                        else:
                                            execute_query(wordlist, """
                                                            UPDATE
                                                              words
                                                            SET
                                                              count = """ + str(execute_read_query(wordlist,"SELECT count FROM words WHERE word = '" + affix_word + "'")[0][0] + 1) + """
                                                            WHERE
                                                              word = '""" + str(affix_word) + """'
                                                            """)
                            except TypeError:
                                pass
                        except IndexError:
                            pass
                except json.decoder.JSONDecodeError:
                    pass


def setup(bot):
    bot.add_cog(FrequencyCog(bot))
    print('Added new Cog: ' + str(FrequencyCog))
