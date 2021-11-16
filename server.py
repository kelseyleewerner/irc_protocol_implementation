import socket
import threading

HOST = '127.0.0.1'
PORT = 2787

# TODO: add comments
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

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
# Return False if lst is empty or if user not found in list
def find_client(lst, value):
    if not lst:
        return -1
    for index, dic in enumerate(lst):
        if dic['user_name'] == value:
            return index
    return -1

# TODO: rename
# This is what happens in an individual thread that listens for client messages and then forwards them
def handle(client):
    while True:
        try:
            # gets message from client and forwards it to everyone
            message = client['socket'].recv(1024)
            broadcast(message)
        except:
            # TODO: this won't work this way need to redo for graceful failure or maybe kind of keep
            # if error detected, deletes client from clients array and closes connection with client
            # thread will close once execution is done
            index = find_client(clients, client['user_name'])
            clients.pop(index)
            client.close()
            broadcast('{} left!'.format(client['user_name']).encode())
            break

# listening for tcp connections
def receive():
    while True:
        # server accepts connection from client
        client, address = server.accept()
        print('Connected with {}'.format(str(address)))

        # server must receive user name from client as part of initializing connection
        name_message = client.recv(1024).decode()

        print("ORIGINAL MESSAGE")
        print(name_message)

        name_message = name_message.split(':')
        command = name_message[0]
        chat_name = name_message[-1]
        
        setting_user_name = True
        while setting_user_name:

            print("ENTERING USER NAME LOOP")

            if command != 'NAME':
                client.send('ERROR:106:Client not registered with server'.encode())
                name_message = client.recv(1024).decode()

                print("ERROR MESSAGE 1")
                print(name_message)

                name_message = name_message.split(':')
                command = name_message[0]
                chat_name = name_message[-1]
            elif find_client(clients, chat_name) != -1:
                client.send('ERROR:105:Username already in use'.encode())
                name_message = client.recv(1024).decode()

                print("ERROR MESSAGE 2")
                print(name_message)

                name_message = name_message.split(':')
                command = name_message[0]
                chat_name = name_message[-1]
            else:
                setting_user_name = False

        connection = {
            'user_name': chat_name,
            'socket': client 
        }
        # Add new socket to list of connected clients
        clients.append(connection)

        print('Username is {}'.format(connection['user_name']))
        broadcast('{} joined!'.format(connection['user_name']).encode())
        connection['socket'].send('Connected to server!'.encode())

        # creating a thread for each client TCP connection
        thread = threading.Thread(target=handle, args=(connection,))
        thread.start()

# Running server and catching all unexpected/unhandled errors
try:
    receive()
except:
    print('Unexpected Server Error: Connection has closed')
    server.close()
