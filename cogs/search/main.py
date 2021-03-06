import discord
from discord.ext import commands
import re
import bot
import json

with open("cogs/search/compact_database.json", encoding='utf-8') as f:
    search_database = json.load(f)


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='search', aliases=['fwew', 'word', 'lì\'u', 'pelì\'u', 'suche'])
    async def search(self, ctx, *args):
        resultnames = []
        resultinfo = []
        # Checks for options
        if '-' in list(args[0]):
            options = (list(args[0].lower())[1:])
            wordlist = args[1:]
        else:
            options = []
            wordlist = args
        for word in wordlist:
            for dictionary in search_database:
                foundname = dictionary["name"]
                info = ''
                founddef = dictionary["definition"]
                info = info + founddef + '\n'
                if 'p' in options:
                    info = info + '\n' + bot.lang.get(str(ctx.guild.id)).get('part_of_speech') + ': ' + dictionary[
                        'pos']
                if 'i' in options:
                    info = info + '\nIPA: (' + dictionary['ipa'] + ')'
                if 'f' in options:
                    stresslist = dictionary['ipa'].split('.')
                    stress = 0
                    for item in stresslist:
                        stress += 1
                        if re.match('\u02c8', item):
                            break
                    info = info + '\n' + bot.lang.get(str(ctx.guild.id)).get('stressed_syllable') + ': ' + str(stress)
                if 's' in options:
                    info = info + '\n' + bot.lang.get(str(ctx.guild.id)).get('source') + ': ' + dictionary['source']
                if 't' in options:
                    info = info + '\n' + bot.lang.get(str(ctx.guild.id)).get('topic') + ': ' + dictionary['topic']
                if 'b' in options:
                    try:
                        if re.search(word, foundname) or re.search(word, founddef):
                            resultnames.append(foundname)
                            resultinfo.append(info)
                    except:
                        continue
                elif 'e' in options:
                    try:
                        if re.fullmatch(word, foundname) or re.fullmatch(word, founddef):
                            resultnames.append(foundname)
                            resultinfo.append(info)
                    except:
                        continue
                else:
                    try:
                        if re.match(word, foundname) or re.match(word, founddef):
                            resultnames.append(foundname)
                            resultinfo.append(info)
                    except:
                        continue
        if not resultnames:
            await ctx.send(embed=discord.Embed(title=bot.lang.get(str(ctx.guild.id)).get('search_title'),
                                               description=bot.lang.get(str(ctx.guild.id)).get('search_no_results'),
                                               color=0xff0000))
        elif len(resultnames) > 20:
            await ctx.send(embed=discord.Embed(title=bot.lang.get(str(ctx.guild.id)).get('search_title'),
                                               description=bot.lang.get(str(ctx.guild.id)).get('search_many_results'),
                                               color=0xff0000))
        else:
            embed = discord.Embed(title=bot.lang.get(str(ctx.guild.id)).get('search_results_title'), color=899718)
            for i, item in enumerate(resultnames):
                embed.add_field(name=item, value=resultinfo[i])
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Search(bot))
    print('Added new Cog: ' + str(Search))
