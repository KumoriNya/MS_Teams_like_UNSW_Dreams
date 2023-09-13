import re
import urllib.request
from PIL import Image
from src.config import url
from src.data import data
from src.auth import detokenise
from src.error import AccessError, InputError
from src.helpers import find, error_check, data_dump

def user_profile_v2(token, u_id):
    '''
    Description:
        For a valid user, returns information about their user_id, email,
        first name, last name, and handle.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - u_id        (type int): An integer refering the the user's id in the database.

    Exceptions:
        AccessError occurs when:
            * auth_user_id doesnt exist in the database.
        InputError occurs when:
            * u_id does not refer to a valid user.

    Return Values:
       Returns { user } on condition of:
            + auth_user_id exists in the database.
            + u_id exists in the database

        - { user } (type dict): A dictionary containg a users u_id, email, first name,
                             last name and handle string.
    '''
    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check for AccessErrors
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Check for InputErrors
    searching_domain = data['users']
    user_idx = 0
    while user_idx < len(searching_domain):
        if searching_domain[user_idx]['auth_user_id'] == u_id:
            break
        user_idx += 1
    if user_idx == len(searching_domain):
        raise InputError(f'User with u_id {u_id} does not exist in database.')

    # Find the correct user
    target_user_pos = find_user_inc_invalid(u_id)
    target_user = data['users'][target_user_pos]
    # print(f"returning from user_profile {target_user['public_info']}")
    return {
        'user': target_user['public_info']
    }

def user_profile_setname_v2(token, name_first, name_last):
    '''
    Description:
        Update the authorised user's first and last name.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - name_first (type string): A string refering to the first name of a user.
        - name_last  (type string): A string refering to the last name of a user.

    Exceptions:
        AccessError occurs when:
          * auth_user_id doesnt exist in the database.
        InputError occurs when:
          * name_first is non-alphabetic and not between 1 - 50 characters
          * name_last is nonalphabetic and not between 1 - 50 characters

    Return Values:
       Returns {} on condition of:
            + auth_user_id exists in the database.
            + name_first is alphabetic and between 1 - 50 characters
            + name_last is alphabetic and between 1 - 50 characters
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check for AccessErrors
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Check for InputErrors
    names = [name_first, name_last]

    for name in names:
        if name_len_check(name) == False:
            raise InputError(f"{name} is too long.")
        if name_char_check(name) == False:
            raise InputError(f"{name} contains non-alphabetic characters")

    # Find the correct user
    target_user_pos = find('user', None, auth_user_id)
    target_user = data['users'][target_user_pos]['public_info']

    # Change the names given
    target_user['name_first'] = name_first
    target_user['name_last'] = name_last

    data_dump()

    return {}

def user_profile_setemail_v2(token, email):
    '''
    Description:
        Update the authorised user's email address.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - email      (type string): A string which refers to a users email.

    Exceptions:
        AccessError occurs when:
            * auth_user_id doesnt exist in the database.
        InputError occurs when:
            * email is in an invalid format or email is already registered

    Return Values:
       Returns {} on condition of:
            + auth_user_id exists in the database.
            + email is in a valid format and not already registered
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check for AccessErrors
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Check for InputErrors
    if check_email_format(email) == False:
        raise InputError("Incorrect email format")
    if check_email_existence(email) == True:
        raise InputError("Email already in use")

    # Find the correct user
    target_user_pos = find('user', None, auth_user_id)
    target_user = data['users'][target_user_pos]['public_info']

    # Change to email given
    target_user['email'] = email

    data_dump()

    return {}

def user_profile_sethandle_v1(token, handle_str):
    '''
    Description:
        Update the authorised user's handle (i.e. display name)

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.
        - handle_str (type string): A string which represents a users display name.

    Exceptions:
        AccessError occurs when:
            * auth_user_id doesnt exist in the database.
        InputError occurs when:
            * handle_str is not between 3 - 20 characters and is used by another user

    Return Values:
       Returns {} on condition of:
            + auth_user_id exists in the database.
            + handle_str is between 3 - 20 characters and not already in use
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check for AccessErrors
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Check for InputErrors
    if check_len_handle(handle_str) == False:
        raise InputError(f"{handle_str} is an invalid length")
    if check_dup_handle(handle_str) == False:
        raise InputError(f"{handle_str} is alreay being used")

    # Find the correct user
    target_user_pos = find('user', None, auth_user_id)
    target_user = data['users'][target_user_pos]['public_info']

    # Change to new handle string
    target_user['handle_str'] = handle_str

    data_dump()

    return {
    }

def users_all_v1(token):
    '''
    Description:
        Returns a list of all users and their associated details

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                auth_user_id and session_id.
            - auth_user_id    (type_int):   An integer indicating a user's ID.
            - session_id      (type_int):   An integer indicating a user's session.

    Exceptions:
        AccessError occurs when:
            * auth_user_id doesnt exist in the database.

    Return Values:
        Returns { users } on condition of:
            + auth_user_id exists in the database.

        - { user } (type dict): A dictionary containg a users u_id, email, first name,
                             last name and handle string.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check for AccessErrors
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # Intialise users list
    users = []

    # Create user profiles for all users.
    for user in data['users']:
        users.append(user_profile_v2(token, user['auth_user_id'])['user'])

    return { 'users' : users }

