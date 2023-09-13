import random
import json
from datetime import datetime, timezone
from src.data import data
from src.error import AccessError, InputError, DuplicateError

def find(string_type, position, search_object):
    '''Description: Find user, channel, dm or message
    in respect to string_type and
    return index corresponding to the desired object.
    Return False if not found in the database.

    Parameters:
    * String_type is the exact type of the target object
    * Including: 'user', 'channel', 'message', 'dm', 'privacy',
    * 'channel_is_owner', 'channel_is_member',
    * 'dm_is_owner', 'dm_is_member'
    (we can modify string_type, for instance let u for user and c for channel etc)
    * Position MUST BE an valid index in database.
    * Search_object can be either a string or an integer
    '''
    return_v = -2
    # Position not given, search in db
    if not isinstance(position, int):
        if string_type == 'user':
            # if position not given, then search in database
            return_v = find_user(search_object, position, False)
        elif string_type == 'channel':
            # search for a channel in db
            return_v = find_channel(search_object, False)
        elif string_type == 'message':
            # find('message', None, mid)
            return_v = find_message(search_object)
        elif string_type == 'dm':
            return_v = find_dm(search_object)
        elif string_type == 'handle':
            return_v = find_handle(search_object)

    # If position is given, then search in a channel or dm
        # if position given and not_owner, then search in all_members
        # if position given and is_owner, then search in owner_members
    if string_type == 'channel_is_owner':
        return_v = find_user(search_object, position, True)
    elif string_type == 'channel_is_member':
        return_v = find_user(search_object, position, False)
    elif string_type == 'dm_is_owner':
        return_v = find_user_dm(search_object, position, True)
    elif string_type == 'dm_is_member':
        return_v = find_user_dm(search_object, position, False)
    elif string_type == 'session':
        return_v = find_session(search_object, position)

    return return_v

def find_handle(to_find_handle):
    '''Find index of user with handle(to_find_handle) in db

    Returns index of user if found, otherwise returns -1
    '''
    for user_idx in range(len(data['users'])):
        user = data['users'][user_idx]['public_info']
        handle = user['handle_str']
        if to_find_handle == handle:
            return user_idx

def find_session(to_search_session, user_position_in_db):
    '''Find index of session_id with given position of user(search_object)

    Returns index of session if found, otherwise returns -1
    '''
    user = data['users'][user_position_in_db]
    for session_idx in range(len(user['sessions'])):
        session = user['sessions'][session_idx]
        if to_search_session == session:
            return session_idx
    return -1

def find_user(search_object, data_channel_idx, is_owner):
    '''Find index of user with auth_user_id(search_object)
    in the database or in the channel - data['channels'][data_channel_idx]

    Returns index of user if found, otherwise returns -1
    '''
    searching_domain = []
    if data_channel_idx is None:
        searching_domain = data['users']
        for user_idx in range(len(searching_domain)):
            if search_object == searching_domain[user_idx]['public_info']['u_id']:
                if check_validity(user_idx) is False:
                    return -1
                return user_idx
        return -1
    else:
        if is_owner:
            searching_domain = data['channels'][data_channel_idx]['owner_members']
        else:
            searching_domain = data['channels'][data_channel_idx]['all_members']
    return_user_idx = 0
    for return_user_idx in range(len(searching_domain)):
        if search_object == searching_domain[return_user_idx]['u_id']:
            return return_user_idx
    return -1

def check_validity(user_position):
    '''Checks whether the user at user_position is valid or not.
    '''
    return data['users'][user_position]['is_valid']

def find_user_dm(search_object, data_dm_idx, is_owner):
    '''Find user index corresponding to given search_object.

    Returns index of user if found, otherwise returns -1
    '''
    operator = data['dms'][data_dm_idx]

    member_list = []
    if is_owner:
        member_list = operator['owner_members']
    else:
        member_list = operator['all_members']

    for member_idx in range(len(member_list)):
        if search_object == member_list[member_idx]['u_id']:
            return member_idx

    return -1

