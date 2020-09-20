from encodings.utf_8 import decode
try:
    import discord, os, random
except:
    os.system("pip install --upgrade discord.py[voice]")
    import discord, os, random
from discord.ext import commands
import config
import json
import random
import re

bot = commands.Bot(command_prefix=config.prefix, description=config.description)


with open("wordgame_words.json", encoding ='utf-8') as f:
    wordgame_words = json.load(f)


with open("compact_database.json", encoding ='utf-8') as f:
    search_database = json.load(f)

with open("swear_database.json", encoding ='utf-8') as f:
    swear_database = json.load(f)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------------')
    await bot.change_presence(activity=discord.Game(name=config.status + " V" + config.version))
    print('status set.')
    print('-------------------')


@bot.event
async def on_message(message):

    if message.content.startswith(config.prefix + 'help'):
        await message.author.send(embed=discord.Embed(description=config.help, colour=0x5b2076))

    await bot.process_commands(message)


@bot.command()
async def exit(ctx):
    if ctx.message.author.id in config.operators:
        await ctx.send(embed=discord.Embed(description="Ikran OS shutting down...", colour=0xff0000))
        os._exit(0)
    else:
        await ctx.send(embed=discord.Embed(title="DENIED!", description="You do not have access to run this command!", colour=0xff0000))

bot.load_extension('searcher')
bot.load_extension('wordgame')
bot.load_extension('numbers')
bot.load_extension('fun')
bot.run(config.token)
