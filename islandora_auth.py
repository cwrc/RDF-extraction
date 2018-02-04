import requests
import sys





def login(auth):
    s = requests.Session()
    response = s.get('http://beta.cwrc.ca/rest/user/login'i, auth=auth)
    if response.status_code != 200:
        raise ValueError('Invalid response')
    return s


def usage():
    print("%s [username] [password]" % sys.argv[0])


def main(argv):            
    # Store the session for future requests.
    s = login((argv[0], argv[1]))


if __name__ == "__main__":
