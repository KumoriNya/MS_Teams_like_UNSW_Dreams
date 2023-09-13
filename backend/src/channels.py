# Imports
from src.data import data
from src.auth import detokenise
from src.error import InputError, AccessError
from src.helpers import find, pack, error_check, randomise, data_dump, update_users_stats, update_user_stats

#Functions
def channels_list_v2(token):
    '''
    Description:
        Provide a list of all channels (and their associated details) that the
        authorised user is part of.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.

    Exceptions:
        AccessError Occurs when:
            * token is invalid.

    Return Values:
        Returns { channels } on condition of:
            + token is valid.

        - { channel }  (type dict): A dictionary which contains the string name, a
                                    list owner_members and a list all_members.
        - owner_members(type list): A list containing all the owners of the channel.
        - all_members  (type list): A list containing all the member of the channel.
    '''


    list_of_channels_with_auth_user = []

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    channels_idx = 0
    while channels_idx < len(data['channels']):
        find_result = find('channel_is_member', channels_idx, auth_user_id)
        if find_result not in [-1, -2]:
            tmp_dict = {}
            tmp_dict = pack('channel_id', channels_idx, tmp_dict)
            tmp_dict = pack('name', channels_idx, tmp_dict)
            list_of_channels_with_auth_user.append(tmp_dict)
        channels_idx += 1

    return {
        'channels'  : list_of_channels_with_auth_user,
    }

def channels_listall_v2(token):
    '''
    Description:
        Provide a list of all channels (and their associated details).

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.

    Exceptions:
        AccessError Occurs when:
            * token is invalid.

    Return Values:
        Returns { channels } on condition of:
            + token is valid.

        - { channel }  (type dict): A dictionary which contains the string name, a
                                  list owner_members and a list all_members

        - owner_members(type list): A list containing all the owners of the channel.

        - all_members  (type list): A list containing all the member of the channel.  
    '''

    # Check if token is valid.

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Initialise return dict called "all_channels"
    all_channels = {
        list(data.keys())[1] : []
    }

    # Add channels info into all_channels.
    for channel in data['channels']:
        channel_info = {
            'channel_id': channel['channel_id'],
            'name': channel['channel_name'],
        }
        all_channels[list(data.keys())[1]].append(channel_info)

    return all_channels

def channels_create_v2(token, name, is_public):
    '''
    Description:
        Creates a new channel with that name that is either a public or private channel.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - name       (type string): A string which represents the name of the channel.
        - is_public (type boolean): A boolean which determines the public status of a
                                    channel.

    Exceptions:
        InputError Occurs when:
            * name is more than 20 characters long.
        AccessError Occurs when:
            * token is invalid

    Return Values:
        Returns { channel_id } on condition of:
            + auth_user_id exists in the database.
            + name is less than or equal to 20 characters long.

        - { channel_id } (type dict): A dictionary containing the channel_id.

        - channel_id      (type int): An integer specific to a channel stored in the database
                                      used to run certain commands.
    '''

    # Initialise empty user dict for creation of members list.
    user = {}

    # Initialise owner_members list containing the creator
    # of the channel.
    # owner_members = []

   # Initialise all_members list containing the creator of
    # the channel.
    # all_members = []

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    auth_user_position_in_db = find('user', None, auth_user_id)
    user = data['users'][auth_user_position_in_db]

    # owner_members.append(
    #     user['public_info']
    # )
    # all_members.append(
    #     user['public_info']
    # )

    # Check if length of name is valid.
    if len(name) > 20:
        raise InputError("Channel name is too long.")

    # Determine how many channels are in data.
    channel_idx = 0
    while channel_idx <= len(data['channels']):
        channel_idx += 1

    # Add the new channel to the 'channels' dictionary.
    data['channels'].append({
        'channel_id'    : randomise('channel_id'),
        'channel_name'  : name,
        'is_public'     : is_public,
        'owner_members' : [user['public_info']],
        'all_members'   : [user['public_info']],
        'messages'      : [],
        'standup': {
            'time_finish': None,
            'is_active': False,
            'messages': [],
        },
    })

    # Create a dict index for searching in 'channels' list.
    dict_idx = channel_idx - 1
    update_user_stats([auth_user_id], 'channels', True)
    update_users_stats('channels', True)
    data_dump()

    return {
        list(data['channels'][dict_idx].keys())[0] : list(data['channels'][dict_idx].values())[0]
    }
