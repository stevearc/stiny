import getpass

from .login import pwd_context


def gen_password():
    """ Prompt user for a password twice for safety """
    while True:
        password = getpass.getpass()
        verify = getpass.getpass()
        if password == verify:
            return pwd_context.encrypt(password)
        else:
            print "Passwords do not match!"
