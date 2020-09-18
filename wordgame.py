import json
import random

import discord
import yaml
from discord.ext import commands
import re
import bot

with open("wordgame_words.json", encoding='utf-8') as f:
    wordgame_words = json.load(f)

with open("wordgame_channels.json", encoding='utf-8') as f:
    wordgame_channels = json.load(f)

with open("wordgame_players.yaml", encoding='utf-8') as f:
    wordgame_players = yaml.load(f, Loader=yaml.FullLoader)


# Replace RandomCog with something that describes the cog.  E.G. SearchCog for a search engine, sl.

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    players = wordgame_players
    lastword = ''
    lastword_end = ''
    last_player = 0
    options = []
    wordgame_activechannels = []
    solo = False
    soloplayer = 0
    competitivehistory = []
    competitive = False

    async def solorandom(self):
        possible_words = []
        for word in wordgame_words:
            if word.startswith(self.lastword_end) and not word in self.competitivehistory:
                possible_words.append(word)
        try:
            word = random.choices(possible_words)
            word = word[0]
            self.lastword_end = word[-1]
            self.lastword = word
        except IndexError:
            word = None
        return word

    async def firstword(self):
        word = random.choices(wordgame_words)
        word = word[0]
        return word

    @commands.command(name='points')
    async def points(self, ctx):
        newlist = {}
        for id in self.players:
            user = int(id)
            name = str(bot.bot.get_user(user))
            newlist[name] = self.players.__getitem__(id)
        newlist = str(newlist)
        newlist = newlist.strip('{}')
        newlist = newlist.replace('\'','')
        newlist = newlist.replace(', ','\n')
        await ctx.send(embed=discord.Embed(description=newlist, colour=899718))

    # commands have this format instead.  For any variables from the main file, use bot.variable.
    @commands.command(name='wordgame', aliases=['lì\'uyä'])
    async def wordgame(self, ctx, *args):
        options = list(args)
        print('?wordgame run with following args: ' + str(options) + '\n')
        channels = wordgame_channels

        if 'solo' in options:
            self.solo = True
        if 'multiplayer' in options:
            self.solo = False
        if 'competitive' in options:
            self.competitive = True
        if 'casual' in options:
            self.competitive = False

        if options == ['add'] or options == ['new']:
            if ctx.message.author.id in bot.config.operators:
                if not ctx.channel.id in channels:
                    print("Creating new wordgame channel: " + str(ctx.channel.id))
                    channels.append(ctx.channel.id)
                    with open("wordgame_channels.json", 'w') as f:
                        json.dump(channels, f)
                    await ctx.send(embed=discord.Embed(
                        description="Added this channel (" + str(ctx.channel.id) + ") as a wordgame channel!",
                        colour=899718))
                else:
                    await ctx.send(
                        embed=discord.Embed(description="This channel is already a wordgame channel!", colour=0xff0000))
                    print('Current channel is already a wordgame channel.')

        if options == ['remove'] or options == ['delete']:
            if ctx.message.author.id in bot.config.operators:
                if ctx.channel.id in channels:
                    print("Removing current wordgame channel: " + str(ctx.channel.id))
                    channels.remove(ctx.channel.id)
                    with open("wordgame_channels.json", 'w') as f:
                        json.dump(channels, f)
                    await ctx.send(embed=discord.Embed(
                        description="Removed this channel (" + str(ctx.channel.id) + ") from wordgame channels!",
                        colour=899718))
                else:
                    await ctx.send(
                        embed=discord.Embed(description="This channel is not a wordgame channel!", colour=0xff0000))
                    print('Current channel is not a wordgame channel.')

        if 'start' in options or 'begin' in options:
            if ctx.channel.id in channels:
                if not ctx.channel.id in self.wordgame_activechannels:
                    print('Found current channel in wordgame_channels: ' + str(ctx.channel.id))
                    self.wordgame_activechannels.append(ctx.channel.id)
                    print('Current active channels: ' + str(self.wordgame_activechannels))
                    await ctx.send(embed=discord.Embed(description="Starting game (WIP)!\nSolo: " + str(self.solo) + "\nCompetitive: " + str(self.competitive), colour=899718))
                    self.lastword = await self.firstword()
                    if self.competitive:
                        self.competitivehistory.append(self.lastword)
                    displayword = self.lastword.replace('d', 'tx').replace('g', 'kx').replace('b', 'px').replace(
            'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à', 'ay').replace(
            'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                    self.lastword_end = self.lastword[-1]
                    self.competitivehistory = ["tì'iluke", 'nìsti', 'ean', 'nìtoitsye', 'inan', 'okup', 'eo', 'ŋeŋa', 'pàoaŋ', "ue'", 'alu', 'áaiei', "'a'á", 'uniltsa', 'ilu', 'entu', 'adge', 'lenʀa', 'utral', 'anìhèu', 'aba', 'lal', 'unil', "uniltìrantogolo'", "lì'u", "am'ake", "'akra", 'nìtam', 'eampin', 'èwa', 'máè', 'mundatan', 'akum', 'nìksran', 'nìdan', "'ánìm", "nìpʀte'", 'nʀa', 'mowan', 'mektseŋ', 'alìm', 'auŋia', 'ŋa', 'oèk', 'alo', 'èkyu', 'kè', 'kanfpìl', 'uk', 'ŋulpin', "lì'ukìŋ", 'ŋampam', 'naŋ', 'pàsmuŋ', 'mip', "'e'al", "ŋa'", "ke'u", "lì'upuk", 'oe', 'ugo', 'námtoruktek', 'egan', 'letog', 'kelutral', 'mefo', 'gam', 'mal', 'omum', 'mèptu', 'lam', 'makto', 'um', 'europa', 'oare', 'oèä', 'aho', "onvä'", 'äo', "'efu", "'ä'", 'ninat', 'uniltaron', 'etrìp', 'tekre', 'lá', 'pil', 'anurai', 'áŋa', 'ontsaŋ', 'io', 'niŋyen', 'ŋèn', 'inanfya', 'numtseŋvi', 'ŋim', 'afpáŋ', 'kar', 'mek', "ko'on", 'rìk', 'egdu', 'nume', 'uniltìranyu', 'uldatu', 'gener', 'uniltìrantog', "mà'", 'rim', 'gid', "'ág", "rä'ä", 'dur', "tswa'", 'änsìt', 'ioaŋ', "'ampi", "lì'fyavi", 'ŋul', 'ohag', 'irào', 'ŋoŋ', 'gamtseŋ', 'atèo', 'ŋoa', 'ŋip', 'oeŋ', 'ohe', 'po', 'uvan', 'eltu', 'mam', 'nim', "uolì'uvi", 'maru', 'nekán', "i'en", 'äzan', 'nefä', 'àoe', 'nìbà', 'ŋimpup', 'ebaŋ', 'nìkefdo', 'poan', 'ulte', 'ontu', 'èk', 'emrè', 'utu', 'kelku', 'iknimàa', 'utumauti', 'adgerel', "am'a", 'ŋà', 'lìŋ']
                    await ctx.send(
                        embed=discord.Embed(description="The first word is " + displayword + "!", colour=899718))
                else:
                    await ctx.send(
                        embed=discord.Embed(description="There is already a game in this channel!", colour=0xff0000))

        if 'stop' in options or 'end' in options:
            if ctx.channel.id in channels:
                if ctx.channel.id in self.wordgame_activechannels:
                    print('Found current channel in wordgame_channels: ' + str(ctx.channel.id))
                    self.wordgame_activechannels.remove(ctx.channel.id)
                    print('Current active channels: ' + str(self.wordgame_activechannels))
                    await ctx.send(embed=discord.Embed(description="Stopping game!", colour=899718))
                    self.last_player = 0
                    self.solo = False
                    self.competitive = False
                else:
                    await ctx.send(
                        embed=discord.Embed(description="There is no active game in this channel!", colour=0xff0000))
        print('---------------------')

    @commands.Cog.listener()
    async def on_message(self, message):
        msg = message.content.lower()
        if message.channel.id in self.wordgame_activechannels:
            if not message.author.bot:
                if not msg.startswith('?') and not msg.startswith('!'):
                    if not ' ' in msg:
                        if not self.solo:
                            if not message.author.id == self.last_player:
                                msg = msg.replace('ng', 'ŋ').replace('tx', 'd').replace('kx', 'g').replace(
                                    'px', 'b').replace('aw', 'á').replace('ew', 'é').replace('ay', 'à').replace(
                                    'ey', 'è').replace('rr', 'ʀ').replace('ll', 'j')
                                if msg.startswith(self.lastword_end):
                                    if msg in wordgame_words:
                                        if self.competitive and not msg in self.competitivehistory or not self.competitive:
                                            newword = msg
                                            self.lastword_end = newword[-1]
                                            self.lastword = newword
                                            if self.competitive:
                                                self.competitivehistory.append(newword)
                                            newword = msg.replace('d', 'tx').replace('g', 'kx').replace('b', 'px').replace(
                                                'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à', 'ay').replace(
                                                'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                                            await message.channel.send(
                                                embed=discord.Embed(
                                                    description=str(message.author.name) + " said " + newword + "!",
                                                    colour=899718))
                                            self.last_player = message.author.id
                                            author = str(message.author.id)
                                            if author in self.players:
                                                self.players[author] += 1
                                            else:
                                                self.players[
                                                    self.players.get(author, author)] = 1
                                            with open("wordgame_players.yaml", 'w') as f:
                                                yaml.dump(self.players, f)
                                    if self.competitive and msg in self.competitivehistory:
                                        await message.channel.send(
                                            embed=discord.Embed(description="You have already used this word!",
                                                                colour=0xff0000))
                            else:
                                await message.channel.send(
                                    embed=discord.Embed(description="You already said a word!", colour=0xff0000))
                        else:
                            msg = msg.replace('ng', 'ŋ').replace('tx', 'd').replace('kx', 'g').replace(
                                'px', 'b').replace('aw', 'á').replace('ew', 'é').replace('ay', 'à').replace(
                                'ey', 'è').replace('rr', 'ʀ').replace('ll', 'j')
                            if msg.startswith(self.lastword_end):
                                if msg in wordgame_words:
                                    if self.competitive and msg in self.competitivehistory:
                                        await message.channel.send(
                                            embed=discord.Embed(description="This word has already been used!",
                                                                colour=0xff0000))
                                    if self.competitive and not msg in self.competitivehistory:
                                        self.lastword = msg
                                        self.lastword_end = msg[-1]
                                        newword = await self.solorandom()
                                        print(newword)
                                        try:
                                            displayword = newword.replace('d', 'tx').replace('g', 'kx').replace('b',
                                                                                                                'px').replace(
                                                'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à',
                                                                                                         'ay').replace(
                                                'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                                        except AttributeError:
                                            return ''
                                        if self.competitive:
                                            self.competitivehistory.append(newword)
                                            self.competitivehistory.append(msg)
                                            templist = []
                                            for word in wordgame_words:
                                                if not word in self.competitivehistory and word in templist:
                                                    print('not vald: ' + word)
                                                    await self.endcompetitive(message, bot.bot.user.name)
                                                    break
                                                if not word in self.competitivehistory and word.startswith(msg[-1]):
                                                    templist.append(word)
                                            if newword is None:
                                                print('newword was none')
                                                await self.endcompetitive(message, message.author)
                                            if newword is not None:
                                                print('newword was not none')
                                                await message.channel.send(embed=discord.Embed(description=displayword + "!", colour=899718))

                                    if not self.competitive:
                                        newword = await self.solorandom()
                                        try:
                                            displayword = newword.replace('d', 'tx').replace('g', 'kx').replace('b','px').replace(
                                                'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à', 'ay').replace(
                                                'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                                        except AttributeError:
                                            return ''
                                        self.lastword = newword
                                        self.lastword_end = newword[-1]
                                        await message.channel.send(embed=discord.Embed(description=displayword + "!", colour=899718))

    async def endcompetitive(self,message,winner):
        if message.channel.id in wordgame_channels:
            print(winner + 'won the game!')
            print('Found current channel in wordgame_channels: ' + str(message.channel.id))
            print('Current active channels: ' + str(self.wordgame_activechannels))
            print(message.channel.id)
            self.wordgame_activechannels.remove(message.channel.id)
            await message.channel.send(embed=discord.Embed(description=str(winner) + " won!", colour=899718))
            self.last_player = 0
            self.solo = False
            self.competitive = False


def setup(bot):
    bot.add_cog(GameCog(bot))
    print('Added new Cog: ' + str(GameCog))
