# This is only a functions file for scrapyFamily.py
def usage():
    print("%s [username] [password]" % sys.argv[0])
def startLogin():
    default_user = "NONE"
    default_password = "NONE"
    if len(sys.argv) > 2:
        default_user = sys.argv[1]
        default_password = sys.argv[2]
    argv = [env.env("USER_NAME", default_user), env.env("PASSWORD", default_password)]
    main(argv)

def login(auth):
    print(auth)
    response = session.post('http://beta.cwrc.ca/rest/user/login', auth)
    print(response)
    if response.status_code != 200:
        raise ValueError('Invalid response')
    else:
        link = 'http://beta.cwrc.ca/islandora/rest/v1/object/'
        objectToGet = 'orlando%3Ad9ab7813-1b1d-42c8-98b0-9712398d8990/datastream/CWRC/?content=true'

        r2 = session.get(link+objectToGet)
        if r2.status_code == 200:
            print("got the content")
            # print(r2.pid)
            getFamilyInfo(r2.text)
            getBirth(r2.text)
            getDeath(r2.text)
        else:
            print(r2.text)
    # print("this is where you would log in")
def main(argv):            
    # Store the session for future requests.
    login({"username": argv[0], "password": argv[1]})


def get_file_description(uuid):
    res = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/' + uuid);
    return res.text

def get_file_with_format(uuid, format):
    res = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/' + uuid + '/datastream/' + format)
    return res.text

