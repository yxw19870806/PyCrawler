#load account information from account.dat
# return
#    {@ACCOUNT_NAME_1: {@ACCOUNT_PASSWORD_1}, @ACCOUNT_NAME_2: {@ACCOUNT_PASSWORD_2}, ... }
def getAccountList():
    file = open("save/account.dat", 'r')
    #for test
#    file = open("../save/account.dat", 'r')
    accountList = file.readlines()
    file.close()
    accountInfoList = {}
    for account in accountList[:]:
        accountInfos = account.replace("\n", "").split("\t")
        accountInfoList[accountInfos[0]] = accountInfos[1]
    return accountInfoList

#write account info to file
def register(accName_str, accPwd_str):
    file = open("save/account.dat", 'a')
    #for test
#    file = open("../save/account.dat", 'a')
    file.write(accName_str + "\t" + accPwd_str + "\n")
    file.close()

#write new role info to file
def createRole(accName_str):
    # default role information
    defaultLevel = 1
    defaultExp = 0
    defaultJob = "default"
    defaultAtk = 10
    defaultDef = 10
    defaultMaxHP = 100
    defaultMaxMP = 100
    defaultHP = 100
    defaultMP = 100
    defaultGold = 100
    defaultMap = 0
    # get uid and plus 1
    uid = int(open("save/uid.dat", 'r').read()) + 1
    open("save/uid.dat", 'w').write(str(uid))
    file = open("save/save.dat", 'a')
    file.write(str(uid) + "\t" + str(accName_str) + "\t" + str(defaultLevel) + "\t" + str(defaultExp) + "\t" + str(defaultJob) + "\t" + str(defaultAtk) + "\t" + str(defaultDef) + "\t" + str(defaultMaxHP) + "\t" + str(defaultMaxMP) + "\t" + str(defaultHP) + "\t" + str(defaultMP) + "\t" + str(defaultGold) + "\t" + str(defaultMap) + "\n")
    file.close()

#load monster information from monster.dat
# return
#    {@MONSTER_NUMBER_1: {@MONSTER_ATTRIBUTES_1}, @MONSTER_NUMBER_2: {@MONSTER_ATTRIBUTES_2}, ... }
#        @MONSTER_ATTRIBUTES
#            'name': MONSTER_NAME       string
#            'level': MONSTER_LEVEL     int
#            'atk': MONSTER_ATTACK      int
#            'def': MONSTER_DEFENSE     int
#            'HP': MONSTER_MAX_HP       int
#            'MP': MONSTER_MAX_MP       int
#            'exp': MONSTER_EXP         int
#            'gold': MONSTER_GOLD       int
def loadAllMonsterInfo():
    file = open("data/monster.dat", 'r')
    monsterList = file.readlines()
    file.close()
    monsterInfoList = {}
    for monster in monsterList[1:]:
        monsterInfo = {}
        monsterInfos = monster.replace("\n", "").split("\t")
        monsterInfo["name"] = monsterInfos[1]
        monsterInfo["level"] = int(monsterInfos[2])
        monsterInfo["atk"] = int(monsterInfos[3])
        monsterInfo["def"] = int(monsterInfos[4])
        monsterInfo["maxHP"] = int(monsterInfos[5])
        monsterInfo["maxMP"] = int(monsterInfos[6])
        monsterInfo["exp"] = int(monsterInfos[7])
        monsterInfo["gold"] = monsterInfos[8]
        monsterInfo["type"] = "monster"
        monsterInfoList[int(monsterInfos[0])] = monsterInfo
    return monsterInfoList

#load map information from map.dat
# return
#    {@MAP_NUMBER_1: {@MONSTER_ID_1: @MONSTER_RATE_1, @MONSTER_ID_2: @MONSTER_RATE_2, ...}, @MAP_NUMBER_2: {@MONSTER_ID_1: @MONSTER_RATE_1, @MONSTER_ID_2: @MONSTER_RATE_2, ...}, ...}
def loadAllMapInfo():
    file = open("data/map.dat", 'r')
    mapList = file.readlines()
    file.close()
    mapInfoList = {}
    for map in mapList[1:]:
        mapInfo = {"name": "unknown", "monster": {}}
        mapInfos = map.replace("\n", "").split("\t")
        mapInfo["name"] = mapInfos[1]
        mapMonster = {}
        for i in range((len(mapInfos) - 2) / 2):
            mapMonster[int(mapInfos[(i + 1) * 2])] = int(mapInfos[(i + 1) * 2 + 1])
        mapInfo["monster"] = mapMonster
        mapInfoList[int(mapInfos[0])] = mapInfo
    return mapInfoList

