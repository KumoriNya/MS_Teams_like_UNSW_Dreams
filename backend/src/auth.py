# Imports
import re
import hashlib
import smtplib
import secrets
from datetime import datetime, timezone
from email.mime.text import MIMEText
import jwt
from src.config import url
from src.error import InputError, AccessError
from src.data import data
from src.helpers import find, randomise, error_check, data_dump, update_users_stats

SECRETKEY = "COMP1531"
re_codes = []


# Functions
def auth_login_v2(email, password):
    '''
    Description:
        Given a registered users' email and password,
        returns a valid token and their `auth_user_id` value.

    Arguements:
        - email       (type string): A string specific to a users email in the database.
        - password    (type string): A string specific to a users password in the database.

    Exceptions:
        InputError Occurs when:
            * Email entered is invalid.
            * Email entered doesnt exist in the database.
            * Password is not correct.

    Return Value:
        Returns { token, auth_user_id } on condition of:
            + Email is valid.
            + Email exists in database.
            + Password is correct.
        
        token    (type string): A string specific to a users session.

        auth_user_id(type int): An integer specific to a user stored in the database,
                                which allows for the use of certain commands.
    '''


    if check_email_format(email) == False:
        raise InputError("Incorrect email format")
    if check_email_existence(email) == False:
        print("Here is")
        raise InputError(description = "Email does not exist!!")
    user_pos = check_password(email, password)
    if user_pos == -1:
        raise InputError("Invalid password")

    user = data['users'][user_pos]
    if user['is_valid'] == False:
        raise AccessError("User removed")
    s_id = randomise('user_id')
    user['sessions'].append(s_id)
    token = tokenise(user['auth_user_id'], s_id)
    data_dump()

    return {
            'token': token,
            'auth_user_id': user['auth_user_id']
    }

def auth_register_v2(email, password, name_first, name_last):
    '''
    Description:
        Given a user's first and last name, email address, and password, create a
        new account for them and return a new `auth_user_id`. A handle is generated
        that is the concatenation of a lowercase-only first name and last name.
        If the concatenation is longer than 20 characters, it is cutoff at 20 characters.
        The handle will not include any whitespace or the '@' character.
        If the handle is already taken, append the concatenated names with the
        smallest number (starting at 0) that forms a new handle that isn't already taken.
        The addition of this final number may result in the handle exceeding the 20 character limit.

    Arguements:
        - email     (type string): A string specific to a users email in the database.
        - password  (type string): A string specific to a users password in the database.
        - name_first(type string): A string describing the first name of the user.
        - name_last (type string): A string describing the last name of the user.


    Exceptions:
        InputError Occurs when:
            * email entered is invalid.
            * email entered already exists in the database.
            * password is less than 6 characters long.
            * name_first is not between 1 and 50 characters inclusively in length.
            * name_last is not between 1 and 50 characters inclusively in length.

    Return Value:
        Returns { token, auth_user_id } on condition of:
            + email entered is valid.
            + email entered doesnt exist in the database.
            + password is more than or equal to 6 characters long.
            + name_first is between 1 and 50 characters inclusively in length.
            + name_last is between 1 and 50 characters inclusively in length.

        - token       (type string): A string specific to a users session.
        - auth_user_id   (type int): An integer specific to a user stored in the database,
                                     which allows for the use of certain commands.
    '''

    # Check for Input errors
    if check_email_format(email) is False:
        raise InputError(description = "Incorrect email format")
    if check_email_existence(email) is True:
        raise InputError("Email has been registered")
    if len(password) < 6:
        raise InputError("Password is too short")
    if len(name_first) > 50:
        # raise InputError(f"{name_first} is too long")
        raise InputError("First name is too long")
    if len(name_last) > 50:
        raise InputError("Last name is too long")
    if name_first.isalpha() is not True:
        raise InputError("First name contains non alphabetical characters")
    if name_last.isalpha() is not True:
        raise InputError("Last name contains non alphabetical characters")

    # Formating handle_str to have no spaces and be all lower case.
    handle_str = name_first.lower() + name_last.lower()
    handle_str.replace(" ", "")

    if len(handle_str) > 20:
        handle_str = handle_str[0: 20]

    repeat_idx = -1
    for user in data['users']:
        if handle_str == user['public_info']['handle_str']:
            repeat_idx += 1

    if repeat_idx != -1:
        suffix = str(repeat_idx)
        if len(handle_str) >= 20:
            handle_str = handle_str[0: 20 - len(suffix)] + suffix
        else:
            handle_str = handle_str + suffix

    # Determining the auth_user_id value.
    user_id = randomise('user_id')

    if data['users'] == []:
        p_id = 1    # give the first person the owner permission
    else:
        p_id = 2    # the rest are all regular users

    # Create dictionary of user's info and add to the database.
    s_list = [0] # a list which record each session of a same user
    current_time = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    users_info = {
        'password'      : hash(password),
        'auth_user_id'  : user_id,
        'sessions'      : s_list,
        'permission_id' : p_id,
        'notifications' : [],
        'is_valid'      : True,
        'reacted_msgs'  : [],
        'public_info'   : {
            'u_id'      : user_id,
            'name_first': name_first,
            'name_last' : name_last,
            'handle_str': handle_str,
            'email'     : email,
            'profile_img_url': url + 'static/default_image.jpg',
        },
        'stats': {
            'channels_joined'   : [{
                                    'num_channels_joined': 0,
                                    'time_stamp': current_time}],
            'dms_joined'        : [{
                                    'num_dms_joined': 0,
                                    'time_stamp': current_time}],
            'messages_sent'     : [{
                                    'num_messages_sent': 0,
                                    'time_stamp': current_time}],
            'involvement_rate'  : 0
        },
    }
    data['users'].append(users_info)
    # Find the new user's auth_user_id to return.
    data_dump()
    return {
                'token': tokenise(user_id, users_info['sessions'][0]),
                'auth_user_id': users_info['auth_user_id']
            }

