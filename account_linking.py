#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

# Programmer's note: The reason the discord accounts are deleted upon unlinking (or an error)
# is they might want to use a different account.

from aiosqlite import Connection
import discord

from queries import delete_discord_account, insert_discord_account, poe_account_exists, update_poe_account_link
from queries import fetch_veteran_roles, get_linked_poe_username, sever_poe_account_link
from utils import purge_prior_roles, query_was_unsuccessful

async def link_account(dbc: Connection, discord_user: discord.User, poe_acc_name: str):
    # Verify that there is an entry of the PoE account in question
    query_result = await poe_account_exists(dbc, poe_acc_name)
    if query_result["value"] is None or not query_result["value"]:
        return query_result["query_error"]

    # Insert Discord account entry
    query_error = await insert_discord_account(dbc, discord_user)
    if query_was_unsuccessful(query_error):
        return query_error

    # Attempt to establish a link between the Discord user and the PoE account
    query_error_update_link = await update_poe_account_link(dbc, discord_user, poe_acc_name)
    if query_was_unsuccessful(query_error_update_link):

        # Delete the Discord account if the linking was unsuccessful
        query_error_delete_account = await delete_discord_account(dbc, discord_user)
        if query_was_unsuccessful(query_error_delete_account):
            return query_error_update_link + "\n" + query_error_delete_account
        # ----------------------------------------------------------

        # -------- Find out what Discord user is linked to the PoE account --------
        query_result = get_linked_discord_account_username(dbc, poe_acc_name)
        if query_result["value"] is None or not query_result["value"]:
            return query_error_update_link + "\n" + query_result["query_error"]
        else:
            return (query_error_update_link +
                    f"Discord user {query_result["value"]} is linked to PoE account {poe_acc_name}.")
        # -------------------------------------------------------------------------

    return f"PoE account {poe_acc_name} has been successfully linked to {discord_user.name}."


async def unlink_account(dbc: Connection, discord_user: discord.User):
    # Check the link and return the name matching the Discord user's id
    query_result = await get_linked_poe_username(dbc, discord_user)
    if query_result["value"] is None:
        return query_result["query_error"]
    else:
        poe_acc_name = query_result["value"]

    # Attempt to sever the link between the user and the PoE account
    query_error = await sever_poe_account_link(dbc, discord_user)
    if query_was_unsuccessful(query_error):
        return query_error

    # Attempt to delete the now redundant Discord account
    query_error = await delete_discord_account(dbc, discord_user)
    if query_was_unsuccessful(query_error):
        return query_error

    # Purge user veteran roles
    query_result = await fetch_veteran_roles(dbc)
    if query_result["value"] is None or not query_result["value"]:
        return query_result["query_error"]
    else:
        vet_roles = query_result["value"]

    vet_roles = [row[0] for row in vet_roles]  # Fetch roles and construct a list of ids
    user_vet_roles = [role.id for role in discord_user.roles if role.id in vet_roles]  # the vet roles the user currently has
    await purge_prior_roles(discord_user, user_vet_roles)

    return f"Successfully unlinked {poe_acc_name}."
