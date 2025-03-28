from typing import Final
import aiosqlite
from aiosqlite import Connection
import discord
import os
from discord import Message, Interaction
from discord.ext import commands
from dotenv import load_dotenv

from db import run_db_query

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
DBPASSWORD: Final[str] = os.getenv("DBPASSWORD")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
dbc: Connection


# ------------- Commands -------------

@bot.tree.command(name="addleague", description="Fetch a league from GGG API and add it to the database")
async def addleague(interaction: Interaction, league_name: str):
    await interaction.response.send_message(league_name)


@bot.tree.command(name="dbquery", description='You can run any database query with this')
async def dbquery(interaction: Interaction, query: str):
    if await run_db_query(dbc, query):
        await interaction.response.send_message('Query executed')
    else:
        await interaction.response.send_message('Query failed to execute')


@bot.tree.command(name='requestrank', description='Get your veteran roles with this!')
async def requestrank(interaction: Interaction):
    await interaction.response.send_message(f'Added rank to {interaction.user.mention}')


# ------------------------------------

@bot.event
async def on_ready() -> None:
    print(f'{bot.user} is now running!')

    # sync the bot command tree
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command{'' if len(synced) == 1 else 's'}")
    except Exception as e:
        print(e)

    # attempt to establish database connection
    try:
        global dbc
        dbc = await aiosqlite.connect('PrivateLeagueData.db')
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