def find_channel(channel_id, is_public):
    '''Find channel corresponding to given channel_id.

    Returns index of channel if found, otherwise returns -1
    '''
    return_channel_idx = -1
    for channel_idx in range(len(data['channels'])):
        if channel_id == data['channels'][channel_idx]['channel_id']:
            # print("Found")
            return_channel_idx = channel_idx
            break
    if is_public and return_channel_idx != -1:
        # in this case it's channel_idX
        channel = data['channels'][return_channel_idx]
        # Is public
        return channel['is_public']

    return return_channel_idx

def find_dm(dm_id):
    '''Find dm corresponding to given dm_id.

    Returns index of dm if found, otherwise returns -1
    '''
    for dm_idx in range(len(data['dms'])):
        dmi = data['dms'][dm_idx]
        if dm_id == dmi['dm_id']:
            return dm_idx
    return -1

def find_message(message_id):
    '''Find the position of a message in the msg_position list]
    as well as its position in the channel.

    Returns the idx of msg in org and msg_p,
    exact org,
    msg_po_idx for data['msg_positions'][msg_po_idx]
    '''
    # Find which org this msg belongs to
    for po_idx in range(len(data['msg_positions'])):
        msg_po_idx = data['msg_positions'][po_idx]
        # Found org, find msg_idx
        for msg_idx in range(len(msg_po_idx['message_ids'])):
            # Found position index of msg in org
            if message_id == msg_po_idx['message_ids'][msg_idx]:
                org_id = msg_po_idx['id']
                # print(f"Found msg in position db. {msg_po_idx}")
                if msg_po_idx['type'] == 'channel':
                    # print("Finding msg in a channel")
                    operating_position_in_db = find('channel', None, org_id)
                    operation = data['channels'][operating_position_in_db]
                elif msg_po_idx['type'] == 'dm':
                    # print("Finding msg in a dm")
                    operating_position_in_db = find('dm', None, org_id)
                    operation = data['dms'][operating_position_in_db]
                return msg_idx, operation, msg_po_idx
    return -1

def update_user_stats(ids, org_type, is_add):
    '''Update statistics for an individual user.

    Parameters:
    * ids is a list of users who require their stats to be updated.
    * org_type is one string out of the three: 'channels' or 'dms' or 'messages'.
    * is_add is a bool type value.
    '''
    current_time = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    if org_type == 'messages':
        key_a = org_type +'_sent'
    else:
        key_a = org_type + '_joined'
    key_b = 'num_' + key_a
    for auth_user_id in ids:
        user_idx = find('user', None, auth_user_id)
        this_user = data['users'][user_idx]
        curr_num = this_user['stats'][key_a][-1][key_b]
        if is_add:
            curr_org_joined = {key_b: curr_num + 1, 'time_stamp': current_time}
        else:
            curr_org_joined = {key_b: curr_num - 1, 'time_stamp': current_time}
        this_user['stats'][key_a].append(curr_org_joined)

def update_users_stats(org_type, is_add):
    '''Update statistics for the dream system.

    Parameters:
    * org_type is one string out of the three: 'channels' or 'dms' or 'messages'.
    * is_add is a bool indicating whether a channel or dm or message is added or removed.
    '''
    current_time = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    key_a = org_type + '_exist'
    key_b = 'num_' + key_a
    if is_add:
        curr_orgs_exist = {key_b: (data['dreams_stats'][key_a][-1][key_b] + 1),
                           'time_stamp': current_time,
                           }
    else:
        curr_orgs_exist = {key_b: (data['dreams_stats'][key_a][-1][key_b] - 1),
                           'time_stamp': current_time,
                           }
    data['dreams_stats'][key_a].append(curr_orgs_exist)

def pack(type_string, pack_object, return_dict):
    '''Pack type_string into a dictionary in respect of pack_object.

    String_type is the exact type of the target object
    (we can modify string_type, for instance let u for user and c for channel etc)
    Pack_object should be an int if packing for info of a channel
    '''
    if type_string == 'name':
        return_dict[type_string] = data['channels'][pack_object]['channel_name']
    if type_string == 'channel_id':
        return_dict[type_string] = data['channels'][pack_object]['channel_id']

    return return_dict

