# -*- coding: utf-8 -*
"""
This file stores the main DShell cog that's added to the bot.

LICENSE - [MIT](https://opensource.org/licenses/MIT)

Copyright 2021-present ImNimboss (https://github.com/ImNimboss)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""
from discord.ext import commands
import discord
from os import getcwd
from os.path import dirname, isdir
from pathlib import Path
from asyncio import TimeoutError, run
import dshell.jskshell as jskshell
from datetime import datetime as dt
from typing import Optional
from io import StringIO
from json import dumps

class DShell(commands.Cog):
    """
    The cog that holds the dshell command and the main functioning of the shell.
    """
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.bot.dshell_config = {
            'show_cd_command_output': True,
            'give_clear_command_confirmation_warning': True,
            'shell_channels': [],
            'shell_in_dms': False
        }
        if bot.owner_id:
            self.bot.dshell_config['shell_whitelisted_users'] = [bot.owner_id]
            self._owners = [bot.owner_id]
        elif bot.owner_ids:
            self.bot.dshell_config['shell_whitelisted_users'] = bot.owner_ids
            self._owners = bot.owner_ids
        else:
            self.bot.dshell_config['shell_whitelisted_users'] = []
            self._owners = []
        self._on_ready_flag: bool = False
        self._og_working_directory: str = getcwd()
        self._cwd: str = self._og_working_directory # this changes with cd commands, of course
        self._home_directory: str = str(Path.home())
        self._load_time: int = int(dt.utcnow().timestamp())
        self._bool_flags_true: list = ['enable', 'true', 'yes', 'y']
        self._bool_flags_false: list = ['disable', 'false', 'no', 'n']

    @commands.group(invoke_without_command = True, aliases = ['dsh'])
    @commands.is_owner()
    async def dshell(self, ctx: commands.Context) -> None:
        """
        The root dshell command. Discord shell or dshell is a customizable Python package that allows you to have a shell in a Discord channel.
        """
        from dshell import __version__ as version

        if ctx.prefix == self.bot.user.mention:
            prefix = f'@{self.bot.name} '
        else:
            prefix = ctx.prefix
        await ctx.send(
            embed = discord.Embed(
                description = f"""
Discord shell or dshell, a Python discord.py library that allows for shell access in Discord.
This library is also compatible with discord.py forks that use the `discord` import. It uses standard message commands as slash commands were never implemented in discord.py.
dshell version `v{version}`, the Shell cog was loaded <t:{self._load_time}:R> (<t:{self._load_time}:F>).

Subcommands:
`{prefix}{ctx.invoked_with} cdcmdoutput/cdout enable/true/yes/y/disable/false/no/n` - Changes the `show_cd_command_output` config property. Enable or disable the output of the `cd` or change directory command in the shell.

`{prefix}{ctx.invoked_with} clearcommandconfirmation/ccc enable/true/yes/y/disable/false/no/n` - Changes the `give_clear_command_confirmation_warning` config property. Enable or disable the confirmation message of the `clear` command in the shell.

`{prefix}{ctx.invoked_with} dmshell/dmsh enable/true/yes/y/disable/false/no/n` - Changes the `shell_in_dms` config property. Enable or disable the usage of the shell in DMs.

`{prefix}{ctx.invoked_with} addshellchannel/addchannel/ach [text channel]` - Changes the `shell_channels` config property. Adds a channel to the list of channels that the shell can be used in.

`{prefix}{ctx.invoked_with} removeshellchannel/removechannel/rch [text channel]` - Changes the `shell_channels` config property. Removes a channel from the list of channels that the shell can be used in.

`{prefix}{ctx.invoked_with} shellchannels/sc` - Shows a list of all the channels that the shell can be used in.

`{prefix}{ctx.invoked_with} showshellconfig/ssc` - Shows your DShell cog's configuration dict.

`{prefix}{ctx.invoked_with} shellwhitelist/shw [user]` - Changes the `shell_whitelisted_users` config property. Whitelist someone to the shell, allowing them to use the shell. This command should be used with caution as giving someone shell access is the equivalent of giving them full access to whatever device the bot is running on. Bot owners are by default whitelisted and this cannot be changed.

