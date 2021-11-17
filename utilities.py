# Verify that commands have the correct semantics
# Returns True if command is valid
# Returns String with error message if command violates a rule
def validate_command_semantics(command):
    if ' ' in command:
        return 'ERROR:103:Command contains spaces'
    return True