def error_check(error_type, domain, check_objects):
    '''Check whether the operation with check_object requires an exception or not.

    Error_type is the exact error.
    (we can modify string_type, for instance let u for user and c for channel etc)
    Check_object should be an int if an _id is passed in, or other scenarios
    that haven't been covered yet.

    * raises an AccessError if check_object is type _id and check_object is not in domain
    '''
    if error_type == AccessError:
        if domain == 'db_user':
            found_auth_user_id = find('user', None, check_objects[0])
            if found_auth_user_id < 0:
                raise AccessError(description = f"Invalid auth_user_id {check_objects[0]}")
            found_session = find('session', found_auth_user_id, check_objects[1])
            if found_session < 0:
                raise AccessError(description = f"Invalid session with session_id {check_objects[1]}")
        elif domain == 'message_auth':
            is_sender       = False
            is_authorised   = False
            results = find('message', None, check_objects[0])
            operating_org = results[1]
            actual_msg = operating_org['messages'][results[0]]
            u_id = check_objects[1]
            if u_id == actual_msg['u_id']:
                is_sender = True
            for owners in operating_org['owner_members']:
                if u_id == owners['u_id']:
                    is_authorised = True
                    break
            if is_sender is False and is_authorised is False:
                dis_p = data['users'][find('user', None, u_id)]
                raise AccessError(description =
                    f"The user attempting to edit this message has no authorisation."\
                    f"auth_id: {dis_p}, owner_members: {operating_org['owner_members']}"
                )
        elif domain == 'owner':
            member_idx = 0
            is_owner = False
            while member_idx < len(check_objects[1]['owner_members']):
                if check_objects[0] == check_objects[1]['owner_members'][member_idx]['u_id']:
                    is_owner = True
                member_idx += 1
            if is_owner is False:
                raise AccessError(f"User with id is not an owner")
        elif isinstance(domain, int):
            # find_result = find('user', domain, check_object)
            find_result = find_user(check_objects[0], domain, False)
            if find_result < 0:
                raise AccessError(description = f"Invalid auth_user_id {check_objects[0]} not in domain {domain}")
    if error_type == InputError:
        if domain == 'db_channel':
            find_result = find('channel', None, check_objects[0])
            # print(f"Result found for finding channel with {check_objects[0]} is {find_result}")
            if find_result < 0:
                raise InputError(description = f"Invalid channel_id {check_objects[0]}")
        if domain == 'db_user':
            find_result = find('user', None, check_objects[0])
            if find_result < 0:
                raise InputError(description = f"Invalid auth_user_id {check_objects[0]}")
        if domain == 'db_dm':
            find_result = find('dm', None, check_objects[0])
            if find_result < 0:
                raise InputError(description = f"Invalid dm_id {check_objects[0]}")
        if domain == 'message':
            find_result = find('message', None, check_objects[0])
            if find_result == -1:
                raise InputError(f"Message with id {check_objects[0]} does not exist.")
        if domain == 'check_pin':
            if check_objects[0]['messages'][check_objects[1]]['is_pinned'] is True:
                raise InputError(f"Message with ID {check_objects[1]} is already pinned")
        if domain == 'check_unpin':
            if check_objects[0]['messages'][check_objects[1]]['is_pinned'] is False:
                raise InputError(f"Message with ID {check_objects[1]} is not pinned")
        if domain == 'time':
            if check_objects[0] < 0:
                raise InputError("Time given is in the past")
        if domain == 'message_length':
            if check_objects[0] > 1000:
                raise InputError("Input message too long")

        # leave this part for now
        # this checks whether user is in dm or not
        # for the moment contradicts with the code from 142~146 so put it
        # under input error
        if isinstance(domain, int):
            dm_idx = find_dm(domain)
            find_result = find_user_dm(check_objects[0], dm_idx, False)
            if find_result == -1:
                raise AccessError(description = f"User with {check_objects[0]} not in dm {domain}")
    if error_type == DuplicateError:
        if check_objects[1] == 'channel':
            find_result = find('channel_is_member', domain, check_objects[0])
            if find_result >= 0:
                return -3
        else:
            find_result = find('dm_is_member', domain, check_objects[0])
            if find_result >= 0:
                return -3

