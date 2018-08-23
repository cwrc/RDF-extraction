# Extraction Validation Scripts
Collection of simple scripts that may provide useful for validating triples that are extracted

## validate_terms.py
Currently checks provided datafile against the CWRC Ontology as available on github 
1. If any cwrc term used in the datafile is not in CWRC Ontology
2. If a used cwrc term has been deprecated and should not be used

### Expected Usage
	`python3 verify_terms.py path/file.ttl`
#### Sample Output
```
224 Triples in provided data file
Term not found: http://sparql.cwrc.ca/ontologies/cwrc#monArchism
Term has been deprecated: http://sparql.cwrc.ca/ontologies/cwrc#hasReligionSelfDefined
Term not found: http://sparql.cwrc.ca/ontologies/cwrc#anglicanist

Results:
Number of deprecated terms: 1
	 deprecated term --> possible replacement
	 http://sparql.cwrc.ca/ontologies/cwrc#hasReligionSelfDefined --> http://sparql.cwrc.ca/ontologies/cwrc#hasReligionSelfReported
Number of invalid terms: 2
	 http://sparql.cwrc.ca/ontologies/cwrc#monArchism
	 http://sparql.cwrc.ca/ontologies/cwrc#anglicanist

```

### Future 
Hoping to extend this past our ontology eventually
Very barebones at the moment
- General error handling (inability to parse file, ...)
- Options for parsing different formats (simple)
- Adding counts for error occurences within the dataset
- Validating other used ontology terms from within the namespace (Not any adv reasoning)
    - catching simple spelling errors
    ex. prov:derivedFrom is not a valid term in the provenance ontology
- Suggest near matches for incorrect terms
    ex. prov:derivedFrom should actually be prov:wasDerivedFrom
