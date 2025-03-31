#########################################
# Author: Veginite
# Module status: UNFINISHED
#########################################

from typing import Final
import os
from dotenv import load_dotenv
import aiosqlite
from aiosqlite import Connection
import aiohttp
from aiohttp import FormData

from db import run_db_query

load_dotenv()
GGG_ACCESS_TOKEN: Final[str] = os.getenv("ACCESS_TOKEN")
GGG_CLIENT_ID: Final[str] = os.getenv("CLIENT_ID")
GGG_AUTHOR_CONTACT: Final[str] = os.getenv("AUTHOR_CONTACT")


async def process_league(league_name: str, dbc: Connection) -> bool:
    league_data = fetch_league_data(league_name)
    return True


async def fetch_league_data(league_name: str) -> str:
    url = f'https://api.pathofexile.com/league/{league_name}/ladder?limit=40'
    header = {
        'Authorization': f'Bearer {GGG_ACCESS_TOKEN}',
        'User-Agent': f'OAuth {GGG_CLIENT_ID}/1.0.0 (contact: {GGG_AUTHOR_CONTACT})'
    }

    response_data: str = ''
    async with aiohttp.ClientSession(headers=header) as session:
        async with session.get(url) as response:
            response_data = await response.text()

    return response_data
