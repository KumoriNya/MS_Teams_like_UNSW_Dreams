from src.data import data
from src.error import InputError, AccessError
from src.auth import detokenise
from src.helpers import find, error_check, data_dump, update_user_stats
def admin_userpermission_change_v1(token, u_id, p_id):
    '''
    Description:
        Given a User by their user ID, set their permissions to new
        permissions described by permission_id.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - u_id            (type_int): An integer representing the id of a user.
        - p_id            (type_int): An integer indicating the level of permission given to a user.
                                      (1 refering to Dreams owner, 2 refering to Dreams member)

    Exceptions:
        InputError Occurs when:
            * u_id does not refer to a valid user.
            * permission_id does not refer to a valid permission value.
        AccessError Occurs when:
            * token is invalid.
            * the authorised user is not an owner.

    Return Value:
        Returns {  } on condition of:
            + u_id refers to a valid user.
            + permission_id refers to a valid permisssion value
            + token is valid
            + the authorised user is an owner.
    '''

    # AccessError: invalid token
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    auth_position = find('user', None, auth_user_id)
    auth_user = data['users'][auth_position]
    if auth_user['permission_id'] != 1:
        raise AccessError(f"User with id {auth_user_id} has no permission access this function.")

    error_check(InputError, 'db_user', [u_id])
    user_position = find('user', None, u_id)
    user = data['users'][user_position]

    if p_id not in [1, 2]:
        raise InputError(f"Invalid input permission_id {p_id}, must be 1 or 2.")
    user['permission_id'] = p_id

    if p_id == 1:
        cnl_idx = 0
        while cnl_idx < len(data['channels']):
            user_in_cnl = find('channel_is_member', cnl_idx, u_id)
            if user_in_cnl > -1:
                cnl = data['channels'][cnl_idx]
                info = cnl['all_members'][user_in_cnl]
                user_an_owner = find('channel_is_owner', cnl_idx, u_id)
                if user_an_owner < 0:
                    cnl['owner_members'].append(info)
            cnl_idx += 1

    data_dump()
    return {}

def admin_user_remove_v1(token, u_id):
    '''
    Description:
        Given a User by their user ID, remove the user from the Dreams. Dreams owners
        can remove other **Dreams** owners (including the original first owner). Once
        users are removed from **Dreams**, the contents of the messages they sent
        will be replaced by 'Removed user'. Their profile must still be retrievable
        with user/profile/v2, with their name replaced by 'Removed user'.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - u_id            (type_int): An integer representing the id of a user.

    Exceptions:
        InputError Occurs when:
            * u_id does not refer to a valid user.
            * u_id is the last user with p_id == 1.
        AccessError Occurs when:
            * token is invalid.
            * the authorised user is not an owner.

    Execution:
            Check for exceptions
            Valid -
            Replace all message sent by this user with 'Removed user'
                Go to orgs with messages via msg_positions
            Leave all the orgs this user is a part of.
            Change validity.
            return

    Return Value:
        Returns {  } on condition of:
            + u_id refers to a valid user.
            + u_id is not the last user with p_id == 1.
            + token is valid
            + the authorised user is an owner.
    '''

    # AccessError: invalid token
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    auth_position = find('user', None, auth_user_id)
    auth_user = data['users'][auth_position]
    if auth_user['permission_id'] != 1:
        raise AccessError(f"User with id {auth_user_id} has no permission access this function.")

    error_check(InputError, 'db_user', [u_id])
    user_position = find('user', None, u_id)
    user = data['users'][user_position]

    count = 0
    for user_db in data['users']:
        if user_db['permission_id'] == 1:
            count += 1
            # Not necessary to loop through the whole user database.
            if count > 1:
                break
    if count == 1 and user['permission_id'] == 1:
        raise InputError(f"User with id {u_id} is the last admin, cannot execute remove.")

    # Finding all messages then edit the info of those messages sent by the to-be removed user.
    orgs_with_msg_list = []
    for msg_position_info in data['msg_positions']:
        this_org_with_msg_position = find(msg_position_info['type'], None, msg_position_info['id'])
        this_org = data[msg_position_info['type'] + 's'][this_org_with_msg_position]
        orgs_with_msg_list.append(this_org)
    for org in orgs_with_msg_list:
        for msg in org['messages']:
            if msg['u_id'] == u_id:
                msg['message'] = 'Removed user'

    # Removing user from all orgs taking this user as a member.
    org_type = ['channel', 'dm']
    count = 0
    while count < len(org_type):
        for org in data[org_type[count] + 's']:
            for member in org['all_members']:
                if u_id == member['u_id']:
                    org['all_members'].remove(member)
                    for owner in org['owner_members']:
                        if u_id == owner['u_id']:
                            org['owner_members'].remove(owner)
                    update_user_stats([auth_user_id], org_type[count] + 's', False)
        count += 1

    user['is_valid'] = False
    user['public_info']['name_first'] = 'Removed'
    user['public_info']['name_last'] = 'user'

    data_dump()
    return {}
