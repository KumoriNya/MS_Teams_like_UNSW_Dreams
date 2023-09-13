'''
Standard module: datetime
Local modules       : data, AccessError, InputError
                    - find, error_check, randomise.
'''
import threading
from datetime import datetime, timezone
from src.data import data
from src.auth import detokenise
from src.error import AccessError, InputError
from src.helpers import find, error_check, randomise, insert_message, send_notification, data_dump, update_user_stats, update_users_stats, find_message

def message_send_v2(token, channel_id, message):
    '''
    Description:
        Send a message from authorised_user to the channel specified by channel_id.
        Note: Each message should have it's own unique ID.
        I.E. No messages should share an ID with another message,
        even if that other message is in a different channel.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.
        - message      (type string): A string containing info sent by user with token.

    Exceptions:
        AccessError Occurs when:
            * token is invalid
            * the authorised user is not a member of the channel.
        InputError Occurs when:
            * channel does not exist
            * 'message' is more than 1000 characters.

    Execution:
        Check for four exceptions,
        Create 'message': {
            'u_id'          : ,
            'message'       : ,
            'time_created'  : ,
        }
        Generate msg_id,
        Add position info into data['msg_positions'],
        Insert into channel['messages'][0]

    Return Value:
        Returns { } on condition of:
            + token is valid
            + the authorised user is a member of the channel.
            + the channel exists.
            + 'message' is less than or equal to 1000 characters.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    error_check(InputError, 'db_channel', [channel_id])
    operating_channel_position_in_db = find('channel', None, channel_id)
    error_check(AccessError, operating_channel_position_in_db, [auth_user_id])
    if len(message) > 1000:
        raise InputError("Message length too long.")

    to_send_message = {
        'u_id'          : auth_user_id,
        'message'       : message,
        'time_created'  : datetime.now().replace(tzinfo=timezone.utc).timestamp(),
        'is_pinned'     : False,
        'reacts'        : [
            {
                'react_id'  : 1,
                'u_ids'     : [],
            }
        ]
    }

    to_send_message['message_id'] = randomise('message_id')
    # Channel contains messages
    insert_message('channel', channel_id, to_send_message)

    # check if tagged
    tagged_list = is_tagged(message)
    # print(f"In the message {message}, {tagged_list} is tagged.\n")

    if len(tagged_list) != 0:
        for tag in tagged_list:
            user_position = find('handle', None, tag['handle'])
            tagged_user = data['users'][user_position]
            if user_position > -1:
                user_in_channel = find(
                    'channel_is_member', operating_channel_position_in_db,\
                    tagged_user['public_info']['u_id']
                )
                if user_in_channel > -1:
                    send_notification(
                        [tagged_user['public_info']['u_id'], auth_user_id], message,
                        'tagged', ['channel', channel_id]
                    )
    update_user_stats([auth_user_id], 'messages', True)
    update_users_stats('messages', True)
    data_dump()
    print(f"Message sent by user {data['users'][find('user', None, auth_user_id)]['public_info']['name_first']} successfully")
    return {
        'message_id': to_send_message['message_id'],
    }

def message_remove_v1(token, message_id):
    '''
    Description:
        Given a message_id for a message
        this message is removed from the channel/DM

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - message_id  (type integer): An integer refering to a message's id in the database.

    Exceptions:
        AccessError Occurs when:
            * token is invalid.
            * the authorised user is not admin/owner/sender.
        InputError Occurs when:
            * message not exist

    Execution:
        Check for three exceptions,
        Goto position info in data['msg_positions'] for position,
        Remove msg_positions
        Remove actual msg in db as well

    Return Value:
        Returns { } on condition of:
            + token is valid.
            + the authorised user is an admin/owner/sender.
            + message exists.
    '''


    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    find_results = find('message', None, message_id)
    if isinstance(find_results, int):
        raise InputError("Message not exist")
    msg_idx = find_results[0]
    operating_org = find_results[1] # Exact organisation containing this message
    message = operating_org['messages'][msg_idx]
    position_info_in_msg_po = find_results[2]   # message position info

    error_check(AccessError, 'message_auth', [message_id, auth_user_id])

    operating_org['messages'].remove(message)
    position_info_in_msg_po['message_ids'].remove(message_id)
    if len(position_info_in_msg_po['message_ids']) == 0:
        data['msg_positions'].remove(position_info_in_msg_po)

    update_users_stats('messages', False)
    data_dump()

    return {}

def message_edit_v2(token, message_id, message):
    '''Description:
        Given a message, update its text with new text.
        If the new message is an empty string, the message is deleted.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - message_id  (type integer): An integer refering to a message's id in the database.
        - message      (type string): A string containing info sent by user with token.

    Exceptions:
        AccessError Occurs when:
            * token is invalid.
            * the authorised user is not admin/owner/sender.
        InputError Occurs when:
            * 'message' is more than 1000 characters.
            * 'message_id' refers to a deleted message.
            * message not exist

    Execution:
        Check for five exceptions,
        Goto position info in data['msg_positions'] for position,
        Apply change into channel['messages'][msg_positions]

    Return Value:
        Returns { } on condition of:
            + token is valid
            + the authorised user is an admin/owner/sender.
            + 'message' is less than or equal to 1000 characters.
            + 'message_id' refers to an existing message.
            + message exists
    '''


    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    find_results = find('message', None, message_id)
    if isinstance(find_results, int):
        raise InputError("Message not exist")
    msg_idx = find_results[0]
    operating_org = find_results[1]

    operator_type = find_results[2]['type']
    operator_id = find_results[2]['id']
    operator_pos = find(operator_type, None, operator_id)

    actual_msg = operating_org['messages'][msg_idx]

    error_check(AccessError, 'message_auth', [message_id, auth_user_id])

    if len(message) > 1000:
        raise InputError("Message length too long.")

    if len(message) == 0:
        actual_msg = operating_org['messages'][msg_idx]
        update_users_stats('messages', False)
        operating_org['messages'].remove(actual_msg)
        position_info_in_msg_po = find_results[2]
        position_info_in_msg_po['message_ids'].remove(message_id)
        if len(position_info_in_msg_po['message_ids']) == 0:
            data['msg_positions'].remove(position_info_in_msg_po)

    actual_msg['message'] = message

    tagged_list = is_tagged(message)
    if len(tagged_list) != 0:
        for tag in tagged_list:
            user_position = find('handle', None, tag['handle'])
            tagged_user = data['users'][user_position]

            if user_position > -1:
                user_in_channel = find(
                    operator_type + '_is_member', operator_pos,\
                    tagged_user['public_info']['u_id']
                )
                if user_in_channel > -1:
                    send_notification(
                        [tagged_user['public_info']['u_id'], auth_user_id], message,
                        'tagged', [operator_type, operator_id]
                    )

    data_dump()

    return {}

def message_senddm_v1(token, dm_id, message):
    '''
    Description:
        Send a message from authorised_user to the dm specified by dm_id.
        Note: Each message should have it's own unique ID.
        I.E. No messages should share an ID with another message,
        even if that other message is in a different dm.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - dm_id       (type integer): An integer refering to a dm's id in the database.
        - message      (type string): A string containing info sent by user with token.

    Exceptions:
        AccessError Occurs when:
            * token is invalid.
            * the authorised user is not a member of the dm.
        InputError Occurs when:
            * 'message' is more than 1000 characters.

    Execution:
        Check for four exceptions,
        Create 'message': {
            'u_id'          : ,
            'message'       : ,
            'time_created'  : ,
        }
        Generate msg_id,
        Add position info into data['msg_positions'],
        Insert into dm['messages'][0]

    Return Value:
        Returns { 'message_id' } on condition of:
            + token is valid.
            + the authorised user is a member of the dm.
            + 'meassage' is less than or equal to 1000 characters.

        - { 'message_id' } (type dict): A dictionary containing an integer
                                        contain 'message_id' (type int).
        - message_id        (type int): An integer used to identify a
                                        specific message.
    '''

    # General Access Error
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    # DM not exist InputError
    error_check(InputError  , 'db_dm'   , [dm_id])
    operating_dm_position_in_db = find('dm', None, dm_id)
    # User not in DM Access Error
    error_check(InputError, dm_id, [auth_user_id])
    if len(message) > 1000:
        raise InputError("Message length too long.")

    to_send_message = {
        'u_id'          : auth_user_id,
        'message'       : message,
        'time_created'  : datetime.now().replace(tzinfo=timezone.utc).timestamp(),
        'is_pinned'     : False,
        'reacts'        : [
            {
                'react_id'  : 1,
                'u_ids'     : [],
            }
        ]
    }

    to_send_message['message_id'] = randomise('message_id')

    insert_message('dm', dm_id, to_send_message)

    # check if tagged
    tagged_list = is_tagged(message)
    if len(tagged_list) != 0:
        for tag in tagged_list:
            user_position = find('handle', None, tag['handle'])
            tagged_user = data['users'][user_position]
            if user_position > -1:
                user_in_dm = find(
                    'dm_is_member', operating_dm_position_in_db,\
                    tagged_user['public_info']['u_id']
                )
                if user_in_dm > -1:
                    send_notification(
                        [tagged_user['public_info']['u_id'], auth_user_id], message,
                        'tagged', ['dm', dm_id]
                    )

    update_user_stats([auth_user_id], 'messages', True)
    update_users_stats('messages', True)
    data_dump()

    return {
        'message_id': to_send_message['message_id'],
    }

def message_share_v1(token, og_message_id, message, channel_id, dm_id):
    '''
    Description:
        og_message_id is the original message.
        channel_id is the channel that the message is being shared to and
        is -1 if it is being sent to a DM.
        dm_id is the DM that the message is being shared to and
        is -1 if it is being sent to a channel.
        message is the optional message in addition to the shared message,
        and will be an empty string '' if no message is given.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - og_message_id   (type int):
        - message      (type string): A string containing info sent by user with token.     
        - channel_id  (type integer): An integer refering to a channel's id in the database.
        - dm_id           (type int): An integer refering to a specific dm in the database.

    Exceptions:
        AccessError when:
            * token is invalid.
            * the authorised user has not joined the channel or DM 
              they are trying to share the message to.

    Execution:
        Check for two exceptions,
        Organise insert data:
        to_share_message = {
            'add_message'               : message,
            'original_message'          : og_message_id_corresponding_msg,
            'u_id'                      : token_corresponding_u_id,
            'time_created'              : timestamp,
            'message_id'                : randomise('message_id'),
            'actual_message_in_display' : message + \\ + ''\\ + original_message +'',
        }
        Find sharing target
        Insert th_share_message['actual_message'],
        Add to_share_message['message_id'] into data['msg_position']

    Return values:
        Returns { shared_message_id } on condition of:
            + token is valid
            + the authorised user is in the channel and dm they are trying
              to send the message to.

        - { shared_message_id } (type dict): A dictionary containing the integer
                                             shared_message_id.
        - shared_message_id      (type int): A integer refering to a specific message
                                             which has been shared.
    '''


    timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    operator_type  = None
    operator_id    = -1
    if channel_id   == -1:
        operator_type  = 'dm'
        operator_id    = dm_id
    else:
        operator_type  = 'channel'
        operator_id    = channel_id

    authen = False
    operator_target_position = find(operator_type, None, operator_id)
    for member in data[operator_type + 's'][operator_target_position]['all_members']:
        if auth_user_id == member['u_id']:
            authen = True
    if authen is False:
        raise AccessError(
            f"User with auth_user_id: {auth_user_id} has no permission to\
            {operator_type} with id {operator_id}"
        )
    # print(f"In share, about to call find message. Share Target Type = {operator_type}, Share Target Id = {operator_id}")
    # print(f"Passing in parameters into find: msg_id is {og_message_id}")
    og_message_relevant_results = find('message', None, og_message_id)
    # print(f"in share, find result: {og_message_relevant_results}")
    operator = og_message_relevant_results[1]
    msg_idx = og_message_relevant_results[0]
    original_message = operator['messages'][msg_idx]
    dist = '\n' + ''''''

    to_share_message = message + dist + original_message['message'] + dist

    final_message = {
        'u_id'          : auth_user_id,
        'message'       : to_share_message,
        'time_created'  : timestamp,
        'message_id'    : randomise('message_id'),
        'is_pinned'     : False,
        'reacts'        : [
            {
                'react_id'  : 1,
                'u_ids'     : [],
            }
        ]
    }

    insert_message(operator_type, operator_id, final_message)

    tagged_list = is_tagged(message)
    if len(tagged_list) != 0:
        for tag in tagged_list:
            user_position = find('handle', None, tag['handle'])
            tagged_user = data['users'][user_position]

            if user_position > -1:
                user_in_channel = find(
                    operator_type + '_is_member', operator_target_position,\
                    tagged_user['public_info']['u_id']
                )
                if user_in_channel > -1:
                    send_notification(
                        [tagged_user['public_info']['u_id'], auth_user_id], message,
                        'tagged', [operator_type, operator_id]
                    )

    update_user_stats([auth_user_id], 'messages', True)
    update_users_stats('messages', True)
    data_dump()

    return {
        'shared_message_id': final_message['message_id']
    }

def message_pin_v1(token, message_id):
    '''
    Description:
        Given a message within a channel or DM, mark it as "pinned" 
        to be given special display treatment by the frontend

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - message_id      (type_int):   An integer indicating a message's ID.

    Exceptions:
        AccessError Occurs when:
            * token is invalid
            * the authorised user is not owner of the channel or dm.
        InputError Occurs when:
            * message id does not exist.
            * message with message_id is already pinned.

    Return Value:
        Returns { } on condition of:
            + token is valid
            + the authorised user is owner of the channel or dm.
            + the message exists.
            + message with message_id isn't already pinned.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check if auth_user_id invalid
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Check is message exist
    error_check(InputError, 'message', [message_id])

    # Find the channel that message belongs to
    result = find('message', None, message_id)

    msg_idx_in_org = result[0]
    org = result[1]
    # Check if the user is the owner of the channel or dm
    error_check(AccessError, 'owner', [auth_user_id, org])

    # Check if the message is already pinned, if not, pin the message
    error_check(InputError, 'check_pin', [org, msg_idx_in_org])

    org['messages'][msg_idx_in_org]['is_pinned'] = True

    return {}

