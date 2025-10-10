# Orlando RDF-extraction based on the CWRC Ontology

Extraction scripts for transforming the Orlando XML data into Linked Data (CWRC Ontology Edition).

> Note: The LINCS (CIDOC-CRM) version of these extraction scripts can be found on the [cidoc-revisions](https://github.com/cwrc/RDF-extraction)

You must have **Python ≥3.14** and **uv** installed.

---

## Optional VS Code configuration

1. Go to Extensions tab: `Shift+Cmd+X`
2. Search `@recommended`
3. Click the download button next to **WORKSPACE RECOMMENDATIONS** to install all recommended extensions.

---

## Setup

### Clone the repository

```bash
git clone https://github.com/cwrc/RDF-extraction.git
cd RDF-extraction

```

### Switch to the CWRC branch

`git switch classic`

> Check [most recent branches](https://github.com/cwrc/RDF-extraction/branches) if unsure and consult @alliyya.
(Oct 4, 2024: currently `59-small-biography-clean-up-tasks`)

---

## Accessing Source Data

### Use source data from GitLab (recommended)

```bash
git clone https://gitlab.com/calincs/cwrc/orlando-2.0-c-modelling.git
cd orlando-2.0-c-modelling
git switch LOD-extraction-2024
```

- Or in VS Code: Command Palette → `Git: Clone` → paste repo URL → switch branch to `LOD-extraction-2024`.
- The repository is large; cloning may take some time.

### Optional: Download files from CWRC (requires permissions)

- Create a `.env` file in the root:

```env
username=YourUsername 
password=YourPassword`
```

- Run download script:
`uv run python -m islandora_auth`
- Files will download to `data/entries_YYYY-MM-DD`.

## Project Environment Setup

1. Create and activate the uv virtual environment:

    ```bash
    uv venv
    source .venv/bin/activate
    ```

2. Sync dependencies:

    ```bash
    uv sync
    ```

---

## Running Extraction Scripts

All commands assume:

- Virtual environment is **active** (`source .venv/bin/activate`)
- You are in the root folder of the repository

### Quick test on 1 random entry

`uv run python -m entry.bio_extraction -r 1`

### Quick test on a specific entry

`uv run python -m entry.bio_extraction -id moulma`

### Full extraction

`uv run python -m entry.bio_extraction`

### Running modular scripts (example: culturalForm)

`uv run python -m entry.culturalForm -r 1`

> Arguments follow the same format as `bio_extraction.py -h`.

## Updating `testcases.json`

- Make sure the `default directory` field matches the path of your source data.
- Can use **absolute paths** or **relative paths** like `data/entries_YYYY-MM-DD/`.

---

## Notes for New Contributors

- `uv run` ensures the **correct Python interpreter** and dependency versions from `uv.lock` are used.
- You can also activate the environment and run scripts directly:

`source .venv/bin/activate python -m entry.bio_extraction -r 1`

> Using `uv run` is safer and ensures reproducibility.

---

## Features

Run:

`python -m entry.bio_extraction -h`

to see all available options:

```text
No particular testcases available, please add to testcases.json usage: bio_extraction.py [-h] [-qa | -s | -g | -i | -id ORLANDO | -f FILE | -d DIRECTORY | -r [RANDOM] | -l [LAST] | -fi [FIRST]] [-v {0,1,2,3}] [-fmt {rdf,rdf/xml,ttl,turtle,json-ld,nt,trix,n3,all}] [-u UPDATE] [-p]  Extract the Majority of biography related data information from selection of orlando xml documents
```

- Each script in `Entry/` can be run independently.
- `bio_extraction.py` is the main driver but modular scripts use the same arguments.
- Examples:

```bash
uv run python -m entry.culturalForm -r 1 
uv run python -m entry.location -r 5`
```

---

## Design Considerations

- Extraction scripts are modular to allow testing of individual components.
- `-r`, `-l`, `-fi`, `-id` options allow fine-grained control over which entries are processed.
- Scripts are designed to work with both GitLab source files and CWRC downloads (with permissions).
- uv ensures consistent Python environment and dependencies across contributors.
