# this file simply holds functions for scrapeFamily.py

import os, sys
import csv
from rdflib import RDF
from scrapeFamily import getch

def getCwrcTag(familyRelation):
    csvFile = open(os.path.expanduser("~/Google Drive/Term 3 - UoGuelph/mapping2.csv"),"r")
    
    cwrcTag = 'CWRC_Tag'
    orlandoTag = 'Orlando_Relation'
    
    fileContent = csv.DictReader(csvFile)
    
    for row in fileContent:
        if row[orlandoTag] == familyRelation:
            return row[cwrcTag]

def graphMaker(sourceName,fileName,familyInfo, birthInfo, deathInfo, childInfo,childlessList,intmtRelationshipsList):
    
    from rdflib import Namespace, Graph, Literal, URIRef
    import rdflib
    numNamelessPeople = 0

    g = Graph()
    personNamespace   = Namespace('http://example.org/')
    cwrcNamespace     = Namespace('http://sparql.cwrc.ca/ontologies/cwrc#')
    oa                = Namespace('http://exampleoa.org/')
    g.bind('cwrc',cwrcNamespace)
    g.bind('oa',oa)
    # put in foaf.name instead of cwrc.hasName
    # namespace_manager.bind('cwrcdata', cwrcNamespace, override=False)

    sourceName = sourceName.replace(" ","_")
    source = URIRef(str(personNamespace) + sourceName)
    g.add((source,cwrcNamespace.hasName,Literal(sourceName.replace("_", " "))))
    g.add((source,RDF.type, cwrcNamespace.NaturalPerson))

    # Adding family info to the ttl file
    for family in familyInfo:
        memberName = family.memberName
        print("=======",memberName,"=========")
        if ',' in memberName:
            splitName = memberName.split(",")
            memberName = splitName[1].strip() + " " + splitName[0].strip()

        memberSource = URIRef(str(personNamespace) + memberName.replace(" ","_"))
        if memberName == "":
            print(sourceName, memberName)
            memberSource = URIRef(str(personNamespace) + sourceName.replace(" ","_") + "_" + family.memberRelation.lower().title())
            numNamelessPeople += 1
        else:
            g.add((memberSource,cwrcNamespace.hasName,Literal(memberName)))

        g.add((memberSource, RDF.type, cwrcNamespace.NaturalPerson))
        
        for jobs in family.memberJobs:
            g.add((memberSource,cwrcNamespace.hasJob,Literal(jobs.strip().title())))
            # print("added job ", jobs)

        for sigActs in family.memberSigActs:
            g.add((memberSource,cwrcNamespace.hasJob,Literal(sigActs.strip().title())))
            # print("added significant ", sigActs)

        predicate = URIRef(str(cwrcNamespace) + getCwrcTag(family.memberRelation))
        # g.add((source,predicate,Literal(memberName)))
        g.add((source,predicate,memberSource))


    # Adding Birth Info to the ttl file
    g.add((source,cwrcNamespace.hasBirthDate,Literal(birthInfo.birthDate)))
    for birthPosition in birthInfo.birthPositions:
        g.add((source,cwrcNamespace.hasBirthPosition,Literal(birthPosition)))
    g.add((source,cwrcNamespace.hasBirthPlace,Literal(birthInfo.birthSettlement+", "+birthInfo.birthRegion+", "+birthInfo.birthGeog)))

    # death validation
    # print(deathInfo.deathDate)
    if deathInfo != None:
        # if dateValidate(deathInfo.deathDate):
        g.add((source,cwrcNamespace.hasDeathDate,Literal(deathInfo.deathDate)))
        
        for deathCause in deathInfo.deathCauses:
            g.add((source,cwrcNamespace.hasDeathCause,Literal(deathCause)))
        
        g.add((source,cwrcNamespace.hasDeathPlace,Literal(deathInfo.deathSettlement+", "+deathInfo.deathRegion+", "+deathInfo.deathGeog)))
        
        if len(deathInfo.deathContexts) > 0:
            # g.add((cwrc.alRecChoice1, dctypes.description, Literal("insert sentence here")))
            # g.add((cwrc.alRecChoice1,  rdf.type, dctypes.text))`
            
            #     # g.add((cwrc.alRecChoice, dctypes.text, cwrc.alRecChoice1))
            # g.add((cwrc.AlReccChoice, as.items, cwrc.alRecChoice1))
            # g.add((cwrc.AlReccChoice, rdf.type, oa.Choice))

            # g.add((cwrc.AnnaLeonowensRaceEthnicityContext, oa.hasBody, cwrc.alRecChoice))
            # g.add((cwrc.AnnaLeonowensRaceEthnicityContext, rdf.type, cwrc.RaceEthnicityContext))
            
            # g.add((cwrc.AnnaLeonowens, cwrc:RaceEthnicityContext, cwrc.AnnaLeonowensRaceEthnicityContext))
            # g.add((cwrc.AnnaLeonowens, rdf.type, cwrc.Person))
            numDeathContexts = 1
            # print(deathInfo.deathContexts[0])
            for thisDeathContext in deathInfo.deathContexts:
                print("context: ", thisDeathContext)
                deathContextURI = URIRef(str(fileName) + "deathContext" + str(numDeathContexts))
                numDeathContexts += 1
                g.add((deathContextURI, oa.hasTarget, source))
                g.add((deathContextURI,cwrcNamespace.hasdescription, Literal(thisDeathContext)))
                # g.add((source,cwrcNamespace.hasDeathContext,(cwrcNamespace.hasDeathContext,cwrcNamespace.hasSource,Literal(deathContext))))


    # if childInfo.ChildType == "numberOfChildren":
    #     if childInfo.NumChildren == "1":
    #         g.add((source, cwrcNamespace.hasChild, Literal(childInfo.NumChildren)))
    #     else:
    #         g.add((source, cwrcNamespace.hasChildren, Literal(childInfo.NumChildren)))

    for childAttribute in childlessList:
        g.add((source,cwrcNamespace.hasReproductiveHistory,Literal(childAttribute.Label.title())))
    checkIntimate = False
    for relationship in intmtRelationshipsList:
        if relationship.AttrValue == "EROTICYES":
            g.add((source,cwrcNamespace.hasEroticRelationhip,Literal(relationship.PersonName.title())))
            print("eroticyes")
            # getch()
        elif relationship.AttrValue == "EROTICNO":
            g.add((source,cwrcNamespace.hasEroticRelationhip,Literal(relationship.PersonName.title())))
            print("eroticno")
            # getch()
        elif relationship.AttrValue == "EROTICPOSSIBLY":
            g.add((source,cwrcNamespace.hasEroticRelationhip,Literal(relationship.PersonName.title())))
            print("EROTICPOSSIBLY")
            # getch()
        else:
            g.add((source,cwrcNamespace.hasEroticRelationhip,Literal(relationship.PersonName.title())))
            print("not erotic")
            # getch()
        checkIntimate = True

    print(g.serialize(format='turtle').decode())
    # if checkIntimate:
    #     getch()

    return len(g),numNamelessPeople