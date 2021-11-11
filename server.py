import socket
import threading

HOST = '127.0.0.1'
PORT = 2787

# TODO: add comments
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

clients = []
nicknames = []

# Broadcast a message to all clients
def broadcast(message):
    for client in clients:
        client.send(message)

# TODO: rename
# This is what happens in an individual thread that listens for client messages and then forwards them
def handle(client):
    while True:
        try:
            # gets message from client and forwards it to everyone
            message = client.recv(1024)
            broadcast(message)
        except:
            # TODO: this won't work this way need to redo for graceful failure or maybe kind of keep
            # if error detected, deletes client from clients array and closes connection with client
            # thread will close once execution is done
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast("{} left!".format(nickname).encode())
            nicknames.remove(nickname)
            break

# listening for tcp connections
def receive():
    while True:
        # server accepts connection from client
        client, address = server.accept()
        print('Connected with {}'.format(str(address)))

        # TODO: refactor nickname stuff
        client.send('NICK'.encode())
        # server receives chat name from client as part of initializing connection
        nickname = client.recv(1024).decode()
        # refactor data object, get rid of nicknames list
        nicknames.append(nickname)
        clients.append(client)

        # notes for refactor
        # blah = {
        #     client_objet: client,
        #     chatname: nickname
        # }
        # clients.append(blah)

        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode())
        client.send("Connected to server!".encode())

        # creating a thread for each client TCP connection
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

# Running server and catching all unexpected/unhandled errors
try:
    receive()
except:
    print('Unexpected Server Error: Connection has closed')
    server.close()
