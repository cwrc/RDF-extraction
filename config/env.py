variables = {}


def env(name, default="NONE"):
    if len(variables) == 0:
        setEnv()

    if name in variables.keys():
        return variables[name]
    else:
        return default


def setEnv():
    with open(".env", 'r', encoding="utf-8") as f:
        for line in f:
            (name, value) = line.split("=")
            variables[name] = value.strip()
