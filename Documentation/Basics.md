# Basics

## Loading the extension

You need to have an instance of [discord.ext.commands.Bot](https://discordpy.readthedocs.io/)

Before your bot.run() statement, put this line in an async function:
```python
await bot.load_extension('dshell')
```
Or import asyncio and use:
```python
asyncio.run(load_extension('dshell'))
```
This will load the main DShell cog into your bot.

## Configuring the bot

Loading the extension will also set an attribute to your bot named `dshell_config`. You can access this module's configuration via `bot.dshell_config` now.

This attribute is a dictionary, and by default it looks like this:
```python
{
    'show_cd_command_output': True,
    'give_clear_command_confirmation_warning': True,
    'shell_channels': [],
    'shell_in_dms': False,
    'shell_whitelisted_users': [r"A list of all the bot's owners' IDs"]
}
```

### What these values mean:

#### `give_clear_command_confirmation_warning`:

This is a boolean property. When you run the `clear` command in your shell channel and this setting is set to `True`, it asks you to confirm whether you really want to delete the channel and make another shell channel copy.

When it is set to `False`, it skips the confirmation altogether and simply deletes the current shell channel and makes another copy it.

By default this is set to `True`.

#### `shell_channels`:

This is a list and simply contains all the channels that the shell can be run in.

By default, this is an empty list.

#### `shell_in_dms`:

This is a boolean property. If it is set to `True` then the shell will work in Direct Messages with the bot. It essentially makes your DMs a shell channel too.

If it is set to `False` the bot will not process any Direct Messages from you as shell commands.

By default this is set to `False`.

#### `show_cd_command_output`:

If it is set to `True`, when you run `cd` in the shell, shows some output details like your current process directory's path, your home directory's path and your new process directory's path.

If it is set to `False` then it won't do that.

By default this is set to `True`.

#### `shell_whitelisted_users`:

This is a list and it contains all the people with the permissions to use the shell. By default this contains all the owners of the bot.

**WARNING: change this list with caution as granting someone access to your bot's shell could literally give them access to do whatever they want with whatever computer/system your bot is running on. They could get every private file and even destroy your bot's computer/system. This package wields a LOT of power. Make sure you only give this to people you fully trust.**

## How to change the default configuration

Since `bot.dshell_config` is a dictionary, you can change its values just like you would with any other normal dictionary.

Eg. if you wanted to enable the shell to work in DMs you would type
```python
bot.dshell_config["shell_in_dms"] = True
```
Easy as that.

If you wanted to add some shell channels to use the shell in (which is something you probably will do) then you would type
```python
bot.dshell_config["shell_channels"].append(930143692545744896)
# OR
bot.dshell_config["shell_channels"] = [930143692545744896, 849233992586362979]
```
etc...you get the point.

# If you're still confused, [check out some examples in Examples.md](https://github.com/ImNimboss/dshell/blob/main/Documentation/Examples.md).