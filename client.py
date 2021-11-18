import socket
import threading
import utilities

# TODO: replace this with AWS host
HOST = '127.0.0.1'
PORT = 2787

# Create TCP connection with server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, PORT))

# listening for chat messages and keepalive messages from server
def listen_for_message():
    while True:
        try:
            message = server.recv(1024).decode()
            message = message.split(':')
            command = message[0]

            command_check = utilities.validate_command_semantics(command)
            if command_check != True:
                server.send(command_check.encode())
                continue

            match command:
                case 'JOIN_RESPONSE':
                    room_name = message[-1]
                    # Validate that room name is correctly formatted
                    param_check = utilities.validate_param_semantics(room_name)
                    if param_check != True:
                        server.send(param_check.encode())
                        continue
                    print('You are a member of {}'.format(room_name))

                case 'ROOMS_RESPONSE':
                    rooms = message[-1]

                    if rooms == ' ':
                        print('There are no chat rooms')
                    else:
                       rooms = rooms.split(' ')
                       print('Chat Rooms:')
                       for room in rooms:
                           print(room)

                case 'ERROR':
                    error_code = message[1]
                    error_msg = message[-1]
                    print('{} Error: {}'.format(error_code, error_msg))

                case _:
                    message = 'ERROR:100:Command is not included in the list of approved commands'
                    server.send(message.encode())
        except Exception as E:
            print(E)
            print('An error!')
            server.close() 
            break


# sending messages
def send_message():
    while True:
        message = input('')
        server.send(message.encode())

# spinning up client and catching all unexpected/unhandled errors
try:
    listening_thread = threading.Thread(target=listen_for_message)
    listening_thread.start()

    # Create unique user name and initiate one-way handshake with server
    # User must format input as NAME:username
    print('Welcome to IRC!')
    user_name_message = input('')
    server.send(user_name_message.encode())

    sending_thread = threading.Thread(target=send_message)
    sending_thread.start()
except:
    print('Unexpected Client Error: Connection has closed')
    server.close()
