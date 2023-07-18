from .models import MyUser


def auth_user_get_jwt_secret_key(user: MyUser) -> str:
    return str(user.jwt_key)


def auth_jwt_response_payload_handler(
        token, user=None, redirect=None, issued_at=None
):
    """
    Return data ready to be passed to serializer.
    """
    return {'token': token, 'redirect': redirect}