`{prefix}{ctx.invoked_with} shellunwhitelist/shuw [user]` - Changes the `shell_whitelisted_users` config property. Unwhitelist someone to the shell. The user to unwhitelist cannot be a bot owner.
                    """.strip(),
                color = ctx.author.color
            )
        )
    
    @dshell.command(name = 'cdcmdoutput', aliases = ['cdout'])
    @commands.is_owner()
    async def cd_cmd_output(self, ctx: commands.Context, argument: str) -> Optional[discord.Message]:
        """
        Changes the `show_cd_command_output` config property. Enable or disable the output of the `cd` or change directory command in the shell.
        """
        if argument.lower() in self._bool_flags_true:
            if self.bot.dshell_config['show_cd_command_output']:
                return await ctx.send('CD command output is already enabled.')
            self.bot.dshell_config['show_cd_command_output'] = True
            await ctx.message.add_reaction('👍')
        elif argument.lower() in self._bool_flags_false:
            if not self.bot.dshell_config['show_cd_command_output']:
                return await ctx.send('CD command output is already disabled.')
            self.bot.dshell_config['show_cd_command_output'] = False
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send('Invalid argument. Your argument must be one of `enable`, `true`, `yes`, `y`, `disable`, `false`, `no` or `n`.')

    @dshell.command(name = 'clearcommandconfirmation', aliases = ['ccc'])
    @commands.is_owner()
    async def clear_command_confirmation(self, ctx: commands.Context, argument: str) -> Optional[discord.Message]:
        """
        Changes the `give_clear_command_confirmation_warning` config property. Enable or disable the confirmation message of the `clear` command in the shell.
        """
        if argument.lower() in self._bool_flags_true:
            if self.bot.dshell_config['give_clear_command_confirmation_warning']:
                return await ctx.send('The clear command confirmation warning is already enabled.')
            self.bot.dshell_config['give_clear_command_confirmation_warning'] = True
            await ctx.message.add_reaction('👍')
        elif argument.lower() in self._bool_flags_false:
            if not self.bot.dshell_config['give_clear_command_confirmation_warning']:
                return await ctx.send('The clear command confirmation warning is already disabled.')
            self.bot.dshell_config['give_clear_command_confirmation_warning'] = False
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send('Invalid argument. Your argument must be one of `enable`, `true`, `yes`, `y`, `disable`, `false`, `no` or `n`.')

    @dshell.command(name = 'dmshell', aliases = ['dmsh'])
    @commands.is_owner()
    async def dm_shell(self, ctx: commands.Context, argument: str) -> Optional[discord.Message]:
        """
        Changes the `shell_in_dms` config property. Enable or disable the usage of the shell in DMs.
        """
        if argument.lower() in self._bool_flags_true:
            if self.bot.dshell_config['shell_in_dms']:
                return await ctx.send('Shell is already enabled in DMs.')
            self.bot.dshell_config['shell_in_dms'] = True
            await ctx.message.add_reaction('👍')
        elif argument.lower() in self._bool_flags_false:
            if not self.bot.dshell_config['shell_in_dms']:
                return await ctx.send('Shell is already disabled in DMs.')
            self.bot.dshell_config['shell_in_dms'] = False
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send('Invalid argument. Your argument must be one of `enable`, `true`, `yes`, `y`, `disable`, `false`, `no` or `n`.')

    @dshell.command(name = 'addshellchannel', aliases = ['addchannel', 'ach'])
    @commands.is_owner()
    async def add_shell_channel(self, ctx: commands.Context, channel: discord.TextChannel) -> Optional[discord.Message]:
        """
        Changes the `shell_channels` config property. Adds a channel to the list of channels that the shell can be used in.
        """
        if channel.id in self.bot.dshell_config['shell_channels']:
            return await ctx.send('This channel is already a shell channel.')
        self.bot.dshell_config['shell_channels'].append(channel.id)
        await ctx.message.add_reaction('👍')

    @dshell.command(name = 'removeshellchannel', aliases = ['removechannel', 'rch'])
    @commands.is_owner()
    async def remove_shell_channel(self, ctx: commands.Context, channel: discord.TextChannel) -> Optional[discord.Message]:
        """
        Changes the `shell_channels` config property. Removes a channel from the list of channels that the shell can be used in.
        """
        if not channel.id in self.bot.dshell_config['shell_channels']:
            return await ctx.send('This channel is not a shell channel.')
        self.bot.dshell_config['shell_channels'].remove(channel.id)
        await ctx.message.add_reaction('👍')

    @dshell.command(name = 'shellchannels', aliases = ['sc'])
    @commands.is_owner()
    async def shell_channels(self, ctx: commands.Context) -> Optional[discord.Message]:
        """
        Shows a list of all the channels that the shell can be used in.
        """
        if len(self.bot.dshell_config['shell_channels']) == 0:
            return await ctx.send('There are no shell channels, add one using the `dshell/dsh addshellchannel` subcommand.')
        channels = [f'<#{id_}>' for id_ in self.bot.dshell_config['shell_channels']]
        chunks = []
        for i in range(0, len(channels), 25):
            chunks.append(channels[i : i + 25])
        for chunk in chunks:
            await ctx.send(', '.join(chunk))

    @dshell.command(name = 'showshellconfig', aliases = ['ssc'])
    @commands.is_owner()
    async def show_shell_config(self, ctx: commands.Context) -> None:
        """
        Shows your DShell cog's configuration dict.
        """
        file = discord.File(
            StringIO(dumps(self.bot.dshell_config, indent = 4)),
            'configdict.json'
        )
        try:
            await ctx.author.send(
                file = discord.File(
                    StringIO(dumps(self.bot.dshell_config, indent = 4)),
                    'configdict.json'
                )
            )
        except: # bare except, i know, no one get angry but i need to suppress any error
            message = await ctx.send('I couldn\'t DM you the file. Would you like me to send it in this channel?')
            await message.add_reaction('✅')
            await message.add_reaction('❌')
            def check(reaction, user):
                return str(reaction.emoji) in ['✅', '❌'] and user == ctx.author and reaction.message.id == message.id and reaction.message.channel.id == ctx.channel.id
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check = check, timeout = 10)
                if str(reaction.emoji) == '✅':
                    await ctx.send(
                        file = discord.File(
                            StringIO(dumps(self.bot.dshell_config, indent = 4)),
                            'configdict.json'
                        )
                    )
                else:
                    await ctx.send('Aborted.')
            except TimeoutError:
                await ctx.send('Aborted.')
        else:
            await ctx.message.add_reaction('👍')

    @dshell.command(name = 'shellwhitelist', aliases = ['shw'])
    @commands.is_owner()
    async def shell_whitelist(self, ctx: commands.Context, user: discord.User) -> Optional[discord.Message]:
        """
        Changes the `shell_whitelisted_users` config property. Whitelist someone to the shell, allowing them to use the shell. This command should be used with caution as giving someone shell access is the equivalent of giving them full access to whatever device the bot is running on. Bot owners are by default whitelisted and this cannot be changed.
        """
        if user.id in self.bot.dshell_config['shell_whitelisted_users']:
            return await ctx.send('This person is already whitelisted.')
        message = await ctx.send(f'{ctx.author.mention}, are you sure you want to whitelist this person? This will give them full access to the computer/system this bot is running on. Press :+1: to confirm, you have 10 seconds.', allowed_mentions = discord.AllowedMentions(users = True))
        await message.add_reaction('👍')
        def check(reaction, user_):
            return str(reaction.emoji == '👍') and user_ == ctx.author and reaction.message.id == message.id and reaction.message.channel.id == ctx.channel.id
        try:
            await self.bot.wait_for('reaction_add', check = check, timeout = 10)
            self.bot.dshell_config['shell_whitelisted_users'].append(user.id)
            await ctx.send(f'Whitelisted {user.mention}.', allowed_mentions = discord.AllowedMentions(users = True))
        except TimeoutError:
            await ctx.send('Aborted.')

    @dshell.command(name = 'shellunwhitelist', aliases = ['shuw'])
    @commands.is_owner()
    async def shell_unwhitelist(self, ctx: commands.Context, user: discord.User) -> Optional[discord.Message]:
        """
        Changes the `shell_whitelisted_users` config property. Unwhitelist someone to the shell. The user to unwhitelist cannot be a bot owner.
        """
        if not user.id in self.bot.dshell_config['shell_whitelisted_users']:
            return await ctx.send('This person is not whitelisted.')
        if user.id in self._owners:
            return await ctx.send('The owner of this bot cannot be unwhitelisted from the shell.')
        self.bot.dshell_config['shell_whitelisted_users'].remove(user.id)
        await ctx.send(f'Unwhitelisted {user.mention}.', allowed_mentions = discord.AllowedMentions(users = True))

    async def _do_cd_command(self, msg: discord.Message) -> bool:
        if msg.content.strip() == 'cd' or msg.content == 'cd ~':
            if self.bot.dshell_config['show_cd_command_output'] is True:
                await msg.channel.send(
                    f'```sh\n$ {msg.content}\n\n' \
                    f'Changing process directory to home directory, {self._home_directory}.\n' \
                    f'Current process directory: {self._cwd}.\n' \
                    f'Original process directory: {self._og_working_directory}.\n\n[status] Return code 0\n```'
                )
            await msg.add_reaction('✅')
            self._cwd = self._home_directory
            return False
        
        if msg.content == 'cd ..':
            directory = dirname(self._cwd)
            if self.bot.dshell_config['show_cd_command_output'] is True:
                await msg.channel.send(
                    f'```sh\n$ {msg.content}\n\n' \
                    f'Changing process directory to {directory}.\n' \
                    f'Current process directory: {self._cwd}.\n' \
                    f'Original process directory: {self._og_working_directory}.\n\n[status] Return code 0\n```'
                )
            await msg.add_reaction('✅')
            self._cwd = directory
            return False
        
        if msg.content.startswith('cd '):
            directory = msg.content[3:]
            if directory.startswith('"') and directory.endswith('"'):
                directory = directory[1:][:-1]
            if not directory.startswith('/'): # implying that a relative path has been entered
                directory = self._cwd + '/' + directory
            if not isdir(directory):
                await msg.channel.send(
                    f'```sh\n$ {msg.content}\n\n' \
                    f'[stderr] cd: {directory}: Not a valid directory.\n\n[status] Return code 1\n```'
                )
                await msg.add_reaction('✅')
                return False
            if self.bot.dshell_config['show_cd_command_output'] is True:
                await msg.channel.send(
                    f'```sh\n$ {msg.content}\n\n' \
                    f'Changing process directory to {directory}.\n' \
                    f'Current process directory: {self._cwd}.\n' \
                    f'Original process directory: {self._og_working_directory}.\n\n[status] Return code 0\n```'
                )
            await msg.add_reaction('✅')
            self._cwd = directory
            return False
        
        return True

    async def _clear_command(self, msg: discord.Message) -> None:
        if self.bot.dshell_config['give_clear_command_confirmation_warning']:
            message = await msg.channel.send(f'{msg.author.mention}, clearing in 5 seconds. Press :x: to abort the process. This will delete this shell channel and create an empty copy.', allowed_mentions = discord.AllowedMentions(users = True))
            await message.add_reaction('❌')
            def check(reaction: discord.Reaction, user):
                return str(reaction.emoji == '❌') and user == msg.author and reaction.message.id == message.id and reaction.message.channel.id == message.channel.id
            try:
                await self.bot.wait_for('reaction_add', check = check, timeout = 5)
                await msg.channel.send('Aborted.')
            except TimeoutError:
                new_channel = await msg.channel.clone()
                await msg.channel.delete()
                del self.bot.dshell_config['shell_channels'][self.bot.dshell_config['shell_channels'].index(msg.channel.id)]
                self.bot.dshell_config['shell_channels'].append(new_channel.id)
                await new_channel.send(f'{msg.author.mention}, the new shell has been made. This message will be deleted after 10 seconds.', allowed_mentions = discord.AllowedMentions(users = True), delete_after = 10)
        else:
            new_channel = await msg.channel.clone()
            await msg.channel.delete()
            del self.bot.dshell_config['shell_channels'][self.bot.dshell_config['shell_channels'].index(msg.channel.id)]
            self.bot.dshell_config['shell_channels'].append(new_channel.id)
            await new_channel.send(f'{msg.author.mention}, the new shell has been made. This message will be deleted after 10 seconds.', allowed_mentions = discord.AllowedMentions(users = True), delete_after = 10)

    @commands.Cog.listener(name = 'on_message')
    async def main_shell(self, msg: discord.Message) -> Optional[discord.Message]:
        if (
            msg.channel.id in self.bot.dshell_config['shell_channels'] or (self.bot.dshell_config['shell_in_dms'] and not msg.guild)
        ) and (
            not msg.author.id == self.bot.user.id
        ) and (
            msg.content
        ) and (
            msg.author.id in self.bot.dshell_config['shell_whitelisted_users']
        ) and (
            not msg.content.startswith('#')
        ):
            if msg.content.startswith('`') and msg.content.endswith('`'):
                msg.content = msg.content[1:][:-1]
            if msg.content == '[DSHELL EXEC FILE]' and msg.attachments:
                msg.content = (await msg.attachments[0].read()).decode('utf-8')
            if msg.content == 'clear':
                return await self._clear_command(msg)
            if await self._do_cd_command(msg):
                ctx = await self.bot.get_context(msg)
                return await jskshell.jsk_shell(ctx, argument = msg, cwd = self._cwd)

    @commands.Cog.listener(name = 'on_ready')
    async def initialize_bot_owners(self):
        if not self._on_ready_flag and not self._owners:
            owner = (await self.bot.application_info()).owner.id
            self.bot.dshell_config['shell_whitelisted_users'] = [owner]
            self._owners = [owner]
            self._on_ready_flag = True

def setup(bot):
    bot.add_cog(DShell(bot))