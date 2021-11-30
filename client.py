from datetime import datetime, timedelta
import socket
import threading
import utilities
import time



HOST = '54.188.19.136'
PORT = 2787

# Create TCP connection with server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, PORT))

connection_status = {
    'alive': True,
    'finalized': False,
    'timestamp': datetime.now()
}



def send_message(server_socket, msg):
    server_socket.send(msg.encode())


def close_connection():
    connection_status['alive'] = False
    server.close()

def join_response_msg_handler(message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(server, param_check)
        return
    print('You are a member of {}\n'.format(room_name))


def rooms_response_msg_handler(message):
    rooms = message[-1]
    if rooms == ' ':
        print('There are no chat rooms\n')
    else:
        rooms = rooms.split(' ')
        print('Chat Rooms:')
        for room in rooms:
            print(room)
        print('')


def users_response_msg_handler(message):
    room_name = message[1]
    members = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(server, param_check)
        return

    if members == ' ':
        print('There are no members of {}\n'.format(room_name))
    else:
        members = members.split(' ')
        print('Members of {}:'.format(room_name))
        for member in members:
            print(member)
        print('')


def leave_response_msg_handler(message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(server, param_check)
        return
    print('You are no longer a member of {}\n'.format(room_name))


def chat_msg_handler(message):
    room_name = message[1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(server, param_check)
        return

    sender = message[2]
    # Validate that message sender is correctly formatted
    param_check = utilities.validate_param_semantics(sender)
    if param_check != True:
        send_message(server, param_check)
        return

    if len(message) > 4:
        message_body = ':'.join(message[3:])
    else:
        message_body = message[3]
    # Validate that message body is correctly formatted
    payload_check = utilities.validate_payload_semantics(message_body)
    if payload_check != True:
        send_message(server, payload_check)
        return

    print('Room: {}'.format(room_name))
    print('User: {}'.format(sender))
    print(message_body)
    print('')



def private_msg_handler(message):
    receiving_user = message[1]
    # Validate that receiving username is correctly formatted
    param_check = utilities.validate_param_semantics(receiving_user)
    if param_check != True:
        send_message(server, param_check)
        return

    sending_user = message[2]
    # Validate that sending username is correctly formatted
    param_check = utilities.validate_param_semantics(sending_user)
    if param_check != True:
        send_message(server, param_check)
        return

    if len(message) > 4:
        message_body = ':'.join(message[3:])
    else:
        message_body = message[3]
    # Validate that message body is correctly formatted
    payload_check = utilities.validate_payload_semantics(message_body)
    if payload_check != True:
        send_message(server, payload_check)
        return

    print('Message From: {}'.format(sending_user))
    print('Message To: {}'.format(receiving_user))
    print(message_body)
    print('')






# listening for chat messages and keepalive messages from server
def listen_for_message():
    while True:
        try:
            message = server.recv(1024).decode()
            message = message.split(':')
            command = message[0]

            command_check = utilities.validate_command_semantics(command)
            if command_check != True:
                send_message(server, command_check)
                continue

            match command:
                case 'STILL_ALIVE':
                    connection_status['timestamp'] = datetime.now()
                    connection_status['finalized'] = True
                case 'JOIN_RESPONSE':
                    join_response_msg_handler(message)
                case 'ROOMS_RESPONSE':
                    rooms_response_msg_handler(message)
                case 'USERS_RESPONSE':
                    users_response_msg_handler(message)
                case 'LEAVE_RESPONSE':
                    leave_response_msg_handler(message)
                case 'MESSAGE':
                    chat_msg_handler(message)
                case 'MESSAGE_USER':
                    private_msg_handler(message)
                case 'QUIT':
                    close_connection()
                    break
                case 'ERROR':
                    error_code = message[1]
                    match error_code:
                        case '107':
                            room_name = message[2]
                            print("{} Error: '{}' room does not exist\n".format(error_code, room_name))
                        case '108':
                            room_name = message[2]
                            print("{} Error: You cannot post to '{}' when you are not a member\n".format(error_code, room_name))
                        case '109':
                            member = message[2]
                            print("{} Error: User '{}' does not exist\n".format(error_code, member))
                        case _:
                            error_msg = message[-1]
                            print('{} Error: {}\n'.format(error_code, error_msg))
                case _:
                    message = 'ERROR:100:Command is not included in the list of approved commands'
                    send_message(server, message)
        except Exception as E:
            print('Unexpected Error: Connection has closed')
            close_connection()
            break

# sending messages
def input_handler():
    try:
        while True:
            message = input('')
            print('')
            if not connection_status['alive']:
                break
            send_message(server, message)
    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection()


def check_status():
    while not connection_status['finalized']:
        if not connection_status['alive']:
            return True
    return False

def keep_alive_wait(seconds):
    counter = 0
    while (counter < seconds):
        time.sleep(1)
        counter += 1
        if not connection_status['alive']:
            return True
    return False



def send_keep_alive():
    try:
        if check_status():
            return

        while True:
            msg = 'STILL_ALIVE'
            send_message(server, msg)

            if keep_alive_wait(5):
                return

    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection()


def verify_keep_alive():
    try:
        alive_window = timedelta(seconds = 10)
        
        if check_status():
            return

        while True:
            if keep_alive_wait(10):
                return

            window_start = datetime.now() - alive_window

            if connection_status['timestamp'] < window_start:
                print('Unexpected Error: Server is no longer online')
                close_connection()
                break

    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection()




# spinning up client and catching all unexpected/unhandled errors
try:
    listening_thread = threading.Thread(target=listen_for_message)
    listening_thread.start()

    # Create unique user name and initiate one-way handshake with server
    # User must format input as NAME:username
    print('Welcome to IRC!\n')
    user_name_message = input('')
    print('')
    send_message(server, user_name_message)

    sending_thread = threading.Thread(target=input_handler)
    sending_thread.start()

    sending_thread = threading.Thread(target=send_keep_alive)
    sending_thread.start()

    sending_thread = threading.Thread(target=verify_keep_alive)
    sending_thread.start()

except Exception as E:
    print('Unexpected Error: Connection has closed')
    connection_status['alive'] = False
    server.close()
