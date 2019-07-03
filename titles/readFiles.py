from bs4 import BeautifulSoup
import os
from os import listdir
import sys
import csv

def parseFile(xmlFile):
    titleList = []
    with open(xmlFile, encoding="ISO-8859-1") as f:
        soup = BeautifulSoup(f, "lxml")
        titles = soup.find_all("title")
        titles_seen = [] # do not duplicate titles that have been seen

        for t in titles:
            if 'reg' in t.attrs:
                regular_text = t.attrs['reg']
            else:
                regular_text = t.get_text()

            if regular_text in titles_seen:
                continue
            
            tempDict = {"normalized": regular_text, "content:": t.get_text(), "documents": [xmlFile.split("/")[-1]]}
            for key, value in t.attrs.items():
                if key == "reg":
                    continue
                tempDict[key] = value

            titleList.append(tempDict)
            titles_seen.append(regular_text)

    return titleList


def compareTitleRefs(xmlFile, ref_title):
    with open(xmlFile, encoding="ISO-8859-1") as f:
        soup = BeautifulSoup(f, "lxml")

        titles = soup.find_all("title")
        bibcites = soup.find_all("bibcit")

        titles_seen = []

        index = 0
        matched_titles = []
        unmatched_titles = []
        for item in titles:
            bibcite = item.parent.find('bibcit')
            
            
            title = item

            normalized_title = title.attrs['reg'] if 'reg' in item.attrs else title.get_text()

            if normalized_title in titles_seen:
                continue

            titles_seen.append(normalized_title)

            tempDict = {"normalized": normalized_title, "content:": title.get_text(), "documents": [xmlFile.split("/")[-1]]}
            for key, value in title.attrs.items():
                if key == "reg":
                    continue
                tempDict[key] = value

            
            if bibcite is None:
                unmatched_titles.append(tempDict)
                continue
            
            if 'dbref' not in bibcite.attrs:
                continue

            item_id = bibcite.attrs['dbref']
            # item_id = item.attrs['dbref']

            if item_id not in ref_title:
                print(str.format("Bibref {} not found", item_id))
                continue

            bib_title = ref_title[item_id]


            if bib_title == title.get_text() or bib_title == normalized_title:
                # Mapping found
                matched_titles.append((tempDict, item_id))
            else:
                unmatched_titles.append(tempDict)
    
    return {"matched": matched_titles, "unmatched": unmatched_titles}


def toFile(name, results, fieldnames):
    with open(name, "w") as f:
        listFieldNames = list(fieldnames)
        # print("fieldnames")
        # print(listFieldNames)
        writer = csv.DictWriter(f, fieldnames=listFieldNames)
        writer.writeheader()
        for key, value in results.items():
            
            value['documents'] = ",".join(value['documents'])
            for unique_key in fieldnames:
                if unique_key not in value:
                    value[unique_key] = ""
                
            #print("values")
            # print(value)
            writer.writerow(value)


def bibligraphyTitles(files):
    ref_title = {}
    for f in files:
        file_name = f.split("/")[-1].split(".")[0]
        with open(f) as of:
            soup = BeautifulSoup(of, "lxml")

            title = soup.find('title')
            if title == None:
                continue
            title_value = title.get_text().strip()
            ref_title[file_name] = title_value
    
    return ref_title




if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(str.format("Usage: python {} [files_dir] [bibliograph_dir]", sys.argv[0]))

    filePath = sys.argv[1]
    
    orlandoFiles = [os.path.join(r,file) for r,d,f in os.walk(filePath) for file in f]
    
    results = {}
    unique_columns = set(['count'])
    matched_columns = set(['count', 'dbref'])
    unmatched_columns = set(['count'])

    bibfile_path = sys.argv[2]
    bibfiles = [os.path.join(r, file) for r,d,f in os.walk(bibfile_path) for file in f]

    ref_titles = bibligraphyTitles(bibfiles)


    matched_titles = {}
    unmatched_titles = {}


    for f in orlandoFiles:
        if f.endswith("-d.xml"):
            continue
        titles = compareTitleRefs(f, ref_titles)

        for matched_vals in titles['matched']:
            matched = matched_vals[0]
            matched_columns = set(matched.keys()).union(matched_columns)

            if matched['normalized'] in matched_titles:
                matched_titles[matched['normalized']]['count'] += 1
                matched_titles[matched['normalized']]['documents'] += matched['documents']
            else:
                matched['count'] = 1
                matched['dbref'] = matched_vals[1]
                matched_titles[matched['normalized']] = matched
        
        for title in titles['unmatched']:
            unmatched_columns = set(title.keys()).union(unmatched_columns)
            if title['normalized'] in results: 
                unmatched_titles[title['normalized']]['count'] += 1
                unmatched_titles[title['normalized']]['documents'] += title['documents']
            else:
                title['count'] = 1
                unmatched_titles[title['normalized']] = title

    toFile("titles_unmatched.csv", unmatched_titles, unmatched_columns)

    toFile("titles_matched.csv", matched_titles, matched_columns)      


    # for f in orlandoFiles: 
    #     # Skip -d files
    #     if f.endswith("-d.xml"):
    #         continue
    #     titles = parseFile(f)
    #     for title in titles: 
    #         # print(title)
    #         unique_columns = set(title.keys()).union(unique_columns)
    #         if title['normalized'] in results: 
    #             results[title['normalized']]['count'] += 1
    #             results[title['normalized']]['documents'] += title['documents']
    #         else:
    #             title['count'] = 1
    #             results[title['normalized']] = title
    
    # toFile("titles_no_bibliography.csv", results, unique_columns)
        
