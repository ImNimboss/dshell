# Examples

## A basic bot

```python
from discord.ext import commands
import discord
from asyncio import run

bot = commands.Bot(
    command_prefix = 'e!',
    intents = discord.Intents.all()
)

@bot.command()
async def hi(ctx):
    await ctx.send(f'Hello, {ctx.author}!')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms.')

# this is where dshell stuff starts 
run(bot.load_extension('dshell'))
bot.dshell_config['shell_channels'] = [930143692545744896, 808404030380441600] # put your own channel IDs here. all the channels that you've put will become shell channels
bot.dshell_config['shell_in_dms'] = True
bot.dshell_config['give_clear_command_confirmation_warning'] = False

# after you're done with whatever configuration you had to do, run the bot
bot.run(TOKEN_GOES_HERE)
```

## A bot specifically dedicated to DShell, whose only purpose is to serve as a shell bot

```python
from discord.ext import commands
from discord import Intents
from asyncio import run

bot = commands.Bot(
    command_prefix = 's!',
    intents = Intents.all()
)

run(bot.load_extension('dshell'))
bot.dshell_config['shell_channels'] = [930143692545744896, 808404030380441600] # again, use your own channel IDs
bot.dshell_config['shell_in_dms'] = True

bot.run(TOKEN_GOES_HERE)
```

## A typical public multipurpose bot with cogs

```python
import discord
import asyncio
from discord.ext import commands, tasks
from os import listdir
from bot_config import BotHelpCommand, get_prefix, TOKEN

bot = commands.Bot(
    command_prefix = get_prefix,
    help_command = BotHelpCommand(),
    description = 'A multipurpose bot that can do anything your heart desires!',
    intents = discord.Intents.all(),
    allowed_mentions = discord.AllowedMentions(roles = False, everyone = False),
    case_insensitive = True,
    strip_after_prefix = True,
    owner_ids = [123123, 6969420]
)

@tasks.loop()
async def change_statuses():
    statuses = [
        f'with {len(bot.guilds)} servers | s!help',
        f'with {len(bot.users)} users | s!help',
        'with everything that you can ever want! | s!help'
    ]
    for status in statuses:
        await bot.change_presence(activity = discord.Game(name = status))
        await asyncio.sleep(60)

@change_statuses
async def before_change_statuses():
    await bot.wait_until_ready()

async def load_extensions:
    for cog in listdir('cogs'):
        await bot.load_extension(f'cogs.{cog[:-3]}') #:-3 to remove the .py extension
    await bot.load_extension('dshell')
asyncio.run(load_extensions())
bot.dshell_config['shell_channels'] = [930143692545744896, 808404030380441600]
bot.run(TOKEN)
```

# These are only examples for you to get a basic idea of how to implement dshell into your bot. This is not a hard set of rules and you can change this according to your needs.