def randomise(type_string):
    '''Description: randomise an id corresponding to the type described by the string.

    Type_string is a string that follows one of the following:
        - 'user_id' or 'channel_id' or 'message_id'.
    (we can modify string_type, for instance let u for user and c for channel etc)
    Returns this id.
    '''
    if type_string == 'user_id':
        uid = random.randint(1000000, 9999999)
        if len(data['users']) >= 9000000:
            raise InputError("Too many users.")
        while find('user', None, uid) != -1:
            uid = random.randint(1000000, 9999999)
        return uid
    if type_string == 'channel_id':
        cid = random.randint(1000000, 9999999)
        if len(data['channels']) >= 9000000:
            raise InputError("Too many channels.")
        while find('channel', None, cid) != -1:
            cid = random.randint(1000000, 9999999)
        return cid
    if type_string == 'dm_id':
        dmid = random.randint(1000000, 9999999)
        if len(data['dms']) >= 9000000:
            raise InputError("Too many dms.")
        while find('dm', None, dmid) != -1:
            dmid = random.randint(1000000, 9999999)
        return dmid
    if type_string == 'message_id':
        mid = random.randint(10000000, 99999999)
        while find('message', None, mid) != -1:
            mid = random.randint(10000000, 99999999)
        return mid
    raise InputError("Wrong input string.")

def send_notification(user_ids, notification_message, trigger_type, place):
    '''Description: Send the notification to the user with user_id
    '''
    tagged_user_id = user_ids[0]

    tager_id = user_ids[1]
    tager_position = find('user', None, tager_id)
    tager = data['users'][tager_position]['public_info']

    place_type = place[0]
    place_id = place[1]

    key = place_type + '_name'
    place_name = data[place_type + 's'][find(place_type, None, place_id)][key]

    if trigger_type == 'tagged':
        tag_msg = notification_message[0:19]
        to_notify_message = f"{tager['handle_str']} tagged you in {place_name}: {tag_msg}"
    else:
        to_notify_message = f"{tager['handle_str']} added you to {place_name}"

    tagged_user = insert_message('notification', tagged_user_id, to_notify_message)
    if place_type == 'channel':
        tagged_user['notifications'][0]['dm_id'] = -1
    else:
        tagged_user['notifications'][0]['channel_id'] = -1
    tagged_user['notifications'][0][place_type + '_id'] = place_id

def insert_message(org_type, org_id, to_insert_message):
    '''Description: Insert the message string into the target position

    org_type is a string that follows one of the following:
        - 'channel' or 'dm' or 'notification'.

    if notification, org_id = auth_user_id
    otherwise org_id = id not idx

    Returns this id if not notification.
    No reaction if notification.
    '''
    if org_type == 'notification':
        user_idx = find('user', None, org_id)
        user = data['users'][user_idx]
        notification = {
            'notification_message': to_insert_message,
        }
        user['notifications'].insert(0, notification)
        return user

    if len(to_insert_message['message']) == 0:
        return
    doc_idx = 0
    while doc_idx < len(data['msg_positions']):
        doc = data['msg_positions'][doc_idx]
        if doc['type'] == org_type:
            if org_id == doc['id']:
                doc['message_ids'].insert(0, to_insert_message['message_id'])
                break
        doc_idx += 1
    if doc_idx == len(data['msg_positions']):
        data['msg_positions'].append(
            {
                'message_ids'   : [
                    to_insert_message['message_id'],
                ],
                'type'          : org_type,
                'id'            : org_id,
            },
        )
    # print(f"Msg insert called. MSG_POSITION DATA is now:\n{data['msg_positions']}")
    # print(f"Sending in type {org_type} with id {org_id} with msg {to_insert_message}")
    org_position_in_db = find(org_type, None, org_id)
    org = data[org_type + 's'][org_position_in_db]
    org['messages'].insert(0, to_insert_message)

# Function that dumps the current state of data into the file json file
# backup.json.
def data_dump():
    with open('src/backup.json', 'w') as file:
        file.write(json.dumps(data))

# Function that loads data into the server.
def data_load():
    with open('src/backup.json', 'r') as file:
        data_backup = json.loads(file.read())
        data['users'] = data_backup['users']
        data['channels'] = data_backup['channels']
        data['dms'] = data_backup['dms']
        data['msg_positions'] = data_backup['msg_positions']
        data['dreams_stats'] = data_backup['dreams_stats']
