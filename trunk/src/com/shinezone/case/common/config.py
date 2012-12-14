#-*- coding:utf-8  -*-
import os, sys, inspect
import gameConfig, log

def current_path():  
    path = os.path.realpath(sys.path[0])
    if os.path.isfile(path):
        path = os.path.dirname(path)
        return os.path.abspath(path)
    else:
        caller_file = inspect.stack()[1][1]
        return os.path.abspath(os.path.dirname(caller_file))

#config file get value
#line[line.find("=>", line.find("COLUMN_NAME")) + 2:line.find(",", line.find("COLUMN_NAME"))].replace(" ", "")
#config file get array
#line[line.find("array(", line.find("=>", line.find("COLUMN_NAME")) + 2) + 6:line.find(")", line.find("=>", line.find("COLUMN_NAME")))]

# GAME SERVER CONFIG
DATABASE_IP = '172.17.0.23';
DATABASE_DB_NAME = "sina_gloryland";
DATABASE_USER = "root"
DATABASE_PASSWORD = "Lhi38rf3rd"
USER_ID = "100001567971464"
GAME_URL = "http://dev-weibo-gloryland.shinezoneapp.com/dev_qa_test/j7/j7.php?/SComd/&signed_request=UyPGppOUrVAzPI-ea3QmkmjQ83v4BsXAkbXhlCGmKl0.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImV4cGlyZXMiOjEzNDU0NDk2MDAsImlzc3VlZF9hdCI6MTM0NTQ0NTIzMSwib2F1dGhfdG9rZW4iOiJBQUFHZkRYVkhwWkJNQkFCYVpDWkFaQkVxTjc1MEFOcnhCT2dwNFgwcG1SeFZxT1pCWE5zY0tmRmRxWkFwcExUMU9scFpCcVlHN1hSYWFtRk9aQ09xZGU2bVpDR3V0MjVTZkk1alJFbTM1T1hxS2FnZ0dGMTdLZUVaQzEiLCJ1c2VyIjp7ImNvdW50cnkiOiJoayIsImxvY2FsZSI6InpoX0NOIiwiYWdlIjp7Im1pbiI6MjF9fSwidXNlcl9pZCI6IjEwMDAwMTU2Nzk3MTQ2NCJ9&wyx_user_id=100001567971464&wyx_session_key=1&wyx_signature=2&token=218d681960530e8cba3bcc6af2236377"
MEM_CACHE_URL = "http://dev-weibo-gloryland.shinezoneapp.com/dev_ycge/j7/j7.php?/test/Memcache/&type=%s&key=%s&value=%s&timeout=%s&token=218d681960530e8cba3bcc6af2236377&wyx_user_id=" + USER_ID
USER_ID_2 = "100004282802566"
GAME_URL_2 = "http://dev-weibo-gloryland.shinezoneapp.com/dev_qa_test/j7/j7.php?/index/index&error_reason=user_denied&error=access_denied&error_description=The+user+denied+your+request.&code=AQA7lg9AreOdCjBmc4llQNSk--x6umhpeO-sXiT_7dXQcC3mPIPTHjLg4QTlipIBwpdViglPMGttk5YIoAVXbC9zzKte4D5XsSrAc9sBqq6aDzNj-DuUW3EKtlzPjQm7YMI9rlzN7zjfl9jolKp6zDx_YG9kXPHFJSM8IV6LuLgeVRgsdNJ0cbmawLbHk3hd_9COB8IDPwaLRV_Q6nMLalRM&signed_request=JmIjRevzzysObw4xA_Zqs895vLjOpowcH6HqLGDavZE.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImV4cGlyZXMiOjEzNDYxMjY0MDAsImlzc3VlZF9hdCI6MTM0NjEyMjM2OSwib2F1dGhfdG9rZW4iOiJBQUFHZkRYVkhwWkJNQkFHZXI4amJ1MjlJeTVGUVpCcXhLQjdZTm9rQUJyMWE2YlI1Q1ljVFlaQVlvT1JYVjQzV1Q3dlpBVUFPN3RwTHc5QU1XWkNHWGl0azFTVmdOWkFxZTRORjdpOUoxTjBZcEZ2VzY5M1lORCIsInVzZXIiOnsiY291bnRyeSI6ImhrIiwibG9jYWxlIjoiemhfQ04iLCJhZ2UiOnsibWluIjoyMX19LCJ1c2VyX2lkIjoiMTAwMDA0MjgyODAyNTY2In0"

