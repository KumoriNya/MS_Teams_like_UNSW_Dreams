TODO: Add any assumption you used here

In this document, whenever the word 'admin' is mentioned, it refers to 
the owners of Dream. Different naming conventionis used 
to distingush between owners of dream and channels separately easily.

Claude:
    channel_details:
        output from stub code contradicts interface requirement, following interface 
        i.e. user contains 5 keys instead of where stub code have 3
    other_clear_v1:
        no other keys under data apart from users and channels
    channel_join&invite:
        when the member is about to be added to the channel's members list,
        if the member is already in the channel, return straight away,
        i.e. do nothing.
        assume that dream admin's position is fixed in database,
        i.e. data['users'][0]
    message:
        deleting a message != removing a message
        deleting a message leaves a non-editable message at the exact position before deleting it which acts identical to editing - different in a way that deleted = no-more-edit
        removing a message removes the message, and all message sent before the deleted message will move 'forward' one spot to fill in the space.
        send:
            not listed in the spec, but channel_id can be invalid => IE
    message_edit:
        For access error, assuming all functionalities can only applied via function interface,
        then if admin is not a member of a channel, then by access error defined in the function
        channel_messages an admin will never be able to access any message of a channel which 
        the admin is not a member. Thus not considering the case where an admin attempts to edit
        a message of a channel of which this admin is not a member.
        Iteration 2:
        If a message is edited and tags any valid user, a notification is made.
    message_share:
        Shared original message containing valid tags will not produce notification again.
        Optional additional message is treated as an original message so any valid tag will trigger
        a notification.
    notifications:
        Once a notification is made, it's gonna stay.

Nathan:
    For channels_create_v1:
        Assumed that the creator of the channel is the owner of the channel.

    For auth_register_v1:
        Assumed that first and last names consist of characters only from the alphabet.