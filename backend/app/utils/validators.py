# Custom schema validation logic
def validate_username(username: str) -> bool:
    return len(username) >= 3
