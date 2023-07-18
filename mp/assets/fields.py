from django.db import models
from common.secret.lib import signer

class CipherCharField(models.CharField):

    def __init__(self, *args, **kwargs):
        if 'prefix' in kwargs:
            self.prefix = kwargs['prefix']
            del kwargs['prefix']
        else:
            self.prefix = "aes:::"
        self.cipher = signer
        super(CipherCharField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CipherCharField, self).deconstruct()
        if self.prefix != "aes:::":
            kwargs['prefix'] = self.prefix
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if value.startswith(self.prefix):
            value = value[len(self.prefix):]
            value = self.cipher.unsign(value)
        return value

    def to_python(self, value):
        if value is None:
            return value
        elif value.startswith(self.prefix):
            value = value[len(self.prefix):]
            value = self.cipher.unsign(value)
        return value

    def get_prep_value(self, value):
        if isinstance(value, str) or isinstance(value, bytes):
            value = self.cipher.sign(value)
            value = self.prefix + value
        elif value is not None:
            raise TypeError(str(value) + " is not a valid value for CipherCharField")
        return value