def message_unpin_v1(token, message_id):
    '''
    Description:
        Given a message within a channel or DM, mark it as "unpinned" 
        to be given special display treatment by the frontend.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - message_id      (type_int):   An integer indicating a message's ID.

    Exceptions:
        AccessError Occurs when:
            * token is invalid
            * the authorised user is not owner of the channel or dm.
        InputError Occurs when:
            * message id does not exist.
            * message with message_id is not pinned.

    Return Value:
        Returns { } on condition of:
            + token is valid
            + the authorised user is owner of the channel or dm.
            + the message exists.
            + message with message_id is pinned.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check if auth_user_id invalid
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Check is message exist
    error_check(InputError, 'message', [message_id])

    # Find the channel that message belongs to
    result = find('message', None, message_id)

    msg_idx_in_org = result[0]
    org = result[1]
    # Check if the user is the owner of the channel or dm
    error_check(AccessError, 'owner', [auth_user_id, org])

    # Check if the message is already unpinned, if not, unpin the message
    error_check(InputError, 'check_unpin', [org, msg_idx_in_org])

    org['messages'][msg_idx_in_org]['is_pinned'] = False

    return {}

def message_sendlater_v1(token, channel_id, message, time_sent):
    '''
    Description:
        Send a message from authorised_user to the channel specified
        by channel_id automatically at a specified time in the future
    Arguments:
        - token       (type string)     :   A string to be detokenised which contains payload containing
                                            auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.
        - channel_id  (type integer)    : An integer referring to a channel's id in the database.
        - message     (type string)     : A string containing info sent by user with token.
        - time_sent   (type integer (unix timestamp)):A integer referring the time to send message
    Exceptions:
        AccessError Occurs when:
            * token is invalid
            * the authorised user is not a member of the channel.
        InputError Occurs when:
            * channel does not exist
            * 'message' is more than 1000 characters.
            * Time sent is a time in the past

    Execution:
        Check for four exceptions,
        Create 'message': {
            'u_id'          : ,
            'message'       : ,
            'time_created'  : ,
        }
        Generate msg_id,
        Add position info into data['msg_positions'],
        Insert into channel['messages'][0]

    Return Value:
        Returns { } on condition of:
            + token is valid
            + the authorised user is a member of the channel.
            + the channel exists.
            + 'message' is less than or equal to 1000 characters.
    '''
    # decode the token
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    # check token valid
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    # check channel_id valid
    error_check(InputError, 'db_channel', [channel_id])

    # check whether the authorised user has joined the channel they are trying to post to
    operating_channel_position_in_db = find('channel', None, channel_id)
    error_check(AccessError, operating_channel_position_in_db, [auth_user_id])

    cur_time = datetime.now().timestamp()
    sleep_time = time_sent - cur_time
    # check sent_time valid
    error_check(InputError, 'time', [sleep_time])
    # Check message length valid
    error_check(InputError, 'message_length', [len(message)])
     
    to_send_message = {
        'u_id'          : auth_user_id,
        'message'       : message,
        'time_created'  : time_sent,
        'is_pinned'     : False,
        'reacts'        : [
            {
                'react_id'  : 1,
                'u_ids'     : [],
            }
        ]
    }
    to_send_message['message_id'] = randomise('message_id')
    
    t = threading.Timer(sleep_time, insert_message, args=['channel', channel_id, to_send_message])
    t.start()
    return {
        'message_id': to_send_message['message_id']
    }

def message_sendlaterdm_v1(token, dm_id, message, time_sent):
    '''
    Description:
        Send a message from authorised_user to the DM specified by dm_id
        automatically at a specified time in the future.

    Arguments:
        - token(type string)        :   A string to be demonetised which contains payload containing
                                auth_user_id and session_id.
        - dm_id(type_int)           :   An integer indicating the DM.
        - message(type_string)      :   A string containing info sent by user with token.
        - time_sent(type_integer)   :   An integer indication the time to send message.

    Exception:
        AccessError Occurs when:
            * token is invalid.
        InputError Occurs when:
            * Dm does not exist.
            * 'message' is more than 1000 characters.
            * time_sent is a time in the past.

    Return Values:
        Returns { message_id } on condition of:
            + token is valid.
            + dm_id is valid.
            + 'message' is less than 1000 characters.

            - { 'message_id' } (type dict): A dictionary containing an integer
                                        contain 'message_id' (type int).
            - message_id        (type int): An integer used to identify a
                                        specific message.
    '''
    # General Access Error
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    # DM not exist InputError
    operating_dm_position_in_db = find('dm', None, dm_id)
    if operating_dm_position_in_db == -1:
        raise InputError(f"DM with dm_id {dm_id} not exist in the DB.")
        # Or return straightaway, but i consider an error is better
    
    # User not in DM Access Error
    error_check(InputError, dm_id, [auth_user_id])
    # time_send is in the past
    cur_time = datetime.now().timestamp()
    sleep_time = time_sent - cur_time
    # check sent_time valid
    error_check(InputError, 'time', [sleep_time])
    # Check message length valid
    error_check(InputError, 'message_length', [len(message)])
    
    to_send_message = {
        'u_id'          : auth_user_id,
        'message'       : message,
        'time_created'  : time_sent,
        'is_pinned'     : False,
        'reacts'        : [
            {
                'react_id'  : 1,
                'u_ids'     : [],
            }
        ]
    }
    to_send_message['message_id'] = randomise('message_id')
    
    t = threading.Timer(sleep_time, insert_message, args=['dm', dm_id, to_send_message])
    t.start()
    return {
        'message_id': to_send_message['message_id']
    }

def message_react_v1(token, message_id, react_id):
    """
    Description:
        Given a message within a channel or DM the authorised user is part of,
        add a "react" to that particular message

    Arguments:
        - token(type string)        :   A string to be demonetised which contains payload containing
                                auth_user_id and session_id.
        - message_id(type_int)           :   An integer indicating the message
        - react_id                       :   An integer indicating the valid reaction
    Exception:
        AccessError Occurs when:
            * token is invalid.
            * The authorised user is not a member of the channel or DM that the message is within
        InputError Occurs when:
            * message_id is not a valid message within a channel or DM that the authorised user has joined
            * react_id is not a valid React ID. The only valid react ID the frontend has is 1
            * Message with ID message_id already contains an active React with ID react_id from the authorised user

    Return Values:
        Returns {} on condition of:
            + token is valid.
            + user is a member of the channel.
            + messgae_id is valid.
            + 'react_id' is 1.
            + user has not reacted to the message.

    """

    # decode the token
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    # check token valid
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    # check message_id valid
    find_results = find('message', None, message_id)
    if isinstance(find_results, int):
        raise InputError(description="Message not exist")
    # check that this user is in where the message belongs to
    AccessError_exist = True
    msg_op = find_message(message_id)
    for member in msg_op[1]['all_members']:
        if member['u_id'] == auth_user_id:
            AccessError_exist = False
            break
    if AccessError_exist:
        raise AccessError(description='token with no authorisation')
    if react_id != 1:
        raise InputError(description='Invalid react_id entered')
    # wait to use the helper to simplify
    msg = find_results[1]['messages'][find_results[0]]
    react_info = msg['reacts'][0]
    if react_info['react_id'] == 1:
        if auth_user_id not in react_info['u_ids']:
            react_info['u_ids'].append(auth_user_id)
        else:
            raise InputError(description='You have already reacted to this message')

    return {
    }

def message_unreact_v1(token, message_id, react_id):
    """
    Description:
        Given a message within a channel or DM the authorised user is part of,
        remove a "react" to that particular message

    Arguments:
        - token(type string)        :   A string to be demonetised which contains payload containing
                                auth_user_id and session_id.
        - message_id(type_int)           :   An integer indicating the message
        - react_id                       :   An integer indicating the valid reaction
    Exception:
        AccessError Occurs when:
            * token is invalid.
            * The authorised user is not a member of the channel or DM that the message is within
        InputError Occurs when:
            * message_id is not a valid message within a channel or DM that the authorised user has joined
            * react_id is not a valid React ID
            * Message with ID message_id does not contain an active React with ID react_id from the authorised user

    Return Values:
        Returns {} on condition of:
            + token is valid.
            + user is a member of the channel.
            + messgae_id is valid.
            + 'react_id' is 1.
            + user has reacted to the message.

    """

    # decode the token
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    # check token valid
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    # check message_id valid
    find_results = find('message', None, message_id)
    if isinstance(find_results, int):
        raise InputError(description="Message not exist")
    # check that this user is in where the message belongs to
    AccessError_exist = True
    msg_op = find_message(message_id)
    for member in msg_op[1]['all_members']:
        if member['u_id'] == auth_user_id:
            AccessError_exist = False
            break
    if AccessError_exist:
        raise AccessError(description='token with no authorisation')
    if react_id != 1:
        raise InputError(description='Invalid react_id entered')

    msg = find_results[1]['messages'][find_results[0]]
    react_info = msg['reacts'][0]
    if react_info['react_id'] == 1:
        if auth_user_id in react_info['u_ids']:
            react_info['u_ids'].remove(auth_user_id)
        else:
            raise InputError(description='You have not reacted to this message')
    return {
    }

def notifications_get_v1(token):
    '''
    Description:
        Given a token, return a list containing 20 most recent notifications.

    Arguements:
        - token(type string)        :   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.

    Exception:
        AccessError Occurs when:
            * token is invalid.

    Return Values:
        Returns { notifications } on condition of:
            + token is valid.

        - { notifications } (type dict): A dictionary containing notifications which is
                                         of type list.

        - notifications     (type list): List of dictionaries, where each dictionary contains
                                         types { channel_id, dm_id, notification_message }.
                                         The list should be ordered from most to least recent.

        - channel_id         (type int): Is the id of the channel that the event happened in,
                                         and is -1 if it is being sent to a DM.
    
        - dm_id              (type int): Is the DM that the event happened in, and is -1 if
                                         it is being sent to a channel.

        - Notification_message (type string): Is a string of the following format for each trigger action:
                                    * tagged: "{User’s handle} tagged you in {channel/DM name}: {first 20 characters of the message}"
                                    * added to a channel/DM: "{User’s handle} added you to {channel/DM name}"

    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    user_position = find('user', None, auth_user_id)
    user = data['users'][user_position]

    notifications = user['notifications']
    if len(notifications) > 20:
        notifications = notifications[0: 20]

    # print(data)
    # print("data above============noti below")
    # print(notifications)
    return {
        'notifications': notifications,
    }

