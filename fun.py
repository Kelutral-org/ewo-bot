import json

import discord
from discord.ext import commands
import bot

import random

with open("compact_database.json", encoding ='utf-8') as f:
    search_database = json.load(f)

with open("swear_database.json", encoding ='utf-8') as f:
    swear_database = json.load(f)


class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def randomWord(self):
        word = random.choices(search_database)
        word = word[0]
        word = word['name'] + ' ' + word['pos'] + ' = \n' + word['definition'].replace('\n', '; ')
        return word

    async def randomSwear(self):
        word = random.choices(swear_database)
        word = word[0]
        word = word['name'] + '!'
        return word

    @commands.command(name='scream')
    async def scream(self, ctx, args):
        screech = "SKR"
        length = int(args)
        if length > 100:
            length = 100
        while length > 0:
            screech = screech + "E"
            length -= 1
        await ctx.send(screech)
    
    @commands.command(name='zawng')
    async def zawng(self, ctx, args):
        screech = "S"
        length = int(args)
        if length > 100:
            length = 100
        while length > 0:
            screech = screech + "A"
            length -= 1
        await ctx.send(screech)
    
    @commands.command(name='hiss', aliases=['oìsss'])
    async def hiss(self, ctx, args):
        screech = "OÌ"
        length = int(args)
        if length > 100:
            length = 100
        while length > 0:
            screech = screech + "S"
            length -= 1
        await ctx.send(screech)
    
    @commands.command(name='random', aliases=['renulke'])
    async def random_word(self, ctx, args):
        randomwords = []
        number = int(args)
        if number > 30:
            number = 30
        while number > 0:
            randomword = await self.randomWord()
            randomwords.append(randomword)
            number -= 1
        randomwords = '\n\n'.join(randomwords)
        await ctx.send(embed=discord.Embed(title="Random Words:", description=randomwords))
    
    @commands.command()
    async def reacthistory(self, ctx,args,emojiname):
        amount = int(args)
        emoji = '<' + emojiname + '>'
        channel = ctx.message.channel
        if ctx.message.author.id in bot.config.operators:
            await ctx.message.delete()
            messages = await channel.history(limit=amount).flatten()
            for message in messages:
                await message.add_reaction(emoji)
    
    @commands.command()
    async def react(self, ctx, msg, emojiname):
        await ctx.message.delete()
        emoji = '<' + emojiname + '>'
        message = await ctx.fetch_message(msg)
        await message.add_reaction(emoji)
    
    @commands.command(name='swear', aliases=['räptum'])
    async def swear(self, ctx):
        randomswear = await self.randomSwear()
        await ctx.send(randomswear)


def setup(bot):
    bot.add_cog(FunCog(bot))
    print('Added new Cog: ' + str(FunCog))
