#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

from typing import Final
import os
import aiosqlite
from aiosqlite import Connection
import aiohttp
import discord
from discord import Message, Interaction
from discord.ext import commands, tasks
from dotenv import load_dotenv

from db import run_db_query
from process_league import process_league, illegitimize_league
from process_role import process_role
from account_linking import link_account, unlink_account
from data_extraction import get_character_tables_from_username
from utils import format_pretty_ascii_table

load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
DB_PASS: Final[str] = os.getenv("DB_PASSWORD")

GGG_ACCESS_TOKEN: Final[str] = os.getenv("GGG_ACCESS_TOKEN")
GGG_CLIENT_ID: Final[str] = os.getenv("GGG_CLIENT_ID")
GGG_AUTHOR_CONTACT: Final[str] = os.getenv("GGG_AUTHOR_CONTACT")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
dbc: Connection
session: aiohttp.ClientSession

bot_spam_channel_id: int = 1221773773339099228
current_private_league_name = "Mercenaries of Conflux (PL70922)"
posting_interval_seconds: int = 3600*2 # 2 hours


# ------------- Admin Commands -------------


@bot.tree.command(name="admin-start-auto-update", description="Start the league auto update task")
async def start_auto_update(interaction: Interaction):
    # Start the auto-processing of the active league
    await interaction.response.send_message('Task loop started.')
    auto_process_league.start()


@bot.tree.command(name="admin-stop-auto-update", description="Stop the league auto update task")
async def stop_auto_update(interaction: Interaction):
    # Stop the auto-processing of the active league
    await interaction.response.send_message('Task loop stopped.')
    auto_process_league.stop()


@bot.tree.command(name="admin-illegitimize-league", description="Make a league not count towards vet roles")
async def admin_illegitimize_league(interaction: Interaction, league_name: str):
    await interaction.response.send_message(f'Making {league_name} ineligible for vet roles...')
    response: str = await illegitimize_league(dbc, league_name)
    await bot.get_channel(interaction.channel_id).send(response)


@bot.tree.command(name="admin-process-league", description="Fetch league data from GGG API and merge it to the database")
async def admin_process_league(interaction: Interaction, league_name: str):
    await interaction.response.send_message(f'Processing league {league_name}, please standby...')
    response = await process_league(league_name, dbc, session)
    await bot.get_channel(interaction.channel_id).send(response)


@bot.tree.command(name='admin-test-code', description='Code playground')
async def admin_test_code(interaction: Interaction):
    await interaction.response.send_message('Testing code')


# ------------- User Commands -------------


@bot.tree.command(name='character-lookup', description='Provide a PoE account name to see what characters are tied to it')
async def user_character_lookup(interaction: Interaction, poe_acc_name: str):
    await interaction.response.send_message(f'Fetching characters from {poe_acc_name}...')
    response: list | str = await get_character_tables_from_username(dbc, poe_acc_name)

    if type(response) == str:
        await bot.get_channel(interaction.channel_id).send(response)
    else:
        tables = response
        for table in tables:
            header = ["Character", "Class", "Level", "League"]
            formatted_table = format_pretty_ascii_table(table, header)
            await bot.get_channel(interaction.channel_id).send(formatted_table)


@bot.tree.command(name="link-account", description="Establish a link between your Discord and PoE account")
async def user_link_account(interaction: Interaction, poe_acc_name: str):
    await interaction.response.send_message(f'Attempting to link you to {poe_acc_name}...')
    discord_user: discord.User = interaction.user
    response: str = await link_account(dbc, discord_user, poe_acc_name)
    await bot.get_channel(interaction.channel_id).send(response)


@bot.tree.command(name='request-role', description='Get your veteran roles with this!')
async def user_request_role(interaction: Interaction):
    await interaction.response.send_message("Updating your veteran role...")
    discord_user: discord.User = interaction.user
    response: str = await process_role(dbc, discord_user)
    await bot.get_channel(interaction.channel_id).send(response)


@bot.tree.command(name="unlink-account", description="WARNING: Veteran roles will be purged upon unlinking!")
async def user_unlink_account(interaction: Interaction):
    await interaction.response.send_message('Attempting to sever the link between your Discord and PoE accounts...')
    discord_user: discord.User = interaction.user
    response: str = await unlink_account(dbc, discord_user)
    await bot.get_channel(interaction.channel_id).send(response)


# -----------------------------------------


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

    # instantiate a client session for HTTP requests from the GGG API
    header = {
        'Authorization': f'Bearer {GGG_ACCESS_TOKEN}',
        'User-Agent': f'OAuth {GGG_CLIENT_ID}/1.0.0 (contact: {GGG_AUTHOR_CONTACT})'
    }

    global session
    session = aiohttp.ClientSession(headers=header)


@bot.event
async def on_message(message: Message) -> None:
    # The bot should not react to the message itself posts or there will be an infinite message loop
    if message.author == bot.user:
        return


@tasks.loop(seconds=posting_interval_seconds)
async def auto_process_league():
    response = await process_league(current_private_league_name, dbc, session)
    await bot.get_channel(bot_spam_channel_id).send(content=response, silent=True, delete_after=posting_interval_seconds)


def main() -> None:
    bot.run(token=DISCORD_TOKEN)


if __name__ == '__main__':
    main()
