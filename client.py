import socket
import threading

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
# if receive either username error, then re-enter username info
            message = server.recv(1024).decode()

            print("RECEIVED FROM SERVER")
            print(message)

            message = message.split(':')
            command = message[0]

            match command:
                case 'ERROR':
                    error_code = message[1]
                    error_msg = message[-1]

                    print('ERROR CODE')
                    print(error_code)

                    match error_code:
                        case '105'|'106':
                            print(error_msg, flush=True)
                            print('Please input a new username: ', end='')
                            user_name = input()
                            print('')
                            message = 'NAME:{}'.format(user_name)

                            print("ERROR RESPONSE MESSAGE")
                            print(message)

                            server.send(message.encode())
                        case _:
                            print(error_msg)
                case _:
                    print(message)

            print("REENTERING LOOP")

        except Exception as e:
            print(e)
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

    # Create unique user name and initiate one-way handshake with server
    user_name = input('Please input your username: ')
    print('')
    message = 'NAME:{}'.format(user_name)

    print("FIRST MESSAGE")
    print(message)

    server.send(message.encode())

    sending_thread = threading.Thread(target=send_message)
    sending_thread.start()
except:
    print('Unexpected Client Error: Connection has closed')
    server.close()
