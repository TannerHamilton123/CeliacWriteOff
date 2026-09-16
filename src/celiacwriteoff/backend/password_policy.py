import re

MIN_LENGTH = 12


def validate_password_strength(password: str) -> None:
    """Raise ValueError with a readable message if the password is too weak."""
    errors = []
    if len(password) < MIN_LENGTH:
        errors.append(f"be at least {MIN_LENGTH} characters long")
    if not re.search(r"[A-Z]", password):
        errors.append("include an uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("include a lowercase letter")
    if not re.search(r"\d", password):
        errors.append("include a digit")
    if not re.search(r"[^\w\s]", password):
        errors.append("include a special character")
    if errors:
        raise ValueError("Password must " + "; ".join(errors))