# GAME CONFIG FILE PATH

CONFIG_FILE_PATH = current_path() + "\\.." + "\configs\\"
GAME_CONFIG_PY_PATH = current_path() + "\\gameConfig.py"
ITEM_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "items\\items_en.php"
SKILL_BOOK_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "books\\skill_books_en.php"
UPGRADE_BOOK_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "books\\upgrade_skills_en.php"
SEED_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "farm\\seeds_en.php"
STONE_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "props\\stones_en.php"
EQUIP_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "props\\equips_en.php"
EQUIP_MERGE_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "props\\equipmerge.php"
FARM_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "farm\\farms.php"
BUILDING_CONFIG_FILE_PATH = CONFIG_FILE_PATH + "building\\buildings.php"
EXP_FILE_PATH = CONFIG_FILE_PATH + "exp\\exp.php"

# TEST CASE CONFIG
# 随机范围测试的测试次数
RANGE_TEST_COUNT = 100
# 检验时间点所允许的最大误差，单位秒（通信和代码运行时间）
TEST_TIME_MAX_PERMISSIBLE_ERROR = 2

def getDBInfoByItemId(itemId):
    BOOK_ID_MIN = 300000
    BOOK_ID_MAX = 400000
    STONE_ID_MIN = 400000
    STONE_ID_MAX = 500000
    SEED_ID_MIN = 500000
    SEED_ID_MAX = 600000
    OTHER_ID_MIN = 600000
    OTHER_ID_MAX = 700000
    #item_id_range                                       tbl_name            column(item_id)      column(count)
    #300000 <= itemId < 400000 : skill_book              tblUserStorages     iItemId             iCount
    #400000 <= itemId < 500000 : stone                   tblUserStones       iStoneId            iCount
    #500000 <= itemId < 600000 : seed                    tblUserSeeds        iSeedId             iCount
    #600000 <= itemId < 700000 : other                   tblUserStorages     iItemId             iCount
    if BOOK_ID_MIN <= itemId < BOOK_ID_MAX:
        return "tblUserStorages", "iItemId"
    elif STONE_ID_MIN <= itemId < STONE_ID_MAX:
        for stone in gameConfig.GAME_STONE_LIST:
            if stone["stoneId"] == itemId:
                return "tblUserStones", "iStoneId"
    elif SEED_ID_MIN <= itemId < SEED_ID_MAX:
        for seed in gameConfig.GAME_SEED_LIST:
            if seed["seedId"] == itemId:
                return "tblUserSeeds", "iSeedId"
    elif OTHER_ID_MIN <= itemId < OTHER_ID_MAX:
        for misc in gameConfig.GAME_ITEM_LIST:
            if misc["itemId"] == itemId:
                return "tblUserStorages", "iItemId"
    log.writeErrorLog("unknown item id: " + str(itemId))
    return False

