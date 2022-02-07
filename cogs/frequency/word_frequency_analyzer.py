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


wordlist = create_connection('word_frequency.db')
soundlist = create_connection('sound_frequency.db')


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


reykunyu_all = requests.get("https://reykunyu.wimiso.nl/api/frau").json()


def monographize(word):
    return word.replace('ng', 'ŋ').replace('ay', 'à').replace('ey', 'è').replace('aw', 'á').replace('ew', 'é') \
        .replace('ll', 'ʟ').replace('rr', 'ʀ').replace('ts', 'c').replace('px', 'b').replace('tx', 'd') \
        .replace('kx', 'g')


def demonographize(word):
    return word.replace('g', 'kx').replace('à', 'ay').replace('è', 'ey').replace('á', 'aw').replace('é', 'ew') \
        .replace('ʟ', 'll').replace('ʀ', 'rr').replace('c', 'ts').replace('b', 'px').replace('d', 'tx') \
        .replace('ŋ', 'ng')


def convert_to_monographic(word):
    monographic = ""
    try:
        # Get pronunciation and stress data if it exists
        pronunciation = reykunyu_all.get(word).get("pronunciation")[0].lower()

        # Split the pronunciation data into syllables
        split_pronunciation = pronunciation.split('-')

        # For every syllable, convert it to monographic using the function
        # (done to fix exceptions like eyawr)
        for num, syllable in enumerate(split_pronunciation):
            split_pronunciation[num] = monographize(syllable)

        # Set the placeholder string to the new, joined monographic word_info
        monographic = ''.join(split_pronunciation)

    # If either of these exceptions are thrown,
    # the list doesn't contain any pronunciation info for this word_info,
    # and we just have to hope there's no exceptions
    except AttributeError:
        monographic = monographize(word)
    return monographic


try:
    while True:
        text = input("Please supply text to analyze...\n")

        text = text.lower().replace('>', '').replace('<', '').replace('!', '').replace(
            '%', '').replace('&', '').replace('^', '').replace('(', '').replace(')', '').replace('$',
                                                                                                 '').replace(
            '#', '').replace('@', '').replace('*', '').replace('{', '').replace('}', '').replace('/',
                                                                                                 '').replace(
            '\\', '').replace('[', '').replace(']', '').replace('|', '').replace('.', '').replace(',',
                                                                                                  '').replace(
            '?', '').replace(':', '').replace(';', '')
        try:
            response = requests.get('https://reykunyu.wimiso.nl/api/fwew?t%C3%ACpawm=' + text).json()
            for word in response:
                try:
                    root_object = word.get('sì\'eyng')[0]
                    word = root_object.get('na\'vi').replace('\'', '’')

                    for character in convert_to_monographic(word):
                        character = character.lower()
                        character = demonographize(character)
                        if not execute_read_query(soundlist, "SELECT * FROM sounds WHERE sound = '" + character + "'"):
                            execute_query(soundlist, """
                                            INSERT INTO
                                              sounds (sound, count)
                                            VALUES
                                            ('""" + character + """', """ + str(1) + """)
                                            """)
                        else:
                            execute_query(soundlist, """
                                            UPDATE
                                              sounds
                                            SET
                                              count = """ + str(execute_read_query(soundlist,
                                                                                   "SELECT count FROM sounds WHERE sound = '" + character + "'")[
                                                                                                                         0][
                                                                                                                         0] + 1) + """
                                            WHERE
                                              sound = '""" + str(character) + """'
                                            """)

                    if not execute_read_query(wordlist, "SELECT * FROM words WHERE word = '" + word + "'"):
                        execute_query(wordlist, """
                                        INSERT INTO
                                          words (word, count, meaning, type)
                                        VALUES
                                        ('""" + word + """', """ + str(1) + """, '""" + root_object.get('translations')[
                            0].get('en').replace('\'', '’') + """', '""" + root_object.get('type') + """')
                                        """)
                    else:
                        execute_query(wordlist, """
                                        UPDATE
                                          words
                                        SET
                                          count = """ + str(
                            execute_read_query(wordlist, "SELECT count FROM words WHERE word = '" + word + "'")[0][
                                0] + 1) + """
                                        WHERE
                                          word = '""" + str(word) + """'
                                        """)
                    try:
                        for affix in root_object.get('affixes'):
                            affix = affix.get('affix')
                            for character in convert_to_monographic(affix):
                                character = character.lower()
                                character = demonographize(character)
                                if not execute_read_query(soundlist,
                                                          "SELECT * FROM sounds WHERE sound = '" + character + "'"):
                                    execute_query(soundlist, """
                                                    INSERT INTO
                                                      sounds (sound, count)
                                                    VALUES
                                                    ('""" + character + """', """ + str(1) + """)
                                                    """)
                                else:
                                    execute_query(soundlist, """
                                                    UPDATE
                                                      sounds
                                                    SET
                                                      count = """ + str(execute_read_query(soundlist,
                                                                                           "SELECT count FROM sounds WHERE sound = '" + character + "'")[
                                                                                                                                         0][
                                                                                                                                         0] + 1) + """
                                                    WHERE
                                                      sound = '""" + str(character) + """'
                                                    """)
                            if 'adp' in affix.get('type'):
                                affix_word = affix.get('na\'vi').replace('\'', '’')

                                if not execute_read_query(wordlist,
                                                          "SELECT * FROM words WHERE word = '" + affix_word + "'"):
                                    execute_query(wordlist, """
                                                    INSERT INTO
                                                      words (word, count, meaning, type)
                                                    VALUES
                                                    ('""" + affix_word + """', """ + str(1) + """, '""" +
                                                  affix.get('translations')[0].get('en').replace('\'',
                                                                                                 '’') + """', '""" + affix.get(
                                        'type') + """')
                                                    """)
                                else:
                                    execute_query(wordlist, """
                                                    UPDATE
                                                      words
                                                    SET
                                                      count = """ + str(execute_read_query(wordlist,
                                                                                           "SELECT count FROM words WHERE word = '" + affix_word + "'")[
                                                                                                                                        0][
                                                                                                                                        0] + 1) + """
                                                    WHERE
                                                      word = '""" + str(affix_word) + """'
                                                    """)
                    except TypeError:
                        pass
                except IndexError:
                    pass
        except json.decoder.JSONDecodeError:
            pass


        word_frequency_total_processed = 0
        word_frequency_total_listed = 0
        words = execute_read_query(wordlist, "SELECT * FROM words")
        for num, word in enumerate(words):
            word_frequency_total_processed += word[1]
            word_frequency_total_listed += 1
        print(word_frequency_total_listed, word_frequency_total_processed)
except KeyboardInterrupt:
    pass
