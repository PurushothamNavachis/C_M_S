# Generic helpers functions
def sanitize_email(email: str) -> str:
    return email.strip().lower()
