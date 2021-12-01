import socket
import threading
import time
import utilities
from datetime import datetime, timedelta

# ==============================================================================================
#                                    Global Server State
# ==============================================================================================

# IP address of local host
HOST = '0.0.0.0'
# Port number specified in protocol
PORT = 2787

# List of TCP connections to all active clients
# Each connection in the list is a dictionary with the following format:
# {
#     'user_name': String,
#     'socket': Socket Object,
#     'timestamp': datetime Object,
#     'alive': Boolean
# }
clients = []

# List of chat rooms
# Each room in the list is a dictionary with the following format:
# {
#     'room_name': String,
#     'members': String[]
# }
chat_rooms = []

# Listen for incoming TCP connection requests
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print('IRC Server is listening...')

# ==============================================================================================
#                               Connection Maintenance Functions
# ==============================================================================================

# Terminate client TCP connection with individual client
# Takes client dictionary as argument
def close_connection(client):
    client['alive'] = False
    # Remove client from list of active clients
    index = find_client(client['user_name'])
    clients.pop(index)

    # Remove client from any chat rooms where they are a member
    for room in chat_rooms:
        if client['user_name'] in room['members']:
            room['members'].remove(client['user_name'])

    client['socket'].close()
    print('{} has left'.format(client['user_name']))

# Terminate client TCP connection with all clients
def close_all_connections():
    for client in clients:
        msg = 'QUIT'
        send_message(client['socket'], msg)
        client['socket'].close()

# Find a specific client socket in the list of client TCP connections using the user name passed as an argument
# If client is found, returns Integer index of client in list of clients
# Returns -1 if clients list is empty or if user not found in list
# Takes String as argument
def find_client(user_name):
    if not clients:
        return -1
    for index, dic in enumerate(clients):
        if dic['user_name'] == user_name:
            return index
    return -1

# Find a specific chat room in the list of chat rooms using the room name passed as an argument
# If chat room is found, returns Integer index of room in list of chat rooms
# Returns -1 if chat rooms list is empty or if room not found in list
# Takes String as argument
def find_chat_room(room_name):
    room_found = False
    room_index = 0

    for room in chat_rooms:
        if room['room_name'] == room_name:
            room_found = True
            break
        room_index += 1

    if room_found:
        return room_index
    else:
        return -1

# Function sends STILL_ALIVE messages to client passed as argument to ensure this client knows that the connection is still alive
# Takes client dictionary as argument
def send_keep_alive(client):
    try:
        while True:
            # Stop sending messages if connection closes
            if not client['alive']:
                break
            msg = 'STILL_ALIVE'
            send_message(client['socket'], msg)
            # Wait 5 seconds in between each STILL_ALIVE message
            time.sleep(5)

    # End program if unexpected error occurs
    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection(client)

# Function verifies that STILL_ALIVE messages are being received from the client passed as an argument within the timeout window
# Takes client dictionary as argument
def verify_keep_alive(client):
    try:
        alive_window = timedelta(seconds = 10)

        while True:
            # Wait 10 seconds in between checking timestamp from last STILL_ALIVE message
            time.sleep(10)
            # Stop checking messages if connection closes
            if not client['alive']:
                break

            # If STILL_ALIVE message is not received from client within the last 10 seconds,
            # then the server assumes client is down and ends the program
            window_start = datetime.now() - alive_window
            if client['timestamp'] < window_start:
                print('Unexpected Error: Client is no longer online')
                close_connection(client)
                break

    # End program if unexpected error occurs
    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection(client)

# ==============================================================================================
#                                    Message Handlers
# ==============================================================================================

# Send encoded message to client over TCP connection
# Takes a socket object and a String as arguments
def send_message(client_socket, msg):
    client_socket.send(msg.encode())

# Receives and parses encoded message from client socket
# Returns the parsed message as a List of Strings and the command portion of the message as a String
# Takes socket object as argument
def receive_message(client_socket):
    message = client_socket.recv(1024).decode()
    message = message.split(':')
    command = message[0]
    return message, command

