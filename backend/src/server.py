from json import dumps
from flask_cors import CORS
from flask import Flask, request, send_from_directory
from src import config
from src.helpers import data_load
from src.error import InputError, AccessError
import src.dm as dm, src.admin as admin, src.user as user, src.message as message
import src.auth as auth, src.channel as channel, src.channels as channels, src.other as other
import src.standup as standup

data_load()

def defaultHandler(err):
    response = err.get_response()
    print('response', err, err.get_response())
    response.data = dumps({
        "code": err.code,
        "name": "System Error",
        "message": err.get_description(),
    })
    response.content_type = 'application/json'
    return response

APP = Flask(__name__, static_url_path='/static/')
CORS(APP)
APP.config['TRAP_HTTP_EXCEPTIONS'] = True
APP.register_error_handler(Exception, defaultHandler)

##################

@APP.route("/standup/start/v1", methods=['POST'])
def http_standup_start():
    params = request.get_json()

    token = params['token']
    channel_id = params['channel_id']
    length = params['length']
    try:
        return dumps(standup.standup_start_v1(token, channel_id, length))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/standup/active/v1", methods=['GET'])
def http_standup_active():
    token = request.args.get('token')
    channel_id = int(request.args.get('channel_id'))

    try:
        return dumps(standup.standup_active_v1(token, channel_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/standup/send/v1", methods=['POST'])
def http_standup_send():
    params = request.get_json()

    token = params['token']
    channel_id = params['channel_id']
    msg = params['message']

    try:
        return dumps(standup.standup_send_v1(token, channel_id, msg))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/user/stats/v1", methods=['GET'])
def http_user_stats():
    token = request.args.get('token')

    try:
        return dumps(user.user_stats_v1(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/users/stats/v1", methods=['GET'])
def http_users_stats():
    token = request.args.get('token')

    try:
        return dumps(user.users_stats_v1(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/user/profile/uploadphoto/v1", methods=['POST'])
def http_user_profile_uploadphoto():
    params = request.get_json()

    token = params['token']
    img_url = params['img_url']
    x_start = params['x_start']
    y_start = params['y_start']
    x_end = params['x_end']
    y_end = params['y_end']
    try:
        return dumps(user.user_profile_uploadphoto(token, img_url, x_start, y_start, x_end, y_end))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/sendlater/v1", methods=['POST'])
def http_message_sendlater():
    params = request.get_json()

    token = params['token']
    channel_id = params['channel_id']
    msg = params['message']
    time_sent = params['time_sent']
    try:
        return dumps(message.message_sendlater_v1(token, channel_id, msg, time_sent))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/sendlaterdm/v1", methods=['POST'])
def http_message_sendlaterdm():
    params = request.get_json()

    token = params['token']
    dm_id = params['dm_id']
    msg = params['message']
    time_sent = params['time_sent']
    try:
        return dumps(message.message_sendlaterdm_v1(token, dm_id, msg, time_sent))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/react/v1", methods=['POST'])
def http_message_react():
    params = request.get_json()

    token = params['token']
    message_id = params['message_id']
    react_id = params['react_id']
    try:
        return dumps(message.message_react_v1(token, message_id, react_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/unreact/v1", methods=['POST'])
def http_message_unreact():
    params = request.get_json()

    token = params['token']
    message_id = params['message_id']
    react_id = params['react_id']
    try:
        return dumps(message.message_unreact_v1(token, message_id, react_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/pin/v1", methods=['POST'])
def http_message_pin():
    params = request.get_json()

    token = params['token']
    message_id = params['message_id']
    try:
        return dumps(message.message_pin_v1(token, message_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/unpin/v1", methods=['POST'])
def http_message_unpin():
    params = request.get_json()

    token = params['token']
    message_id = params['message_id']
    try:
        return dumps(message.message_unpin_v1(token, message_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err


@APP.route("/auth/passwordreset/request/v1", methods=["POST"])
def passwordreset_request():
    data = request.get_json()
    email = str(data['email'])

    try:
        return dumps(auth.auth_passwordreset_request_v1(email))
    except InputError as err:
        raise InputError(err) from err

@APP.route("/auth/passwordreset/reset/v1", methods=["POST"])
def passwordreset_reset():
    data = request.get_json()
    reset_code = str(data['reset_code'])
    new_password = str(data['new_password'])

    try:
        return dumps(auth.auth_passwordreset_reset_v1(reset_code, new_password))
    except InputError as err:
        raise InputError(err) from err

##################
# Example
@APP.route("/echo", methods=['GET'])
def echo():
    ddata = request.args.get('data')
    if ddata == 'echo':
        raise InputError(description = 'Cannot echo "echo"')
    return dumps({
        'data': ddata
    })

@APP.route("/auth/login/v2", methods=['POST'])
def http_auth_login():
    inputs = request.get_json()
    email = inputs['email']
    password = inputs['password']

    try:
        return dumps(auth.auth_login_v2(email, password))
    except InputError as err:
        raise InputError(err) from err

@APP.route("/auth/register/v2", methods=['POST'])
def http_auth_register():
    params = request.get_json()

    email = params['email']
    password = params['password']
    name_first = params['name_first']
    name_last = params['name_last']
    try:
        return dumps(auth.auth_register_v2(email, password, name_first, name_last))
    except InputError as err:
        raise InputError(err) from err

@APP.route("/auth/logout/v1", methods=['POST'])
def http_auth_logout():
    inputs = request.get_json()

    token = inputs['token']

    try:
        return dumps(auth.auth_logout_v1(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/admin/userpermission/change/v1", methods=['POST'])
def http_admin_userpermission_change():
    inputs = request.get_json()
    token = inputs['token']
    u_id = inputs['u_id']
    p_id = inputs['permission_id']

    try:
        return dumps(admin.admin_userpermission_change_v1(token, u_id, p_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/admin/user/remove/v1", methods=['DELETE'])
def http_admin_user_remove():
    inputs = request.get_json()
    token = inputs['token']
    u_id = inputs['u_id']

    try:
        return dumps(admin.admin_user_remove_v1(token, u_id))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/clear/v1", methods=['DELETE'])
def http_clear():
    return dumps(other.clear_v1())

@APP.route("/search/v2", methods=['GET'])
def http_search():
    token = request.args.get('token')
    query_str = request.args.get('query_str')

    try:
        return dumps(other.search_v2(token, query_str))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/channels/list/v2", methods=['GET'])
def http_channels_list():
    token = request.args.get('token')

    try:
        return dumps(channels.channels_list_v2(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/channels/listall/v2", methods=['GET'])
def http_channels_listall():
    token = request.args.get('token')

    try:
        return dumps(channels.channels_listall_v2(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/channels/create/v2", methods=['POST'])
def http_channels_create():
    inputs = request.get_json()
    token = inputs['token']
    name = inputs['name']
    is_public = inputs['is_public']

    try:
        return dumps(channels.channels_create_v2(token, name, is_public))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/channel/invite/v2", methods=['POST'])
def http_channel_invite():
    inputs = request.get_json()
    token = inputs['token']
    channel_id = inputs['channel_id']
    u_id = inputs['u_id']

    try:
        return dumps(channel.channel_invite_v2(token, channel_id, u_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/channel/join/v2", methods=['POST'])
def http_channel_join():
    inputs = request.get_json()
    token = inputs['token']
    channel_id = inputs['channel_id']

    try:
        return dumps(channel.channel_join_v2(token, channel_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/channel/details/v2", methods=['GET'])
def http_channel_details():
    token = request.args.get('token')
    channel_id = int(request.args.get('channel_id'))

    try:
        return dumps(channel.channel_details_v2(token, channel_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/channel/messages/v2", methods=['GET'])
def http_channel_messages():
    token = request.args.get('token')
    channel_id = int(request.args.get('channel_id'))
    start = int(request.args.get('start'))

    try:
        return dumps(channel.channel_messages_v2(token, channel_id, start))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/channel/leave/v1", methods=['POST'])
def http_channel_leave():
    inputs = request.get_json()
    token = inputs['token']
    channel_id = inputs['channel_id']

    try:
        return dumps(channel.channel_leave_v1(token, channel_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/channel/addowner/v1", methods=['POST'])
def http_channel_addowner():
    inputs = request.get_json()
    token = inputs['token']
    channel_id = inputs['channel_id']
    u_id = inputs['u_id']

    try:
        return dumps(channel.channel_addowner_v1(token, channel_id, u_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/channel/removeowner/v1", methods=['POST'])
def http_channel_removeowner():
    inputs = request.get_json()
    token = inputs['token']
    channel_id = inputs['channel_id']
    u_id = inputs['u_id']

    try:
        return dumps(channel.channel_removeowner_v1(token, channel_id, u_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/dm/create/v1", methods=['POST'])
def http_dm_create():
    inputs = request.get_json()
    token = inputs['token']
    u_ids = inputs['u_ids']

    try:
        return dumps(dm.dm_create_v1(token, u_ids))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/dm/list/v1", methods=['GET'])
def http_dm_list():
    token = request.args.get('token')

    try:
        return dumps(dm.dm_list_v1(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/dm/invite/v1", methods=['POST'])
def http_dm_invite():
    inputs = request.get_json()
    token = inputs['token']
    dm_id = inputs['dm_id']
    u_id = inputs['u_id']

    try:
        return dumps(dm.dm_invite_v1(token, dm_id, u_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/dm/leave/v1", methods=['POST'])
def http_dm_leave():
    inputs = request.get_json()
    token = inputs['token']
    dm_id = inputs['dm_id']

    try:
        return dumps(dm.dm_leave_v1(token, dm_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/dm/details/v1", methods=['GET'])
def http_dm_details():
    token = request.args.get('token')
    dm_id = int(request.args.get('dm_id'))

    try:
        return dumps(dm.dm_details_v1(token, dm_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/dm/remove/v1", methods=['DELETE'])
def http_dm_remove():
    inputs = request.get_json()
    token = inputs['token']
    dm_id = inputs['dm_id']

    try:
        return dumps(dm.dm_remove_v1(token, dm_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/dm/messages/v1", methods=['GET'])
def http_dm_messages():
    token = request.args.get('token')
    dm_id = int(request.args.get('dm_id'))
    start = int(request.args.get('start'))

    try:
        return dumps(dm.dm_messages_v1(token, dm_id, start))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/send/v2", methods=['POST'])
def http_message_send_v2():
    inputs = request.get_json()
    token = inputs['token']
    channel_id = inputs['channel_id']
    msg = inputs['message']

    try:
        return dumps(message.message_send_v2(token, channel_id, msg))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/edit/v2", methods=['PUT'])
def http_message_edit():
    inputs = request.get_json()
    token = inputs['token']
    message_id = inputs['message_id']
    msg = inputs['message']

    try:
        return dumps(message.message_edit_v2(token, message_id, msg))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/senddm/v1", methods=['POST'])
def http_message_senddm():
    inputs = request.get_json()
    token = inputs['token']
    dm_id = inputs['dm_id']
    msg = inputs['message']

    try:
        return dumps(message.message_senddm_v1(token, dm_id, msg))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/share/v1", methods=['POST'])
def http_message_share():
    inputs = request.get_json()
    token = inputs['token']
    og_message_id = inputs['og_message_id']
    msg = inputs['message']
    channel_id = inputs['channel_id']
    dm_id = inputs['dm_id']

    try:
        return dumps(message.message_share_v1(token, og_message_id, msg, channel_id, dm_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/message/remove/v1", methods=['DELETE'])
def http_message_remove():
    inputs = request.get_json()
    token = inputs['token']
    message_id = inputs['message_id']

    try:
        return dumps(message.message_remove_v1(token, message_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err
    
@APP.route("/notifications/get/v1", methods=['GET'])
def http_notifications_get():
    token = request.args.get('token')
    
    try:
        return dumps(message.notifications_get_v1(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route("/user/profile/v2", methods=['GET'])
def http_user_profile():
    token = request.args.get('token')
    u_id = int(request.args.get('u_id'))

    try:
        return dumps(user.user_profile_v2(token, u_id))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/user/profile/setname/v2", methods=["PUT"])
def http_user_profile_setname():
    inputs = request.get_json()
    token = inputs['token']
    name_first = inputs['name_first']
    name_last = inputs['name_last']

    try:
        return dumps(user.user_profile_setname_v2(token, name_first, name_last))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/user/profile/setemail/v2", methods=['PUT'])
def http_user_profile_setemail():
    inputs = request.get_json()
    token = inputs['token']
    email = inputs['email']

    try:
        return dumps(user.user_profile_setemail_v2(token, email))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/user/profile/sethandle/v1", methods=['PUT'])
def http_user_profile_sethandle():
    inputs = request.get_json()
    token = inputs['token']
    handle_str = inputs['handle_str']

    try:
        return dumps(user.user_profile_sethandle_v1(token, handle_str))
    except AccessError as err:
        raise AccessError(err) from err
    except InputError as err:
        raise InputError(err) from err

@APP.route("/users/all/v1", methods=['GET'])
def users_all_v1():
    token = request.args.get('token')

    try:
        return dumps(user.users_all_v1(token))
    except AccessError as err:
        raise AccessError(err) from err

@APP.route('/static/img')
def send_js(img):
    return send_from_directory('', img)

if __name__ == "__main__":
    APP.run(port=config.port, debug = True) # Do not edit this port
