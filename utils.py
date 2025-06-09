#########################################
# Author: Veginite
# Module status: FINISHED
#########################################

def get_host_mention() -> str:
    return f'<@{str(243795149291782146)}> '

def query_was_unsuccessful(query_error: str):
    return len(query_error) > 0