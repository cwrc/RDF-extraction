import requests
import sys
from Env import env

session = requests.Session()


def login(auth):
    print(auth)
    response = session.post('http://beta.cwrc.ca/rest/user/login', auth)
    print(response)
    if response.status_code != 200:
        raise ValueError('Invalid response')


def usage():
    print("%s [username] [password]" % sys.argv[0])


def main(argv):            
    # Store the session for future requests.
    login({"username": argv[0], "password": argv[1]})
    res = session.get('http://beta.cwrc.ca/islandora/object/orlando%3A79764579-bb88-4d9f-9c6b-a70276b00d3a')
    print(res)



if __name__ == "__main__":
    argv = [env.env("USER_NAME", "NONE"), env.env("PASSWORD", "NONE")]
    main(argv)