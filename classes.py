class ChildlessStatus:
    def __init__(self, label):
        self.Label = label

class ChildStatus:
    def __init__(self, childType,numChild):
        self.ChildType = childType
        self.NumChildren = numChild

class PersonAttribute:
    def __init__(self,attrValue,name):
        self.AttrValue = attrValue;
        self.PersonName = name;

class IntimateRelationships:
    def __init__(self, Person, attrValue,context):
        self.PersonName =  Person
        self.Context = context
        self.AttrValue = attrValue

class birthData:
    def __init__(self, bDate, bPosition, bSettl, bRegion, bGeog, bContexts):
        self.birthDate = bDate
        self.birthPositions = bPosition
        self.birthSettlement = bSettl
        self.birthRegion = bRegion
        self.birthGeog = bGeog
        self.birthContexts = bContexts

class deathData:
    def __init__(self, dDate, dCauses, dSettl, dRegion, dGeog, dContexts, dBurialSettl, dBurialRegion, dBurialGeog):
        self.deathDate = dDate
        self.deathCauses= dCauses

        self.deathSettlement = dSettl
        self.deathRegion = dRegion
        self.deathGeog = dGeog

        self.deathContexts = dContexts

        self.burialSettl = dBurialSettl
        self.burialRegion = dBurialRegion
        self.burialGeog = dBurialGeog

class Family:
    def __init__(self, memName, memRLTN,memJobs,memSigActs):
        if memName == "":
            self.isNoName = True
        else:
            self.isNoName = False
        self.noNameLetter = ''
        self.memberName = memName
        self.memberRelation = memRLTN
        self.memberJobs = list(memJobs)
        self.memberSigActs = list(memSigActs)

    def samplePrint(self):
        print("......................\nName: ",self.memberName,"\nRelation: ",self.memberRelation)
        print("Jobs: ",end="")
        print(*self.memberJobs,sep=", ")
        print("SigAct: ",end="")
        print(*self.memberSigActs,sep=", ")

class JobSigAct:
    def __init__(self,jobPredicate,jobName):
        self.predicate  = jobPredicate
        self.job = jobName

class PeopleAndContext:
    def __init__(self, name, contexts):
        self.names = name
        self.contexts = contexts