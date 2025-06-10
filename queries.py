#########################################
# Author: Veginite
# Module status: SEMI-FINISHED
#########################################

from aiosqlite import Connection
import discord

from db import run_db_query, run_many_db_queries, get_generic_query_error_msg
from utils import get_host_mention


async def delete_discord_account(dbc: Connection, discord_user: discord.User) -> str:
    query = "DELETE FROM discord_account WHERE discord_id = :discord_id;"
    query_response = await run_db_query(dbc, query, {"discord_id": discord_user.id})

    query_error = ""
    if query_response is None:
        query_error = "Unable to remove Discord account from db. " + get_host_mention()

    return query_error


async def fetch_eligible_role(dbc: Connection, unique_years_played: int) -> dict:
    query = "SELECT name, discord_role_id FROM veteran_role WHERE required_years = :unique_years_played;"
    eligible_role = await run_db_query(dbc, query, {'unique_years_played': unique_years_played})

    result = {"value": None, "query_error": ""}
    if eligible_role is None: # Query error
        result["query_error"] = get_generic_query_error_msg()
    elif not eligible_role:  # Empty list
        result["query_error"] = "Process aborted: Query returned no eligible roles. " + get_host_mention()
    else:
        result["value"] = eligible_role[0][1]

    return result


async def fetch_unique_years_played(dbc: Connection, poe_acc_name: str) -> dict:
    query = (f"SELECT COUNT(DISTINCT strftime('%Y', l.start_at)) FROM character "
             f"INNER JOIN poe_account a ON a.id = character.owner "
             f"INNER JOIN league l ON l.id = character.league "
             f"WHERE a.username = :username AND l.awards_veteran_roles = TRUE;")

    unique_years_played = await run_db_query(dbc, query, {'username': poe_acc_name})

    result = {"value": None, "query_error": ""}
    if unique_years_played is None:  # Query error
        result["query_error"] = get_generic_query_error_msg()
    elif not unique_years_played:  # Empty list
        result["query_error"] = (f'Process aborted: Query returned no Conflux records for PoE account {poe_acc_name}.'
                f'If you are new to Conflux and have recently joined your first league, please await a database update.')
    else:
        result["value"] = unique_years_played[0][0]

    return result


async def fetch_veteran_roles(dbc: Connection) -> dict:
    query = f"SELECT discord_role_id FROM veteran_role;"

    query_response = await run_db_query(dbc, query, {})

    result = {"value": None, "query_error": ""}
    if query_response is None: # Query error
        result["query_error"] = get_generic_query_error_msg()
    elif not query_response: # Empty list
        result["query_error"] = "Process aborted: Query returned no veteran roles. " + get_host_mention()
    else:
        result["value"] = query_response

    return result


async def get_linked_poe_username(dbc: Connection, discord_user: discord.User) -> dict:
    query = "SELECT username from poe_account WHERE discord_link = :discord_id;"
    query_response = await run_db_query(dbc, query, {"discord_id": discord_user.id})

    result = {"value": None, "query_error": ""}
    if query_response is None:
        result["query_error"] = get_generic_query_error_msg() + get_linked_poe_username.__name__
    elif not query_response:
        result["query_error"] = "There is no PoE account linked to you."
    else:
        result["value"] = query_response[0][0]

    return result


async def get_linked_discord_account_username(dbc: Connection, poe_acc_name: str) -> dict:
    query = ("SELECT da.username FROM discord_account da "
             "INNER JOIN poe_account p ON p.discord_link = da.discord_id "
             "WHERE p.username = :poe_acc_name;")
    query_response = await run_db_query(dbc, query, {"poe_acc_name": poe_acc_name})

    result = {"value": None, "query_error": ""}
    if query_response is None:
        result["query_error"] = get_generic_query_error_msg() + get_linked_discord_account_username.__name__
    elif not query_response:
        result["query_error"] = f"There is no PoE account with link id: {discord_link} " + get_host_mention()
    else:
        result["value"] = query_response[0][0]

    return result


async def insert_discord_account(dbc: Connection, discord_user: discord.User) -> str:
    account_details = {"discord_id": discord_user.id, "username": discord_user.name}
    query = "INSERT INTO discord_account (discord_id, username) VALUES(:discord_id, :username);"
    query_response = await run_db_query(dbc, query, account_details)

    query_error = ""
    if query_response is None:
        query_error = f"User '{discord_user.name}' already has a PoE account linked."

    return query_error



async def poe_account_exists(dbc: Connection, poe_acc_name: str) -> dict:
    query = "SELECT id FROM poe_account WHERE username = :poe_acc_name;"
    query_response = await run_db_query(dbc, query, {"poe_acc_name": poe_acc_name})

    result = {"value": None, "query_error": ""}
    if query_response is None:
        result["query_error"] = get_generic_query_error_msg() + get_linked_discord_account_username.__name__
    elif not query_response:
        result["query_error"] = f"PoE account: {poe_acc_name} returned no results. "
    else:
        result["value"] = query_response[0][0]

    return result



async def sever_poe_account_link(dbc: Connection, user: discord.User) -> str:
    account_link = {'null_value': None, "discord_id": user.id}
    query = ("UPDATE poe_account SET discord_link = :null_value "
             "WHERE poe_account.discord_link = :discord_id")
    query_response = await run_db_query(dbc, query, account_link)

    query_error = ""
    if query_response is None:
        # Should never fail as redundant Discord accounts are removed during processing
        query_error = "Unable to sever PoE account link. " + get_host_mention()

    return query_error


async def update_poe_account_link(dbc: Connection, discord_user: discord.User, poe_acc_name) -> str:
    account_details = {"discord_id": discord_user.id, "poe_acc_name": poe_acc_name}
    query = ("UPDATE poe_account SET discord_link = :discord_id "
             "WHERE username = :poe_acc_name AND discord_link IS NULL;")
    query_response = await run_db_query(dbc, query, account_details)

    query_error = ""
    if query_response is None:
        query_error = "Unable to establish PoE account link. " + get_host_mention()

    return query_error
