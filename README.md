# RDF-extraction

Extraction scripts for transforming the Orlando XML data into Linked Data. (CWRC Ontology Edition)

Note: The LINCS (CIDOC-CRM) version of these extraction scripts can be found on the [cidoc-revisions](https://github.com/cwrc/RDF-extraction)

You must have Python installed, at least version 3.8.

## Setup

Clone the repository if you haven't already.
`git clone https://github.com/cwrc/RDF-extraction.git`

Switch to the CWRC branch
`git checkout origin/classic`

### Download files from CWRC

#### Prerequisites

You must have a CWRC account to be able to do this with the appropriate permissions. ([Sign up here](https://cwrc.ca/user))

In Root folder:

1. Create a Virtual Environment:
`python3 -m venv venv`
1. Start Virtual Environment:
`source ./venv/bin/activate`
1. Install modules:
`pip install -r requirements.txt`
1. Create an `.env` file with `username=XXX` and `password=yyy`, replacing `xxx` and `yyy` with the respective credentials.

Example file:

```env
username=John Doe
password=mySuperSecretpassword12!
```

#### Run download script

1. Run script:
`python3 islandora_auth.py`
(This by default will only download the Entries to `data/entries_YYYY-MM-DD` where YYYY, MM, DD are replaced with their respective date valuess)
1. Deactivate Virtual Environment:
`deactivate`

### To Run Extraction scripts (First time)

These commands take place in `Entry` folder (`cd Entry`)

1. Update `default directory` field within `testcases.json` to match where your source data files are (You can either copy the full path of the directory and add `/` or use a relative path like `../data/entry_YYYY-MM-DD/`)
1. Create a Virtual Environment:
`python3 -m venv venv`
1. Start Virtual Environment:
`source ./venv/bin/activate`
1. Install modules:
`pip install -r requirements.txt`
1. Run script `python3 bio_extraction.py`

### Running Extraction Scripts after set-up

1. in `Entry` folder (`cd Entry`), start Virtual Environment
`source ./venv/bin/activate`
1. Run script `python3 bio_extraction.py` or `python3 bio_extraction.py`

## Features

Run `python3 bio_extraction.py -h` for a list of available options

```text
No particular testcases available, please add to testcases.json
usage: bio_extraction.py [-h] [-qa | -s | -g | -i | -id ORLANDO | -f FILE | -d DIRECTORY | -r [RANDOM] | -l [LAST] | -fi [FIRST]] [-v {0,1,2,3}] [-fmt {rdf,rdf/xml,ttl,turtle,json-ld,nt,trix,n3,all}] [-u UPDATE] [-p]

Extract the Majority of biography related data information from selection of orlando xml documents

optional arguments:
  -h, --help            show this help message and exit
  -qa                   will run through qa test cases that are related to www.github.com/cwrc/testData/tree/master/qa, Which currently are:'aguigr', 'alcolo', 'atwoma', 'bronch', 'bronem', 'levyam', 'seacma',
                        'shakwi', 'woolvi'
  -s, -special          will run through special cases that are of particular interest atm which currently are: 'fielmi'
  -g, -graffles, -graffle
                        will run through cases related to our graffles'seacma', 'lel___', 'edgema', 'blesma', 'leonan'
  -i, -ignored          will run through files that are currently being ignored which currently include: 'fielmi'
  -id ORLANDO, -orlando ORLANDO, --orlando ORLANDO
                        entry id of a single orlando document to run extraction upon, ex. woolvi
  -f FILE, -file FILE, --file FILE
                        single orlando xml document to run extraction upon
  -d DIRECTORY, -directory DIRECTORY, --directory DIRECTORY
                        directory of files to run extraction upon
  -r [RANDOM], -random [RANDOM], --random [RANDOM]
                        chooses {RANDOM} random file(s) to run extraction upon
  -l [LAST], -last [LAST], --last [LAST]
                        chooses {last} file(s) to run extraction upon, ex. the last 20 files
  -fi [FIRST], -first [FIRST], --first [FIRST]
                        chooses {first} file(s) to run extraction upon, ex. the first 20 files
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        increase output verbosity
  -fmt {rdf,rdf/xml,ttl,turtle,json-ld,nt,trix,n3,all}, --format {rdf,rdf/xml,ttl,turtle,json-ld,nt,trix,n3,all}
  -p, -pause, --pause   pause after every entry to examine output and be prompted to continue/quit
```

Each script within `Entry/` can be run on its own, `bio_extraction.py` is the current main driver of biography that calls needed functions within separate scripts. The same arguments are applicable to those scripts.

Example:
If you just wanted to test the extraction of cultural forms. You could do `python3 culturalForm.py -r 1`

This would only extract from culturalform tags, from 1 random source file. This allows for better testing and more modular classes to be made.

## Additional Configuration details

## Design Considerations
