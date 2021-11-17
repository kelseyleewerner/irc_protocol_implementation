import socket
import threading

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
def handle(connection):
    # server must receive user name from client as part of initializing connection
    name_message = connection.recv(1024).decode()
    name_message = name_message.split(':')
    command = name_message[0]
    chat_name = name_message[-1]

    # Error check client message before adding client to list of connected clients
    setting_user_name = True
    while setting_user_name:
        if command != 'NAME':
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
            # gets message from client and forwards it to everyone
            message = client['socket'].recv(1024)
            broadcast(message)
        except:
            # TODO: this won't work this way need to redo for graceful failure or maybe kind of keep
            # if error detected, deletes client from clients array and closes connection with client
            # thread will close once execution is done
            # TODO: need to test that can add user w same name after that user leaves to check that they are correctly removed
            index = find_client(clients, client['user_name'])
            clients.pop(index)
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
        thread = threading.Thread(target=handle, args=(connection,))
        thread.start()

# Running server and catching all unexpected/unhandled errors
try:
    listen_for_connect_reqs()
except:
    print('Unexpected Server Error: Connection has closed')
    server.close()
