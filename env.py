import sys


class Env:
    instance = None

    class __Env:
        def __init__(self):
            with open('.env', 'r') as f:
                for line in f:
                    (name, value) = line.split("=")
                    self.variables[name] = value

        def env(self, name, default):
            """
            returns the env variable if it exists otherwise the default value
            :param name: the variable name
            :param default: the default value to use if the variable does not exist
            :return: string value
            """
            if name in self.variables:
                return self.variables[name]
            else:
                return default

    def __init__(self):
        if Env.instance is not None:
            Env.instance = Env.__Env()
        else:
            return  Env.instance



a = Env()
a = a.instance



