import raising
configList = {}
#DATABASE_IP 
#DATABASE_USER
#DATABASE_PASSWORD
#DATABASE_DB_NAME
#GAME_MAX_LEVEL
def init():
    file = open("config.cfg", 'r')
    configs = file.readlines()
    file.close()
    global configList
    for config in configs:
        if config[0] == ';':
            continue
        config = config.replace("\n", "").replace(" ", "").split("=")
        configList[config[0]] = config[1]

def getConfigValue(key):
    try:
        return configList[key]
    except Exception:
        raise raising.ConfigNotInitException

