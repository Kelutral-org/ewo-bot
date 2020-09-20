try:
    import discord, os, random
except:
    os.system("pip install --upgrade discord.py[voice]")
    import discord, os, random
import json
from discord.ext import commands
import config

bot = commands.Bot(command_prefix=config.prefix, help_command=None, description=config.description)

with open("help.json", encoding='utf-8') as f:
    help_file = json.load(f)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------------')
    await bot.change_presence(activity=discord.Game(name=config.status + " V" + config.version))
    print('status set.')
    print('-------------------')


@bot.command(name='help', aliases=['srung'])
async def help(ctx, *args):
    try:
        args = args[0]
    except IndexError:
        args = ""
    args = args.replace('?','')
    displayhelp = ""
    if not args:
        displayhelp = "Here is a list of all Ewo's commands! Run ?help <command> to see more info for that command.\n"
        for entry in help_file:
            displayhelp += "\n" + entry["command"] + ": " + entry["description"]
    else:
        for entry in help_file:
            if str(entry["command"]).strip('**{?}**') == args:
                displayhelp += "\n\n" + entry["command"] + ": " + entry["description"] + "\n"
                try:
                    templist = []
                    if entry["aliases"]:
                        displayhelp += "**Aliases**: "
                    for key in entry["aliases"]:
                        templist.append(key)
                    displayhelp += ', '.join(templist) + "\n"
                except KeyError:
                    displayhelp += "\n"
                displayhelp += "**Usage**: " + entry["usage"] + "\n"
                try:
                    if entry["arg_types"]:
                        displayhelp += "**Args**:\n"
                    for key in entry["arg_types"]:
                        displayhelp += key + ": " + "```" + entry["arg_types"].get(key) + "```" + "\n"
                except KeyError:
                    displayhelp += "\n"
                displayhelp += "**Example**: " + entry["example"]

        if displayhelp == "Here is a list of all Ewo's commands! Run ?help <command> to see more info for that command.\n" or displayhelp == "":
            await ctx.send(
                embed=discord.Embed(title="?help " + str(args), description=str(args) + " is not an Ewo' command!",
                                    colour=0xff0000))
    if not displayhelp == "Here is a list of all Ewo's commands! Run ?help <command> to see more info for that command.\n" and not displayhelp == "":
        await ctx.send(embed=discord.Embed(title="?help " + str(args), description=displayhelp, colour=899718))


@bot.command()
async def exit(ctx):
    if ctx.message.author.id in config.operators:
        await ctx.send(embed=discord.Embed(description="Ikran OS shutting down...", colour=899718))
        os._exit(0)
    else:
        await ctx.send(embed=discord.Embed(title="DENIED!", description="You do not have access to run this command!",
                                           colour=0xff0000))


bot.load_extension('cogs.search.main')
bot.load_extension('cogs.numbers.main')
bot.load_extension('cogs.wordgame.main')
bot.load_extension('cogs.fun.main')
bot.run(config.token)
