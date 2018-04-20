import requests
import sys
from Env import env

session = requests.Session()


def login(auth):
    #print(auth)
    response = session.post('http://beta.cwrc.ca/rest/user/login', auth)
    print(response)
    if response.status_code != 200:
        raise ValueError('Invalid response')


def usage():
    print("%s [username] [password]" % sys.argv[0])


def main(argv):            
    # Store the session for future requests.
    login({"username": argv[0], "password": argv[1]})


def get_file_description(uuid):
    res = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/' + uuid);
    return res.text

def get_file_with_format(uuid, format):
    res = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/' + uuid + '/datastream/' + format)
    return res.text



if __name__ == "__main__":
    default_user = "NONE"
    default_password = "NONE"
    if len(sys.argv) > 2:
        default_user = sys.argv[1]
        default_password = sys.argv[2]
    argv = [env.env("USER_NAME", default_user), env.env("PASSWORD", default_password)]
    main(argv)