#        'tblEssenceCharms'=>array('ct'=>range(0,1)),
#        'tblStagingWorlds'=>array('ct'=>range(0,1)),
#        'tblTasks'=>array('ct'=>range(0,1)),
#        'tblUserEmail'=>array('ct'=>range(0,4)),
#        'tblUserEquips'=>array('ct'=>range(0,4)),
#        'tblUserHeros'=>array('ct'=>range(0,3)),
#        'tblUserHeroSkills'=>array('ct'=>range(0,4)),
#        'tblUserHeroSouls'=>array('ct'=>range(0,4)),
#        'tblUserSeeds'=>array('ct'=>range(0,4)),
#        'tblUserStagings'=>array('ct'=>range(0,1)),
#        'tblUserStones'=>array('ct'=>range(0,4)),
#        'tblUserStorages'=>array('ct'=>range(0,4)),
def getDBName(dbName, userId):
    TBL_ESSENCECHARMS_COUNT = 2
    TBL_STAGINGWORLDS_COUNT = 2
    TBL_TASKS_COUNT = 2
    TBL_USERSTAGINGS_COUNT = 2
    TBL_USERHEROS_COUNT = 4
    TBL_USEREMAIL_COUNT = 5
    TBL_USEREQUIPS_COUNT = 5
    TBL_USERHEROSKILLS_COUNT = 5
    TBL_USERHEROSOULS_COUNT = 5
    TBL_USERSEEDS_COUNT = 5
    TBL_USERSTONES_COUNT = 5
    TBL_USERSTORAGES_COUNT = 5
    dbName = dbName
    if dbName == "tblEssenceCharms":
        dbName = dbName + "_" + str(int(userId) % TBL_ESSENCECHARMS_COUNT)
    elif dbName == "tblStagingWorlds":
        dbName = dbName + "_" + str(int(userId) % TBL_STAGINGWORLDS_COUNT)
    elif dbName == "tblTasks":
        dbName = dbName + "_" + str(int(userId) % TBL_TASKS_COUNT)
    elif dbName == "tblUserEmail":
        dbName = dbName + "_" + str(int(userId) % TBL_USEREMAIL_COUNT)
    elif dbName == "tblUserEquips":
        dbName = dbName + "_" + str(int(userId) % TBL_USEREQUIPS_COUNT)
    elif dbName == "tblUserHeros":
        dbName = dbName + "_" + str(int(userId) % TBL_USERHEROS_COUNT)
    elif dbName == "tblUserHeroSkills":
        dbName = dbName + "_" + str(int(userId) % TBL_USERHEROSKILLS_COUNT)
    elif dbName == "tblUserHeroSouls":
        dbName = dbName + "_" + str(int(userId) % TBL_USERHEROSOULS_COUNT)
    elif dbName == "tblUserSeeds":
        dbName = dbName + "_" + str(int(userId) % TBL_USERSEEDS_COUNT)
    elif dbName == "tblUserStagings":
        dbName = dbName + "_" + str(int(userId) % TBL_USERSTAGINGS_COUNT)
    elif dbName == "tblUserStones":
        dbName = dbName + "_" + str(int(userId) % TBL_USERSTONES_COUNT)
    elif dbName == "tblUserStorages":
        dbName = dbName + "_" + str(int(userId) % TBL_USERSTORAGES_COUNT)
    return dbName

def isEquip(equipId):
    EQUIP_ID_MIN = 200000
    EQUIP_ID_MAX = 300000
    if EQUIP_ID_MIN <= equipId < EQUIP_ID_MAX:
        for equip in gameConfig.GAME_EQUIP_LIST:
            if equip["equipId"] == equipId:
                return True
        log.writeErrorLog("unknown equip id: " + str(equipId))
    return False

def getMaxMemberCountByGuildLevel(level):
    if type(level) != int:
        return False
    return 5 * (level + 1)

