import discord
from discord.ext import commands
import re
import bot
import math


def checkdigit(digit):
    if digit == '1':
        affix = ''
    elif digit == '2':
        affix = 'me'
    elif digit == '3':
        affix = 'pxe'
    elif digit == '4':
        affix = 'tsì'
    elif digit == '5':
        affix = 'mrr'
    elif digit == '6':
        affix = 'pu'
    elif digit == '7':
        affix = 'ki'
    else:
        affix = 'ERROR'
    return affix

# Replace RandomCog with something that describes the cog.  E.G. SearchCog for a search engine, sl.
class NumbersCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot


    # commands have this format instead.  For any variables from the main file, use bot.variable.
    @commands.command(name='number',aliases=['num','holpxay'])
    async def number(self, ctx, *args):
        if '-' in args[0]:
            print("options detected")
            options = args[0]
            args = args[1:]
        else:
            options = []
        for item in args:
            print(item)
            try:
                i = len(item)-1
                item = int(item)
                if 'o' in options:
                    decimal = 0
                    if '8' in str(item) or '9' in str(item):
                        await ctx.send('Invalid octal number: 8 and 9 are not valid octal digits!')
                    for digit in str(item):
                        digit = 8**i * int(digit)
                        decimal = decimal+digit
                        i-=1
                    octal = item
                else:
                    decimal = item
                    octal = oct(item)
                    octal = int(''.join(list(str(octal))[2:]))
                    octstring = str(octal)
                if 'c' in options:
                    await ctx.send("Decimal: " + str(decimal) + "\nOctal: " + str(octal))
                    continue
                elif len(octstring) > 5:
                    await ctx.send('Too large to translate!\nPlease choose a number between 0 and 32767 decimal or 77777 octal.\nUse the -c flag to convert without translating.')
                    break
                elif len(octstring) == 1:
                    digit = octstring
                    if digit == '1':
                        ones = '\'aw'
                    elif digit == '2':
                        ones = 'mune'
                    elif digit == '3':
                        ones = 'pxey'
                    elif digit == '4':
                        ones = 'tsìng'
                    elif digit == '5':
                        ones = 'mrr'
                    elif digit == '6':
                        ones = 'pukap'
                    elif digit == '7':
                        ones = 'kinä'
                    elif digit == '0':
                        ones = 'kew'
                    else:
                        ones = 'ERROR'
                    navinum = ones
                else:
                    i = len(octstring) - 1
                    navinum = ''
                    check = 'done'
                    for digit in octstring:
                        if digit == '0':
                            i-=1
                            continue
                        elif i == 0:
                            if digit == '1':
                                if navinum[-1] == 'o':
                                    navinum = navinum+'l'
                                ones = 'aw'
                            elif digit == '2':
                                if navinum[-1] == 'm':
                                    navinum = navinum[:-1]
                                ones = 'mun'
                            elif digit == '3':
                                ones = 'pey'
                            elif digit == '4':
                                ones = 'sìng'
                            elif digit == '5':
                                if navinum[-1] == 'm':
                                    navinum = navinum[:-1]
                                ones = 'mrr'
                            elif digit == '6':
                                ones = 'fu'
                            elif digit == '7':
                                ones = 'hin'
                            elif digit == '0':
                                ones = ''
                            else:
                                ones = 'ERROR'
                            navinum = navinum + ones
                        elif i == 1:
                            affix = checkdigit(digit)
                            if (digit == '0'):
                                continue
                            elif digit == '2' or digit == '5':
                                if navinum[-1] == 'm':
                                    navinum = navinum[:-1]
                                navinum = navinum + affix + 'vo'
                                check = 'check'
                            else:
                                navinum = navinum + affix + 'vo'
                            if octstring[-1] == '0':
                                navinum = navinum+'l'
                            check = 'done'
                            i-=1
                        elif i == 2:
                            affix = checkdigit(digit)
                            if (digit == '0'):
                                continue
                            elif digit == '2' or digit == '5':
                                if navinum[-1] == 'm':
                                    navinum = navinum[:-1]
                                check = 'check'
                            navinum = navinum + affix + 'zam'
                            i-=1
                        elif i == 3:
                            affix = checkdigit(digit)
                            if (digit == '0'):
                                continue
                            elif digit == '2' or digit == '5':
                                if navinum[-1] == 'm':
                                    navinum = navinum[:-1]
                            navinum = navinum + affix + 'vozam'
                            i-=1
                        elif i == 4:
                            affix = checkdigit(digit)
                            navinum = navinum + affix + 'zazam'
                            i-=1

                await ctx.send("Decimal: "+str(decimal)+"\nOctal: "+str(octal)+'\nNa\'vi: '+navinum)
            except:
                await ctx.send("Not a number!")
                pass


def setup(bot):
    bot.add_cog(NumbersCog(bot))