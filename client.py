import socket
import threading
import time
import utilities
from datetime import datetime, timedelta

# ==============================================================================================
#                                    Global Client State
# ==============================================================================================

# IP address of AWS hosted server
HOST = '54.188.19.136'
# Port number specified in protocol
PORT = 2787

# Dictionary to track information about the status of the client's TCP connection with the server
connection_status = {
    # 'alive' key is set to False if connection with server is severed
    'alive': True,
    # 'finalized' key is set to True once client and server have finished exchanging connection initialization messages
    'finalized': False,
    # 'timestamp' key tracks the last time a STILL_ALIVE message is received from the server
    'timestamp': datetime.now()
}

# Create TCP connection with server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, PORT))

# ==============================================================================================
#                               Connection Maintenance Functions
# ==============================================================================================

# Close client connection with server
def close_connection():
    connection_status['alive'] = False
    server.close()

# Function waits until connection with server has finished initializing
# Returns True if the connection is terminated before it finishes initializing
# Returns False once the connection has successfully finished initializing
def check_status():
    while not connection_status['finalized']:
        if not connection_status['alive']:
            return True
    return False

# Function monitors connection status while sleeping for the number of seconds specified by the seconds parameter
# Returns True if the connection is terminated before wait finishes
# Returns False once the wait has finished
# Takes Integer as argument
def keep_alive_wait(seconds):
    counter = 0
    while (counter < seconds):
        time.sleep(1)
        counter += 1
        if not connection_status['alive']:
            return True
    return False

# Function sends STILL_ALIVE messages to server to ensure server knows that this client's connection is still alive
def send_keep_alive():
    try:
        # Don't send STILL_ALIVE message if connection does not initialize successfully
        if check_status():
            return

        while True:
            msg = 'STILL_ALIVE'
            send_message(server, msg)

            # Wait 5 seconds in between each STILL_ALIVE message and stop sending messages if connection closes
            if keep_alive_wait(5):
                return
    
    # End program if unexpected error occurs
    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection()

# Function verifies that STILL_ALIVE messages are being received from the server within the timeout window
def verify_keep_alive():
    try:
        alive_window = timedelta(seconds = 10)

        # Don't check for STILL_ALIVE messages if connection does not initialize successfully
        if check_status():
            return

        while True:
            # Wait 10 seconds in between checking timestamp from last STILL_ALIVE message
            # and stop checking messages if connection closes
            if keep_alive_wait(10):
                return

            # If STILL_ALIVE message is not received from the server within the last 10 seconds,
            # then the client assumes the server is down and ends the program
            window_start = datetime.now() - alive_window
            if connection_status['timestamp'] < window_start:
                print('Unexpected Error: Server is no longer online')
                close_connection()
                return

    # End program if unexpected error occurs
    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection()

# ==============================================================================================
#                                    Message Handlers
# ==============================================================================================

# Send encoded message to server over TCP connection
# Takes a socket object and a string as arguments
def send_message(server_socket, msg):
    server_socket.send(msg.encode())

# Function displays confirmation that user has successfully created or joined a chat room
# Called in response to receiving JOIN_RESPONSE message from the server
# Takes List of Strings as argument
def join_response_msg_handler(message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(server, param_check)
        return
    print('You are a member of {}\n'.format(room_name))

# Function displays list of chat rooms
# Called in response to receiving ROOMS_RESPONSE message from the server
# Takes List of Strings as argument
def rooms_response_msg_handler(message):
    rooms = message[-1]
    # Displays default text if no chat rooms have been created
    if rooms == ' ':
        print('There are no chat rooms\n')
    else:
        rooms = rooms.split(' ')
        print('Chat Rooms:')
        for room in rooms:
            print(room)
        print('')

# Function displays members list of a chat room
# Called in response to receiving USERS_RESPONSE message from the server
# Takes List of Strings as argument
def users_response_msg_handler(message):
    room_name = message[1]
    members = message[-1]

    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(server, param_check)
        return

    # Displays default text if no users in chat room
    if members == ' ':
        print('There are no members of {}\n'.format(room_name))
    else:
        members = members.split(' ')
        print('Members of {}:'.format(room_name))
        for member in members:
            print(member)
        print('')

# Function displays confirmation that user has successfully exited a chat room
# Called in response to receiving LEAVE_RESPONSE message from the server
# Takes List of Strings as argument
def leave_response_msg_handler(message):
    room_name = message[-1]
    # Validate that room name is correctly formatted
    param_check = utilities.validate_param_semantics(room_name)
    if param_check != True:
        send_message(server, param_check)
        return
    print('You are no longer a member of {}\n'.format(room_name))

# Function displays messages sent to a chat room where the user is a member
# Called in response to receiving MESSAGE message from the server
# Takes List of Strings as argument
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


# Called in response to receiving MESSAGE message from the server
# Takes List of Strings as argument
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

        # End program if unexpected error occurs     
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

    # End program if unexpected error occurs
    except Exception as E:
        print('Unexpected Error: Connection has closed')
        close_connection()

# ==============================================================================================
#                                       Client Program
# ==============================================================================================

try:
    # Launch thread to listen for messages from the server
    listening_thread = threading.Thread(target=listen_for_message)
    listening_thread.start()

    # Create unique user name and initiate one-way handshake with server
    # User must format input as NAME:username
    print('Welcome to IRC!\n')
    user_name_message = input('')
    print('')
    send_message(server, user_name_message)

    # Launch thread to collect input from the user
    sending_thread = threading.Thread(target=input_handler)
    sending_thread.start()

    # Launch thread to send STILL_ALIVE messages to server
    sending_thread = threading.Thread(target=send_keep_alive)
    sending_thread.start()

    # Launch thread to monitor if connection with server is being maintained
    sending_thread = threading.Thread(target=verify_keep_alive)
    sending_thread.start()

# End program if unexpected error occurs
except Exception as E:
    print('Unexpected Error: Connection has closed')
    close_connection()
