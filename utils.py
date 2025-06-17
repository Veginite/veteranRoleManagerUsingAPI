#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

import discord
from table2ascii import table2ascii as t2a, PresetStyle, Alignment


def format_pretty_ascii_table(table: list, header: list) -> str:
    output = t2a(
        header=header,
        body=table,
        alignments=Alignment.LEFT,
        style=PresetStyle.thin_compact_rounded
    )
    return f"```\n{output}\n```"


def get_host_mention() -> str:
    return f'<@{str(243795149291782146)}> '


def query_was_unsuccessful(query_error: str) -> bool:
    return len(query_error) > 0


async def purge_roles(discord_user: discord.User, roles_to_remove: list) -> None:
    for role in roles_to_remove:
        await discord_user.remove_roles(discord_user.guild.get_role(role))
