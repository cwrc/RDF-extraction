# this file simply holds functions for scrapeFamily.py

import os, sys
import csv
from rdflib import RDF
from rdflib import Namespace, Graph, Literal, URIRef, BNode
from rdflib.namespace import XSD
from classes import *

from stringAndMemberFunctions import *
nsLongShortForm = [
    {
        "l":"http://sparql.cwrc.ca/ontologies/cwrc#",
        "s":"cwrc"
    }
]
cwrcNamespace   = Namespace('http://sparql.cwrc.ca/ontologies/cwrc#')
oa              = Namespace('http://www.w3.org/ns/oa#')
data            = Namespace('http://cwrc.ca/cwrcdata/')
foaf            = Namespace('http://xmlns.com/foaf/0.1/')
dctypes         = Namespace("http://purl.org/dc/dcmitype/")
rdfs            = Namespace("http://www.w3.org/2000/01/rdf-schema#")
dcterms         = Namespace("http://purl.org/dc/terms/")

def newGraph():
    new = Graph()
    new.bind('cwrc', cwrcNamespace)
    new.bind('oa', oa)
    new.bind('data', data)
    new.bind('foaf', foaf)
    new.bind("dctypes", dctypes)
    new.bind("rdfs", rdfs)
    new.bind("dcterms", dcterms)

    return new

g         = newGraph()
megaGraph = newGraph()


def longFormtoShort(longForm):
    for entry in nsLongShortForm:
        if entry["l"] in longForm:
            longForm = longForm.replace(entry["l"],entry["s"]+":")

    return longForm

def getCwrcTag(familyRelation):
    csvFile = open(os.path.expanduser("~/Google Drive/Term 3 - UoGuelph/mapping2.csv"),"r")
    
    cwrcTag = 'CWRC_Tag'
    orlandoTag = 'Orlando_Relation'
    
    fileContent = csv.DictReader(csvFile)
    
    for row in fileContent:
        if row[orlandoTag] == familyRelation:
            return row[cwrcTag]


def addContexts(fileName,contextName,context,source,numContexts):
    # for context in contexts:
    contextURI = URIRef(str(cwrcNamespace) + str(fileName) + contextName + str(numContexts))
    g.add((contextURI, oa.hasTarget, source))
    g.add((contextURI, cwrcNamespace.hasdescription, Literal(context)))

    numContexts += 1

    return numContexts

def addContextsNew(fileName,contextName,context,source,numContexts,propertyDict):
    descType = propertyDict["descType"]
    descLabel = contextName
    subjectName = propertyDict["subjectName"]
    subsObjs = propertyDict["subjectsObjects"]
    descSource = propertyDict["unchangedName"]

    # if len(contexts) > 1:
    #     print("too many contexts")
    # for context in contexts:
    snippetURI = URIRef(str(cwrcNamespace) + str(fileName) + contextName +"_snippet"+ str(numContexts))
    # g.add((snippetURI, oa.hasTarget, source))
    g.add((snippetURI, dctypes.description, Literal(context)))
    g.add((snippetURI, RDF.type, oa.TextualBody))
    g.add((snippetURI, rdfs.label, Literal(subjectName + " " + descLabel + " snippet")))
    # ########################################################################################################
    indentURI = URIRef(str(cwrcNamespace) + str(fileName) + contextName +"identifying"+ str(numContexts))
    for objs in subsObjs:
        if objs["prsn"] == True:
            g.add((indentURI,oa.hasBody,createPerson(objs["o"])))
        else:
            g.add((indentURI, oa.hasBody, Literal(objs["o"])))
    g.add((indentURI,oa.hasBody,source))

    g.add((indentURI,oa.hasTarget,snippetURI))
    g.add((indentURI,oa.motivatedBy,oa.describing))
    # ########################################################################################################
    descURI = URIRef(str(cwrcNamespace) + str(fileName) + contextName +"_describing"+ str(numContexts))
    g.add((descURI, RDF.type, descType))
    g.add((descURI, rdfs.label, Literal(subjectName + " "+descLabel + " describing annotation")))

    for objs in subsObjs:
        if objs["prsn"] == True:
            g.add((descURI, dcterms.subject, createPerson(objs["o"])))
        else:
            g.add((descURI, dcterms.subject, Literal(objs["o"])))

    g.add((descURI, dcterms.subject, source))
    g.add((descURI, cwrcNamespace.hasIdDependencyOn, indentURI))

    for body in subsObjs:
        bodyURI = BNode()
        g.add((bodyURI, RDF.type,oa.TextualBody))
        g.add((bodyURI, URIRef(str(dcterms) + "format"), Literal("text/turtle",datatype=XSD.string)))
        pred = body["p"]
        obj = body["o"]
        isPerson = body["prsn"]
        if body["prsn"] == True:
            value = "data:" + getStandardUri(descSource) + " " + body["p"] + " " + "data:"+ getStandardUri(body["o"])
        else:
            value = "data:" + getStandardUri(descSource) + " " + body["p"] + " " + Literal(body["o"])
        g.add((bodyURI, RDF.value, Literal(value)))
        g.add((descURI,oa.hasBody,bodyURI))
        # g.add((descURI,))

    g.add((descURI, oa.hasTarget, source))
    g.add((descURI, oa.hasTarget, snippetURI))
    g.add((descURI, oa.motivatedBy, oa.describing))



    numContexts += 1

    return numContexts