def user_profile_uploadphoto(token, img_url, x_start, y_start, x_end, y_end):
    '''
    Description:
        Given a URL of an image on the internet, crops the image within bounds
        (x_start, y_start) and (x_end, y_end). Position (0,0) is the top left.

    Arguements:
        - token        (type string):   A string to be detokenised which contains payload containing
                                        auth_user_id and session_id.
        - img_url      (type string):   A string containing the url to an image.
        - x_start         (type int):   An integer refering to the starting x position of an image.
        - y_start         (type int):   An integer refering to the starting y position of an image.
        - x_end           (type int):   An integer refering to the ending x position of an image.
        - y_end           (type int):   An integer refering to the ending y position of an image.

    Exceptions:
        AccessError occurs when:
            * Invalid token is passed.
        InputError occurs when:
            * img_url does not exist or returns an HTTP status other than 200.
            * Starting and ending positions are invalid for the image dimensions.
            * The image uploaded is not a jpg or jpeg.

    Return Values:
        Returns { } on condition of:
            + Token is valid.
            + img_url exists and returns an HTTP status of 200.
            + Starting and ending positions fit within the dimension of the image.
            + The image is a jpg or jpeg.
    '''

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']

    # Check for AccessError
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    # If the image is not a jpg or jpeg
    if img_url.endswith('.jpg') is False and img_url.endswith('.jpeg') is False:
        raise InputError(description = "Invalid image format.")

    # Storing image url.
    user = data['users'][find('user', None, auth_user_id)]
    user_name = user['public_info']['name_first'] + user['public_info']['name_last']
    pic_store_local = f"src/static/{user_name}_image.jpg"

    # Check if the url is valid.
    try:
        test = urllib.request.urlopen(img_url)
        if test.getcode() != 200:
            print(False)
    except ValueError as error:
        raise InputError from error

    urllib.request.urlretrieve(img_url, pic_store_local)
    # Check if image coords are non negative.
    if x_start < 0 or x_end < 0 or y_start < 0 or y_end < 0:
        raise InputError(description = "Invalid bounds: Bounds are negative.")

    # Cropping the photo in the right shape
    bounds = (x_start, y_start, x_end, y_end)

    new_width = x_end - x_start
    new_height = y_end - y_start

    photo = Image.open(pic_store_local)

    og_width, og_height = photo.size

    # Check if input coords are too far apart.
    if new_width > og_width or new_height > og_height:
        raise InputError(description = "Invalid bounds: Coords lie outside image bounds.")

    cropped = photo.crop(bounds)

    cropped.save(pic_store_local)

    # Find the correct user
    target_user_pos = find('user', None, auth_user_id)
    target_user = data['users'][target_user_pos]['public_info']

    # Saving the cropped image as the user profile.
    pic_store_local = f"static/{user_name}_image.jpg"
    target_user['profile_img_url'] = url + pic_store_local

    data_dump()

    return {}

def user_stats_v1(token):
    """
    Description:
        Given a token, fetch the required statistics about this user's use of UNSW Dreams.

    Arguments:
        - token        (type string):   A string to be detokenised which contains payload containing
                                        auth_user_id and session_id.

    Exceptions:
        AccessError occurs when:
            * Invalid token is passed.

    Return Values:
        Returns {
            'user_stats': {
                'channels_joined'   : [
                    {'num_channels_joined': , 'time_stamp': },
                    ...
                ],
                'dms_joined'        : [
                    {'num_dms_joined': , 'time_stamp': },
                    ...
                ],
                'messages_sent'     : [
                    {'num_messages_sent': , 'time_stamp': },
                    ...
                ],
                'involvement_rate'  : ,
            }
        } on condition of:
            + Token is valid.
        - channels_joined   (type list):    list of dictionaries which contains info about
                                        user's number of channels joined with unix timestamp.
        - dms_joined        (type list):    list of dictionaries which contains info about
                                        user's number of dms joined with unix timestamp.
        - messages_sent     (type list):    list of dictionaries which contains info about
                                        user's number of messages sent with unix timestamp.
        - involvement_rate  (type int):  involvement_rate of current dreams.
    """

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    # Check for AccessErrors
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    user_idx = find('user', None, auth_user_id)
    this_user = data['users'][user_idx]

    count_cnl   = this_user['stats']['channels_joined'][-1]['num_channels_joined']
    count_dm    = this_user['stats']['dms_joined'][-1]['num_dms_joined']
    count_msg   = this_user['stats']['messages_sent'][-1]['num_messages_sent']
    total_cnl   = data['dreams_stats']['channels_exist'][-1]['num_channels_exist']
    total_dm    = data['dreams_stats']['dms_exist'][-1]['num_dms_exist']
    total_msg   = data['dreams_stats']['messages_exist'][-1]['num_messages_exist']

    if total_cnl == 0 and total_dm == 0 and total_msg == 0:
        curr_involvement_rate = 0
    else:
        print(f"In user stats, total = {total_cnl+total_dm+total_msg}")
        curr_involvement_rate = (count_msg + count_dm + count_cnl) / (total_cnl + total_dm + total_msg)
    this_user['stats']['involvement_rate'] = curr_involvement_rate
    print(this_user['stats'])
    return {'user_stats': this_user['stats']}

