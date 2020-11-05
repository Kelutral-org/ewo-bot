try:
    import discord, os, random
except:
    os.system("pip install --upgrade discord.py[voice]")
    import discord, os, random
import json
from discord.ext import commands
import config
import git

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=config.prefix, help_command=None, description=config.description, intents=intents)

# Open file for English lang
with open("lang/messages-english.json", encoding='utf-8') as f:
    english_lang = json.load(f)

# Open file for German lang
with open("lang/messages-german.json", encoding='utf-8') as f:
    german_lang = json.load(f)

# Open file for English help menu
with open("help-english.json", encoding='utf-8') as f:
    english_help_file = json.load(f)

# Open file for German help menu
with open("help-german.json", encoding='utf-8') as f:
    german_help_file = json.load(f)

# Open default options file
with open("default_bot_options.json", encoding='utf-8') as f:
    default_bot_options = json.load(f)

# Open file for options
with open("bot_options.json", encoding='utf-8') as f:
    bot_options = json.load(f)

lang = {}


async def set_lang():
    for guild in bot_options:
        if bot_options.get(str(guild)).get('server_language').get('value') == "English":
            lang[str(guild)] = english_lang
        elif bot_options.get(str(guild)).get('server_language').get('value') == "German":
            lang[str(guild)] = german_lang


# Setup presence and print some info
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------------')
    await bot.change_presence(activity=discord.Game(name="Version " + config.version))
    print('status set.')
    print('-------------------')

    for guild in bot.guilds:
        if not str(guild.id) in bot_options:
            bot_options[str(guild.id)] = default_bot_options

    with open("bot_options.json", 'w', encoding='utf-8') as f:
        json.dump(bot_options, f, indent=4)

    await set_lang()

    for guild in bot_options:
        if bot_options[guild]['display_online_message'].get('value') == "True":
            channel = bot.get_channel(int(bot_options.get(guild).get('bot_channel').get('value')))
            await channel.send(lang.get(str(guild)).get('online_message').replace('&1', config.version))


@bot.command(name='options', aliases=['optionen'])
async def options(ctx, *args):
    display = ""
    try:
        mode = args[0]
        option = args[1]
        value = args[2]
    except IndexError:
        pass
    if ctx.author.id in config.operators:
        if mode == 'toggle':
            if bot_options.get(str(ctx.guild.id)).get(option).get('values') == ["True", "False"]:
                if bot_options.get(str(ctx.guild.id)).get(option)['value'] == "True":
                    bot_options.get(str(ctx.guild.id)).get(option)['value'] = "False"
                else:
                    bot_options.get(str(ctx.guild.id)).get(option)['value'] = "True"

                await ctx.send(
                    embed=discord.Embed(title=lang.get(str(ctx.guild.id)).get('options_title'), description=lang.get(str(ctx.guild.id)).get('option_set').replace('&1', option).replace('&2', bot_options.get(str(ctx.guild.id)).get(option).get('value')),
                                        colour=899718))
            else:
                await ctx.send(
                    embed=discord.Embed(title=lang.get(str(ctx.guild.id)).get('options_title'), description=lang.get(str(ctx.guild.id)).get('option_not_boolean').replace('&1', option),
                                        colour=0xff0000))
        if mode == 'set':
            if bot_options.get(str(ctx.guild.id)).get(option).get('values') is None:
                bot_options.get(str(ctx.guild.id)).get(option)['value'] = value

                await ctx.send(
                    embed=discord.Embed(title=lang.get(str(ctx.guild.id)).get('options_title'),
                                        description=lang.get(str(ctx.guild.id)).get('option_set').replace('&1', option).replace('&2', bot_options.get(str(ctx.guild.id)).get(option).get('value')),
                                        colour=899718))
            elif value in bot_options.get(str(ctx.guild.id)).get(option).get('values'):
                bot_options.get(str(ctx.guild.id)).get(option)['value'] = value

                await ctx.send(
                    embed=discord.Embed(title=lang.get(str(ctx.guild.id)).get('options_title'),
                                        description=lang.get(str(ctx.guild.id)).get('option_set').replace('&1', option).replace('&2', bot_options.get(str(ctx.guild.id)).get(option).get('value')),
                                        colour=899718))
            else:
                await ctx.send(
                    embed=discord.Embed(title=lang.get(str(ctx.guild.id)).get('options_title'), description=lang.get(str(ctx.guild.id)).get('option_invalid_value').replace('&1', option).replace('&2', value),
                                        colour=0xff0000))
        if mode == 'list':
            display = "**" + lang.get(str(ctx.guild.id)).get('options_list') + ":**\n\n"
            for option in bot_options.get(str(ctx.guild.id)):
                display += option.replace('_', '\_') + ": \n"
                display += "・" + lang.get(str(ctx.guild.id)).get('options_value') + ": " + bot_options.get(str(ctx.guild.id)).get(option).get('value') + "\n"
                display += "・" + lang.get(str(ctx.guild.id)).get('options_values') + ": " + str(bot_options.get(str(ctx.guild.id)).get(option).get('values')) + "\n\n"

            await ctx.send(
                embed=discord.Embed(title=lang.get(str(ctx.guild.id)).get('options_title'),
                                    description=display,
                                    colour=899718))

        if option == 'server_language':
            await set_lang()

    with open(r'bot_options.json', 'w', encoding='utf-8') as f:
        json.dump(bot_options, f, indent=4)