#load role information from save.dat
# return
#    {@ROLE_ID_1: {@ROLE_ATTRIBUTES_1}, @ROLE_ID_2: {@ROLE_ATTRIBUTES_2}, ... }
#        @ROLE_ATTRIBUTES
#            'uid': UID                                   
#            'username': USERNAME   string
#            'level': USER_LEVEL    int
#            'exp': USER_EXP        int
#            'job': USER_JOB        TBD(string)
#            'atk': USER_ATTACK     int
#            'def': USER_DEFENSE    int
#            'maxHP': USER_MAX_HP   int
#            'maxMP': USER_MAX_MP   int
#            'HP': USER_HP          int
#            'MP': USER_MP          int
#            'gold': USER_GOLD      int
#            'map': USER_MAP_ID     int
def loadAllRoleInfo():
    file = open("save/save.dat", 'r')
    roleList = file.readlines()
    file.close()
    roleInfoList = {}
    i = 0
    for role in roleList[1:]:
        roleInfo = {}
        roleInfos = role.replace("\n", "").split("\t")
        roleInfo["uid"] = int(roleInfos[0])
        roleInfo["username"] = roleInfos[1]
        roleInfo["level"] = int(roleInfos[2])
        roleInfo["exp"] = int(roleInfos[3])
        roleInfo["job"] = roleInfos[4]
        roleInfo["atk"] = int(roleInfos[5])
        roleInfo["def"] = int(roleInfos[6])
        roleInfo["maxHP"] = int(roleInfos[7])
        roleInfo["maxMP"] = int(roleInfos[8])
        roleInfo["HP"] = int(roleInfos[9])
        roleInfo["MP"] = int(roleInfos[10])
        roleInfo["gold"] = int(roleInfos[11])
        roleInfo["map"] = int(roleInfos[12])
        roleInfo["type"] = "role"
        roleInfoList[i] = roleInfo
        i += 1
    return roleInfoList

# attr:
#    roleInfoList    {@ROLE_ID_1: {"username": @USERNAME_1, ...}, @ROLE_ID_2: {"username": @USERNAME_2, ...}, ...}
# return
#    {@ROLE_ATTRIBUTES_1}
#        @ROLE_ATTRIBUTES 
#            'uid': UID                                   
#            'username': USERNAME   string
#            'level': USER_LEVEL    int
#            'exp': USER_EXP        int
#            'job': USER_JOB        TBD(string)
#            'atk': USER_ATTACK     int
#            'def': USER_DEFENSE    int
#            'maxHP': USER_MAX_HP   int
#            'maxMP': USER_MAX_MP   int
#            'HP': USER_HP          int
#            'MP': USER_MP          int
#            'gold': USER_GOLD      int
#            'map': USER_MAP_ID     int
#    None: Not Found
def getRoleInfoByUserame(username_str, roleInfoList_dict):
    for id in roleInfoList_dict:
        if roleInfoList_dict[id]["username"] == username_str:
            return roleInfoList_dict[id]
    return None

#get level up exp which level
def getLevelUpExp(level_int):
    exp = level_int * level_int * level_int * 10
    return exp

#write all role info to file
# attr
#    roleInfoList    {@ROLE_ID_1: {@ROLE_ATTRIBUTES_1}, @ROLE_ID_2: {@ROLE_ATTRIBUTES_2}, ... }
#        @ROLE_ATTRIBUTES
#            'uid': UID                                   
#            'username': USERNAME   string
#            'level': USER_LEVEL    int
#            'exp': USER_EXP        int
#            'job': USER_JOB        TBD(string)
#            'atk': USER_ATTACK     int
#            'def': USER_DEFENSE    int
#            'maxHP': USER_MAX_HP   int
#            'maxMP': USER_MAX_MP   int
#            'HP': USER_HP          int
#            'MP': USER_MP          int
#            'gold': USER_GOLD      int
#            'map': USER_MAP_ID     int
def saveRoleInfo(roleInfoList_dict):
    roleInfo = "uid\tusername\tlevel\texp\tjob\tattack\tdefense\tmaxHP\tmaxMP\tHP\tMP\tgold\tmap\n"
    for number in roleInfoList_dict:
        roleInfo = roleInfo + str(roleInfoList_dict[number]["uid"]) + "\t"
        roleInfo = roleInfo + roleInfoList_dict[number]["username"] + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["level"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["exp"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["job"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["atk"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["def"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["maxHP"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["maxMP"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["HP"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["MP"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["gold"]) + "\t"
        roleInfo = roleInfo + str(roleInfoList_dict[number]["map"]) + "\n"
    file = open("save/save2.dat", 'w') 
    file.write(roleInfo)
    file.close()
