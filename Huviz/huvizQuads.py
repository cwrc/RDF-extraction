from rdflib import *
import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON, XML, N3, RDFXML
import json
import sys


CWRC = rdflib.Namespace( "http://sparql.cwrc.ca/ontologies/cwrc#")

class HuvizQuads:

    contextGraph = None

    conjunctiveGraph = ConjunctiveGraph()

    def __init__(self, instanceUri):
        self.instanceUri = instanceUri
        self.contextGraph = self.get_context_graph()

        # Do the extraction
        self.construct_huviz_graph()
    

    def get_context_graph(self):
        """Get Context Graph
        
        Arguments:
            instanceUri {str} -- A string representation of the instance uri
        
        Returns:
            Graph -- The graph from RDFlib of all context triples with the mapping predicates
        """


        sparql = SPARQLWrapper("http://sparql.cwrc.ca/sparql")
        sparql.setMethod("POST")
        query = """
        PREFIX cwrc: <http://sparql.cwrc.ca/ontologies/cwrc#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX data: <http://cwrc.ca/cwrcdata/>
        PREFIX oa: <http://www.w3.org/ns/oa#>

        CONSTRUCT {{
            ?context <http://sparql.cwrc.ca/ontologies/cwrc#contextFocus> ?contextFocus ;
                            ?contextPredicates ?contextObjects ;
                            oa:hasTarget ?target ;
                            .
            ?target oa:hasSource ?source ;
                    oa:hasSelector ?selector ;
            .
            ?selector rdf:value ?xpath ;
                oa:refinedBy ?quoteSelector ;
            .
            ?quoteSelector oa:exact ?textQuote .
            ?contextPredicates cwrc:subjectCentricPredicate ?subjectCentricPrecate .
        }} WHERE {{

        GRAPH <http://sparql.cwrc.ca/db/BiographyV2Beta> {{
            BIND({0} AS ?contextFocus)
                ?context <http://sparql.cwrc.ca/ontologies/cwrc#contextFocus> ?contextFocus ;
                                ?contextPredicates ?contextObjects ;
                                oa:hasTarget ?target ;
                                .
                ?target oa:hasSource ?source ;
                        oa:hasSelector ?selector ;
                .
                ?selector rdf:value ?xpath .
                OPTIONAL {{
                    ?selector oa:refinedBy ?quoteSelector .
                    ?quoteSelector oa:exact ?textQuote .
                }}
            }}
            ?contextPredicates cwrc:subjectCentricPredicate ?subjectCentricPrecate .
        }}
        """.format(self.instanceUri)

        sparql.setQuery(query)

        print(query)

        sparql.setReturnFormat(RDFXML)

        results = sparql.query().convert()
        results.bind("cwrc", CWRC)

        return results


    def get_unique_contexts(self):
        """Get Unique Contexts
        
        Gets unique context URIs that are attached to the instance

        Arguments:
            graph {Graph} -- RDFLib Graph
        
        Returns:
            list -- List of subject, object tuples for context values
        """
        unique_contexts = []
        for subject, obj in self.contextGraph.subject_objects(CWRC.contextFocus):
            unique_contexts.append((subject, obj))
        
        return unique_contexts

    def build_predicate_mappings(self):
        """Builds a mapping between context centric predicates and subject centric
        
        Arguments:
            contextGraph {Graph} -- The context graph
        """

        predicate_mappings = {}
        for subject, obj in self.contextGraph.subject_objects(CWRC.subjectCentricPredicate):
            predicate_mappings[subject] = obj

        return predicate_mappings

    def construct_huviz_graph(self):
        predicate_mappings = self.build_predicate_mappings()

        for context, subject in self.get_unique_contexts():
            predicate_object = self.contextGraph.predicate_objects(context)
            
            for predicate, obj in predicate_object:

                # Check for the predicate in subject mappings convert to subject centric and continue
                if predicate in predicate_mappings:
                    self.conjunctiveGraph.add((subject, predicate_mappings[predicate], obj, context))
                    continue

                self.conjunctiveGraph.add((context, predicate, obj, context))
                # Look for sub items of each object
                inner_predObj = self.contextGraph.predicate_objects(obj)
                for pp, oo in inner_predObj:
                    self.conjunctiveGraph.add((obj, pp, oo, context)) 
                    for ppp, ooo, in self.contextGraph.predicate_objects(oo):
                        self.conjunctiveGraph.add((oo, ppp, ooo, context))
                        for pppp, oooo, in self.contextGraph.predicate_objects(ooo):
                            self.conjunctiveGraph.add((ooo, pppp, oooo, context))

    def serialize(self, format="turtle"):
        return self.conjunctiveGraph.serialize(format=format)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:python {0} [instance_uri]")
        sys.exit(1)
    
    instanceUri = sys.argv[1]

    hq = HuvizQuads(instanceUri)

    print(hq.serialize())

