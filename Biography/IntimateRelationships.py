class IntimateRelationships:
    def __init__(self, Person, attrValue):
        self.PersonName =  Person
        self.AttrValue = attrValue

        self.predicate = None
        self.value = None

        if self.AttrValue == "EROTICYES":
            self.predicate = NS_DICT["cwrc"].hasEroticRelationshipWith
            self.value = make_standard_uri(Person)
        elif self.AttrValue == "EROTICNO":
            self.predicate = NS_DICT["cwrc"].hasNonEroticRelationshipWith
            self.value = make_standard_uri(Person)
        elif self.AttrValue == "EROTICPOSSIBLY":
            self.predicate = NS_DICT["cwrc"].hasPossiblyEroticRelationshipWith
            self.value = make_standard_uri(Person)
        else:
            if self.PersonName.title() != "Intimate Relationship":
                self.predicate = NS_DICT["cwrc"].hasIntimateRelationshipWith
                self.value = make_standard_uri(Person)
            else:
                self.predicate = NS_DICT["cwrc"].hasIntimateRelationshipWith
                self.value = make_standard_uri(Person)

    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((person.uri,self.predicate,self.value))
        # spList = []

        # for relationship in intmtRelationships.Persons:


        # listProperties = {}
        # listProperties["subjectName"] = getStandardUri(person.name)
        # listProperties["unchangedName"]= person.name
        # listProperties["descType"] = NS_DICT["cwrc"].IntimateRelationshipsContext
        # listProperties["subjectsObjects"] = spList
        #
        # person.contextCounts["intimateRelationship"] = addContextsNew(person.id, "hasIntimateRelationshipsContext", self.Context,
        #                                     person.uri, person.contextCounts["intimateRelationship"], listProperties)

        return g