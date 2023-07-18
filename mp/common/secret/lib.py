# -*- coding: utf-8 -*
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
import hashlib, base64


def generate_key(value) -> bytes:
    return base64.urlsafe_b64encode(value)


class Singleton(type):
    def __init__(cls, name, bases, attrs):
        super(Singleton,cls).__init__(name, bases, attrs)
        cls.__instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Singleton,cls).__call__(*args, **kwargs)
        return cls.__instance


# 对称加密
class Cipher(metaclass=Singleton):
    def __init__(self, key):
        self.key = generate_key(hashlib.sha256(key.encode()).digest())
        self.f = Fernet(self.key)

    def sign(self,value):
        if isinstance(value,str):
            value = value.encode('utf-8')
        return self.f.encrypt(value).decode('utf-8')

    def unsign(self,value,ttl=None):
        if isinstance(value,str):
            value = value.encode('utf-8')
        try:
            if ttl:
                return self.f.decrypt(value,ttl=ttl).decode('utf-8')
            else:
                return self.f.decrypt(value).decode('utf-8')
        except InvalidToken:
            return None


signer = Cipher(settings.SECRET_KEY)
