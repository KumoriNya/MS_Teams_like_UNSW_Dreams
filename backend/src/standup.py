import threading
import time
from datetime import datetime, timezone
from src.data import data
from src.error import AccessError, InputError
from src.auth import detokenise
from src.helpers import error_check, find, randomise, insert_message, data_dump, update_user_stats, update_users_stats

def standup_start_v1(token, channel_id, length):
    '''
    Description:
        For a given channel, start the standup period whereby for the next "length" seconds
        if someone calls "standup_send" with a message, it is buffered during the X second window
        then at the end of the X second window a message will be added to the message queue
        in the channel from the user who started the standup.
        X is an integer that denotes the number of seconds that the standup occurs for.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.
        - length      (type integer): An integer indicating time duration.

    Exceptions:
        AccessError Occurs when:
            * token is invalid
            * the authorised user is not a member of the channel.
        InputError Occurs when:
            * channel does not exist
            * is_active == True

    Execution:
        Check for four exceptions,
        Find channel
        set 'standup' : {
            'is_active'     : True,
            'time_finish'   : length + now
            'messages'      : [],
        }
        start threading

    Return Value:
        Returns { 'time_finish' } on condition of:
            + token is valid
            + the authorised user is a member of the channel.
            + the channel exists.
            + the channel is not active.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    error_check(InputError, 'db_channel', [channel_id])
    org_position = find('channel', None, channel_id)
    error_check(AccessError, org_position, [auth_user_id])
    org = data['channels'][org_position]
    if org['standup']['is_active'] is True:
        raise InputError(
            description = f"Channel with channel_id: {channel_id} is in a standup already :)"
        )

    org['standup']['is_active'] = True
    t = threading.Timer(length, end_standup, args = (auth_user_id, org))   
    t.start()
    now = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    end = now + length
    org['standup']['time_finish'] = end

    data_dump()

    return {'time_finish': org['standup']['time_finish']}

def standup_active_v1(token, channel_id):
    '''
    Description:
        For a given channel, return whether a standup is active in it.
        If active, what time the standup finishes.
        If no standup is active, then time_finish returns None

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.

    Exceptions:
        AccessError Occurs when:
            * token is invalid
        InputError Occurs when:
            * channel does not exist

    Execution:
        Check for two exceptions,
        Find channel
        Return corresponding things

    Return Value:
        Returns { 'is_active', 'time_finish' } on condition of:
            + token is valid
            + the authorised user is a member of the channel.
            + the channel exists.
            + the channel is not active.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    error_check(InputError, 'db_channel', [channel_id])
    org_position = find('channel', None, channel_id)
    org = data['channels'][org_position]

    return {
        'is_active'     : org['standup']['is_active'],
        'time_finish'   : org['standup']['time_finish'],
    }

def standup_send_v1(token, channel_id, message):
    '''
    Description:
        Sending a message to get buffered in the standup queue

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.
        - message      (type string): A string of message.

    Exceptions:
        AccessError Occurs when:
            * token is invalid
            * the authorised user is not a member of the channel.
        InputError Occurs when:
            * message is too long
            * channel does not exist
            * is_active == False

    Execution:
        Check for five exceptions,
        Find channel
        Go to channel['standup']['messages']

    Return Value:
        Returns { } on condition of:
            + token is valid
            + the channel exists.
            + the authorised user is a member of the channel.
            + the message is longer than 1000 characters.
            + the channel is not active.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    error_check(InputError, 'db_channel', [channel_id])
    org_position = find('channel', None, channel_id)
    error_check(AccessError, org_position, [auth_user_id])

    org = data['channels'][org_position]
    if org['standup']['is_active'] is False:
        raise InputError(
            description = f"Channel with channel_id: {channel_id} is not in a standup."
        )

    if len(message) > 1000:
        raise InputError(description = "The message is too long (longer than 1000 characters)")

    sender_position = find('user', None, auth_user_id)
    sender = data['users'][sender_position]

    to_append_msg = {
        'message'       : message,
        'sender'        : sender['public_info']['name_first'] \
                        + ' ' + sender['public_info']['name_last'],
    }
    org['standup']['messages'].append(to_append_msg)

    return { }

def end_standup(auth_user_id, org):
    '''
    Description:
        For a given channel, when this function is called:
        Pack the buffered messages into one single message
        Insert this single message into the channel
        Reset 'is_active' back to False

    Arguements:
        - auth_user_id    (type_int): An integer indicating a standup starter's ID.
        - org      (type dictionary): A dictionary of exact channel
                                    that the operation is applied on.

    Execution:
        for all messages in org['standup']['messages']:
            summary += '\n' + f'{sender_name}: ' + 'message'
        insert this message into org['messages'] with
            u_id = auth_user_id
            message_id = randomise
            message = summary
            time = timestamp
        org['standup']['is_active'] = False
        org['standup']['time_finish] = None

    Return Value:
        Returns { } 
    '''

    summary = ''
    for msg in org['standup']['messages']:
        summary += msg['sender'] + ': ' + msg['message'] + '\n'

    summary_msg = {
        'message'       : summary,
        'u_id'          : auth_user_id,
        'message_id'    : randomise('message_id'),
        'time_created'  : org['standup']['time_finish'],
        'is_pinned'     : False,
        'reacts'        : [
            {
                'react_id'  : 1,
                'u_ids'     : [],
            }
        ]
    }

    insert_message('channel', org['channel_id'], summary_msg)

    org['standup']['time_finish']   = None
    org['standup']['is_active']     = False
    org['standup']['messages']      = []
    if len(summary) > 0:
        print(f"Finishing standup, {summary}")
        update_user_stats([auth_user_id], 'messages', True)
        update_users_stats('messages', True)
    data_dump()

    return { }
