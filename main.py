from typing import Final
from dotenv import load_dotenv
import discord, os, asyncio, aiosqllite
from discord import Intents, Message
from discord.ext import commands
from dbc import create_server_connection

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
DBPASSWORD: Final[str] = os.getenv("DBPASSWORD")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

#------------- Commands -------------

@bot.tree.command(name="addleague", description="Fetch a league from GGG API and add it to the database")
async def addleague(interaction: discord.Interaction, league_name: str):
    await interaction.response.send_message(league_name)


@bot.tree.command(name='requestrank', description='Get your veteran roles with this!')
async def requestrank(interaction: discord.Interaction):
    await interaction.response.send_message(f'Added rank to {interaction.user.mention}')

#------------------------------------

@bot.event
async def on_ready() -> None:
    print(f'{bot.user} is now running!')

    #sync the bot's command tree
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command{'' if len(synced) == 1 else 's'}")
    except Exception as e:
        print(e)

    #attempt to establish database connection
    try:
        bot.db = await aiosqlite.connect('privateleaguedata.db')
        print('Database connection established!')
    except Exception as e:
        print(e)

@bot.event
async def on_message(message: Message) -> None:
    # Prevents a potential infinite message loop
    if message.author == bot.user:
        return

    else:
        print('working')


def main() -> None:
    bot.run(token=TOKEN)


if __name__ == '__main__':
    main()