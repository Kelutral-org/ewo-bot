import json
import yaml
import random
from collections import OrderedDict

import discord
from discord.ext import commands
import bot

with open("wordgame_words.json", encoding='utf-8') as f:
    wordgame_words = json.load(f)

with open("wordgame_channels.json", encoding='utf-8') as f:
    wordgame_channels = json.load(f)

with open("wordgame_players.yaml", encoding='utf-8') as f:
    wordgame_players = yaml.load(f, Loader=yaml.FullLoader)

players = {}
for key, value in sorted(wordgame_players.items(), key=lambda x: int(x[1]), reverse=True):
    players[key] = value
with open("wordgame_players.yaml", 'w') as f:
    yaml.safe_dump(players, f, default_flow_style=False, sort_keys=False)
    f.close()
wordgame_players = players


# Replace RandomCog with something that describes the cog.  E.G. SearchCog for a search engine, sl.

class WordgameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    players = OrderedDict(wordgame_players)
    lastword = ''
    lastword_end = ''
    last_player = 0
    options = []
    wordgame_activechannels = []
    solo = False
    soloplayer = 0
    competitivehistory = []
    competitive = False
    gamepoints = {}

    async def solorandom(self):
        possible_words = []
        if self.competitive:
            for word in wordgame_words:
                if word.startswith(self.lastword_end) and not word in self.competitivehistory:
                    possible_words.append(word)
            try:
                word = random.choices(possible_words)
                word = word[0]
                self.lastword_end = word[-1]
                self.lastword = word
            except IndexError:
                return None
        else:
            for word in wordgame_words:
                if word.startswith(self.lastword_end):
                    possible_words.append(word)
            word = random.choices(possible_words)
            word = word[0]
            self.lastword_end = word[-1]
            self.lastword = word
        return word

    async def firstword(self):
        word = random.choices(wordgame_words)
        word = word[0]
        self.lastword = word
        self.lastword_end = self.lastword[-1]
        return word

    @commands.command(name='points')
    async def points(self, ctx):
        newlist = {}
        for id in self.players:
            user = int(id)
            name = bot.discord.Guild.get_member(ctx.guild, user)
            name = str("!" + str(name.nick) + "!")
            if name == "!" + 'None' + "!":
                name = bot.bot.get_user(user)
                name = str("!" + name.display_name + "!")
            newlist[name] = self.players.get(id)
        newlist = str(newlist)
        newlist = newlist.strip('{}')
        newlist = newlist.replace('!\'', '')
        newlist = newlist.replace('\'!', '')
        newlist = newlist.replace(', ', '\n')
        await ctx.send(embed=discord.Embed(title="Points:", description=newlist, colour=899718))

    # commands have this format instead.  For any variables from the main file, use bot.variable.
    @commands.command(name='wordgame', aliases=['lì\'uyä'])
    async def wordgame(self, ctx, *args):
        options = list(args)
        print('?wordgame run with following args: ' + str(options) + '\n')
        channels = wordgame_channels

        if 'solo' in options:
            if ctx.channel.id in self.wordgame_activechannels:
                await ctx.channel.send(
                    embed=discord.Embed(description="This game is now solo!", colour=899718))
            self.solo = True
            print('Solo = True')
        if 'multiplayer' in options:
            if ctx.channel.id in self.wordgame_activechannels:
                await ctx.channel.send(
                    embed=discord.Embed(description="This game is now multiplayer!", colour=899718))
            self.solo = False
            print('Solo = False')
        if 'competitive' in options:
            if ctx.channel.id in self.wordgame_activechannels:
                await ctx.channel.send(
                    embed=discord.Embed(description="This game is now competitive!", colour=899718))
            self.competitive = True
            print('Competitive = True')
        if 'casual' in options:
            if ctx.channel.id in self.wordgame_activechannels:
                await ctx.channel.send(
                    embed=discord.Embed(description="This game is now casual!", colour=899718))
            self.competitive = False
            print('Competitive = False')

        if options == ['add'] or options == ['new']:
            if ctx.message.author.id in bot.config.operators:
                if not ctx.channel.id in channels:
                    print("Creating new wordgame channel: " + str(ctx.channel.id))
                    channels.append(ctx.channel.id)
                    with open("wordgame_channels.json", 'w') as f:
                        json.dump(channels, f)
                        f.close()
                    await ctx.send(embed=discord.Embed(description="Added this channel (" + str(
                        ctx.channel.id) + ") as a wordgame channel!",
                                                       colour=899718))
                else:
                    await ctx.send(
                        embed=discord.Embed(description="This channel is already a wordgame channel!",
                                            colour=0xff0000))
                    print('Current channel is already a wordgame channel.')

        if options == ['remove'] or options == ['delete']:
            if ctx.message.author.id in bot.config.operators:
                if ctx.channel.id in channels:
                    print("Removing current wordgame channel: " + str(ctx.channel.id))
                    channels.remove(ctx.channel.id)
                    with open("wordgame_channels.json", 'w') as f:
                        json.dump(channels, f)
                        f.close()
                    await ctx.send(embed=discord.Embed(description="Removed this channel (" + str(
                        ctx.channel.id) + ") from wordgame channels!",
                                                       colour=899718))
                else:
                    await ctx.send(
                        embed=discord.Embed(description="This channel is not a wordgame channel!",
                                            colour=0xff0000))
                    print('Current channel is not a wordgame channel.')

        if 'start' in options or 'begin' in options:
            if ctx.channel.id in channels:
                if not ctx.channel.id in self.wordgame_activechannels:
                    print('Found current channel in wordgame_channels: ' + str(ctx.channel.id) + ", activating it...")
                    self.wordgame_activechannels.append(ctx.channel.id)
                    print('Current active channels: ' + str(self.wordgame_activechannels))
                    await self.firstword()
                    if self.competitive:
                        self.competitivehistory.append(self.lastword)
                    displayword = self.lastword.replace('d', 'tx').replace('g', 'kx').replace('b', 'px').replace(
                        'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à', 'ay').replace(
                        'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                    await ctx.send(embed=discord.Embed(description="Starting game (WIP)!\nSolo: " + str(
                        self.solo) + "\nCompetitive: " + str(
                        self.competitive) + "\n\nThe first word is " + displayword + "!", colour=899718))
                else:
                    await ctx.send(
                        embed=discord.Embed(description="There is already a game in this channel!",
                                            colour=0xff0000))

        if 'stop' in options or 'end' in options:
            if ctx.channel.id in channels:
                if ctx.channel.id in self.wordgame_activechannels:
                    print('Found current channel in wordgame_activechannels: ' + str(
                        ctx.channel.id) + ", deactivating it...")
                    self.wordgame_activechannels.remove(ctx.channel.id)
                    print('Current active channels: ' + str(self.wordgame_activechannels))
                    pointlist = {}
                    for id in self.gamepoints:
                        user = int(id)
                        name = bot.discord.Guild.get_member(ctx.guild, user)
                        name = str("!" + str(name.nick) + "!")
                        if name == "!" + 'None' + "!":
                            name = bot.bot.get_user(user)
                            name = str("!" + name.display_name + "!")
                        pointlist[name] = self.gamepoints.get(id)
                    pointlist = str(pointlist)
                    pointlist = pointlist.strip('{}')
                    pointlist = pointlist.replace('!\'', '')
                    pointlist = pointlist.replace('\'!', '')
                    pointlist = pointlist.replace(', ', '\n')
                    if not self.solo:
                        await ctx.channel.send(embed=discord.Embed(
                            description="Stopping game!\n" + "Total points for this round:\n" + pointlist,
                            colour=899718))
                    else:
                        await ctx.channel.send(embed=discord.Embed(description="Stopping game!",
                                                                   colour=899718))
                    self.last_player = 0
                    self.solo = False
                    self.competitive = False
                    self.gamepoints = {}
                else:
                    await ctx.send(
                        embed=discord.Embed(description="There is no active game in this channel!",
                                            colour=0xff0000))
        print('---------------------')

    @commands.Cog.listener()
    async def on_message(self, message):

        if '’' in message.content:
            message.content = message.content.replace('’', '\'')

        msg = message.content.lower()
        if message.channel.id in self.wordgame_activechannels and not message.author.bot and not msg.startswith(
                '?') and not msg.startswith('!') and not ' ' in msg:
            if not self.solo:
                msg = msg.replace('ng', 'ŋ').replace('tx', 'd').replace('kx', 'g').replace(
                    'px', 'b').replace('aw', 'á').replace('ew', 'é').replace('ay', 'à').replace(
                    'ey', 'è').replace('rr', 'ʀ').replace('ll', 'j')
                if msg.startswith(self.lastword_end):
                    if msg in wordgame_words and message.author.id == self.last_player:
                        await message.channel.send(
                            embed=discord.Embed(description="You already said a word!", colour=0xff0000))
                    if msg in wordgame_words and not message.author.id == self.last_player:
                        if self.competitive and msg in self.competitivehistory:
                            await message.channel.send(
                                embed=discord.Embed(description="This word has already been used!",
                                                    colour=0xff0000))
                        if (self.competitive and not msg in self.competitivehistory) or not self.competitive:
                            newword = msg
                            displayword = msg.replace('d', 'tx').replace('g', 'kx').replace('b',
                                                                                            'px').replace(
                                'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à',
                                                                                         'ay').replace(
                                'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                            self.lastword_end = newword[-1]
                            self.lastword = newword

                            name = bot.discord.Guild.get_member(message.guild, message.author.id)
                            name = str(name.nick)
                            if name == 'None':
                                name = bot.bot.get_user(message.author.id)
                                name = str(name.display_name)

                            await message.channel.send(
                                embed=discord.Embed(description=str(
                                    name) + " said " + displayword + "!",
                                                    colour=899718))

                            if self.competitive:
                                self.competitivehistory.append(newword)

                                templist = []
                                for word in wordgame_words:
                                    if not word in self.competitivehistory and word.startswith(newword[-1]):
                                        templist.append(word)
                                if templist == []:
                                    await self.endcompetitive(message, name)
                                    author = str(message.author.id)
                                    if author in self.players:
                                        self.players[author] += 5
                                    else:
                                        self.players[
                                            self.players.get(author, author)] = 5
                                    playerdata = {}
                                    for key, value in sorted(self.players.items(), key=lambda x: int(x[1]),
                                                             reverse=True):
                                        playerdata[key] = value
                                    with open("wordgame_players.yaml", 'w') as f:
                                        yaml.safe_dump(playerdata, f, default_flow_style=False,
                                                       sort_keys=False)
                                        f.close()
                                    self.players = playerdata

                            # GAME POINTS
                            gameauthor = str(message.author.id)
                            if gameauthor in self.gamepoints:
                                self.gamepoints[gameauthor] += 1
                            else:
                                self.gamepoints[
                                    self.gamepoints.get(gameauthor, gameauthor)] = 1
                            gameplayerdata = {}
                            for key, value in sorted(self.gamepoints.items(), key=lambda x: int(x[1]),
                                                     reverse=True):
                                gameplayerdata[key] = value
                            self.gamepoints = gameplayerdata

                            # GLOBAL POINTS

                            self.last_player = message.author.id
                            author = str(message.author.id)
                            if author in self.players:
                                self.players[author] += 1
                            else:
                                self.players[
                                    self.players.get(author, author)] = 1
                            playerdata = {}
                            for key, value in sorted(self.players.items(), key=lambda x: int(x[1]),
                                                     reverse=True):
                                playerdata[key] = value
                            with open("wordgame_players.yaml", 'w') as f:
                                yaml.safe_dump(playerdata, f, default_flow_style=False, sort_keys=False)
                                f.close()
                            self.players = playerdata

            else:
                msg = msg.replace('ng', 'ŋ').replace('tx', 'd').replace('kx', 'g').replace(
                    'px', 'b').replace('aw', 'á').replace('ew', 'é').replace('ay', 'à').replace(
                    'ey', 'è').replace('rr', 'ʀ').replace('ll', 'j')
                if msg.startswith(self.lastword_end) and msg in wordgame_words:
                    if not self.competitive:
                        self.lastword = msg
                        self.lastword_end = msg[-1]
                        newword = await self.solorandom()
                        try:
                            displayword = newword.replace('d', 'tx').replace('g', 'kx').replace('b', 'px').replace(
                                'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à', 'ay').replace(
                                'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                        except AttributeError:
                            print('displayword is fucked')
                        await message.channel.send(
                            embed=discord.Embed(description=displayword + "!", colour=899718))
                    if self.competitive and msg in self.competitivehistory:
                        await message.channel.send(
                            embed=discord.Embed(description="This word has already been used!",
                                                colour=0xff0000))
                    if self.competitive and not msg in self.competitivehistory:
                        self.lastword = msg
                        self.lastword_end = msg[-1]
                        newword = await self.solorandom()
                        try:
                            displayword = newword.replace('d', 'tx').replace('g', 'kx').replace('b',
                                                                                                'px').replace(
                                'ŋ', 'ng').replace('á', 'aw').replace('é', 'ew').replace('à',
                                                                                         'ay').replace(
                                'è', 'ey').replace('ʀ', 'rr').replace('j', 'll')
                        except AttributeError:
                            print('displayword is fucked')
                        if self.competitive:
                            self.competitivehistory.append(newword)
                            self.competitivehistory.append(msg)

                            templist = []
                            for word in wordgame_words:
                                try:
                                    if not word in self.competitivehistory and word.startswith(newword[-1]):
                                        templist.append(word)
                                except TypeError:
                                    break

                            user = message.author.id
                            name = bot.discord.Guild.get_member(message.guild, user)
                            name = name.nick
                            if name == 'None':
                                name = bot.bot.get_user(user)
                                name = str(name.display_name)

                            if newword is None:
                                await self.endcompetitive(message, name)
                            if newword is not None:
                                await message.channel.send(
                                    embed=discord.Embed(description=displayword + "!", colour=899718))

                            if templist == []:
                                await self.endcompetitive(message, bot.bot.user.name)

    async def endcompetitive(self, message, winner):
        if message.channel.id in self.wordgame_activechannels:
            print(str(winner) + ' won the game!')
            print(
                'Found current channel in wordgame_activechannels: ' + str(message.channel.id) + ', deactivating it...')
            print('Current active channels: ' + str(self.wordgame_activechannels))
            self.wordgame_activechannels.remove(message.channel.id)
            pointlist = {}
            for id in self.gamepoints:
                user = int(id)
                name = bot.discord.Guild.get_member(message.guild, user)
                name = str("!" + str(name.nick) + "!")
                if name == "!" + 'None' + "!":
                    name = bot.bot.get_user(user)
                    name = str("!" + name.display_name + "!")
                pointlist[name] = self.gamepoints.get(id)
            pointlist = str(pointlist)
            pointlist = pointlist.strip('{}')
            pointlist = pointlist.replace('!\'', '')
            pointlist = pointlist.replace('\'!', '')
            pointlist = pointlist.replace(', ', '\n')
            if not self.solo:
                await message.channel.send(embed=discord.Embed(description=str(
                    winner) + " won!\n" + "Total points for this round:\n" + pointlist, colour=899718))
            else:
                await message.channel.send(embed=discord.Embed(description=str(
                    winner) + " won!\n", colour=899718))
            self.last_player = 0
            self.solo = False
            self.competitive = False
            self.gamepoints = {}


def setup(bot):
    bot.add_cog(WordgameCog(bot))
    print('Added new Cog: ' + str(WordgameCog))
