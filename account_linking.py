#########################################
# Author: Veginite
# Module status: SEMI-FINISHED
# To do: Purge veteran roles upon unlinking account
#########################################

# Programmer's note: The reason the discord accounts are deleted upon unlinking (or an error)
# is they might want to use a different account.

from aiosqlite import Connection
import discord

from db import run_db_query, get_generic_query_error_msg

async def link_account(dbc: Connection, user: discord.User, poe_acc_name: str):
    discord_id = await insert_discord_account(dbc, user)
    if discord_id is None:
        return get_generic_query_error_msg()
    elif not discord_id:
        return "Process aborted: Discord user entry already exists. Please unlink your existing account first."
    else:
        discord_id = discord_id[0][0]


    params = {"discord_id": discord_id, "poe_acc_name": poe_acc_name}
    query = ("UPDATE poe_account SET discord_link = :discord_id "
             "WHERE poe_account.username = :poe_acc_name AND poe_account.discord_link IS NULL "
             "RETURNING poe_account.discord_link;")

    discord_link = await run_db_query(dbc, query, params)

    if discord_link is None or not discord_link: # If either fails, delete the inserted Discord account
        discord_account_deletion = await delete_discord_account(dbc, discord_id)
        if discord_account_deletion is None:
            return get_generic_query_error_msg()
        elif not discord_account_deletion:
            return "Failed to delete redundant Discord account. Ping Vegi."

    if discord_link is None: # Query failed
        return get_generic_query_error_msg()
    elif not discord_link: # Empty list, meaning the 2-condition WHERE clause didn't match any rows
        # There is a link. Find out who the account is linked to. If there is no link, there is no PoE account record
        query = ("SELECT da.username FROM discord_account da "
                 "INNER JOIN poe_account p ON p.discord_link = da.discord_id "
                 "WHERE p.username = :poe_acc_name;")
        discord_username = await run_db_query(dbc, query, {"poe_acc_name": poe_acc_name})

        if discord_username is None:
            return get_generic_query_error_msg()
        elif not discord_username:
            return f"There is no such PoE account {poe_acc_name} on record."
        else:
            return f"PoE account {poe_acc_name} is already linked to {discord_username[0][0]}."

    return f"PoE account {poe_acc_name} has been successfully linked to {user.name}."


async def delete_discord_account(dbc: Connection, discord_id: int):
    query = "DELETE FROM discord_account WHERE discord_id = :discord_id RETURNING discord_id;"
    return await run_db_query(dbc, query, {"discord_id": discord_id})


async def unlink_account(dbc: Connection, user: discord.User):
    owner = await get_linked_discord_account(dbc, user.id)
    if owner is None:
        return get_generic_query_error_msg()
    elif not owner:
        return f"Process aborted: You are not linked to a PoE account."

    sever_link = {'null_value': None, "discord_id": user.id}
    query = ("UPDATE poe_account SET discord_link = :null_value "
             "WHERE poe_account.discord_link = :discord_id RETURNING poe_account.username;")
    poe_acc_name = await run_db_query(dbc, query, sever_link)

    if poe_acc_name is None:
        return get_generic_query_error_msg()
    elif not poe_acc_name:
        return "Process aborted: Something went wrong with severing the foreign key. Ping Vegi."
    poe_acc_name = poe_acc_name[0][0]

    discord_account_deletion = await delete_discord_account(dbc, user.id)
    if discord_account_deletion is None:
        return get_generic_query_error_msg()
    elif not discord_account_deletion:
        return "Failed to delete redundant Discord account. Ping Vegi."

    return f"Successfully unlinked {poe_acc_name}."


async def insert_discord_account(dbc: Connection, user: discord.User):
    account_details = {"discord_id": user.id, "username": user.name}
    query = ("INSERT INTO discord_account (discord_id, username) "
             "VALUES(:discord_id, :username) "
             "ON CONFLICT (discord_id) DO NOTHING "
             "RETURNING discord_id;")
    return await run_db_query(dbc, query, account_details)


async def get_linked_discord_account(dbc: Connection, discord_id: int):
    query = "SELECT discord_link from poe_account WHERE poe_account.discord_link = :discord_id;"
    return await run_db_query(dbc, query, {"discord_id": discord_id})