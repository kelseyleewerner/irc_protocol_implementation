import socket
import threading
import time
import utilities
from datetime import datetime, timedelta



HOST = '0.0.0.0'
# Port number specified in protocol
PORT = 2787



# List of TCP connections to different clients
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


# TODO: add comments
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print('IRC Server is listening...')


# find a specific socket in the list of client TCP connections
# Returns connection object if user is found in list
# Return -1 if lst is empty or if user not found in list
def find_client(user_name):
    if not clients:
        return -1
    for index, dic in enumerate(clients):
        if dic['user_name'] == user_name:
            return index
    return -1


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

def receive_message(connection):
    message = connection.recv(1024).decode()
    message = message.split(':')
    command = message[0]
    return message, command


def send_message(client_socket, msg):
    client_socket.send(msg.encode())


def close_connection(client):
    client['alive'] = False
    index = find_client(client['user_name'])
    clients.pop(index)

    for room in chat_rooms:
        if client['user_name'] in room['members']:
            room['members'].remove(client['user_name'])

    client['socket'].close()
    print('{} has left'.format(client['user_name']))


def close_all_connections():
    for client in clients:
        msg = 'QUIT'
        send_message(client['socket'], msg)
        client['socket'].close()


def join_msg_handler(client, message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    # If room already in list of chat rooms, add user to the existing room
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

def rooms_msg_handler(client):
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


def users_msg_handler(client, message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    if not chat_rooms:
        msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
        send_message(client['socket'], msg)
    else:
        room_index = find_chat_room(room_name)

        if room_index > -1:
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
        else:
            msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
            send_message(client['socket'], msg)

def leave_msg_handler(client, message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    if not chat_rooms:
        msg = 'LEAVE_RESPONSE:{}'.format(room_name)
        send_message(client['socket'], msg)
    else:
        room_index = find_chat_room(room_name)

        if room_index > -1:
            if client['user_name'] in chat_rooms[room_index]['members']:
                chat_rooms[room_index]['members'].remove(client['user_name'])
        msg = 'LEAVE_RESPONSE:{}'.format(room_name)
        send_message(client['socket'], msg)


def chat_msg_handler(client, message):
    room_name = message[1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

    if len(message) > 3:
        message_body = ':'.join(message[2:])
    else:
        message_body = message[2]
    # Validate that message body is correctly formatted
    payload_check = utilities.validate_payload_semantics(message_body)
    if payload_check != True:
        send_message(client['socket'], payload_check)
        return

    if not chat_rooms:
        msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
        send_message(client['socket'], msg)
    else:
        room_index = find_chat_room(room_name)

        if room_index > -1:
            if client['user_name'] in chat_rooms[room_index]['members']:
                for member in chat_rooms[room_index]['members']:
                    for connection in clients:
                        if connection['user_name'] == member:
                            msg = 'MESSAGE:{}:{}:{}'.format(room_name, client['user_name'], message_body)
                            send_message(connection['socket'], msg)
                            break
            else:
                msg = 'ERROR:108:{}:User is not a member of this chat room'.format(room_name)
                send_message(client['socket'], msg)
        else:
            msg = 'ERROR:107:{}:This chat room does not exist'.format(room_name)
            send_message(client['socket'], msg)


def private_msg_handler(client, message):
    target_user = message[1]
    # Validate that target username is correctly formatted
    param_check = utilities.validate_param_semantics(target_user)
    if param_check != True:
        send_message(client['socket'], param_check)
        return

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
        msg = 'MESSAGE_USER:{}:{}:{}'.format(target_user, client['user_name'], message_body)
        send_message(clients[client_index]['socket'], msg)
        if client['user_name'] != clients[client_index]['user_name']:
            msg = 'MESSAGE_USER:{}:{}:{}'.format(target_user, client['user_name'], message_body)
            send_message(client['socket'], msg)
    else:
        msg = 'ERROR:109:{}:This user does not exist'.format(target_user)
        send_message(client['socket'], msg)



def send_keep_alive(client):
    try:
        while True:
            if not client['alive']:
                break
            msg = 'STILL_ALIVE'
            send_message(client['socket'], msg)
            time.sleep(5)

    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection(client)



def verify_keep_alive(client):
    try:
        alive_window = timedelta(seconds = 10)

        while True:
            time.sleep(10)
            if not client['alive']:
                break

            window_start = datetime.now() - alive_window

            if client['timestamp'] < window_start:
                print('Unexpected Error: Client is no longer online')
                close_connection(client)
                break

    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection(client)



# TODO: rename
# This is what happens in an individual thread that listens for client messages and then forwards them
def message_handler(connection):
    try:
        # server must receive user name from client as part of initializing connection
        name_message, command = receive_message(connection)
        chat_name = name_message[-1]

        # Error check client message before adding client to list of connected clients
        setting_user_name = True
        while setting_user_name:
            command_check = utilities.validate_command_semantics(command)
            param_check = utilities.validate_param_semantics(chat_name)
            if command_check != True:
                send_message(connection, command_check)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            elif param_check != True:
                send_message(connection, param_check)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            elif command != 'NAME':
                msg = 'ERROR:106:Client not registered with server'
                send_message(connection, msg)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            elif find_client(chat_name) != -1:
                msg = 'ERROR:105:Username already in use'
                send_message(connection, msg)
                name_message, command = receive_message(connection)
                chat_name = name_message[-1]
            else:
                setting_user_name = False

    except Exception as E:
        print('Unexpected Error: Connection has closed')
        print(E)
        connection.close()
        return

    client = {
        'user_name': chat_name,
        'socket': connection,
        'timestamp': datetime.now(),
        'alive': True
    }
    # Add new socket to list of connected clients
    clients.append(client)
    print('New User: {}'.format(client['user_name']))

    thread = threading.Thread(target=send_keep_alive, args=(client,))
    thread.start()

    sending_thread = threading.Thread(target=verify_keep_alive, args=(client,))
    sending_thread.start()

    while True:
        try:
            message, command = receive_message(client['socket'])

            command_check = utilities.validate_command_semantics(command)
            if command_check != True:
                send_message(client['socket'], command_check)
                continue

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
                case 'ERROR':
                    error_code = message[1]
                    error_msg = message[-1]
                    print('{} Error: {}'.format(error_code, error_msg))
                case _:
                    msg = 'ERROR:100:Command is not included in the list of approved commands'
                    send_message(client['socket'], msg)

        except Exception as E:
            print('Unexpected Error: Connection has closed')
            print(E)
            close_connection(client)
            break

# listening for tcp connections
def listen_for_connect_reqs():
    while True:
        # server accepts connection from client
        connection, address = server.accept()
        print('Connected with {}'.format(str(address)))

        # creating a thread for each client TCP connection
        thread = threading.Thread(target=message_handler, args=(connection,))
        thread.start()

# Running server and catching all unexpected/unhandled errors
try:
    listen_for_connect_reqs()
except Exception as E:
    print('Unexpected Error: Connection has closed')
    print(E)
    close_all_connections()
    server.close()
