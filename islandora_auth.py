import requests
import sys
import os
import datetime
from Env import env

session = requests.Session()

collections = {
    "bibliography": "orlando:7397f8b2-10d9-48b6-8af5-6c2cd24f50b5",
    "person": "orlando:348397a1-6edb-4c23-ba26-59f35e5bc8d6",
    "events": "orlando:e6b8f85f-5a79-4124-b2a2-3b41c3ddb2cf",
    "organizations": "orlando:455113b8-703d-4c15-af1e-53ce0a3beef2",
    "entry": "orlando:c5f53703-1f08-4c72-9425-2874bb7cf544"
}

def login(auth):
    response = session.post('https://cwrc.ca/rest/user/login', auth)
    if response.status_code != 200:
        raise ValueError('Invalid response')


def usage():
    print( f"{sys.argv[0]} [username] [password]")


def get_datastream(file_desc):
    models = file_desc["models"]
    if "cwrc:documentCModel" in models:
        return "CWRC"
    elif "cwrc:citationCModel" in models:
        return "MODS"
    elif "cwrc:person-entityCModel" in models:
        return "PERSON"
    elif "cwrc:organization-entityCModel" in models:
        return "ORGANIZATION"
    
    print("Unexpected Models:")
    print(models)
    exit(1)

def download_data(subset="all"):
    date = str(datetime.date.today())
    
    if subset== "all":
        for key in collections.keys():
            print(key)
            # r = get_file_description(collections[key])  s
            docs = get_document_ids(collections[key])
            dir =  f"data/{key}_{date}"
     
            try:
                os.mkdir(dir)
            except OSError as error:
                pass
            datastream = get_datastream(get_file_description(docs[0]))

            total = len(docs)
            count = 1
            for x in docs:
                print(count, "/", total, ": ", x)
                count += 1
                file_id = x.split(":")[1]
                
                content = get_file_with_format(x, datastream)
                f = open(dir+"/"+file_id+".xml", "w")
                f.write(content)
                f.close()
    else:
        if subset not in collections:
            print(f"Invalid subset '{subset}' specified")
            print(f"Valid subsets include: ",sep="")
            print(*collections.keys(), sep="\n")
            exit(1)
        docs = get_document_ids(collections[subset])
        dir =  f"data/{subset}_{date}"

        try:
            os.mkdir(dir)
        except OSError as error:
            pass
        datastream = get_datastream(get_file_description(docs[0]))

        total = len(docs)
        count = 1
        for x in docs:
            print(count, "/", total, ": ", x)
            count += 1
            file_id = x.split(":")[1]
            content = get_file_with_format(x, datastream)
            f = open(dir+"/"+file_id+".xml", "w")
            f.write(content)
            f.close()

def main(argv):            
    # Store the session for future requests.
    login({"username": argv[0], "password": argv[1]})
    download_data("entry")


def get_document_ids(collection_id):
    # Returns list of document IDS given the collection
    res = session.get(
        'https://cwrc.ca/islandora/rest/v1/solr/RELS_EXT_isMemberOfCollection_uri_mt:"'+collection_id+'"?fl=PID&rows=999999&start=0&wt=json')
    res = res.json()
    docs = [x["PID"] for x in res["response"]["docs"]]
    return docs

def get_file_description(uuid,json=True):
    res = session.get('https://cwrc.ca/islandora/rest/v1/object/' + uuid)
    if json:
        return res.json()
    return res.text

def get_file_with_format(uuid, format):
    res = session.get('https://cwrc.ca/islandora/rest/v1/object/' + uuid + '/datastream/' + format)
    res.encoding = "utf-8"
    return res.text


if __name__ == "__main__":
    default_user = "NONE"
    default_password = "NONE"
    if len(sys.argv) > 2:
        default_user = sys.argv[1]
        default_password = sys.argv[2]
    argv = [env.env("username", default_user), env.env("password", default_password)]
    main(argv)
