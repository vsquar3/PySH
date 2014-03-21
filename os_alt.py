import sys
import string
import re
from os import *
from os import getcwd, _Environ, chdir

class EnvironVarException(Exception):
    pass

class Environ_alt(_Environ):
    def __getitem__(self, key):
        try:
            value = self._data[self.encodekey(key)]
        except KeyError:
            raise EnvironVarException("Environmental variable not set: '%s'" % key)
        return self.decodevalue(value)

def _createenviron():
    encoding = sys.getfilesystemencoding()
    def encode(value):
        if not isinstance(value, str):
            value = str(value)
        return value.encode(encoding, 'surrogateescape')
    def encodekey(value):
        if not isinstance(value, str) or not value[0] in string.ascii_letters or len(list(re.finditer("[^\w\d_]", value))) > 0:
            raise EnvironVarException("Invalid variable name: '%s'" % value)
        return value.encode(encoding, 'surrogateescape')
    def decode(value):
        return value.decode(encoding, 'surrogateescape')
    data = environb
    return Environ_alt(data, encodekey, decode, encode, decode, _putenv, _unsetenv)

_putenv = putenv
_unsetenv = unsetenv
environ = _createenviron()
