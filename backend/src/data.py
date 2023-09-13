from datetime import datetime, timezone

''' The data storage file for the project.

Formatted as following:

data = {
    'users'         : [
        {
            'email'         : type_string,
            'password'      : type_string,
            'name_first'    : type_string,
            'name_last'     : type_string,
            'auth_user_id'  : type_int,
            'token'         : type_string,
            'handle_str'    : type_string,
            'permission_id' : in [1, 2],
        },
    ],
    'channels'      : [
        {
            'channel_id'    : type_int,
            'channel_name'  : type_string,
            'is_public'     : type_bool,
            'owner_members' : type_members,
            'all_members'   : type_members,
            'messages'      : type_messages,
        },
    ],
    'dms'            : [
        {
            'dm_id'         : type_int,
            'dm_name'       : type_string,
            'owner_members' : type_members,
            'all_members'   : type_members,
            'messages'      : type_messages,
        },
    ],
    'msg_position'  : [
        {
            'message_ids'   : [],
            'type'          : type_string,
            'id'            : type_int,
        }
    ]
    'dreams_stats': {
        'users_exist'   : [{
                            'num_users_exist'   :type_int,
                            'time_stamp'        :type_int}],
        'channels_exist': [{
                            'num_channels_exist':type_int,
                            'time_stamp'        :type_int}],
        'dms_exist'     : [{
                            'num_dms_exist'     :type_int,
                            'time_stamp'        :type_int}],
        'messages_exist': [{
                            'num_messages_exist':type_int,
                            'time_stamp'        :type_int}],
        'utilization_rate' = type_float
    }

}

Will be initilised as a dictionary containing two keys:
'users' and 'channels'. Where the keys are two empty lists.

===DATA STRUCTURE FOR OUTPUT ARE BELOW===

============USERS RELEVANT===========

user = {
    'u_id'      : type_int,
    'email'     : type_string,
    'name_last' : type_string,
    'name_first': type_string,
    'handle_str': type_string,
}

users = [
        user,
        user,
        ...
]


_members = [
        user,
        user,
        ...
]

============USERS RELEVANT============

==========CHANNELS RELEVANT===========

channels = [
    {
        'channel_id': type_int,
        'name'      : type_string,
    },
    ...
]

messages = [
    {
        'message_id'    : type_int,
        'u_id'          : type_int,
        'message'       : type_string,
        'time_created'  : type_int, (unix timestamp)
    },
    {
        ...
    },
    ...
]

===========CHANNELS RELEVANT==========
==============DM RELEVANT=============

dms = [
    {
        'dm_id' : type_int,
        'name'  : type_string,
    },
    {
        ...
    },
    ...
]

==============DM RELEVANT=============

End of description
'''

data = {
    'users'         : [

    ],
    'channels'      : [

    ],
    'dms'           : [

    ],
    'msg_positions' : [

    ],
    'dreams_stats'  :{
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
    },
}
