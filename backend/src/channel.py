from src.data       import data
from src.error      import AccessError, InputError, DuplicateError
from src.helpers    import find, error_check, send_notification, data_dump, update_user_stats
from src.auth       import detokenise

def channel_invite_v2(token, channel_id, u_id):
    '''
    Description:
        Invites a user (with user id u_id) to join a channel with ID channel_id.
        Once invited the user is added to the channel immediately.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.'
        - u_id        (type integer): An integer refering to a user's id in the database.

    Exceptions:
        InputError Occurs when:
            * channel_id is invalid.
            * u_id is invalid.
        AccessError Occurs when:
            * invalid token.
            * the authorised user is not a member of the channel.

    Return Value:
        Returns { } on condition of:
            + Channel_id is valid.
            + none of the exception are raised.
            + token is valid.
            + user being invited is not already in the channel.
    '''


    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # InputError: invalid channel_id
    error_check(InputError, 'db_channel', [channel_id])
    operating_channel_position_in_db = find('channel', None, channel_id)

    # AccessError: authorised user with auth_user_id does not belong to the channel with channel_id
    error_check(AccessError, operating_channel_position_in_db, [auth_user_id])

    # InputError: invalid u_id
    error_check(InputError, 'db_user', [u_id])
    invited_user_position_in_db = find('user', None, u_id)

    # Duplicate?
    is_dup = error_check(DuplicateError, operating_channel_position_in_db, [u_id, 'channel'])
    if is_dup == -3:
        return {}

    # Add user to the channel all_members
    operating_channel = data['channels'][operating_channel_position_in_db]
    invited_user = data['users'][invited_user_position_in_db]
    operating_channel['all_members'].append(
        invited_user['public_info']
    )
    # Admin
    if invited_user['permission_id'] == 1:
        operating_channel['owner_members'].append(
            invited_user['public_info']
        )

    send_notification([u_id, auth_user_id], None, 'invite', ['channel', channel_id])
    update_user_stats([u_id], 'channels', True)
    data_dump()

    return {}

def channel_join_v2(token, channel_id):
    '''
    Description:
        Given a channel_id of a channel that the authorised user
        can join, adds them to that channel.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.

    Exceptions:
        InputError Occurs when:
            * channel_id does not refer to a valid channel.
        AccessError Occurs when:
            * invalid token.
            * the channel_id refers to a channel that is private
              (when the authorised user is not a global owner).

    Return Value:
        Returns { } on condition of:
            + channel_id is valid.
            + token is valid.
            + user is a dream admin/owner if they are joining a private channel.
    '''


    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    user_position_in_db = find('user', None, auth_user_id)
    user = data['users'][user_position_in_db]

    # InputError: invalid channel_id
    error_check(InputError, 'db_channel', [channel_id])
    operating_channel_position_in_db = find('channel', None, channel_id)
    this_channel = data['channels'][operating_channel_position_in_db]

    if this_channel['is_public'] is False:
        # If admin, append
        if user['permission_id'] == 1:
            this_channel['owner_members'].append(
                user['public_info']
            )
            this_channel['all_members'].append(
                user['public_info']
            )
            return {}
        raise AccessError(f'User with auth_user_id {auth_user_id} \
            is not an admin is trying to join a private channel.')
        # If not admin, error

    is_dup = error_check(
        DuplicateError, operating_channel_position_in_db, [auth_user_id, 'channel']
    )
    if is_dup == -3:
        return {}
    this_channel['all_members'].append(
        user['public_info']
    )
    if user['permission_id'] == 1:
        this_channel['owner_members'].append(
            user['public_info']
        )
    update_user_stats([auth_user_id], 'channels', True)
    data_dump()

    return {}

def channel_details_v2(token, channel_id):
    '''
    Description:
        Given a Channel with ID channel_id that the authorised user is part of,
        provide basic details about the channel.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.

    Exceptions:
        InputError Occurs when:
            * channel_id does not refer to a valid channel.
        AccessError Occurs when:
            * the authorised user is not a member of channel with channel_id
            * the authorised user does not exist in the database.

    Return Value:
        Returns { 'name', 'is_public', 'owner_members', 'all_members' } on condition of:
            + channel_id is valid.
            + token is valid.
            + authorised user is a member of the channel.

        - 'name'        (type string): Is the name of the channel.
        - 'is_public   (type boolean): Is a boolean which describes if a channel is public or
                                       private.
        - 'owner_members' (type list): Is a list containing dictionaries of owner users in 
                                       the channel.
        - 'all_members'   (type list): Is a list containing dictionaries of all users in
                                       the channel.
    '''


    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    # InputError: invalid channel_id
    error_check(InputError, 'db_channel', [channel_id])
    operating_channel_position_in_db = find('channel', None, channel_id)
    this_channel = data['channels'][operating_channel_position_in_db]
    # AccessError: authorised user with auth_user_id does not belong to the channel with channel_id
    error_check(AccessError, operating_channel_position_in_db, [auth_user_id])

    detail_list = {
        'name'          : this_channel['channel_name'],
        'is_public'     : this_channel['is_public'],
        'owner_members' : [],
        'all_members'   : [],
    }

    for owner_m in this_channel['owner_members']:
        detail_list['owner_members'].append(owner_m)
    for all_m in this_channel['all_members']:
        detail_list['all_members'].append(all_m)
    return detail_list

