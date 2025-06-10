#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

import discord

def get_host_mention() -> str:
    return f'<@{str(243795149291782146)}> '

def query_was_unsuccessful(query_error: str):
    return len(query_error) > 0

async def purge_prior_roles(discord_user: discord.User, user_veteran_roles: list):
    for role in user_veteran_roles:
        await discord_user.remove_roles(discord_user.guild.get_role(role))
