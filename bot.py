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


async def randomWord():
    word = random.choices(search_database)
    word = word[0]
    word = word['name'] + ' ' + word['pos'] + ' = \n' + word['definition'].replace('\n', '; ')
    return word

async def randomSwear():
    word = random.choices(swear_database)
    word = word[0]
    word = word['name'] + '!'
    return word


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
    lowermsg = message.content.lower()

    if message.content.startswith(config.prefix + 'help'):
        await message.author.send(embed=discord.Embed(description=config.help, colour=0x5b2076))

    if lowermsg.startswith("ma ewo', repeat after me: "):
        await message.channel.send(message.content.lower().replace("ma ewo', repeat after me: ", ''))

    await bot.process_commands(message)


@bot.command()
async def exit(ctx):
    if ctx.message.author.id in config.operators:
        await ctx.send(embed=discord.Embed(description="Ikran OS shutting down...", colour=0xff0000))
        os._exit(0)
    else:
        await ctx.send(embed=discord.Embed(title="DENIED!", description="You do not have access to run this command!", colour=0xff0000))


@bot.command(name='scream')
async def scream(ctx, args):
    screech = "SKR"
    length = int(args)
    if length > 100:
        length = 100
    while length > 0:
        screech = screech + "E"
        length -= 1
    await ctx.send(screech)

@bot.command(name='zawng')
async def zawng(ctx, args):
    screech = "S"
    length = int(args)
    if length > 100:
        length = 100
    while length > 0:
        screech = screech + "A"
        length -= 1
    await ctx.send(screech)

@bot.command(name='hiss', aliases=['oìsss'])
async def hiss(ctx, args):
    screech = "OÌ"
    length = int(args)
    if length > 100:
        length = 100
    while length > 0:
        screech = screech + "S"
        length -= 1
    await ctx.send(screech)


@bot.command(name='random', aliases=['renulke'])
async def random_word(ctx, args):
    randomwords = []
    number = int(args)
    if number > 30:
        number = 30
    while number > 0:
        randomword = await randomWord()
        randomwords.append(randomword)
        number -= 1
    randomwords = '\n\n'.join(randomwords)
    await ctx.send(embed=discord.Embed(title="Ewo'", description=randomwords))

@bot.command()
async def react(ctx,args,emojiname):
    amount = int(args)
    emoji = '<' + emojiname + '>'
    channel = ctx.message.channel
    if ctx.message.author.id in config.operators:
        await ctx.message.delete()
        messages = await channel.history(limit=amount).flatten()
        for message in messages:
            await message.add_reaction(emoji)

@bot.command()
async def reactmsg(ctx,msg,emojiname):
    if ctx.message.author.id in config.operators:
        await ctx.message.delete()
        emoji = '<' + emojiname + '>'
        message = await ctx.fetch_message(msg)
        await message.add_reaction(emoji)

@bot.command(name='swear', aliases=['räptum'])
async def swear(ctx):
    randomswear = await randomSwear()
    await ctx.send(randomswear)
bot.load_extension('searcher')
bot.load_extension('wordgame')
bot.load_extension('numbers')
bot.run(config.token)