# Function creates new chat room or adds user to existing chat room based on the room name received from the client
# Called in response to receiving JOIN message from a client
# Takes client dictionary and List of Strings as argument
def join_msg_handler(client, message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    # If room is already in list of chat rooms, add user to the existing room
    create_room = True
    for room in chat_rooms:
        if room['room_name'] == room_name:
            # Verify user is not already in room, so duplicate user_names aren't added to members list
            if client['user_name'] not in room['members']:
                room['members'].append(client['user_name'])
            create_room = False
            break

    # If room is not already in list of rooms, create new room
    if create_room:
        new_room = {
            'room_name': room_name,
            'members': [client['user_name']]
        }
        chat_rooms.append(new_room)

    # Send confirmation message to client
    msg = 'JOIN_RESPONSE:{}'.format(room_name)
    send_message(client['socket'], msg)

# Function sends list of chat rooms to requesting user
# Called in response to receiving ROOMS message from a client
# Takes client dictionary as argument
def rooms_msg_handler(client):
    # Sends empty ROOMS_RESPONSE message to client if no chat rooms have been created
    if not chat_rooms:
        msg = 'ROOMS_RESPONSE: '
        send_message(client['socket'], msg)
    else:
        rooms = []
        for room in chat_rooms:
            rooms.append(room['room_name'])
        rooms = ' '.join(rooms)
        msg = 'ROOMS_RESPONSE:{}'.format(rooms)
        send_message(client['socket'], msg)

# Function sends member list of a chat room to requesting user
# Called in response to receiving USERS message from a client
# Takes client dictionary and List of Strings as argument
def users_msg_handler(client, message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    # Sends error message to client if no chat rooms have been created
    if not chat_rooms:
        msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
        send_message(client['socket'], msg)
    else:
        room_index = find_chat_room(room_name)

        if room_index > -1:
            # Sends empty USERS_RESPONSE message to client if requested chat room doesn't have any members
            if not chat_rooms[room_index]['members']:
                msg = 'USERS_RESPONSE:{}: '.format(room_name)
                send_message(client['socket'], msg)
            else:
                members = []
                for member in chat_rooms[room_index]['members']:
                    members.append(member)
                members = ' '.join(members)
                msg = 'USERS_RESPONSE:{}:{}'.format(room_name, members)
                send_message(client['socket'], msg)
        # Sends error message to client if requested room has not been created
        else:
            msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
            send_message(client['socket'], msg)

# Function removes requesting user from chat room
# Called in response to receiving LEAVE message from a client
# Takes client dictionary and List of Strings as argument
def leave_msg_handler(client, message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    # Send confirmation message to client even if chat rooms list is empty
    if not chat_rooms:
        msg = 'LEAVE_RESPONSE:{}'.format(room_name)
        send_message(client['socket'], msg)
    else:
        room_index = find_chat_room(room_name)
        if room_index > -1:
            if client['user_name'] in chat_rooms[room_index]['members']:
                chat_rooms[room_index]['members'].remove(client['user_name'])
        # Send confirmation message to client even if user wasn't a member of room prior to LEAVE request
        # or if room doesn't exist in list of chat rooms
        msg = 'LEAVE_RESPONSE:{}'.format(room_name)
        send_message(client['socket'], msg)

# Function broadcasts message body received from a user to all members of a chat room
# Called in response to receiving MESSAGE message from a client
# Takes client dictionary and List of Strings as argument
def chat_msg_handler(client, message):
    room_name = message[1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    # Properly format a message body that contains colons
    if len(message) > 3:
        message_body = ':'.join(message[2:])
    else:
        message_body = message[2]
    # Validate that message body is correctly formatted
    payload_check = utilities.validate_payload_semantics(message_body)
    if payload_check != True:
        send_message(client['socket'], payload_check)
        return

    # Sends error message to client if no chat rooms have been created
    if not chat_rooms:
        msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
        send_message(client['socket'], msg)
    else:
        room_index = find_chat_room(room_name)

        if room_index > -1:
            if client['user_name'] in chat_rooms[room_index]['members']:
                # Finds the socket that corresponds to the user name of each member in the chat room
                # and broadcasts message body to all members
                for member in chat_rooms[room_index]['members']:
                    for connection in clients:
                        if connection['user_name'] == member:
                            msg = 'MESSAGE:{}:{}:{}'.format(room_name, client['user_name'], message_body)
                            send_message(connection['socket'], msg)
                            break
            # Sends error message to client if they are not a member of the requested chat room
            else:
                msg = 'ERROR:108:{}:User is not a member of this chat room'.format(room_name)
                send_message(client['socket'], msg)
        # Sends error message to client if requested chat room has not been created
        else:
            msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
            send_message(client['socket'], msg)

# Function forwards messages body to a user directly from another user
# Called in response to receiving MESSAGE_USER message from a client
# Takes client dictionary and List of Strings as argument
def private_msg_handler(client, message):
    target_user = message[1]
    # Validate that target username is correctly formatted
    param_check = utilities.validate_param_semantics(target_user)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    # Properly format a message body that contains colons
    if len(message) > 3:
        message_body = ':'.join(message[2:])
    else:
        message_body = message[2]
        # Validate that message body is correctly formatted
        payload_check = utilities.validate_payload_semantics(message_body)
        if payload_check != True:
            send_message(client['socket'], payload_check)
            return

    client_index = find_client(target_user)
    if client_index > -1:
        # Sends message to recipient user name requested by client sender
        msg = 'MESSAGE_USER:{}:{}:{}'.format(target_user, client['user_name'], message_body)
        send_message(clients[client_index]['socket'], msg)
        # Send confirmation MESSAGE_USER message to sending user
        # If user sent a message to themselves, then the initial MESSAGE_USER response will serve as confirmation
        # and a duplicate MESSAGE_USER confirmation is not needed
        if client['user_name'] != clients[client_index]['user_name']:
            msg = 'MESSAGE_USER:{}:{}:{}'.format(target_user, client['user_name'], message_body)
            send_message(client['socket'], msg)
    # Sends error message to client if requested recipient user name is not connected to the server
    else:
        msg = 'ERROR:109:{}:This user does not exist'.format(target_user)
        send_message(client['socket'], msg)

# Function listens for messages from a client
# and calls the message handler that corresponds to the command portion of the message
def message_handler(connection):
    try:
        # Server must receive user name from client as to finish initializing connection
        name_message, command = receive_message(connection)
        chat_name = name_message[-1]

        # Error check client-selected user name before adding client to list of connected clients
        setting_user_name = True
        while setting_user_name:
            command_check = utilities.validate_command_semantics(command)
            param_check = utilities.validate_param_semantics(chat_name)
            # Validate that command portion of message is correctly formatted
            if command_check != True:
                send_message(connection, command_check)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            # Validate that user name is correctly formatted
            elif param_check != True:
                send_message(connection, param_check)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            # Validate that correct NAME command was sent
            elif command != 'NAME':
                msg = 'ERROR:106:Client not registered with server'
                send_message(connection, msg)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            # Validate that user name is unique
            elif find_client(chat_name) != -1:
                msg = 'ERROR:105:Username already in use'
                send_message(connection, msg)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            else:
                setting_user_name = False

    # End program if unexpected error occurs
    except Exception as E:
        print('Unexpected Error: Connection has closed')
        print(E)
        connection.close()
        return

    # Client dictionary
    client = {
        'user_name': chat_name,
        'socket': connection,
        'timestamp': datetime.now(),
        'alive': True
    }
    # Add new socket to list of connected clients
    clients.append(client)
    print('New User: {}'.format(client['user_name']))

    # Launch thread to send STILL_ALIVE messages to client
    thread = threading.Thread(target=send_keep_alive, args=(client,))
    thread.start()

    # Launch thread to monitor if connection with client is being maintained
    sending_thread = threading.Thread(target=verify_keep_alive, args=(client,))
    sending_thread.start()

    # After connection has finished initializing, listen for messages from the client
    while True:
        try:
            message, command = receive_message(client['socket'])

            # Validate that command is correctly formatted
            command_check = utilities.validate_command_semantics(command)
            if command_check != True:
                send_message(client['socket'], command_check)
                continue

            # Identify corresponding action for command portion of client message
            match command:
                case 'STILL_ALIVE':
                    client['timestamp'] = datetime.now()
                case 'JOIN':
                    join_msg_handler(client, message)
                case 'ROOMS':
                    rooms_msg_handler(client)
                case 'USERS':
                    users_msg_handler(client, message)
                case 'LEAVE':
                    leave_msg_handler(client, message)
                case 'MESSAGE':
                    chat_msg_handler(client, message)
                case 'MESSAGE_USER':
                    private_msg_handler(client, message)
                case 'QUIT':
                    msg = 'QUIT'
                    send_message(client['socket'], msg)
                    close_connection(client)
                    break
                # Displays error messages received from client
                case 'ERROR':
                    error_code = message[1]
                    error_msg = message[-1]
                    print('{} Error: {}'.format(error_code, error_msg))
                # Alerts client if unrecognized command is received
                case _:
                    msg = 'ERROR:100:Command is not included in the list of approved commands'
                    send_message(client['socket'], msg)

        # End program if unexpected error occurs
        except Exception as E:
            print('Unexpected Error: Connection has closed')
            print(E)
            close_connection(client)
            break

# ==============================================================================================
#                                       Server Program
# ==============================================================================================

try:
    while True:
        # Listen for TCP connection requests from clients
        connection, address = server.accept()
        print('Connected with {}'.format(str(address)))

        # Launch a thread for each client TCP connection
        thread = threading.Thread(target=message_handler, args=(connection,))
        thread.start()

# End program if unexpected error occurs
except Exception as E:
    print('Unexpected Error: Connection has closed')
    print(E)
    close_all_connections()
    server.close()
