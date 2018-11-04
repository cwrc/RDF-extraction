import rdflib
from rdflib import RDF, RDFS, Literal, URIRef,BNode, Graph
from rdflib.namespace import XSD
from event import format_date

from biography import bind_ns, NS_DICT, make_standard_uri, create_uri

g = Graph()

class ChildlessStatus:
    def __init__(self, label):
        self.Label = label
        self.predicate = None
        self.value = None

        if label.title() == "Birth Control":
            self.predicate = NS_DICT["cwrc"].hasReproductiveHistory
            self.value = NS_DICT["cwrc"].birthControl
        elif label.title() == "Adoption":
            self.predicate = NS_DICT["cwrc"].hasReproductiveHistory
            self.value = NS_DICT["cwrc"].adoption
        elif label.title() == "Childlessness":
            self.predicate = NS_DICT["cwrc"].hasReproductiveHistory
            self.value = NS_DICT["cwrc"].childlessness

    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((person.uri,self.predicate,self.value))
        return g

class ChildStatus:
    def __init__(self, childType,numChild):
        self.ChildType = childType
        self.NumChildren = numChild

        self.predicate = None
        self.value = None

        if childType == "numberOfChildren":
            if numChild == "1":
                self.predicate = NS_DICT["cwrc"].hasChild
            else:
                self.predicate = NS_DICT["cwrc"].hasChildren
            self.value = Literal(numChild)

    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((person.uri, self.predicate, self.value))
        return g







def getStandardUri(std_str):
    import string
    translator = str.maketrans('', '', string.punctuation.replace("-", ""))
    temp_str = std_str.translate(translator)
    temp_str = temp_str.replace(" ", "_")
    return temp_str

def longFormtoShort(longForm):
    for key,value in NS_DICT.items():
        if Literal(value) in longForm:
            longForm = longForm.replace(Literal(value),key+":")
    # for entry in nsLongShortForm:
    #     if entry["l"] in longForm:
    #         longForm = longForm.replace(entry["l"],entry["s"]+":")

    return longForm
def addDict(entryPredicate,entryObject,isPerson):
    return {
        "p":entryPredicate,
        "o":entryObject,
        "prsn":isPerson
    }
def returnPersonUri(personName):
    return URIRef(str(NS_DICT["data"]) + getStandardUri(personName))
def createPerson(personName):
    global g
    # if personName == "":
    #     getch()
    personURI = returnPersonUri(personName)

    if (personURI, None, None) in g:
        return personURI

    thisMember = returnPersonUri(personName)
    g.add((thisMember, RDF.type, NS_DICT["cwrc"].NaturalPerson))
    g.add((thisMember, NS_DICT["foaf"].name, Literal(personName)))

    return thisMember
def addContextsNew(fileName,contextName,context,source,numContexts,propertyDict):
    global g
    descType = propertyDict["descType"]
    descLabel = contextName
    subjectName = propertyDict["subjectName"]
    subsObjs = propertyDict["subjectsObjects"]
    descSource = propertyDict["unchangedName"]

    # if len(contexts) > 1:
    #     print("too many contexts")
    # for context in contexts:
    snippetURI = URIRef(str(NS_DICT["data"]) + str(fileName) + contextName +"_snippet"+ str(numContexts))
    # g.add((snippetURI, oa.hasTarget, source))
    g.add((snippetURI, NS_DICT["dctypes"].description, Literal(context)))
    g.add((snippetURI, RDF.type, NS_DICT["oa"].TextualBody))
    g.add((snippetURI, NS_DICT["rdfs"].label, Literal(subjectName + " " + descLabel + " snippet")))
    # ########################################################################################################
    indentURI = URIRef(str(NS_DICT["data"]) + str(fileName) + contextName +"identifying"+ str(numContexts))
    for objs in subsObjs:
        if objs["prsn"] == True:
            g.add((indentURI,NS_DICT["oa"].hasBody,createPerson(objs["o"])))
        else:
            g.add((indentURI, NS_DICT["oa"].hasBody, Literal(objs["o"])))
    g.add((indentURI,NS_DICT["oa"].hasBody,source))

    g.add((indentURI,NS_DICT["oa"].hasTarget,snippetURI))
    g.add((indentURI,NS_DICT["oa"].motivatedBy,NS_DICT["oa"].describing))
    # ########################################################################################################
    descURI = URIRef(str(NS_DICT["data"]) + str(fileName) + contextName +"_describing"+ str(numContexts))
    g.add((descURI, RDF.type, descType))
    g.add((descURI, NS_DICT["rdfs"].label, Literal(subjectName + " "+descLabel + " describing annotation")))

    for objs in subsObjs:
        if objs["prsn"] == True:
            g.add((descURI, NS_DICT["dcterms"].subject, createPerson(objs["o"])))
        else:
            g.add((descURI, NS_DICT["dcterms"].subject, Literal(objs["o"])))

    g.add((descURI, NS_DICT["dcterms"].subject, source))
    g.add((descURI, NS_DICT["cwrc"].hasIDependencyOn, indentURI))

    for body in subsObjs:
        bodyURI = BNode()
        g.add((bodyURI, RDF.type,NS_DICT["oa"].TextualBody))
        g.add((bodyURI, URIRef(str(NS_DICT["dcterms"]) + "format"), Literal("text/turtle",datatype=XSD.string)))
        pred = body["p"]
        obj = body["o"]
        isPerson = body["prsn"]
        if body["prsn"] == True:
            value = "data:" + getStandardUri(descSource) + " " + body["p"] + " " + "data:"+ getStandardUri(body["o"])
        else:
            value = "data:" + getStandardUri(descSource) + " " + body["p"] + " " + Literal(body["o"])
        g.add((bodyURI, RDF.value, Literal(value)))
        g.add((descURI,NS_DICT["oa"].hasBody,bodyURI))
        # g.add((descURI,))

    g.add((descURI, NS_DICT["oa"].hasTarget, source))
    g.add((descURI, NS_DICT["oa"].hasTarget, snippetURI))
    g.add((descURI, NS_DICT["oa"].motivatedBy, NS_DICT["oa"].describing))

    numContexts += 1

    return numContexts
