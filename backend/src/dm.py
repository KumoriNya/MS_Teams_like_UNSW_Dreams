from src.data import data
from src.error import AccessError, InputError, DuplicateError
from src.helpers import find, error_check, randomise, send_notification, data_dump, update_user_stats, update_users_stats
from src.auth import detokenise

def dm_create_v1(token, u_ids):
    ''' Description:
        Given a list of u_id and token, create a DM with creator token and
        members with users corresponding to u_ids.
        u_ids contains the user(s) that this DM is directed to, and will
        not include the creator. The creator is the owner of the DM.
        Name of DM should be automatically generated based on the user(s) that is in this dm.
        The name should be an alphabetically-sorted, comma-separated list of user handles.
        e.g. 'handle1, handle2, handle3'.

    Arguements:
        - token(type string)        :   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.
        - u_ids           : List of users that DM is directed to.

    Exceptions:
        AccessError Occurs when:
            - token is in valid.
        InputError Occurs when:
            - u_id does not refer to a valid user.

    Return Values:
        Returns { dm_id, dm_name } on condition of:
            - token exists in the database.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Initialise owner_members list containing the creator of the dm.
    owner_members = []

    # Initialise all_members list containing the creator of the dm.
    all_members = []

    # Initialise user handles list.
    handles_user = []

    # Check if auth_user_id is valid.

    # Check if u_id refers to a valid user.
    for u_id in u_ids:
        error_check(InputError, 'db_user', [u_id])

    # Create infomation in dm.
    auth_user_position_in_db = find('user', None, auth_user_id)
    user = data['users'][auth_user_position_in_db]['public_info']
    owner_members.append(
        user
    )
    all_members.append(
        user
    )

    handles_user.append(user['handle_str'])

    for u_id in u_ids:
        auth_user_position_in_db = find('user', None, u_id)
        user = data['users'][auth_user_position_in_db]['public_info']
        all_members.append(
            user
        )
        handles_user.append(user['handle_str'])

    handles_user.sort()
    name_dm = ', '.join(handles_user)

    dm_id = randomise('dm_id')
    data['dms'].append({
        'dm_id'    : dm_id,
        'dm_name'  : name_dm,
        'owner_members' : owner_members,
        'all_members'   : all_members,
        'messages'      : [],
    })

    print(f"In create, creating dm called by user with id {auth_user_id}")

    for u_id in u_ids:
        send_notification([u_id, auth_user_id], None, 'invite', ['dm', dm_id])
    # u_ids.append(auth_user_id)
    update_user_stats(u_ids, 'dms', True)
    update_user_stats([auth_user_id], 'dms', True)
    update_users_stats('dms', True)
    data_dump()

    return {
        'dm_id': dm_id,
        'dm_name': name_dm,
    }

def dm_list_v1(token):
    ''' Description:
        Returns the list of DMs that take the user as a member.

        Arguements:
        - token(type string)        :   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.

        Exceptions:
        AccessError Occurs when:
          - token is invalid.

        Return Value:
        Returns a dictionary containing keys: 'dms' when:
          - none of the exception are raised.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    print(f"In list, beginning, user is {auth_user_id}")
    # Initialise dm list containing the dms.
    dm_list = []

    # Go through dms to find user's dms.
    dm_idx = 0
    while dm_idx < len(data['dms']):
        find_result = find('dm_is_member', dm_idx, auth_user_id)
        if find_result not in [-1, -2]:
            dm_info = {
                'dm_id': data['dms'][dm_idx]['dm_id'],
                'name': data['dms'][dm_idx]['dm_name']
            }
            dm_list.append(dm_info)
        dm_idx += 1
    print(f"In list, finished. found_dm: {dm_list}")

    data_dump()

    return {
        'dms'   : dm_list,
    }

