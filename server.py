import socket
import threading
import utilities

HOST = '127.0.0.1'
PORT = 2787

# TODO: add comments
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print('IRC Server is listening...')

# List of TCP connections to different clients
# Each connection in the list is a dictionary with the following format:
# {
#     'user_name': String,
#     'socket': Socket Object 
# }
clients = []

# List of chat rooms
# Each room in the list is a dictionary with the following format:
# {
#     'room_name': String,
#     'members': String[]
# }
chat_rooms = []

# Broadcast a message to all clients
def broadcast(message):
    for client in clients:
        client['socket'].send(message)

# find a specific socket in the list of client TCP connections
# Returns connection object if user is found in list
# Return -1 if lst is empty or if user not found in list
def find_client(lst, value):
    if not lst:
        return -1
    for index, dic in enumerate(lst):
        if dic['user_name'] == value:
            return index
    return -1

# TODO: rename
# This is what happens in an individual thread that listens for client messages and then forwards them
def message_handler(connection):
    # server must receive user name from client as part of initializing connection
    name_message = connection.recv(1024).decode()
    name_message = name_message.split(':')
    command = name_message[0]
    chat_name = name_message[-1]

    # Error check client message before adding client to list of connected clients
    setting_user_name = True
    while setting_user_name:
        command_check = utilities.validate_command_semantics(command)
        param_check = utilities.validate_param_semantics(chat_name)
        if command_check != True:
            connection.send(command_check.encode())
            name_message = connection.recv(1024).decode()
            name_message = name_message.split(':')
            command = name_message[0]
            chat_name = name_message[-1]
        elif param_check != True:
            connection.send(param_check.encode())
            name_message = connection.recv(1024).decode()
            name_message = name_message.split(':')
            command = name_message[0]
            chat_name = name_message[-1]
        elif command != 'NAME':
            connection.send('ERROR:106:Client not registered with server'.encode())
            name_message = connection.recv(1024).decode()
            name_message = name_message.split(':')
            command = name_message[0]
            chat_name = name_message[-1]
        elif find_client(clients, chat_name) != -1:
            connection.send('ERROR:105:Username already in use'.encode())
            name_message = connection.recv(1024).decode()
            name_message = name_message.split(':')
            command = name_message[0]
            chat_name = name_message[-1]
        else:
            setting_user_name = False

    client = {
        'user_name': chat_name,
        'socket': connection
    }
    # Add new socket to list of connected clients
    clients.append(client)
    print('New User: {}'.format(client['user_name'])) 

    while True:
        try:
            message = client['socket'].recv(1024).decode()

            print('ORIGINAL MESSAGE')
            print(message)

            message = message.split(':')
            command = message[0]

            command_check = utilities.validate_command_semantics(command)
            if command_check != True:
                client['socket'].send(command_check.encode())
                continue

            match command:
                case 'JOIN':
                    room_name = message[-1]
                    # Validate that room name is correctly formatted
                    param_check = utilities.validate_param_semantics(room_name)
                    if param_check != True:
                        client['socket'].send(param_check.encode())
                        continue
                    
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
                    client['socket'].send('JOIN_RESPONSE:{}'.format(room_name).encode())

                case 'ROOMS':
                    if not chat_rooms:
                        client['socket'].send('ROOMS_RESPONSE: '.encode())
                    else:
                        rooms = []
                        for room in chat_rooms:
                            rooms.append(room['room_name'])
                        rooms = ' '.join(rooms)
                        client['socket'].send('ROOMS_RESPONSE:{}'.format(rooms).encode())

                case 'USERS':
                    room_name = message[-1]
                    # Validate that room name is correctly formatted
                    param_check = utilities.validate_param_semantics(room_name)
                    if param_check != True:
                        client['socket'].send(param_check.encode())
                        continue

                    if not chat_rooms:
                        client['socket'].send('ERROR:107:{}:This chat room does not exist'.format(room_name).encode())
                    else:
                        room_found = False
                        room_index = 0
                        for room in chat_rooms:
                            if room['room_name'] == room_name:
                                room_found = True
                                break
                            room_index += 1
                        
                        if room_found:
                            if not chat_rooms[room_index]['members']:
                                client['socket'].send('USERS_RESPONSE:{}: '.format(room_name).encode())
                            else:
                                members = []
                                for member in chat_rooms[room_index]['members']:
                                    members.append(member)
                                members = ' '.join(members)
                                client['socket'].send('USERS_RESPONSE:{}:{}'.format(room_name, members).encode())
                        else:
                            client['socket'].send('ERROR:107:{}:This chat room does not exist'.format(room_name).encode())

                case 'ERROR':
                    error_code = message[1]
                    error_msg = message[-1]
                    print('{} Error: {}'.format(error_code, error_msg))

                case _:
                    message = 'ERROR:100:Command is not included in the list of approved commands'
                    client['socket'].send(message.encode())
        except Exception as E:
            # TODO: this won't work this way need to redo for graceful failure or maybe kind of keep
            # if error detected, deletes client from clients array and closes connection with client
            # thread will close once execution is done
            # TODO: need to test that can add user w same name after that user leaves to check that they are correctly removed
            
            print(E)
            
            index = find_client(clients, client['user_name'])
            clients.pop(index)

            # TODO: should i remove users from a chat room when they leave irc?
            for room in chat_rooms:
                if client['user_name'] in room['members']:
                    room['members'].remove(client['user_name'])

            client['socket'].close()
            broadcast('{} left!'.format(client['user_name']).encode())
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
except:
    print('Unexpected Server Error: Connection has closed')
    server.close()