def auth_logout_v1(token):
    '''
    Description:
        Given an active token, invalidates the token to log the user out.
        If a valid token is given, and the user is successfully logged out,
        it returns true, otherwise false.

    Arguements:
        - token    (type string): A string specific to a users session.

    Exceptions:
        AccessError occurs when:
            * token input is invalid.

    Return Values:
        Returns { is_sucess } on condition of:
            + Valid token input.

        - is_sucess (type boolean): A boolean which indicates if the user
                                    logged out sucessfully.
    '''

    decoded_token = detokenise(token)
    auth_user_id = decoded_token['auth_user_id']
    s_id = decoded_token['session_id']
    error_check(AccessError, 'db_user', [auth_user_id, s_id])

    user_pos = find('user', None, auth_user_id)
    user = data['users'][user_pos]
    print(f"User with id {auth_user_id} has session {s_id}")
    for session in user['sessions']:
        if s_id == session:
            print("Found")
            user['sessions'].remove(session)
    data_dump()

    return {'is_success': True}

def auth_passwordreset_request_v1(email):
    """
    Description:
        Given an email address, if the user is a registered user, sends them an email containing a specific secret code,
        that when entered in auth_passwordreset_reset,
        shows that the user trying to reset the password is the one who got sent this email.

    Arguments:
        - email    (type string): A string specific to a user's email.

    Exceptions:
        InputError occurs when:
            * email is invalid.

    Return Values:
        Returns {} on condition of:
            + Valid email input.
    """
    # user not found with this email
    use_found = False
    for user_data in data['users']:
        if user_data['public_info'].get('email') == email:
            use_found = True
            break
    if not use_found:
        raise InputError('Email not registered')

    re_code = secrets.token_hex(3)

    re_codes_data = {
        'email': email,
        're_code': re_code
    }

    new_code = {'re_code': secrets.token_hex(3)}
    re_codes.append(re_codes_data)
    if_ever_request = False
    for code in re_codes:
        if code.get('email') == email:
            code.update(new_code)
            if_ever_request = True
            break

    if not if_ever_request:
        re_codes.append(re_codes_data)

    sender = 'wed13caero1531@gmail.com'
    receiver = [email]
    msg = MIMEText(re_code)
    msg['Subject'] = 'Reset Code'
    msg['From'] = 'wed13caero1531@gmail.com'
    msg['to'] = email

    sever = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    sever.ehlo()
    sever.login("wed13caero1531@gmail.com", "A123B!xyz")
    sever.sendmail(sender, receiver, msg.as_string())
    sever.quit()
    return { }

def auth_passwordreset_reset_v1(reset_code, new_password):
    """
    Description:
        Given a reset code for a user, set that user's new password to the password provided
    Arguments:
        - reset_code    (type string): A string specific to a user's received code.
        - new_password  (type string): A string specific to a user's new password.
    Exceptions:
        InputError occurs when:
            * reset_code is not a valid reset code
            * Password entered is less than 6 characters long
    Return Values:
        Returns {} on condition of:
            + reset_valid is correct
            + password is in correct type
    """
    # check reset_code valid
    valid_code = False
    for code in re_codes:
        if reset_code == code.get('re_code'):
            email = code.get('email')
            valid_code = True
            break

    if not valid_code:
        raise InputError('reset_code is not a valid reset code')

    if len(new_password) < 6:
        raise InputError('Password entered is less than 6 characters long')

    # encrypt password
    encrypt_password = hashlib.sha256(new_password.encode('utf8')).hexdigest()
    password_new = {
        'password': encrypt_password}
    for user in data['users']:
        if user['email'] == email:
            user.update(password_new)
            break
    return { }

# Below are all helpers functions
# ------------------------------------------------------------------------------------

#   Description: Checks if the input email's format is valid.
def check_email_format(email):
    matched = re.search("^[a-zA-Z0-9]+[\\._]?[a-zA-Z0-9]+[@]\\w+[.]\\w{2,3}$", email)
    return True if matched else False

#   Description: Checks if the input email's exists in the database.
def check_email_existence(email):
    for user in data['users']:
        if user['public_info']['email'] == email:
            return True
    return False

#   Description: Checks if the input password matches the given email in the database.
def check_password(email, password):
    for index in range(len(data['users'])):
        user = data['users'][index]
        if user['public_info']['email'] == email:
            if user['password'] == hash(password):
                return index
    return -1

# Function the encodes a string.
def hash(string):
    return hashlib.sha256(string.encode()).hexdigest()

# Function that generates a JWT token for a user.
def tokenise(auth_idx, s_id):
    payload = {}
    payload.update({'auth_user_id': auth_idx})
    payload.update({'session_id': s_id})

    token = jwt.encode(payload, SECRETKEY, algorithm='HS256')
    return token

# Function that decodes a JWT token.
def detokenise(token):
    global SECRETKEY
    try:
        data = jwt.decode(token, SECRETKEY, algorithms='HS256')
        return data
    except:
        raise AccessError("Invalid token!") from None
