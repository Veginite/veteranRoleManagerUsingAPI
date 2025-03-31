#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from typing import Final
import os
import aiosqlite
from aiosqlite import Connection
import discord
from discord import Message, Interaction
from discord.ext import commands
from dotenv import load_dotenv

from process_league import process_league
from db import run_db_query

load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
DB_PASS: Final[str] = os.getenv("DB_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
dbc: Connection


# ------------- Commands -------------

@bot.tree.command(name="addleague", description="Fetch a league from GGG API and add it to the database")
async def add_league(interaction: Interaction, league_name: str):

    await process_league(league_name, dbc)

    await interaction.response.send_message(league_name)


@bot.tree.command(name="dbquery", description='You can run any database query with this')
async def db_query(interaction: Interaction, query: str):
    if await run_db_query(dbc, query):
        await interaction.response.send_message('Query executed')
    else:
        await interaction.response.send_message('Query failed to execute')


@bot.tree.command(name='requestrank', description='Get your veteran roles with this!')
async def request_rank(interaction: Interaction):
    await interaction.response.send_message(f'Added rank to {interaction.user.mention}')


@bot.tree.command(name='testcode', description='Code playground')
async def test_code(interaction: Interaction):
    return


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
    bot.run(token=DISCORD_TOKEN)


if __name__ == '__main__':
    main()