# Help command
@bot.command(name='help', aliases=['srung', 'hilfe'])
async def help(ctx, *args):
    help_file = None
    if bot_options.get(str(ctx.guild.id)).get('server_language').get('value') == "English":
        help_file = english_help_file
    elif bot_options.get(str(ctx.guild.id)).get('server_language').get('value') == "German":
        help_file = german_help_file

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
        display_help = lang.get(str(ctx.guild.id)).get('help_info') + "\n"
        
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
        if display_help == lang.get(str(ctx.guild.id)).get('help_info') + "\n" or display_help == "":
            await ctx.send(
                embed=discord.Embed(title=ctx.message.content, description=lang.get(str(ctx.guild.id)).get('help_invalid_command').replace('&1', str(args)),
                                    colour=0xff0000))

    # If display_help has been changed from its default (values were found for the args), send the finished help menu
    if not display_help == lang.get(str(ctx.guild.id)).get('help_info') + "\n" and not display_help == "":
        await ctx.send(embed=discord.Embed(title=ctx.message.content, description=display_help, colour=899718))


# Exit command
@bot.command()
async def exit(ctx):

    # If the sender of the command is an Ewo' operator
    if ctx.message.author.id in config.operators:

        # Send a shutdown message and exit
        await ctx.send(embed=discord.Embed(description=lang.get(str(ctx.guild.id)).get('exit_message'), colour=899718))
        os._exit(0)

    # If the sender of the command is NOT an Ewo' operator
    else:

        # Send a deny message and do nothing
        await ctx.send(embed=discord.Embed(title=lang.get(str(ctx.guild.id)).get('denied'), description=lang.get(str(ctx.guild.id)).get('no_access'),
                                           colour=0xff0000))


# Updates the bot and relaunches
@bot.command(name='update')
async def update(ctx, commit):
    if ctx.message.author.id in config.operators:
        REPO = config.repo
        g = git.cmd.Git(config.directory)
        COMMIT_MESSAGE = commit

        repo = git.Repo(REPO)
        repo.git.add(update=True)
        repo.index.commit(COMMIT_MESSAGE)

        origin = repo.remote(name='ewo-bot')
        await ctx.send(lang.get(str(ctx.guild.id)).get('updating'))

        msg = g.pull()
        await ctx.send(lang.get(str(ctx.guild.id)).get('pulling'))

        await bot.close()

        os.system('python bot.py')
        quit()


# Reload command
@bot.command(name='reload')
async def reload(ctx):
    if ctx.message.author.id in config.operators:
        await ctx.send(lang.get(str(ctx.guild.id)).get('reloading'))
        await bot.close()
        os.system('python bot.py')
        quit()


# Load cogs
bot.load_extension('cogs.search.main')
bot.load_extension('cogs.numbers.main')
bot.load_extension('cogs.wordgame.main')
bot.load_extension('cogs.fun.main')
bot.load_extension('cogs.lessons.main')

# Run bot
bot.run(config.token)
