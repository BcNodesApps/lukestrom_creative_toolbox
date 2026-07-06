# Minimal stub for Python 3.13 where stdlib 'aifc' was removed.
# We don't actually read AIFF in this project; this is only to satisfy optional imports.
class Error(Exception):
    pass

def open(file, mode=None):
    raise Error("AIFF reading not supported in this environment.")