def returnPersonUri(personName):
    return URIRef(str(data) + getStandardUri(personName))

def addDict(entryPredicate,entryObject,isPerson):
    return {
        "p":entryPredicate,
        "o":entryObject,
        "prsn":isPerson
    }
def createPerson(personName):
    # if personName == "":
    #     getch()
    personURI = returnPersonUri(personName)

    if (personURI, None, None) in g:
        return personURI

    thisMember = returnPersonUri(personName)
    g.add((thisMember, RDF.type, cwrcNamespace.NaturalPerson))
    g.add((thisMember, foaf.name, Literal(personName)))

    return thisMember

def graphMaker(sourceName, fileName, unfixedSourceName, familyInfo, birthInfo, deathInfo,
               childInfo, childlessList, intmtRelationships, friendAssociateList, occupations, cohabitantList, sexualityContexts, cntr):
    global g
    global megaGraph
    import rdflib
    numNamelessPeople = 0

    g = newGraph()



    sourceName = sourceName.replace(" ","_")
    # source = URIRef(str(data) + sourceName)
    source = URIRef(str(data)+ str(getStandardUri(unfixedSourceName)))
             # URIRef(str(cwrcNamespace) + str(fileName) + "deathContext" + str(numDeathContexts))
    # g.add((source,foaf.name,Literal(sourceName.replace("_", " "))))
    g.add((source,RDF.type, cwrcNamespace.NaturalPerson))

    # Adding family info to the ttl file
    for family in familyInfo:
        memberName = family.memberName
        print("=======",memberName,"=========")
        # FIXME : name rearranement removed to match alliyya's code
        # if ',' in memberName:
        #     splitName = memberName.split(",")
        #     memberName = splitName[1].strip() + " " + splitName[0].strip()
        # memberName = getStandardUri(memberName)
        memberSource = URIRef(str(data) + getStandardUri(memberName))
        if family.isNoName:
            if family.noNameLetter == "":
                # print(sourceName, memberName)
                # if family.memberRelation == "UNCLE":
                #     if (source, URIRef(str(cwrcNamespace) + "hasUncle"),None) in g:
                #         print("multipleUncles")
                #     print(family.memberRelation)
                memberSource = URIRef(str(data) + sourceName.replace(" ","_") + "_" + family.memberRelation.lower().title())
                numNamelessPeople += 1
            else:
                memberSource = URIRef(str(data) + sourceName.replace(" ", "_") + "_" + family.memberRelation.lower().title() + "_" + family.noNameLetter)
                numNamelessPeople += 1

        else:
            g.add((memberSource,foaf.name,Literal(memberName)))

        g.add((memberSource, RDF.type, cwrcNamespace.NaturalPerson))
        
        for jobs in family.memberJobs:
            if jobs.job == "":
                continue
            if jobs.predicate == "familyOccupation":
                predicate = cwrcNamespace.hasFamilyBasedOccupation
            else:
                predicate = cwrcNamespace.hasPaidOccupation


            # FIXME : change jobs to jogs.job in order to make the thing work. right now, it is not functional.

            if jobs in occupations:
                g.add((memberSource, predicate, Literal(occupations[jobs.job].title())))
            else:
                g.add((memberSource,predicate,Literal(jobs.job.strip().title())))
            # print("added job ", jobs)

        for sigActs in family.memberSigActs:
            if sigActs.job == "":
                continue
            if sigActs.predicate == "volunteerOccupation":
                predicate = cwrcNamespace.hasVolunteerOccupation
            else:
                predicate = cwrcNamespace.hasOccupation

            if sigActs in occupations:
                g.add((memberSource, predicate, Literal(occupations[sigActs.job].title())))
            else:
                g.add((memberSource,predicate,Literal(sigActs.job.strip().title())))
            # print("added significant ", sigActs)

        cwrcTag = getCwrcTag(family.memberRelation)

        predicate = URIRef(str(cwrcNamespace) + cwrcTag)
        # g.add((source,predicate,Literal(memberName)))
        g.add((source,predicate,memberSource))


    # Adding Birth Info to the ttl file
    spList = []
    if birthInfo.birthDate != "":
        g.add((source,cwrcNamespace.hasBirthDate,Literal(birthInfo.birthDate)))
        spList.append(addDict("cwrc.hasBirthDate",birthInfo.birthDate,False))

    for birthPosition in birthInfo.birthPositions:
        if birthPosition == "ONLY":
            positionObj = cwrcNamespace.onlyChild
        elif birthPosition == "ELDEST":
            positionObj = cwrcNamespace.eldestChild
        elif birthPosition == "YOUNGEST":
            positionObj = cwrcNamespace.youngestChild
        elif birthPosition == "MIDDLE:":
            positionObj = cwrcNamespace.middleChild
        g.add((source,cwrcNamespace.hasBirthPosition,positionObj))
        spList.append(addDict("cwrc.hasBirthPosition",longFormtoShort(Literal(positionObj)),False))


    if birthInfo.birthSettlement != "" or birthInfo.birthRegion != "" or birthInfo.birthGeog != "":
        birthPlaceStr = Literal(birthInfo.birthSettlement+", "+birthInfo.birthRegion+", "+birthInfo.birthGeog)
        g.add((source,cwrcNamespace.hasBirthPlace,birthPlaceStr))
        spList.append(addDict("cwrc.hasBirthPlace",birthPlaceStr,False))


    if birthInfo.birthContexts != None and len(birthInfo.birthContexts) > 0:
        listProperties = {}
        listProperties["subjectName"] = sourceName
        listProperties["unchangedName"] = unfixedSourceName
        listProperties["descType"] = cwrcNamespace.FriendsAndAssociatesContext
        listProperties["subjectsObjects"] = spList
        for context in birthInfo.birthContexts:
            addContextsNew(fileName,"birthContext",context,source,1,listProperties)
        # addContexts(fileName, "birthContext", birthInfo.birthContexts, source, 1)

        # print(deathInfo.deathContexts[0])

        # for thisBirthContext in birthInfo.birthContexts:
        #     print("context: ", thisBirthContext)
        #     birthContextURI = URIRef(str(cwrcNamespace) + str(fileName) + "birthContext" + str(numBirthContexts))
        #     numBirthContexts += 1
        #
        #     g.add((birthContextURI, oa.hasTarget, source))
        #     g.add((birthContextURI, cwrcNamespace.hasdescription, Literal(thisBirthContext)))
    # death validation
    # print(deathInfo.deathDate)
    spList = []

    if deathInfo != None:
        # if dateValidate(deathInfo.deathDate):
        if deathInfo.deathDate != "":
            g.add((source,cwrcNamespace.hasDeathDate,Literal(deathInfo.deathDate)))
            spList.append(addDict("cwrc.hasDeathDate",Literal(deathInfo.deathDate),False))
        
        # for deathCause in deathInfo.deathCauses:
        #     g.add((source,cwrcNamespace.hasDeathCause,Literal(deathCause)))
        if deathInfo.deathSettlement !="" or deathInfo.deathRegion != "" or deathInfo.deathGeog != "":
            deathPlaceStr = Literal(deathInfo.deathSettlement+", "+deathInfo.deathRegion+", "+deathInfo.deathGeog)
            g.add((source,cwrcNamespace.hasDeathPlace,deathPlaceStr))
            spList.append(addDict("cwrc.hasDeathPlace",deathPlaceStr,False))


        if deathInfo.burialSettl != "" or deathInfo.burialRegion != "" or deathInfo.burialGeog != "":
            burialPlaceStr = Literal(deathInfo.burialSettl+", "+deathInfo.burialRegion+", "+deathInfo.burialGeog)
            g.add((source,cwrcNamespace.hasBurialPlace,burialPlaceStr))
            spList.append(addDict("cwrc.hasBurialPlace",burialPlaceStr,False))


        
        if deathInfo.deathContexts != None and len(deathInfo.deathContexts) > 0:
            listProperties = {}
            listProperties["subjectName"] = sourceName
            listProperties["unchangedName"] = unfixedSourceName
            listProperties["descType"] = cwrcNamespace.FriendsAndAssociatesContext
            listProperties["subjectsObjects"] = spList
            for context in deathInfo.deathContexts:
                addContextsNew(fileName, "deathContext", context, source, 1, listProperties)

            # addContexts(fileName,"hasDeathContext",deathInfo.deathContexts,source,1)


    for child in childInfo:
        if child.ChildType == "numberOfChildren":
            if child.NumChildren == "1":
                g.add((source, cwrcNamespace.hasChild, Literal(child.NumChildren)))
            else:
                g.add((source, cwrcNamespace.hasChildren, Literal(child.NumChildren)))

    for childAttribute in childlessList:
        label = childAttribute.Label.title()
        if label == "Birth Control":
            g.add((source, cwrcNamespace.hasReproductiveHistory, cwrcNamespace.birthControl))
        elif label == "Adoption":
            g.add((source, cwrcNamespace.hasReproductiveHistory, cwrcNamespace.adoption))
        elif label == "Childlessness":
            g.add((source, cwrcNamespace.hasReproductiveHistory, cwrcNamespace.childlessness))



    if intmtRelationships != None:
        numIntimateContext = 1
        for relationship in intmtRelationships:
            # print(relationship.Context)
            # numIntimateContext = addContexts(fileName,"hasIntimateRelationshipsContext",relationship.Contexts,source,numIntimateContext)
            spList = []


        # for relationship in intmtRelationships.Persons:
            if relationship.AttrValue == "EROTICYES":
                g.add((source, cwrcNamespace.hasEroticRelationshipWith, createPerson(relationship.PersonName.title())))
                spList.append(addDict("cwrc.hasEroticRelationshipWith",relationship.PersonName,True))
            elif relationship.AttrValue == "EROTICNO" :
                g.add((source, cwrcNamespace.hasNonEroticRelationshipWith, createPerson(relationship.PersonName.title())))
                spList.append(addDict("cwrc.hasNonEroticRelationshipWith",relationship.PersonName,True))


            elif relationship.AttrValue == "EROTICPOSSIBLY":
                g.add((source, cwrcNamespace.hasPossiblyEroticRelationshipWith, createPerson(relationship.PersonName.title())))
                spList.append(addDict("cwrc.hasPossiblyEroticRelationshipWith",relationship.PersonName,True))

            else:

                if relationship.PersonName.title() != "Intimate Relationship":
                    g.add((source,cwrcNamespace.hasIntimateRelationshipWith, createPerson(relationship.PersonName.title())))
                    spList.append(addDict("cwrc.hasIntimateRelationshipWith", relationship.PersonName, False))

                else:
                    g.add((source, cwrcNamespace.hasIntimateRelationshipWith, Literal(relationship.PersonName.title())))
                    spList.append(addDict("cwrc.hasIntimateRelationshipWith", relationship.PersonName, True))

            listProperties = {}
            listProperties["subjectName"] = sourceName
            listProperties["unchangedName"] = unfixedSourceName
            listProperties["descType"] = cwrcNamespace.IntimateRelationshipContext
            listProperties["subjectsObjects"] = spList

            numIntimateContext = addContextsNew(fileName, "hasIntimateRelationshipsContext", relationship.Context,
                                                source, numIntimateContext, listProperties)


    numFriendContext = 1
    for friend in friendAssociateList:
        if friend != None:
            for name in friend.names:
                g.add((source,cwrcNamespace.hasInterpersonalRelationshipWith,createPerson(name)))
                # break
            # continue
            listProperties = {}
            listProperties["subjectName"] = sourceName
            listProperties["unchangedName"]= unfixedSourceName
            listProperties["descType"] = cwrcNamespace.FriendsAndAssociatesContext
            spList = []
            for name in friend.names:
                dictEntry = {}
                dictEntry["p"]  = "cwrcNamespace.hasInterpersonalRelationshipWith"
                dictEntry["o"]     = name
                dictEntry["prsn"]   = True
                spList.append(dictEntry)
            listProperties["subjectsObjects"] = spList
            # listProperties["descPredicate"] = "cwrcNamespace.hasInterpersonalRelationshipWith"
            # getch()
            numFriendContext = addContextsNew(fileName,"FriendsAndAssociatesContext",friend.contexts,source,numFriendContext,listProperties)
            # numFriendContext = addContexts(fileName,"friendAssociateContext",friend.contexts,source,numFriendContext)


    # print(g.serialize(format='turtle').decode())


    for habitant in cohabitantList:
        g.add((source,cwrcNamespace.hasCohabitant,createPerson(habitant)))

    # g = newGraph()
    # g.add((source, RDF.type, cwrcNamespace.NaturalPerson))
    for context in sexualityContexts:
        listProperties = {}
        listProperties["subjectName"] = sourceName
        listProperties["unchangedName"] = unfixedSourceName
        listProperties["descType"] = cwrcNamespace.hasSexualityContext
        listProperties["subjectsObjects"] = []

        addContextsNew(fileName, "hasSexualityContext", context,
                                            source, 1, listProperties)
    print(g.serialize(format='turtle').decode())

    # addContexts(fileName,"hasSexualityContext", sexualityContexts, source, 1)
    # print(g.serialize(format='turtle').decode())
    # officialPath = os.path.expanduser("~/Documents/UoGuelph Projects/CombiningTriples/birthDeathFamily_triples/"+ fileName+ '.txt')
    fileTestPath = os.path.expanduser("~/Documents/extraction2/testingFileNew.txt")
    # testingPath = os.path.expanduser('./oldContext/'+ fileName+ '.txt')
    # testingPath = os.path.expanduser('./newContext/'+ fileName+ '.txt')

    # g.serialize(destination=officialPath, format='turtle')
    # g.serialize(destination=fileTestPath, format='turtle')

    if cntr == 1369:
        megaGraph.serialize(destination=os.path.expanduser("~/Documents/UoGuelph Projects/"+ "motherGraph2"+ '.txt'), format='turtle')
    else:
        megaGraph += g

    return len(g),numNamelessPeople

