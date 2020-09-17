import discord
from discord.ext import commands
import re
import bot

class SearchCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name='search', aliases=['fwew', 'word', 'lì\'u', 'pelì\'u'])
    async def search(self, ctx, *args):
        resultnames = []
        resultinfo = []
        # Checks for options
        if '-' in list(args[0]):
            print("options detected")
            options = (list(args[0].lower())[1:])
            wordlist = args[1:]
        else:
            options = []
            wordlist = args
        for word in wordlist:
            for dictionary in bot.search_database:
                foundname = dictionary["name"]
                info = ''
                founddef = dictionary["definition"]
                info = info + founddef+'\n'
                if 'p' in options:
                    info = info +'\nPart of Speech: '+ dictionary['pos']
                if 'i' in options:
                    info = info + '\nIPA: (' + dictionary['ipa'] + ')'
                if 'f' in options:
                    stresslist = dictionary['ipa'].split('.')
                    stress = 0
                    for item in stresslist:
                        stress += 1
                        if re.match('\u02c8',item):
                            break
                    info = info + '\nStressed Syllable: '+str(stress)
                if 's' in options:
                    info = info + '\nSource: ' + dictionary['source']
                if 't' in options:
                    info = info + '\nTopic: '+ dictionary['topic']
                if 'e' in options:
                    try:
                        if re.match(word, foundname) or re.match(word, founddef):
                            resultnames.append(foundname)
                            resultinfo.append(info)
                    except:
                        continue
                else:
                    try:
                        if re.search(word, foundname) or re.search(word, founddef):
                            resultnames.append(foundname)
                            resultinfo.append(info)
                    except:
                        continue
        if resultnames == []:
            await ctx.send("No Results")
        elif len(resultnames)>9:
            await ctx.send("Too Many Results")
        else:
            resultit = 0
            for item in resultnames:
                await ctx.send(embed=discord.Embed(title = item,description=resultinfo[resultit], colour=0xff0000))
                resultit += 1
def setup(bot):
    bot.add_cog(SearchCog(bot))