from datetime       import datetime, timezone
from src.data       import data
from src.auth       import detokenise
from src.error      import AccessError, InputError
from src.channels   import channels_list_v2 as channels_list
from src.dm         import dm_list_v1       as dm_list
from src.helpers    import find, error_check, data_dump

def clear_v1():
    '''
    Description:
        Resets the internal data of the application to it's initial state.

    Arguements:
        No arguments required.

    Exceptions:
        No exception is raised.

    Return Value:
        Returns { }
    '''

    data['users']           = []
    data['channels']        = []
    data['msg_positions']   = []
    data['dms']             = []
    data['dreams_stats']={
        'channels_exist': [{
                        'num_channels_exist': 0,
                        'time_stamp': datetime.now().replace(tzinfo=timezone.utc).timestamp()}],
        'dms_exist': [{
                        'num_dms_exist': 0,
                        'time_stamp': datetime.now().replace(tzinfo=timezone.utc).timestamp()}],
        'messages_exist': [{
                        'num_messages_exist': 0,
                        'time_stamp': datetime.now().replace(tzinfo=timezone.utc).timestamp()}],
        'utilization_rate':  0,
    }

    data_dump()
    return {}

def search_v2(token, query_str):
    '''
    Description:
        Given a query string, return a collection of messages in all of the
        channels/DMs that the user has joined that match the query.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - query_str    (type string): A string which contains a combination of characters
                                      which is to be found in the collection of messages.

    Exceptions:
        AcessError Occurs when:
            * token is invalid.
        InputError Occurs when:
            * query_str is above 1000 characters.

    Return values:
        Returns { messages } on condition of:
            + token is valid.
            + query_str is less than or equal too 1000 characters.

        - messages (type list): A list of dictionaries, where each
                                dictionary contains types:
                                { message_id,
                                  u_id,
                                  message,
                                  time_created,
                                }

        - message_id      (type int): An integer used to identify a specific message.
        - u_id        (type integer): An integer refering to a user's id in the database.
        - message      (type string): A string containing info sent by user with token.
        - time_created (type string): A string referring to the time a message was created.
    '''

    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    if len(query_str) > 1000:
        raise InputError("Query string is too long!\
            Reduce it so the length is below 1000 characters :3")

    channels    = channels_list(token)['channels']
    dms         = dm_list(token)['dms']
    return_list = []
    find_and_append('channel'   , channels  , return_list   , query_str)
    find_and_append('dm'        , dms       , return_list   , query_str)

    return {
        'messages': return_list,
    }

def find_and_append(type_string, org_list, return_list, query_str):
    print(f"In find & append, {org_list}")
    if len(org_list) == 0:
        return
    if type_string == 'channel':
        org_id = 'channel_id'
    else:
        org_id = 'dm_id'
    for org in org_list:
        position = find(type_string, None, org[org_id])
        checking_org = data[type_string + 's'][position]
        for message in checking_org['messages']:
            if query_str in message['message']:
                msg = message
                append_info = {
                    'message_id'    : msg['message_id'],
                    'u_id'          : msg['u_id'],
                    'message'       : msg['message'],
                    'time_created'  : msg['time_created'],
                }
                return_list.append(append_info)