def users_stats_v1(token):
    """
    Description:
        Given a token, fetch the required statistics about the use of UNSW Dreams.

    Arguments:
        - token        (type string):   A string to be detokenised which contains payload containing
                                        auth_user_id and session_id.

    Exceptions:
        AccessError occurs when:
            * Invalid token is passed.

    Return Values:
        Returns {
            'dreams_stats': {
                'channels_exist'   : [
                    {'num_channels_exist': , 'time_stamp': },
                    ...
                ],
                'dms_exist'        : [
                    {'num_dms_exist': , 'time_stamp': },
                    ...
                ],
                'messages_exist'     : [
                    {'num_messages_exist': , 'time_stamp': },
                    ...
                ],
                'utilization_rate'  : ,
            }
        } on condition of:
            + Token is valid.
        - channels_joined   (type list):    list of dictionaries which contains info about
                                        the system of dream's number of existing channels with unix timestamp.
        - dms_joined        (type list):    list of dictionaries which contains info about
                                        the system of dream's number of existing dms with unix timestamp.
        - messages_sent     (type list):    list of dictionaries which contains info about
                                        the system of dream's number of existing messages with unix timestamp.
        - involvement_rate  (type int):  involvement_rate of current dreams.
    """

    payload = detokenise(token)
    auth_user_id = payload['auth_user_id']
    session_id = payload['session_id']
    # Check for AccessErrors
    error_check(AccessError, 'db_user', [auth_user_id, session_id])

    active_users = 0
    all_users = 0
    for user in data['users']:
        # invalid == removed, hence not counting
        if user['is_valid'] is True:
            # valid, if this user is in any org, count this user
            # print(f"{user['public_info']['name_first']}")
            if user['stats']['channels_joined'][-1]['num_channels_joined'] > 0 or user['stats']['dms_joined'][-1]['num_dms_joined'] > 0:
                active_users += 1
                # print("active + 1")
            # counting valid user
            all_users += 1
        # invalid user info↓
        # else:
            # print(f"invalid user: {user['public_info']['name_first']}")

    if all_users > 0:
        utilization_rate = active_users / all_users
    else:
        utilization_rate = 0
    data['dreams_stats']['utilization_rate'] = utilization_rate
    return {'dreams_stats': data['dreams_stats']}

# ========== Helper Functions ==========

# Function that checks if the length of a string is between 1 - 50 characters.
def name_len_check(name):
    if len(name) >= 1 and len(name) <= 50:
        return True
    else:
        return False

# Function that check if a string contains only alphabetic characters.
def name_char_check(name):
    if name.isalpha() == True:
        return True
    else:
        return False

# Function that checks if an email is in the correct format.
def check_email_format(email):
    matched = re.search("^[a-zA-Z0-9]+[\\._]?[a-zA-Z0-9]+[@]\\w+[.]\\w{2,3}$", email)
    return True if matched else False

# Function that checks if an email already exists.
def check_email_existence(email):
    for user in data['users']:
        if user['public_info']['email'] == email:
            return True
    return False

# Function that checks if the handle string is too long.
def check_len_handle(handle_str):
    if len(handle_str) >= 3 and len(handle_str) <= 20:
        return True
    else:
        return False

# Function that checks if a handle string already exists.
def check_dup_handle(handle_str):
    for user in data['users']:
        if handle_str == user['public_info']['handle_str']:
            return False
    return True

# Function that searches for a user in the database including
# invalid users(removed users).
def find_user_inc_invalid(u_id):
    user_idx = 0
    users = data['users']
    for user in users:
        if u_id != user['auth_user_id']:
            user_idx += 1
        else:
            break
    return user_idx
            
