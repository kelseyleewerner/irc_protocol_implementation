# Verify that commands have the correct semantics
# Returns True if command is valid
# Returns String with error message if command violates a rule
# Takes String as argument
def validate_command_semantics(command):
    if ' ' in command:
        return 'ERROR:103:Command contains spaces'
    return True

# Verify that parameters have the correct semantics
# Returns True if parameter is valid
# Returns String with error message if parameter violates a rule
# Takes String as argument
def validate_param_semantics(param):
    if ' ' in param:
        return 'ERROR:104:Parameter contains spaces'
    elif len(param) > 50:
        return 'ERROR:101:Parameter has exceeded allowed value of 50 characters'
    return True

# Verify that payload has the correct semantics
# Returns True if payload is valid
# Returns String with error message if payload violates a rule
# Takes String as argument
def validate_payload_semantics(payload):
    if len(payload) > 500:
        return 'ERROR:102:Payload has exceeded allowed value of 500 characters'
    return True