class predicateValue():
    def __init__(self,predicate,value):
        self.predicate = predicate
        self.value = value

    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        g.add((person.uri, self.predicate, self.value))
        return g

class birthData:
    def __init__(self, name, id, uri, bDate, bPosition, bSettl, bRegion, bGeog):
        self.name              = name
        self.id                = id
        self.uri               = uri
        self.birthDate         = bDate
        self.birthPositions    = bPosition
        self.birthSettlement   = bSettl
        self.birthRegion       = bRegion
        self.birthGeog         = bGeog
        self.birth_list = []

        if self.birthDate != "":
            self.birth_list.append(predicateValue(NS_DICT["cwrc"].hasBirthDate,Literal(self.birthDate)))
        for birthPosition in self.birthPositions:
            if birthPosition == "ONLY":
                positionObj = NS_DICT["cwrc"].onlyChild
            elif birthPosition == "ELDEST":
                positionObj = NS_DICT["cwrc"].eldestChild
            elif birthPosition == "YOUNGEST":
                positionObj = NS_DICT["cwrc"].youngestChild
            elif birthPosition == "MIDDLE:":
                positionObj = NS_DICT["cwrc"].middleChild

            self.birth_list.append(predicateValue(NS_DICT["cwrc"].hasBirthPosition,positionObj))



        if self.birthSettlement != "" or self.birthRegion != "" or self.birthGeog != "":
            birthPlaceStr = Literal(self.birthSettlement + ", " + self.birthRegion + ", " + self.birthGeog)

            self.birth_list.append(predicateValue(NS_DICT["cwrc"].hasBirthPlace,birthPlaceStr))


    def to_triple(self):
        global g
        spList = []
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        if self.birthDate != "":
            g.add((self.uri, NS_DICT["cwrc"].hasBirthDate, Literal(self.birthDate)))
            spList.append(addDict("cwrc.hasBirthDate", self.birthDate, False))

        for birthPosition in self.birthPositions:
            if birthPosition == "ONLY":
                positionObj = NS_DICT["cwrc"].onlyChild
            elif birthPosition == "ELDEST":
                positionObj = NS_DICT["cwrc"].eldestChild
            elif birthPosition == "YOUNGEST":
                positionObj = NS_DICT["cwrc"].youngestChild
            elif birthPosition == "MIDDLE:":
                positionObj = NS_DICT["cwrc"].middleChild
            g.add((self.uri, NS_DICT["cwrc"].hasBirthPosition, positionObj))
            spList.append(addDict("cwrc.hasBirthPosition", longFormtoShort(Literal(positionObj)), False))

        if self.birthSettlement != "" or self.birthRegion != "" or self.birthGeog != "":
            birthPlaceStr = Literal(
                self.birthSettlement + ", " + self.birthRegion + ", " + self.birthGeog)
            g.add((self.uri, NS_DICT["cwrc"].hasBirthPlace, birthPlaceStr))
            spList.append(addDict("cwrc.hasBirthPlace", birthPlaceStr, False))

        # if self.birthContexts != None and len(self.birthContexts) > 0:
        #     listProperties = {}
        #     listProperties["subjectName"] = getStandardUri(self.name)
        #     listProperties["unchangedName"] = self.name
        #     listProperties["descType"] = NS_DICT["cwrc"].FriendsAndAssociatesContext
        #     listProperties["subjectsObjects"] = spList
        #
        #     for context in self.birthContexts:
        #         addContextsNew(self.id,"birthContext",context,self.uri,1,listProperties)
        return g


