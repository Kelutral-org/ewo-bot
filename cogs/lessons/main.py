import json
import re

import discord
from discord.ext import commands
import bot


# Cog
class Lessons(commands.Cog):

    message_listens = {}
    listen_for_messages = False
    confirm_adding_level = False
    listen_type = ""
    level = 0
    description = ""

    def __init__(self, bot):
        self.bot = bot
        with open("cogs/lessons/teacher_roles.json", encoding="utf-8") as f:
            self.teacher_roles = json.load(f)
        with open("cogs/lessons/levels.json", encoding="utf-8") as f:
            self.levels = json.load(f)
        with open("cogs/lessons/students.json", encoding="utf-8") as f:
            self.students = json.load(f)

    @commands.command(name='lesson', aliases=['lessons', 'sänumvi', 'aysänumvi'])
    async def lesson(self, ctx, *args):
        args = list(args)
        teacher_roles = []
        author_role = 0

        # Karyu commands
        for value1 in self.teacher_roles:
            for value2 in ctx.author.roles:
                teacher_roles.append(value1)
                author_role = value2

        if author_role.id in teacher_roles:

            if 'addrole' in args:
                for arg in args:
                    if re.search(r'<@&[0123456789]*?>', arg):
                        self.teacher_roles.append(int(arg.strip('<>').replace('@', '').replace('&', '')))
                        with open("cogs/lessons/teacher_roles.json", 'w', encoding="utf-8") as f:
                            json.dump(self.teacher_roles, f, indent=4)
                        await ctx.send(
                            embed=discord.Embed(title="Add Role", description="Added!",
                                                colour=899718))

            if 'removerole' in args:
                for arg in args:
                    if re.search(r'<@&[0123456789]*?>', arg):
                        self.teacher_roles.remove(int(arg.strip('<>').replace('@', '').replace('&', '')))
                        with open("cogs/lessons/teacher_roles.json", 'w', encoding="utf-8") as f:
                            json.dump(self.teacher_roles, f, indent=4)
                        await ctx.send(
                            embed=discord.Embed(title="Remove Role", description="Removed!",
                                                colour=899718))

            if 'addlevel' in args:
                current_levels = 0
                for count, value in enumerate(self.levels.get(str(ctx.author.id), {})):
                    current_levels = count + 1
                self.level = current_levels + 1
                self.listen_type = "add"
                self.message_listens[ctx.author.id] = ctx.channel.id
                self.listen_for_messages = True
                await ctx.send(
                    embed=discord.Embed(title="New Level", description="Please supply a description for this level. "
                                                    "This should include any topics to discuss "
                                                    "during lessons for this level, "
                                                    "as well as any notes you have to members of this level"
                                                    ".\n Say \"cancel\" to cancel adding the new level.",
                                        colour=899718))

            if 'removelevel' in args:
                for count, arg in enumerate(args):
                    if arg.isdigit() and count == 1:
                        values = self.levels.get(str(ctx.author.id))
                        if values is None:
                            values = {}

                        if arg in values:
                            self.levels[str(ctx.author.id)].pop(arg, None)
                            if self.levels[str(ctx.author.id)] == {}:
                                self.levels.pop(str(ctx.author.id), None)

                            levels_copy = self.levels.copy()
                            for level in self.levels[str(ctx.author.id)].copy():
                                if int(level) > int(arg):
                                    levels_copy[str(ctx.author.id)][str(int(level) - 1)] = levels_copy[
                                        str(ctx.author.id)].pop(level)
                            self.levels = levels_copy

                            with open("cogs/lessons/levels.json", 'w', encoding="utf-8") as f:
                                json.dump(self.levels, f, indent=4)
                            await ctx.send(
                                embed=discord.Embed(title="Remove Level" ,description="Removed level " + arg + "!",
                                                    colour=899718))
                        else:
                            await ctx.send(
                                embed=discord.Embed(description="This level does not exist!",
                                                    colour=0xff0000))

            if 'students' in args:
                if not 'default' in args:
                    teacher_name = ctx.author.nick
                    if teacher_name is None:
                        teacher_name = ctx.author.name
                    display = "**Students in " + teacher_name + "'s system:**\n\n"

                    for student in self.students:
                        # Get the member of the user id
                        student_name = bot.discord.Guild.get_member(ctx.guild, int(student))
                        # Get their nickname
                        student_name = student_name.nick

                        # If the user has no nickname
                        if student_name is None:
                            # Get the user of the user id
                            student_name = bot.bot.get_user(int(student))
                            # Get their display name
                            student_name = student_name.name
                        if str(ctx.author.id) in self.students.get(student):
                            display += student_name + ": " + str(self.students[student].get(str(ctx.author.id))) + "\n"
                else:
                    display = "Students in the default system:\n\n"

                    for student in self.students:
                        # Get the member of the user id
                        student_name = bot.discord.Guild.get_member(ctx.guild, int(student))
                        # Get their nickname
                        student_name = student_name.nick

                        # If the user has no nickname
                        if student_name is None:
                            # Get the user of the user id
                            student_name = bot.bot.get_user(int(student))
                            # Get their display name
                            student_name = student_name.name
                        if 'default' in self.students.get(student):
                            display += student_name + ": " + str(self.students[student].get('default')) + "\n"

                await ctx.send(
                    embed=discord.Embed(title="Students", description=display, colour=899718))

            if 'editlevel' in args:
                for count, arg in enumerate(args):
                    if arg.isdigit() and count == 1:
                        values = self.levels.get(str(ctx.author.id))
                        if values is None:
                            values = {}

                        if arg in values:
                            self.level = arg
                            self.listen_type = "add"
                            self.message_listens[ctx.author.id] = ctx.channel.id
                            self.listen_for_messages = True
                            await ctx.send(
                                embed=discord.Embed(title="New Level", description="Please supply a description for this level. "
                                                                                   "This should include any topics to discuss "
                                                                                   "during lessons for this level, "
                                                                                   "as well as any notes you have to members of this level"
                                                                                   ".\n Say \"cancel\" to cancel adding the new level.",
                                                    colour=899718))

                        else:
                            await ctx.send(
                                embed=discord.Embed(description="This level does not exist!",
                                                    colour=0xff0000))

            if 'nudgelevel' in args:
                for count, arg in enumerate(args):
                    if arg.isdigit() and count == 1:
                        values = self.levels.get(str(ctx.author.id))
                        if values is None:
                            values = {}

                        if arg in values:
                            self.level = int(arg)
                            self.listen_type = "nudge"
                            self.message_listens[ctx.author.id] = ctx.channel.id
                            self.listen_for_messages = True
                            await ctx.send(
                                embed=discord.Embed(title="New Level", description="Please supply a description for this level. "
                                                                "This should include any topics to discuss "
                                                                "during lessons for this level, "
                                                                "as well as any notes you have to members of this level"
                                                                ".\n Say \"cancel\" to cancel adding the new level.",
                                                    colour=899718))

                        else:
                            await ctx.send(
                                embed=discord.Embed(description="This level does not exist!",
                                                    colour=0xff0000))

            if 'setlevel' in args:
                teacher_id = 0
                teacher_name = ""
                student_id = 0
                student_name = ""
                level = 0

                for count, arg in enumerate(args):
                    if re.match(r'<@![0123456789]*?>', arg) and count == 1:
                        student_id = int(arg.strip('<>').replace('@!', ''))
                        teacher_id = ctx.author.id
                        # Get the member of the user id
                        student_name = bot.discord.Guild.get_member(ctx.guild, student_id)
                        # Get their nickname
                        student_name = str(student_name.nick)

                        # If the user has no nickname
                        if student_name == 'None':
                            # Get the user of the user id
                            student_name = bot.bot.get_user(student_id)
                            # Get their display name
                            student_name = str(student_name.name)

                        # Get the member of the user id
                        teacher_name = bot.discord.Guild.get_member(ctx.guild, teacher_id)
                        # Get their nickname
                        teacher_name = str(teacher_name.nick)

                        # If the user has no nickname
                        if teacher_name == 'None':
                            # Get the user of the user id
                            teacher_name = bot.bot.get_user(teacher_id)
                            # Get their display name
                            teacher_name = str(teacher_name.name)
                    if arg.isdigit() and count == 2:
                        level = int(arg)
                if not 'default' in args and str(level) in self.levels.get(str(teacher_id)):
                    self.set_level(str(teacher_id), str(student_id), str(level))
                    await ctx.send(
                        embed=discord.Embed(title="Set Level", description=student_name + " was set to level " + str(level) + " in " + teacher_name + "'s system",
                                            colour=899718))
                if 'default' in args and str(level) in self.levels.get(str(teacher_id)):
                    teacher_id = 'default'
                    self.set_level(str(teacher_id), str(student_id), str(level))
                    await ctx.send(
                        embed=discord.Embed(title="Set Level", description=student_name + " was set to level " + str(
                            level) + " in the default system",
                                            colour=899718))
                if not str(level) in self.levels.get(str(teacher_id)):
                    await ctx.send(
                        embed=discord.Embed(title="Levels", description="That level is not in the specified system!",
                                            colour=0xff0000))
                        
        if 'system' in args:
            display = ""
            for count, arg in enumerate(args):
                if re.match(r'<@![0123456789]*?>', arg) and count == 1:
                    if arg.strip('<>').replace('@!', '') in self.levels:

                        # Get user id
                        user = int(arg.strip('<>').replace('@!', ''))
                        # Get the member of the user id
                        name = bot.discord.Guild.get_member(ctx.guild, user)
                        # Get their nickname
                        name = str(name.nick)

                        # If the user has no nickname
                        if name == 'None':
                            # Get the user of the user id
                            name = bot.bot.get_user(user)
                            # Get their display name
                            name = str(name.name)
                        try:
                            level_number = args[2]
                        except IndexError:
                            level_number = "None"
                        if not level_number.isdigit():
                            level_list = []
                            for level in self.levels.get(arg.strip('<>').replace('@!', '')):
                                level_list.append(level)
                            level_list_string = ', '.join(level_list)
                            display = "**" + name + "\'s system contains these levels:**" + "\n" + level_list_string + "\n\n Run \"?lesson levels <teacher> <level_number>\" to see the details for a level."
                        else:
                            try:
                                display = "```Level " + level_number + " in " + name + "\'s system:```" + "\n"
                                display += self.levels.get(arg.strip('<>').replace('@!', '')).get(level_number)
                            except TypeError:
                                display = name + " has no level " + level_number + "!"
                        await ctx.send(
                            embed=discord.Embed(title="Levels", description=display,
                                                colour=899718))

                    else:
                        await ctx.send(
                            embed=discord.Embed(title="Levels", description="This user either is not a teacher "
                                                            "or has not set a custom level system!",
                                                colour=0xff0000))
                elif arg == 'default' and count == 1:
                    try:
                        level_number = args[2]
                    except IndexError:
                        level_number = "None"
                    if not level_number.isdigit():
                        level_list = []
                        for level in self.levels.get('default'):
                            level_list.append(level)
                        level_list_string = ', '.join(level_list)
                        display = "**The default system contains these levels:**" + "\n" + level_list_string + "\n\n Run \"?lesson levels default <level_number>\" to see the details for a level."
                    else:
                        try:
                            display = "```Level " + level_number + " in the default system:```" + "\n"
                            display += self.levels.get('default').get(level_number)
                        except TypeError:
                            display = "The default system has no level " + level_number + "!"
                    await ctx.send(
                        embed=discord.Embed(title="Levels", description=display,
                                            colour=899718))
        if 'levels' in args:
            display = ""
            for count, arg in enumerate(args):
                if re.match(r'<@![0123456789]*?>', arg) and count == 1:
                    if arg.strip('<>').replace('@!', '') in self.students:

                        # Get user id
                        user = int(arg.strip('<>').replace('@!', ''))
                        # Get the member of the user id
                        name = bot.discord.Guild.get_member(ctx.guild, user)
                        # Get their nickname
                        name = str(name.nick)

                        # If the user has no nickname
                        if name == 'None':
                            # Get the user of the user id
                            name = bot.bot.get_user(user)
                            # Get their display name
                            name = str(name.name)

                        display = name + "'s levels are:\n\n"

                        for system in self.students.get(arg.strip('<>').replace('@!', '')):
                            if system == "default":
                                display += "・Default System: " + str(self.students[arg.strip('<>').replace('@!', '')].get(system)) + "\n"
                            else:
                                # Get user id
                                user = int(system)
                                # Get the member of the user id
                                system_name = bot.discord.Guild.get_member(ctx.guild, user)
                                # Get their nickname
                                system_name = str(system_name.nick)

                                # If the user has no nickname
                                if system_name == 'None':
                                    # Get the user of the user id
                                    system_name = bot.bot.get_user(user)
                                    # Get their display name
                                    system_name = str(system_name.name)

                                display += "・" + system_name + "'s System: " + str(self.students[arg.strip('<>').replace('@!', '')].get(system)) + "\n"

                        await ctx.send(
                            embed=discord.Embed(title="Student Levels", description=display,
                                                colour=899718))

                    else:
                        await ctx.send(
                            embed=discord.Embed(title="Student Levels", description="This user has not been set to any levels",
                                                colour=0xff0000))
                        
        elif ctx.author.guild_permissions.manage_roles:
            if 'addrole' in args:
                for arg in args:
                    if re.search(r'<@&[0123456789]*?>', arg):
                        self.teacher_roles.append(int(arg.strip('<>').replace('@', '').replace('&', '')))
                        with open("cogs/lessons/teacher_roles.json", 'w', encoding="utf-8") as f:
                            json.dump(self.teacher_roles, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.content.startswith('?') and not message.content.startswith('?'):
            if self.listen_for_messages and message.author.id in self.message_listens:
                if self.message_listens[message.author.id] == message.channel.id:
                    if self.listen_type == 'add':
                        if self.confirm_adding_level:
                            if message.content.lower() == 'cancel':
                                self.description = ""
                                self.message_listens.pop(message.author.id, None)
                                self.listen_for_messages = False
                                self.confirm_adding_level = False
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Canceled adding new level!",
                                                        colour=899718))
                            elif message.content.lower() == 'redo':
                                self.description = ""
                                self.confirm_adding_level = False
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Please supply a description for this level. "
                                                                    "This should include any topics to discuss "
                                                                    "during lessons for this level, "
                                                                    "as well as any notes you have to members of this level"
                                                                    ".\n Say \"cancel\" to cancel adding the new level.",
                                                        colour=899718))
                            elif message.content == 'confirm':
                                self.add_level(message.author.id, self.level, self.description)
                                self.message_listens.pop(message.author.id, None)
                                self.listen_for_messages = False
                                self.confirm_adding_level = False
                                self.listen_type = ""
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Level " + str(self.level) +
                                                                    " was added with the description:\n\n" +
                                                                    self.description,
                                                        colour=899718))
                        else:
                            if message.content.lower() == 'cancel':
                                self.message_listens.pop(message.author.id, None)
                                self.listen_for_messages = False
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Canceled adding new level!",
                                                        colour=899718))
                            else:
                                self.description = message.content
                                self.confirm_adding_level = True
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Is this correct for level " +
                                                                                       str(self.level) +
                                                                            "?:\n\n" + self.description +
                                                                            "\n\n Say \"confirm\" to confirm. "
                                                                            "Say \"redo\" to change the description. "
                                                                            "Say \"cancel\" to cancel adding the new level."
                                                        , colour=899718))

                    elif self.listen_type == 'nudge':
                        if self.confirm_adding_level:
                            if message.content.lower() == 'cancel':
                                self.description = ""
                                self.message_listens.pop(message.author.id, None)
                                self.listen_for_messages = False
                                self.confirm_adding_level = False
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Canceled adding new level!",
                                                        colour=899718))
                            elif message.content.lower() == 'redo':
                                self.description = ""
                                self.confirm_adding_level = False
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Please supply a description for this level. "
                                                                    "This should include any topics to discuss "
                                                                    "during lessons for this level, "
                                                                    "as well as any notes you have to members of this level"
                                                                    ".\n Say \"cancel\" to cancel adding the new level.",
                                                        colour=899718))
                            elif message.content == 'confirm':
                                self.nudge_level(message.author.id, self.level, self.description)
                                self.message_listens.pop(message.author.id, None)
                                self.listen_for_messages = False
                                self.confirm_adding_level = False
                                self.listen_type = ""
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Level " + str(self.level) +
                                                                    " was added with the description:\n\n" +
                                                                    self.description,
                                                        colour=899718))
                        else:
                            if message.content.lower() == 'cancel':
                                self.message_listens.pop(message.author.id, None)
                                self.listen_for_messages = False
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Canceled adding new level!",
                                                        colour=899718))
                            else:
                                self.description = message.content
                                self.confirm_adding_level = True
                                await message.channel.send(
                                    embed=discord.Embed(title="New Level", description="Is this correct for level " +
                                                                                       str(self.level) +
                                                                            "?:\n\n" + self.description +
                                                                            "\n\n Say \"confirm\" to confirm. "
                                                                            "Say \"redo\" to change the description. "
                                                                            "Say \"cancel\" to cancel adding the new level."
                                                        , colour=899718))

    def add_level(self, teacher_id, level_number, level_description):
        if not str(teacher_id) in self.levels:
            self.levels[str(teacher_id)] = {}
        self.levels[str(teacher_id)][str(level_number)] = level_description
        with open("cogs/lessons/levels.json", 'w', encoding="utf-8") as f:
            json.dump(self.levels, f, indent=4)

    def nudge_level(self, teacher_id, level_number, level_description):
        if not str(teacher_id) in self.levels:
            self.levels[str(teacher_id)] = {}
        self.levels[str(teacher_id)][str(level_number)] = level_description

        levels_copy = self.levels[str(teacher_id)].copy()
        for level in self.levels[str(teacher_id)].copy():
            if int(level) > int(level_number):
                levels_copy[str(int(level) + 1)] = self.levels[str(teacher_id)].copy().pop(level)
        self.levels[str(teacher_id)] = levels_copy

        with open("cogs/lessons/levels.json", 'w', encoding="utf-8") as f:
            json.dump(self.levels, f, indent=4)

    def set_level(self, teacher_id, student_id, level):
        if not student_id in self.students:
            self.students[student_id] = {}
        self.students[student_id][teacher_id] = level
        with open("cogs/lessons/students.json", 'w', encoding="utf-8") as f:
            json.dump(self.students, f, indent=4)


# Set up cog
def setup(bot):
    # Add the cog
    bot.add_cog(Lessons(bot))
    # Print some info
    print('Added new Cog: ' + str(Lessons))