def dm_invite_v1(token, dm_id, u_id):
    ''' Description:
      Inviting a user to an existing dm

        Arguements:
        - token(type string)        :   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.
        - dm_id (type integer) :  An integer refering to a dm's id in the database.'
        - u_id  (type integer) :  An integer refering to a user's id in the database.

        Exceptions:
        AccessError Occurs when:
            - token is invalid.
            - token corresponding user is not a member of the dm.
        InputError Occurs when:
            - dm_id does not refer to an existing dm.
            - u_id does not refer to a valid user.

        Return Value:
        Returns an empty dictionary when:
        - none of the exception are raised
        and will append user refered to by u_id to the members' lists if
        - user being invited is not in the DM
    '''
    # AccessError: invalid token
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError , 'db_user' , [auth_user_id, session_id])

    # InputError: invalid dm_id.
    error_check(InputError  , 'db_dm'   , [dm_id])
    org_position = find('dm', None, dm_id)

    # AccessError: token corresponding user is not in the DM.
    error_check(InputError , dm_id, [auth_user_id])

    # InputError: invalid u_id.
    error_check(InputError  , 'db_user' , [u_id])
    invited_user_position_in_db = find('user', None, u_id)

    # Check if user is already in dm.
    is_dup = error_check(DuplicateError, org_position, [u_id, 'db'])
    if is_dup == -3:
        return {}

    # Add user to the dm all_members.
    invited_user = data['users'][invited_user_position_in_db]
    data['dms'][org_position]['all_members'].append(
        invited_user['public_info']
    )
    send_notification([u_id, auth_user_id], None, 'invite', ['dm', dm_id])

    update_user_stats([u_id], 'dms', True)
    data_dump()

    return {}

def dm_leave_v1(token, dm_id):
    ''' Description:
        Given a DM ID, the user is removed as a member of this DM.

        Arguements:
        - token (type string)       :   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.
        - dm_id(type integer)       : An integer refering to a DM's id in the database.

        Exceptions:
            AccessError Occurs when:
                - token is invalid.
                - token is not a member of DM with dm_id.
            InputError Occurs when:
                - dm_id does not refer to a valid DM.

        Return Values:
        Returns an empty dictionary when:
        - none of the exception are raised
    '''
    org_type = 'dm'
    # AccessError: invalid token
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError , 'db_user' , [auth_user_id, session_id])

    # InputError: invalid dm_id.
    error_check(InputError  , 'db_dm'   , [dm_id])
    org_position = find('dm', None, dm_id)

    # AccessError: token corresponding user is not in the DM.
    error_check(InputError , dm_id, [auth_user_id])

    org = data[org_type + 's'][org_position]
    # Get information of the member to leave.
    for all_member in org['all_members']:
        if all_member['u_id'] == auth_user_id:
            org['all_members'].remove(all_member)
    for owner_member in org['owner_members']:
        if owner_member['u_id'] == auth_user_id:
            org['owner_members'].remove(owner_member)
    print("dm leave called")
    update_user_stats([auth_user_id], 'dms', False)
    data_dump()

    return {}

def dm_details_v1(token, dm_id):
    ''' Description:
        Given a DM with ID dm_id that the authorised user is part of,
        provide basic details about the DM

        Arguements:
        - token(type string)        :   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.
        - dm_id (type integer) : An integer refering to a dm's id in the database.

        Exceptions:
        AccessError Occurs when:
            - token is invalid.
            - token refer to user is not a member of this DM with dm_id.
        InputError Occurs when:
            - DM ID is not a valid DM.

        Return Value:
        Returns a dictionary containing keys: { 'name', 'members' } when:
            - none of the exception are raised
        where:
            - 'name' (type list): is an alphabetically-sorted, comma-separated list of user handles,
            - 'members' (type list): is a list containing multiple dictionaries (type user),
            - user (type dictionary): is a dictionary containing keys:
            {'u_id', 'name_first', 'name_last', 'handle_str', 'email'} where:
                - 'u_id'       (type integer) : An integer refering to a user's id in the database.
                - 'name_first' (type string)  : A string describing the first name of the user.
                - 'name_last'  (type string)  : A string describing the last name of the user.
                - 'handle_str' (type string)  : A string obtained from the user's first name and
                                                last name and possibly with a suffix for
                                                differentiating users with the same names.
                - 'email'      (type integer) : A string specific to a user's email address.
    '''

    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])
    # InputError: invalid dm_id
    error_check(InputError, 'db_dm', [dm_id])
    operator_position = find('dm', None, dm_id)
    operator = data['dms'][operator_position]
    # AccessError: token corresponding user is not in the DM
    error_check(InputError, dm_id, [auth_user_id])

    # Initialise detail list containing the name and members of dm.
    detail_list = {
        'name'      : operator['dm_name'],
        'members'   : [],
    }

    for all_m in operator['all_members']:
        detail_list['members'].append(all_m)

    return detail_list