def channel_messages_v2(token, channel_id, start):
    '''
    Description:
        Given a Channel with ID channel_id that the authorised user is part of,
        return up to 50 messages between index "start" and "start + 50".
        Message with index 0 is the most recent message in the channel.
        This function returns a new index "end" which is the value of "start + 50",
        or, if this function has returned the least recent messages in the channel,
        returns -1 in "end" to indicate there are no more messages to load after this return.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id (type integer): An integer refering to a channel's id in the database.
        - start      (type integer): An integer as an index for the starting position of messages.

    Exceptions:
        InputError Occurs when:
            * channel_id is not a valid channel
            * start is greater than the total number of messages in the channel
        AccessError Occurs when:
            * authorised user is not a member of channel with channel_id
            * the authorised user does not exist in the database.

    Return Value:
        Returns { 'messages', 'start', 'end' } on condition of:
            + channel_id is valid.
            + start is less than or equal to the total number of messages in channel.
            + authorised user is a member of the channel.
            + the authorised user exists in the database.


        - 'messages' (type dictionary): contains a list of dictionary message,
        - 'start'       (type integer): An integer as an index for the starting position of messages.
        - 'end'        (type interger): An interger as an index for the ending position of messages.
    '''


    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Check if the channel_id is valid
    error_check(InputError, 'db_channel', [channel_id])
    operating_channel_position_in_db = find('channel', None, channel_id)
    messages_of_this_channel = data['channels'][operating_channel_position_in_db]['messages']

    # AccessError: authorised user with auth_user_id does not belong to the channel with channel_id
    error_check(AccessError, operating_channel_position_in_db, [auth_user_id])

    # Check if start is in the range of total number of messages.
    if start > len(messages_of_this_channel):
        raise InputError('Start is greater than the total number of messages in the channel')
    if start + 50 > len(messages_of_this_channel):
        end = -1
    else:
        end = start + 50

    messages_list = {
        'messages': [],
        'start': start,
        'end': end,
    }
    message_idx = start
    # Add messages into messages_list
    if end > 0:
        while message_idx < len(messages_of_this_channel) and message_idx < end:
            message = messages_of_this_channel[message_idx]
            output_reacts = message['reacts']
            if auth_user_id in output_reacts[0]['u_ids']:
                output_reacts[0]['is_this_user_reacted'] = True
            else:
                output_reacts[0]['is_this_user_reacted'] = False
            messages_list['messages'].append({
                'message_id': message['message_id'],
                'u_id': message['u_id'],
                'message': message['message'],
                'time_created': message['time_created'],
                'is_pinned': message['is_pinned'],
                'reacts': output_reacts,
            })
            message_idx += 1
    else:
        while message_idx < len(messages_of_this_channel):
            message = messages_of_this_channel[message_idx]
            output_reacts = message['reacts']
            if auth_user_id in output_reacts[0]['u_ids']:
                output_reacts[0]['is_this_user_reacted'] = True
            else:
                output_reacts[0]['is_this_user_reacted'] = False
            messages_list['messages'].append({
                'message_id': message['message_id'],
                'u_id': message['u_id'],
                'message': message['message'],
                'time_created': message['time_created'],
                'is_pinned': message['is_pinned'],
                'reacts': output_reacts,
            })
            message_idx += 1
    return messages_list

def channel_leave_v1(token, channel_id):
    '''
    Description:
        Given a channel_id of a channel that takes authorised user as a member.
        Remove user from this channel.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id (type integer): An integer refering to a channel's id in the database.

    Exceptions:
        AccessError Occurs when:
        - invalid token.
        - the authorised user does not exist in the channel.
        InputError Occurs when:
        - channel_id does not refer to a valid channel.

    Return Value:
        Returns an { } on condition of:
            + token is valid.
            + authorised user exists in the channel.
            + channel_id is valid.
    '''

    org_type = 'channel'
    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # InputError: invalid channel_id
    error_check(InputError, 'db_channel', [channel_id])
    org_position = find(org_type, None, channel_id)

    # AccessError: user not in org
    error_check(AccessError, org_position, [auth_user_id])

    org = data[org_type + 's'][org_position]
    for all_member in org['all_members']:
        if all_member['u_id'] == auth_user_id:
            org['all_members'].remove(all_member)
    for owner_member in org['owner_members']:
        if owner_member['u_id'] == auth_user_id:
            org['owner_members'].remove(owner_member)
    update_user_stats([auth_user_id], 'channels', False)
    data_dump()

    return {
    }