class deathData:
    def __init__(self, name, id, uri,dDate, dCauses, dSettl, dRegion, dGeog, dContexts, dBurialSettl, dBurialRegion, dBurialGeog):
        self.name = name
        self.id = id
        self.uri = uri
        self.deathDate = dDate
        self.deathCauses= dCauses

        self.deathSettlement = dSettl
        self.deathRegion = dRegion
        self.deathGeog = dGeog

        self.deathContexts = dContexts

        self.burialSettl = dBurialSettl
        self.burialRegion = dBurialRegion
        self.burialGeog = dBurialGeog
        self.death_list = []

        if self.deathDate != "":
            self.death_list.append(predicateValue(NS_DICT["cwrc"].hasDeathDate, Literal(self.deathDate)))

        if self.deathSettlement != "" or self.deathRegion != "" or self.deathGeog != "":
            deathPlaceStr = Literal(
                self.deathSettlement + ", " + self.deathRegion + ", " + self.deathGeog)
            self.death_list.append(predicateValue(NS_DICT["cwrc"].hasDeathPlace, deathPlaceStr))

        if self.burialSettl != "" or self.burialRegion != "" or self.burialGeog != "":
            burialPlaceStr = Literal(
                self.burialSettl + ", " + self.burialRegion + ", " + self.burialGeog)
            self.death_list.append(predicateValue(NS_DICT["cwrc"].hasBurialPlace, burialPlaceStr))

    def to_triples(self):
        global g
        spList = []
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        if self != None:
            # if dateValidate(self.deathInfo.deathDate):
            if self.deathDate != "":
                g.add((self.uri, NS_DICT["cwrc"].hasDeathDate, Literal(self.deathDate)))
                spList.append(addDict("cwrc.hasDeathDate", Literal(self.deathDate), False))

            # for deathCause in self.deathCauses:
            #     g.add((self.uri,NS_DICT["cwrc"].hasDeathCause,Literal(deathCause)))
            if self.deathSettlement != "" or self.deathRegion != "" or self.deathGeog != "":
                deathPlaceStr = Literal(
                    self.deathSettlement + ", " + self.deathRegion + ", " + self.deathGeog)
                g.add((self.uri, NS_DICT["cwrc"].hasDeathPlace, deathPlaceStr))
                spList.append(addDict("cwrc.hasDeathPlace", deathPlaceStr, False))

            if self.burialSettl != "" or self.burialRegion != "" or self.burialGeog != "":
                burialPlaceStr = Literal(
                    self.burialSettl + ", " + self.burialRegion + ", " + self.burialGeog)
                g.add((self.uri, NS_DICT["cwrc"].hasBurialPlace, burialPlaceStr))
                spList.append(addDict("cwrc.hasBurialPlace", burialPlaceStr, False))

            # if self.deathContexts != None and len(self.deathContexts) > 0:
            #     listProperties = {}
            #     listProperties["subjectName"] = getStandardUri(self.name)
            #     listProperties["unchangedName"] = self.name
            #     listProperties["descType"] = NS_DICT["cwrc"].FriendsAndAssociatesContext
            #     listProperties["subjectsObjects"] = spList
            #     for context in self.deathContexts:
            #         addContextsNew(self.id, "deathContext", context, self.uri, 1, listProperties)
            #
            #     # addContexts(fileName,"hasDeathContext",self.deathContexts,sou
        return g


class JobSigAct:
    def __init__(self,jobPredicate,jobName):
        self.predicate  = jobPredicate
        self.job = jobName

class FriendAssociate:
    def __init__(self,name):
        self.name = name
        self.predicate = NS_DICT["cwrc"].hasInterpersonalRelationshipWith
        self.value = make_standard_uri(name)

    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        g.add((person.uri,self.predicate,self.value))
        return g

class PeopleAndContext:
    def __init__(self, name, contexts):
        self.names = name
        self.contexts = contexts


    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        if self != None:
            for name in self.names:
                g.add((person.uri,NS_DICT["cwrc"].hasInterpersonalRelationshipWith,createPerson(name)))
            # listProperties = {}
            # listProperties["subjectName"] = getStandardUri(person.name)
            # listProperties["unchangedName"]= person.name
            # listProperties["descType"] = NS_DICT["cwrc"].selfsAndAssociatesContext
            # spList = []
            # for name in self.names:
            #     dictEntry = {}
            #     dictEntry["p"]  = "cwrc.hasInterpersonalRelationshipWith"
            #     dictEntry["o"]     = name
            #     dictEntry["prsn"]   = True
            #     spList.append(dictEntry)
            # listProperties["subjectsObjects"] = spList
            # person.contextCounts["friendsAssociates"] = addContextsNew(person.id,"FriendsAndAssociatesContext",self.contexts,person.uri,person.contextCounts["friendsAssociates"],listProperties)

        # print(g.serialize(format='turtle').decode())
        return g

class Cohabitant:
    def __init__(self,habitant):
        self.name = habitant
        self.predicate = NS_DICT["cwrc"].hasCohabitant
        self.value = make_standard_uri(self.name)


    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((person.uri, self.predicate, self.value))
        return g

