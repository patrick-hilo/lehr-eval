from fastapi import Request


ADMIN_SESSION_KEY = "admin_authenticated"


def admin_is_authenticated(request: Request) -> bool:
    return bool(request.session.get(ADMIN_SESSION_KEY))


def mark_admin_authenticated(request: Request) -> None:
    request.session[ADMIN_SESSION_KEY] = True


def clear_admin_authentication(request: Request) -> None:
    request.session.pop(ADMIN_SESSION_KEY, None)


def password_matches(candidate: str, expected: str) -> bool:
    return bool(expected) and candidate == expected
