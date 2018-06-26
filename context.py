import rdflib
import re


def strip_all_whitespace(string):
# temp function for condensing the context strings in visibility
    return re.sub('[\s+]', '', str(string))


class Context(object):
    """docstring for Context"""
    context_types = ["GenderContext", "PoliticalContext", "SocialClassContext",
                     "SexualityContext", "RaceEthnicityContext", "ReligionContext", "NationalityContext"]
    context_map = {"classissue": "SocialClassContext", "raceandethnicity": "RaceEthnicityContext",
                   "nationalityissue": "NationalityContext", "sexuality": "SexualityContext",
                   "religion": "ReligionContext", "culturalformation": "CulturalFormContext"}

    def __init__(self, id, text, type="culturalformation", motivation="describing"):
        super(Context, self).__init__()
        self.id = id

        self.tag = text
        # Will possibly have to clean up citations sans ()
        self.text = ' '.join(str(text.get_text()).split())

        # holding off till we know how src should work may have to do how we're grabbing entries from islandora api
        # self.src = src
        self.type = self.context_map[type]
        self.motivation = motivation
        self.subjects = []

    def to_triple(self, person_uri):
        # Pending OA stuff
        # type context as type
        # loop through subjects for dc subject
        # create hasbody
        # create dctypes:text
        # hasbody's object a oa:choice will have items identical to subjects plus
        pass

    def __str__(self):
        string = "\tid: " + str(self.id) + "\n"
        # text = strip_all_whitespace(str(self.text))
        string += "\ttype: " + self.type + "\n"
        string += "\tmotivation: " + self.motivation + "\n"
        string += "\ttag: \n\t\t{" + str(self.tag) + "}\n"
        string += "\ttext: \n\t\t{" + self.text + "}\n"
        if self.subjects:
            string += "\tsubjects:\n"
            for x in self.subjects:
                string += "\t\t" + str(x) + "\n"
        return string + "\n"

    # def context_count(self,type):
    #     pass