def getItemConfig():
    file = open(ITEM_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    items = []
    for line in lines:
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            item = {}
            itemId = int(line[line.find("=>", line.find("iItemId")) + 2:line.find(",", line.find("iItemId"))].replace(" ", ""))
            item["itemId"] = itemId
            iType = int(line[line.find("=>", line.find("iType")) + 2:line.find(",", line.find("iType"))].replace(" ", ""))
            item["itemType"] = iType
            if line.find("iReward") != -1:
                iReward = int(line[line.find("=>", line.find("iReward")) + 2:line.find(",", line.find("iReward"))].replace(" ", ""))
                item["itemReward"] = iReward
            if line.find("aReward") != -1:
                aReward = line[line.find("array(", line.find("=>", line.find("aReward")) + 2) + 6:line.find(")", line.find("=>", line.find("aReward")))].split(",")
                item["itemReward"] = aReward
            if line.find("iSellPrice") != -1:
                price = int(line[line.find("=>", line.find("iSellPrice")) + 2:line.find(",", line.find("iSellPrice"))].replace(" ", ""))
                item["price"] = price
            items.append(item)
    file.close()
    return items

def getSkillBookConfig():
    file = open(SKILL_BOOK_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    books = []
    for line in lines:   
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            book = {}
            bookId = int(line[line.find("=>", line.find("iBookId")) + 2:line.find(",", line.find("iBookId"))].replace(" ", ""))
            price = int(line[line.find("=>", line.find("iSellPrice")) + 2:line.find(",", line.find("iSellPrice"))].replace(" ", ""))
            skillId = int(line[line.find("=>", line.find("iLearnSkillId")) + 2:line.find(",", line.find("iLearnSkillId"))].replace(" ", ""))
            book["bookId"] = bookId
            book["price"] = price
            book["skillId"] = skillId
            books.append(book)
    file.close()
    return books

def getUpgradeBookConfig():
    file = open(UPGRADE_BOOK_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    books = []
    for line in lines:   
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            book = {}
            bookId = int(line[line.find("=>", line.find("iBookId")) + 2:line.find(",", line.find("iBookId"))].replace(" ", ""))
            price = int(line[line.find("=>", line.find("iSellPrice")) + 2:line.find(",", line.find("iSellPrice"))].replace(" ", ""))
            bookLevel = int(line[line.find("=>", line.find("iBookLevel")) + 2:line.find(",", line.find("iBookLevel"))].replace(" ", ""))
            book["bookId"] = bookId
            book["price"] = price
            book["bookLevel"] = bookLevel
            books.append(book)
    file.close()
    return books

def getSeedConfig():
    file = open(SEED_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    seeds = []
    for line in lines:   
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            seed = {}
            seedType = int(line[line.find("=>", line.find("iSeedType")) + 2:line.find(",", line.find("iSeedType"))].replace(" ", ""))
            seedId = int(line[line.find("=>", line.find("iSeedId")) + 2:line.find(",", line.find("iSeedId"))].replace(" ", ""))
            matureTime = int(line[line.find("=>", line.find("iMature")) + 2:line.find(",", line.find("iMature"))].replace(" ", ""))
            reward = int(line[line.find("=>", line.find("iReward")) + 2:line.find(",", line.find("iReward"))].replace(" ", ""))
            seed["seedType"] = seedType
            seed["seedId"] = seedId
            seed["matureTime"] = matureTime
            seed["reward"] = reward
            seeds.append(seed)
    file.close()
    return seeds

def getStoneConfig():
    file = open(STONE_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    stones = []
    for line in lines:
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            stone = {}
            stoneId = int(line[line.find("=>", line.find("iStoneId")) + 2:line.find(",", line.find("iStoneId"))].replace(" ", ""))
            stone["stoneId"] = stoneId
            stones.append(stone)
    file.close()
    return stones

def getEquipConfig():
    file = open(EQUIP_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    equips = []
    for line in lines:
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            equip = {}
            equipId = line[line.find("=>", line.find("iEquipId")) + 2:line.find(",", line.find("iEquipId"))].replace(" ", "")
            equip["equipId"] = int(equipId)
            equips.append(equip)
    file.close()
    return equips

def getEquipMergeConfig():
    file = open(EQUIP_MERGE_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    equipMerges = []
    for line in lines:
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            equipMerge = {}
            itemId = line[line.find("/*START*/") + 9:line.find(" ", line.find("/*START*/"))]
            equipId = line[line.find("=>", line.find("iEquipId")) + 2:line.find(",", line.find("iEquipId"))].replace(" ", "")
            count = line[line.find("=>", line.find("iCount")) + 2:line.find(")", line.find("iCount"))].replace(" ", "")
            equipMerge["itemId"] = int(itemId)
            equipMerge["equipId"] = int(equipId)
            equipMerge["count"] = int(count)
            equipMerges.append(equipMerge)
    file.close()
    return equipMerges

def getFarmConfig():
    file = open(FARM_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    farms = ""
    isStart = False
    for line in lines:
        if line.find("farm/farms") != -1:
            isStart = True
            continue
        if line.find("$J7CONFIG") != -1:
            lines = farms.replace("\n\n", "\n").split("\n")
        if line.find("/*END*/") == -1:
            line = line.replace("\n", "")
        if line.find("/*START*/") != -1:
            line = "\n" + line
        if isStart:
            farms += line.replace("\t", "")
    farms = []
    for line in lines[:-1]:
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            farm = {}
            farmId = line[line.find("/*START*/") + 9:line.find(" ", line.find("/*START*/"))]
            farmType = line[line.find("=>", line.find("iFarmType")) + 2:line.find(",", line.find("iFarmType"))].replace(" ", "")
            unlock = line[line.find("array(", line.find("=>", line.find("oUnlocks")) + 2) + 6:line.find(")", line.find("=>", line.find("oUnlocks")))]
            heroLevel = friendCount = goldIngot = percent = 0
            if int(farmType) == 1:
                heroLevel = unlock[unlock.find("=>", unlock.find("iMainHeroLevel")) + 2:unlock.find(",", unlock.find("iMainHeroLevel"))].replace(" ", "")
                friendCount = unlock[unlock.find("=>", unlock.find("iFriendCount")) + 2:unlock.find(",", unlock.find("iFriendCount"))].replace(" ", "")
                farm["heroLevel"] = int(heroLevel)
                farm["friendCount"] = int(friendCount)
            elif int(farmType) == 2:
                goldIngot = unlock[unlock.find("=>", unlock.find("iGoldIngot")) + 2:unlock.find(",", unlock.find("iGoldIngot"))].replace(" ", "")
                percent = unlock[unlock.find("=>", unlock.find("iPercent")) + 2:unlock.find(",", unlock.find("iPercent"))].replace(" ", "")
                farm["goldIngot"] = int(goldIngot)
                farm["percent"] = int(percent)
            farm["farmId"] = int(farmId)
            farm["farmType"] = int(farmType)            
            farms.append(farm)
    file.close()
    return farms

def getBuildingConfig():
    file = open(BUILDING_CONFIG_FILE_PATH, 'r')
    lines = file.readlines()
    buildings = ""
    isStart = False
    for line in lines:
        if line.find("building/buildings") != -1:
            isStart = True
            continue
        lines = buildings.replace("\n\n", "\n").split("\n")
        if line.find("/*END*/") == -1:
            line = line.replace("\n", "")
        if line.find("/*START*/") != -1:
            line = "\n" + line
        if isStart:
            buildings += line.replace("\t", "")
    buildings = []
    for line in lines[:-1]:
        if line.find("/*START*/") != -1:
            if line.find("=>") == -1:
                continue
            building = {}
            buildingId = line[line.find("=>", line.find("iBuildingId")) + 2:line.find(",", line.find("iBuildingId"))].replace(" ", "")
            unlockLevel = line[line.find("=>", line.find("iBuildingUnlock")) + 2:line.find(",", line.find("iBuildingUnlock"))].replace(" ", "")
            building["buildingId"] = int(buildingId)
            building["unlockLevel"] = int(unlockLevel)            
            buildings.append(building) 
    return buildings

def getLevelUpExpConfig():
    file = open(EXP_FILE_PATH, 'r')
    lines = file.readlines()
    expList = [0 for exp in range (100 + 1)]
    for line in lines:
        if line.find("=>") != -1:
            level = line[:line.find("=>")].replace("\t", "").replace(" ", "")
            exp = line[line.find("=>") + 2:line.find(",")].replace(" ", "")
            expList[int(level)] = int(exp)
    file.close()
    return expList

def initGameConfig():
    file = open(GAME_CONFIG_PY_PATH, 'w')
    item = getItemConfig()
    skillBook = getSkillBookConfig()
    upgrade = getUpgradeBookConfig()
    seed = getSeedConfig()
    stone = getStoneConfig()
    equip = getEquipConfig()
    equipMerge = getEquipMergeConfig()
    farm = getFarmConfig()
    building = getBuildingConfig()
    exp = getLevelUpExpConfig()
    file.write("GAME_MAX_LEVEL = 101" + "\n")
    file.write("GAME_GUILD_REQUIRE_SILVER = 10000" + "\n")
    file.write("GAME_GUILD_REQUIRE_LEVEL = 15" + "\n")
    file.write("GAME_GUILD_ROLE_MASTER = 5000001" + "\n")
    file.write("GAME_GUILD_ROLE_SENATOR = 5000002" + "\n")
    file.write("GAME_GUILD_ROLE_ELITE = 5000003" + "\n")
    file.write("GAME_GUILD_ROLE_MEMBER = 5000004" + "\n")
    file.write("GAME_MAIN_HERO_ID = [110000, 110001]" + "\n")
    file.write("GAME_GUILD_TECHNOLOGY_LIST = [20650, 20651, 20652, 20653, 20654, 20655]" + "\n")
    file.write("GAME_ITEM_LIST = " + str(item) + "\n")
    file.write("GAME_SKILL_BOOK_LIST = " + str(skillBook) + "\n")
    file.write("GAME_UPGRADE_BOOK_LIST = " + str(upgrade) + "\n")
    file.write("GAME_SEED_LIST = " + str(seed) + "\n")
    file.write("GAME_STONE_LIST = " + str(stone) + "\n")
    file.write("GAME_EQUIP_LIST = " + str(equip) + "\n")
    file.write("GAME_EQUIP_MERGE_LIST = " + str(equipMerge) + "\n")
    file.write("GAME_FARM_LIST = " + str(farm) + "\n")
    file.write("GAME_BUILDING_LIST = " + str(building) + "\n")
    file.write("GAME_EXP_LIST = " + str(exp) + "\n")
    file.close()

#initGameConfig()