def channel_addowner_v1(token, channel_id, u_id):
    '''
    Description:
        Given a channel_id of a channel that takes user with u_id as a member.
        Make user with user id u_id an owner of this channel

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - channel_id (type integer): An integer refering to a channel's id in the database.
        - u_id           (type_int): An integer representing the id of a user.

    Exceptions:
        AccessError Occurs when:
            * invalid token.
            * the authorised user is not an owner nor an admin.
        InputError Occurs when:
            * u_id corresponding user not exist.
            * channel_id does not refer to a valid channel.
            * u_id corresponding user is an owner of the channel.

    Return Value:
        Returns an empty list when:
            + token is valid.
            + authorised user is an owner or admin of the channel.
            + u_id corresponds to a valid user.
            + channel_id is valid.
            + u_id is not an owner of the channel.
    '''


    org_type = 'channel'
    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # InputError: invalid channel_id
    error_check(InputError, 'db_channel', [channel_id])
    org_position = find(org_type, None, channel_id)
    org = data[org_type + 's'][org_position]

    # AccessError: caller no permission
    caller_position = find('user', None, auth_user_id)
    caller = data['users'][caller_position]
    if (find('channel_is_owner', org_position, auth_user_id) < 0) and caller['permission_id'] != 1:
        raise AccessError(f"Caller whose id is {auth_user_id} \
            has no permission to access this function.")

    # InputError: user not exist
    if find('user', None, u_id) < 0:
        raise InputError(f"User whose id is {u_id} does not exist.")

    # InputError: user already an owner
    if find('channel_is_owner', org_position, u_id) >= 0:
        raise InputError(f"User whose id is {u_id} is already an owner.")

    user = data['users'][find('user', None, u_id)]

    if find('channel_is_member', org_position, u_id) < 0:
        org['all_members'].append(user['public_info'])
        org['owner_members'].append(user['public_info'])
        send_notification([u_id, auth_user_id], None, 'invite', ['channel', channel_id])
        update_user_stats([u_id], 'channels', True)
    else:
        org['owner_members'].append(user['public_info'])
    data_dump()

    return {
    }

def channel_removeowner_v1(token, channel_id, u_id):
    '''
    Description:
        Given a channel_id of a channel that takes user with u_id as an owner.
        Remove this user from the owner list.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - auth_user_id    (type_int): An integer indicating a user's ID.
        - session_id      (type_int): An integer indicating a user's session.
        - channel_id  (type integer): An integer refering to a channel's id in the database.
        - u_id            (type_int): An integer representing the id of a user.

    Exceptions:
        AccessError Occurs when:
            * invalid token.
            * the authorised user is not an owner nor an admin.
        InputError Occurs when:
            * channel_id does not refer to a valid channel.
            * u_id corresponding user not exist.
            * u_id corresponding user is not an owner of the channel.
            * the user is the only owner.

    Return Value:
        Returns { } on condition of:
            + token is valid.
            + the authorised user is an owner or admin of the channel.
            + channel_id is valid.
            + u_id exists in the database.
            + u_id is an owner of the channel.
            + there is more than one owner in the channel.
    '''


    org_type = 'channel'
    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # InputError: invalid channel_id
    error_check(InputError, 'db_channel', [channel_id])
    org_position = find(org_type, None, channel_id)
    org = data[org_type + 's'][org_position]


    # AccessError: caller no permission
    caller_position = find('user', None, auth_user_id)
    caller = data['users'][caller_position]
    if (find('channel_is_owner', org_position, auth_user_id) < 0) and caller['permission_id'] != 1:
        raise AccessError(f"Caller whose id is {auth_user_id} \
            has no permission to access this function.")

    # InputError: user not exist
    if find('user', None, u_id) < 0:
        raise InputError(f"User whose id is {u_id} does not exist.")

    # InputError: user is not an owner
    if find('channel_is_owner', org_position, u_id) < 0:
        raise InputError(f"User whose id is {u_id} is not an owner.")

    # InputError: user is the only owner
    if find('channel_is_owner', org_position, u_id) >= 0 and len(org['owner_members']) == 1:
        raise InputError(f"User whose id is {u_id} is the only owner.")

    user = data['users'][find('user', None, u_id)]

    org['owner_members'].remove(user['public_info'])

    data_dump()

    return {
    }
