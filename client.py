import socket
import threading

# TODO: replace this with AWS host
HOST = '127.0.0.1'
PORT = 2787

# Create TCP connection with server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, PORT))

# Create unique user name and initiate one-way handshake with server
user_name = input('Please input your username: ')
message = 'NAME:{}'.format(user_name)
server.send(message.encode())

# listening for chat messages and keepalive messages from server
def listen_for_message():
    while True:
        try:
# if receive either username error, then re-enter username info

            message = server.recv(1024).decode()
            print(message)
        except:
            print('An error!')
            server.close() 
            break

# sending messages
def send_message():
    while True:
        message = '{}: {}'.format(user_name, input(''))
        server.send(message.encode())

# spinning up client and catching all unexpected/unhandled errors
try:
    listening_thread = threading.Thread(target=listen_for_message)
    listening_thread.start()

    sending_thread = threading.Thread(target=send_message)
    sending_thread.start()
except:
    print('Unexpected Client Error: Connection has closed')
    server.close()
