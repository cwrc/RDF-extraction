import requests
import sys
from Env import env

session = requests.Session()


def login(auth):
    response = session.get('http://beta.cwrc.ca/rest/user/login', auth=auth)
    if response.status_code != 200:
        raise ValueError('Invalid response')


def usage():
    print("%s [username] [password]" % sys.argv[0])


def main(argv):            
    # Store the session for future requests.
    login((argv[0], argv[1]))


if __name__ == "__main__":
    argv = [env.env("USER_NAME", "NONE"), env.env("PASSWORD", "NONE")]
    main(argv)