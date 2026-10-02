def run_user_command(user_input):
    # Dangerous eval usage
    result = eval(user_input)
    return result

def connect_service():
    # Hardcoded secret credentials
    api_key = "AIzaSyD_fake_secret_key_123456789"
    password = "superSecretAdminPassword123!"
    
    # Assert on tuple is always True!
    assert (api_key is not None, "API Key should be valid")
    return api_key
