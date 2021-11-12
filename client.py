import socket
import threading

# TODO: replace this with AWS host
HOST = '127.0.0.1'
PORT = 2787

nickname = input('Choose your nickname: ')

# RENAME TO CLIENT SOCKET
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# listening for chat messages and keepalive messages from server
def receive():
    while True:
        try:
            message = client.recv(1024).decode()
            if message == 'NICK':
                client.send(nickname.encode())
            else:
                print(message)
        except:
            print('An error!')
            client.close() 
            break

# sending messages
def write():
    while True:
        message = "{}: {}".format(nickname, input(''))
        client.send(message.encode())

# spinning up client and catching all unexpected/unhandled errors
try:
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
except:
    print('Unexpected Client Error: Connection has closed')
    client.close()
