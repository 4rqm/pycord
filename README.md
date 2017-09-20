<div align="center">
        <p> <img src="https://i.imgur.com/SbFk45Y.png"/> </p>
        <p><i><b>A discord api wrapper in progress :)</b></i></p>
	<p> 
		<a href="https://discord.gg/pmQSbAd"><img src="https://discordapp.com/api/guilds/345787308282478592/embed.png" alt="" /></a>
		<img src="https://img.shields.io/badge/python-3.6-brightgreen.svg" alt="python 3.6" /></a>
	</p>
</div> 

## About
pycord is a discord api wrapper currently in development. Its easy to use, asynchronous and object oriented. It has a commands framework currently under development that makes it easy to write discord bots.

## Installation
The library isn't done yet so its not registered on the pypi. However if you want to test it out, just clone this repository!

## Examples

```py
import pycord

client = pycord.Client()

@client.on('ready')
async def on_ready():
    print(f'Logged in as: {client.user}')
    print(f'User ID: {client.user.id}')
    print(f'Is Bot: {client.user.bot}')
    print(f'With {len(client.guilds)} guilds')

@client.on('message')
async def ping_command(message):
    if message.content.startswith('py.ping'):
        await message.reply('Pong!')

client.login('token')
```

### Commands examples

```py
import pycord

client = pycord.Client()

@client.on('ready')
async def ready():
   print('Bot online!')

@client.command()
async def ping(message): # the message that called the command
    message.reply('Pong!')

@client.command() 
async def add(message, *numbers: int): # different argument examples
    await message.reply(sum(numbers))

# type hint converters are supported, can either be a function or a class with a convert() method

@client.command()
async def kick(msg, member, *, reason): 
    await msg.reply(f'**Kicked:** {member}\n**Reason:** {reason}')
    ...

client.login('token')
```
We will be replacing `message` with seperate context class later on.
