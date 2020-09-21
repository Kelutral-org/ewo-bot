try:
    import discord, os, random
except:
    os.system("pip install --upgrade discord.py[voice]")
    import discord, os, random
import json
from discord.ext import commands
import config

bot = commands.Bot(command_prefix=config.prefix, help_command=None, description=config.description)

# Open file for help menu
with open("help.json", encoding='utf-8') as f:
    help_file = json.load(f)


# Setup presence and print some info
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------------')
    await bot.change_presence(activity=discord.Game(name=config.status + " V" + config.version))
    print('status set.')
    print('-------------------')


# Help command
@bot.command(name='help', aliases=['srung'])
async def help(ctx, *args):
    # Try to select first section of args
    try:
        args = args[0]
        
    # If args cannot be indexed (if it is None), set it to an empty string
    except IndexError:
        args = ""
        
    # Remove prefixes from beginning of arg (For more intuitive arguments)
    args = args.replace('?','')

    # Empty string to reference later
    display_help = ""
    
    # If user has run ?help with no args, display the main help menu
    if not args:
        
        # Begin by setting the string to the instructions
        display_help = "Here is a list of all Ewo's commands! Run ?help <command> to see more info for that command.\n"
        
        # For each command in the help file
        for command in help_file:
            
            # Add this command's command name and description to the string
            display_help += "\n" + command["command"] + ": " + command["description"]
            
    # If there are arguments
    else:
        
        # For each command in the help file
        for command in help_file:
            
            # Find command for argument by stripping the current command's command name of its formatting and prefix,
            # then testing if the result is equal to the argument
            if str(command["command"]).strip('**{?}**') == args:
                
                # Add command name and description
                display_help += "\n\n" + command["command"] + ": " + command["description"] + "\n"
                
                # Try to find aliases for command
                try:
                    # Empty list to reference later
                    alias_list = []
                    
                    # If there are aliases, add a section for them to the string
                    if command["aliases"]:
                        display_help += "**Aliases**: "
                        
                    # Add any aliases to alias_list
                    for alias in command["aliases"]:
                        alias_list.append(alias)
                    
                    # Join alias_list into a string and add it to display_help
                    display_help += ', '.join(alias_list)

                    # If there are aliases, add a new line to display_help
                    if command["aliases"]:
                        display_help += "\n"

                # If there are no aliases
                except KeyError:
                    # Do nothing
                    pass

                # Add usage section and a new line
                display_help += "**Usage**: " + command["usage"] + "\n"

                # Try to find arg types for command
                try:

                    # If there is an arg_types section
                    if command["arg_types"]:

                        # Add section for them to display_help
                        display_help += "**Args**:\n"

                    # For every key in arg_types, add it's name to the string and add its value as a code block,
                    # followed by a new line
                    for key in command["arg_types"]:
                        display_help += key + ": " + "```" + command["arg_types"].get(key) + "```" + "\n"

                # If there is no arg_types section
                except KeyError:
                    # Do nothing
                    pass
                # Add an example of command usage
                display_help += "**Example**: " + command["example"]

        # If display_help has not been changed from its default (nothing was found for the args), send a warning
        if display_help == "Here is a list of all Ewo's commands! Run ?help <command> to see more info for that command.\n" or display_help == "":
            await ctx.send(
                embed=discord.Embed(title="?help " + str(args), description=str(args) + " is not an Ewo' command!",
                                    colour=0xff0000))

    # If display_help has been changed from its default (values were found for the args), send the finished help menu
    if not display_help == "Here is a list of all Ewo's commands! Run ?help <command> to see more info for that command.\n" and not display_help == "":
        await ctx.send(embed=discord.Embed(title="?help " + str(args), description=display_help, colour=899718))


# Exit command
@bot.command()
async def exit(ctx):

    # If the sender of the command is an Ewo' operator
    if ctx.message.author.id in config.operators:

        # Send a shutdown message and exit
        await ctx.send(embed=discord.Embed(description="Ikran OS shutting down...", colour=899718))
        os._exit(0)

    # If the sender of the command is NOT an Ewo' operator
    else:

        # Send a deny message and do nothing
        await ctx.send(embed=discord.Embed(title="DENIED!", description="You do not have access to run this command!",
                                           colour=0xff0000))


# Load cogs
bot.load_extension('cogs.search.main')
bot.load_extension('cogs.numbers.main')
bot.load_extension('cogs.wordgame.main')
bot.load_extension('cogs.fun.main')

# Run bot
bot.run(config.token)
