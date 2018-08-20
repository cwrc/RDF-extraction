# this file simply holds functions for scrapeFamily.py

import os, sys
import csv
from rdflib import RDF
from rdflib import Namespace, Graph, Literal, URIRef
from stringAndMemberFunctions import *

g         = Graph()
megaGraph = Graph()

cwrcNamespace     = Namespace('http://sparql.cwrc.ca/ontologies/cwrc#')
oa                = Namespace('http://www.w3.org/ns/oa#')
data              = Namespace('http://cwrc.ca/cwrcdata/')
foaf              = Namespace('http://xmlns.com/foaf/0.1/')

def getCwrcTag(familyRelation):
    csvFile = open(os.path.expanduser("~/Google Drive/Term 3 - UoGuelph/mapping2.csv"),"r")
    
    cwrcTag = 'CWRC_Tag'
    orlandoTag = 'Orlando_Relation'
    
    fileContent = csv.DictReader(csvFile)
    
    for row in fileContent:
        if row[orlandoTag] == familyRelation:
            return row[cwrcTag]


def addContexts(fileName,contextName,contexts,source,numContexts):
    for context in contexts:
        contextURI = URIRef(str(cwrcNamespace) + str(fileName) + contextName + str(numContexts))
        g.add((contextURI, oa.hasTarget, source))
        g.add((contextURI, cwrcNamespace.hasdescription, Literal(context)))

        numContexts += 1

    return numContexts

def createPerson(personName):
    # if personName == "":
    #     getch()
    thisMember = URIRef(str(data) + getStandardUri(personName))
    g.add((thisMember, RDF.type, cwrcNamespace.NaturalPerson))
    g.add((thisMember, foaf.name, Literal(personName)))

    return thisMember
def graphMaker(sourceName, fileName, unfixedSourceName, familyInfo, birthInfo, deathInfo,
               childInfo, childlessList, intmtRelationships, friendAssociateList, occupations, cohabitantList, sexualityContext, cntr):
    global g
    global megaGraph
    import rdflib
    numNamelessPeople = 0

    g = Graph()

    g.bind('cwrc',cwrcNamespace)
    g.bind('oa',oa)
    g.bind('data',data)
    g.bind('foaf',foaf)

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
                print(jobs,"->",occupations[jobs])
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
                print(sigActs,"-->",occupations[sigActs])
                g.add((memberSource, predicate, Literal(occupations[sigActs.job].title())))
            else:
                g.add((memberSource,predicate,Literal(sigActs.job.strip().title())))
            # print("added significant ", sigActs)

        cwrcTag = getCwrcTag(family.memberRelation)

        predicate = URIRef(str(cwrcNamespace) + cwrcTag)
        # g.add((source,predicate,Literal(memberName)))
        g.add((source,predicate,memberSource))


    # Adding Birth Info to the ttl file
    if birthInfo.birthDate != "":
        g.add((source,cwrcNamespace.hasBirthDate,Literal(birthInfo.birthDate)))

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

    if birthInfo.birthSettlement != "" and birthInfo.birthRegion != "" and birthInfo.birthGeog != "":
        g.add((source,cwrcNamespace.hasBirthPlace,Literal(birthInfo.birthSettlement+", "+birthInfo.birthRegion+", "+birthInfo.birthGeog)))

    if birthInfo.birthContexts != None and len(birthInfo.birthContexts) > 0:

        addContexts(fileName,"birthContext",birthInfo.birthContexts,source,1)
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
    if deathInfo != None:
        # if dateValidate(deathInfo.deathDate):
        if deathInfo.deathDate != "":
            g.add((source,cwrcNamespace.hasDeathDate,Literal(deathInfo.deathDate)))
        
        # for deathCause in deathInfo.deathCauses:
        #     g.add((source,cwrcNamespace.hasDeathCause,Literal(deathCause)))
        if deathInfo.deathSettlement !="" or deathInfo.deathRegion != "" or deathInfo.deathGeog != "":
            g.add((source,cwrcNamespace.hasDeathPlace,Literal(deathInfo.deathSettlement+", "+deathInfo.deathRegion+", "+deathInfo.deathGeog)))

        if deathInfo.burialSettl != "" or deathInfo.burialRegion != "" or deathInfo.burialGeog != "":
            g.add((source,cwrcNamespace.hasBurialPlace,Literal(deathInfo.burialSettl+", "+deathInfo.burialRegion+", "+deathInfo.burialGeog)))

        
        if deathInfo.deathContexts != None and len(deathInfo.deathContexts) > 0:
            addContexts(fileName,"hasDeathContext",deathInfo.deathContexts,source,1)


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
        print(intmtRelationships.Contexts)
        numIntimateContext = addContexts(fileName,"hasIntimateRelationshipsContext",intmtRelationships.Contexts,source,numIntimateContext)

        for relationship in intmtRelationships.Persons:
            if relationship.AttrValue == "EROTICYES":
                g.add((source, cwrcNamespace.hasEroticRelationshipWith, createPerson(relationship.PersonName.title())))

            elif relationship.AttrValue == "EROTICNO" :
                g.add((source, cwrcNamespace.hasNonEroticRelationshipWith, createPerson(relationship.PersonName.title())))


            elif relationship.AttrValue == "EROTICPOSSIBLY":
                g.add((source, cwrcNamespace.hasPossiblyEroticRelationshipWith, createPerson(relationship.PersonName.title())))

            else:

                if relationship.PersonName.title() != "Intimate Relationship":
                    g.add((source,cwrcNamespace.hasIntimateRelationshipWith, createPerson(relationship.PersonName.title())))

                else:
                    g.add((source, cwrcNamespace.hasIntimateRelationshipWith, Literal(relationship.PersonName.title())))
    numFriendContext = 1
    for friend in friendAssociateList:
        if friend != None:
            for name in friend.names:
                g.add((source,cwrcNamespace.hasInterpersonalRelationshipWith,createPerson(name)))
            numFriendContext = addContexts(fileName,"friendAssociateContext",friend.contexts,source,numFriendContext)



    for habitant in cohabitantList:
        g.add((source,cwrcNamespace.hasCohabitant,createPerson(habitant)))

    addContexts(fileName,"hasSexualityContext",sexualityContext,source,1)
    # print(g.serialize(format='turtle').decode())
    officialPath = os.path.expanduser("~/Documents/UoGuelph Projects/CombiningTriples/birthDeathFamily_triples/"+ fileName+ '.txt')
    # testingPath = os.path.expanduser('./oldContext/'+ fileName+ '.txt')
    # testingPath = os.path.expanduser('./newContext/'+ fileName+ '.txt')

    g.serialize(destination=officialPath, format='turtle')
    if cntr == 1369:
        megaGraph.serialize(destination=os.path.expanduser("~/Documents/UoGuelph Projects/"+ "motherGraph2"+ '.txt'), format='turtle')
    else:
        megaGraph += g

    return len(g),numNamelessPeople