def dm_remove_v1(token, dm_id):
    ''' Description:
        Given a dm_id of a DM that takes authorised user as a member.
        Remove this dm.

        Arguements:
        - token(type string)        :   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id(type_int)    :   An integer indicating a user's ID.
            - session_id(type_int)      :   An integer indicating a user's session.
        - dm_id (type integer) : An integer refering to a dm's id in the database.

        Exceptions:
        AccessError Occurs when:
        - invalid token.
        - the authorised user is not the owner of the DM.
        InputError Occurs when:
        - dm_id does not refer to a valid DM.

        Return Value:
        Returns an empty dictionary when:
        - none of the exception are raised
    '''

    print(f"Data before remove: {data['dms']}, {data['msg_positions']}")
    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # InputError: invalid dm_id.
    error_check(InputError  , 'db_dm'   , [dm_id])
    org_position = find('dm', None, dm_id)

    if find('dm_is_owner', org_position, auth_user_id) < 0:
        raise AccessError(
            f"User with ID{auth_user_id} is not the creator of the DM with id {dm_id}"
        )

    to_remove_org = data['dms'][org_position]
    member_id_list = []
    for member in to_remove_org['all_members']:
        member_id_list.append(member['u_id'])
    data['dms'].remove(to_remove_org)

    for history in data['msg_positions']:
        if history['type'] == 'dm' and history['id'] == dm_id:
            data['msg_positions'].remove(history)
            update_users_stats('messages', False)

    update_user_stats(member_id_list, 'dms', False)
    update_users_stats('dms', False)
    data_dump()
    return {}

def dm_messages_v1(token, dm_id, start):
    ''' Description:
       Given a DM with ID dm_id that the authorised user is part of, 
       return up to 50 messages between index "start" and "start + 50". 
       Message with index 0 is the most recent message in the channel. 
       This function returns a new index "end" which is the value of "start + 50", 
       or, if this function has returned the least recent messages in the channel, 
       returns -1 in "end" to indicate there are no more messages to load after this return.

        Arguements:
        - token (JWTs encode data): A token refering to a user's id in the database.
        - dm_id (type integer): An integer refering to a dm's id in the database.
        - start (type integer): An integer as an index for the starting position of messages.

        Exceptions:
        AccessError Occurs when:
            - token refer to invlid user.
            - token refer to user is not a member of DM with dm_id
        InputError Occurs when:
            - DM ID is not a valid DM
            - start is greater than the total number of messages in the channel

        Return Value:
        Returns a dictionary containing keys: 'messages', 'start' and 'end' when:
        - none of the exception are raised
        where:
        - 'messages' (type dictionary): contains a list of dictionary message,
        - 'start' (type integer): An integer as an index for the starting position of messages.
        - 'end' (type interger): An interger as an index for the ending position of messages.
        - message (type dictionary): is a dictionary containing keys:
        { 'message_id', 'u_id', 'message', 'time_created' } where:
            - 'message_id'    (type integer)   : An integer identifying the identity of a message.
            - 'u_id'          (type integer)   : An integer refering to a the user who sent the message.
                                                and whose user's id in the database.
            - 'message'       (type string)    : A string of message.
            - 'time_created'  (type integer)   : An integer indicating
                                                 the time when the message is created.
    '''
    # AccessError: invalid token
    payload         = detokenise(token)
    auth_user_id    = payload['auth_user_id']
    session_id      = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # InputError: invalid dm_id.
    error_check(InputError  , 'db_dm'   , [dm_id])
    org_position = find('dm', None, dm_id)
    org = data['dms'][org_position]

    # AccessError: token corresponding user is not in the DM.
    error_check(InputError , dm_id, [auth_user_id])

    # Check if start is in the range of total number of messages.
    if start > len(org['messages']):
        raise InputError('Start is greater than the total number of messages in the dm')
    if start + 50 > len(org['messages']):
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
        while message_idx < len(org['messages']) and message_idx < end:
            message = org['messages'][message_idx]
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
        while message_idx < len(org['messages']):
            message = org['messages'][message_idx]
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