def is_tagged(message):
    '''
    Description: 
    Helper function that takes a given message and finds if there is any valid tag.

    Return a list of valid tags.
    '''

    tag_notation = 0
    tag_nums = 0
    tags = []
    invalid = []
    for character_idx in range(len(message)):
        character = message[character_idx]
        if character == '@' and tag_notation == 0:
            tag_notation += 1
            tags.append(
                {
                    'position'  : character_idx,
                    'handle'    : '',
                }
            )
        if tag_notation != 0:
            if character != ' ':
                dicti = tags[tag_nums]
                dicti['handle'] = dicti['handle'] + character
                tags[tag_nums] = dicti
            else:
                tag_notation -= 1
                tag_nums += 1
    # Modify handle
    for tag in tags:
        tag['handle'] = tag['handle'][1:]

    for tag_idx in range(len(tags)):
        tag = tags[tag_idx]
        if len(tag['handle']) == 0:
            # print("invalid")
            invalid_copy = tag
            invalid.append(
                invalid_copy
            )
        for character in tag['handle']:
            if character.isalnum() is False:
                invalid_copy = tag
                invalid.append(
                    invalid_copy
                )
                break
    i = 0
    while i < len(tags):
        tag = tags[i]
        if tag in invalid:
            tags.remove(tag)
        else:
            i += 1
    return tags
