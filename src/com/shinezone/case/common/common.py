#-*- coding:utf-8  -*-
import random
import communication, config, database, gameConfig, log

def clearCache(userId=config.USER_ID):
    return communication.doPost("", "http://dev-weibo-gloryland.shinezoneapp.com/dev_qa_test/j7/j7.php?/fsadmin/addUserExp/&action=clearRedisDbCache&sUid=" + userId)

def dataInit(userId=config.USER_ID):
    return communication.request('["System","dataInit",[]]')

def getServerTime():
    return communication.toJson(communication.request('["Lucky","ping",[]]', False))[1][2]

def getDBTime():
    return database.select("dual", ["unix_timestamp(now())"])

def addEquip(equipId, heroId=0, strengthenLevel=0, grooveCount=3, userId=config.USER_ID):
    if config.isEquip(equipId):
        return database.insert("tblUserEquips", ["sUid", "iUEid", "iHeroId", "iEquipId", "iStrengThenLevel", "iGrooveCount"], [userId, random.randint(1000000, 100000000), heroId , equipId, strengthenLevel, grooveCount])
    return False

def delEquip(iUEid=0, equipId=0, userId=config.USER_ID):
    if iUEid != 0:
        return database.delete("tblUserEquips", {"sUid":userId, "iUEid":iUEid})
    if equipId != 0:
        if config.isEquip(equipId):
            return database.delete("tblUserEquips", {"sUid":userId, "iEquipId":equipId})
        return False
    return database.delete("tblUserEquips", {"sUid":userId})

def getEquipInfo(equipId=0, count= -1, userId=config.USER_ID):
    if equipId == 0:
        equipInfo = database.select("tblUserEquips", ["iUEid", "iHeroId", "iEquipId", "iStrengThenLevel", "iGrooveCount"], {"sUid":userId}, count)
    else:
        equipInfo = database.select("tblUserEquips", ["iUEid", "iHeroId", "iEquipId", "iStrengThenLevel", "iGrooveCount"], {"sUid":userId, "iEquipId":equipId}, count)
    return equipInfo

def getHeroSoulCount(heroId, userId=config.USER_ID):
    return database.select("tblUserHeroSouls", ["iCount"], {"sUid":userId, "iHeroId":heroId})

def setHeroSoulCount(heroId, count, userId=config.USER_ID):
    return database.update("tblUserHeroSouls", {"iCount":count}, {"sUid":userId, "iHeroId":heroId})

def getHeroStrong(heroId, userId=config.USER_ID):
    return database.select("tblUserHeros", ["iStrong"], {"sUid":userId, "iHeroId":heroId})
    
def setHeroStrong(heroId, strong, userId=config.USER_ID):
    return database.update("tblUserHeros", {"iStrong":strong}, {"sUid":userId, "iHeroId":heroId})

def getHeroIntelligence(heroId, userId=config.USER_ID):
    return database.select("tblUserHeros", ["iIntelligence"], {"sUid":userId, "iHeroId":heroId})
    
def setHeroIntelligence(heroId, intelligence, userId=config.USER_ID):
    return database.update("tblUserHeros", {"iIntelligence":intelligence}, {"sUid":userId, "iHeroId":heroId})

def getHeroAgility(heroId, userId=config.USER_ID):
    return database.select("tblUserHeros", ["iAgility"], {"sUid":userId, "iHeroId":heroId})
    
def setHeroAgility(heroId, agility, userId=config.USER_ID):
    return database.update("tblUserHeros", {"iAgility":agility}, {"sUid":userId, "iHeroId":heroId})

def getHeroEndurance(heroId, userId=config.USER_ID):
    return database.select("tblUserHeros", ["iEndurance"], {"sUid":userId, "iHeroId":heroId})
    
def setHeroEndurance(heroId, endurance, userId=config.USER_ID):
    return database.update("tblUserHeros", {"iEndurance":endurance}, {"sUid":userId, "iHeroId":heroId})

def getSliverCoin(userId=config.USER_ID):
    return int(database.select("tblUsers", ["iSilverCoin"], {"sUid":userId}))

def setSliverCoin(silverCoin, userId=config.USER_ID):
    return database.update("tblUsers", {"iSilverCoin":silverCoin}, {"sUid":userId})

def getGoldIngot(userId=config.USER_ID):
    return int(database.select("tblUsers", ["iGoldIngot"], {"sUid":userId}))

def setGoldCoin(goldCoin, userId=config.USER_ID):
    return database.update("tblUsers", {"iGoldCoin":goldCoin}, {"sUid":userId})

def getGoldCoin(userId=config.USER_ID):
    return int(database.select("tblUsers", ["iGoldCoin"], {"sUid":userId}))

def setGoldIngot(goldIngot, userId=config.USER_ID):
    return database.update("tblUsers", {"iGoldIngot":goldIngot}, {"sUid":userId})

def getEnergy(userId=config.USER_ID):
    return int(database.select("tblUsers", ["iEnergy"], {"sUid":userId}))

def setEnergy(energy, userId=config.USER_ID):
    return database.update("tblUsers", {"iEnergy":energy}, {"sUid":userId})

def getAchievement(userId=config.USER_ID):
    return int(database.select("tblUsers", ["iAchievement"], {"sUid":userId}))

def setAchievement(achievement, userId=config.USER_ID):
    return database.update("tblUsers", {"iAchievement":achievement}, {"sUid":userId})

def getItemCount(itemId, userId=config.USER_ID):
    DBInfo = config.getDBInfoByItemId(itemId)
    if DBInfo:
        tbl_name, col_item = DBInfo
        count = database.select(tbl_name, ["iCount"], {"sUid":userId, col_item:itemId})
        if count is None:
            count = 0
        return int(count) 
    return False

# itemId = 0 & count = 0:删除所有物品
# itemId = 0 & count != 0:添加所有物品
def setItemCount(itemId, count, userId=config.USER_ID):
    if itemId == 0:
        # delete all item
        if count == 0:
            database.delete("tblUserStorages", {"sUid":userId})
            database.delete("tblUserStones", {"sUid":userId})
            database.delete("tblUserSeeds", {"sUid":userId})
        # add all item
        else:
            for item in gameConfig.GAME_ITEM_LIST:
                database.delete("tblUserStorages", {"sUid":userId, "iItemId":itemId})
                database.insert("tblUserStorages", ["sUid", "iItemId", "iCount"], [userId, item["itemId"], count])
            for seed in gameConfig.GAME_SEED_LIST:
                database.delete("tblUserStones", {"sUid":userId, "iStoneId":itemId})
                database.insert("tblUserStones", ["sUid", "iStoneId", "iCount"], [userId, seed["seedId"], count])
            for stone in gameConfig.GAME_STONE_LIST:
                database.delete("tblUserSeeds", {"sUid":userId, "iSeedId":itemId})
                database.insert("tblUserSeeds", ["sUid", "iSeedId", "iCount"], [userId, stone["stoneId"], count])
    else:
        DBInfo = config.getDBInfoByItemId(itemId)
        if not DBInfo:
            return False
        tbl_name, col_item = DBInfo
        if count == 0:
            return database.delete(tbl_name, {"sUid":userId, col_item:itemId})
        else:
            database.delete(tbl_name, {"sUid":userId, col_item:itemId})
            database.insert(tbl_name, ["sUid", col_item, "iCount"], [userId, itemId, count])

# heroId: =0    主将
def getLevel(heroId=0, userId=config.USER_ID):
    if heroId == 0:
        for tmpHeroId in gameConfig.GAME_MAIN_HERO_ID:
            if database.select("tblUserHeros", ["iHeroId"], {"iHeroId":tmpHeroId, "sUid":userId}) != None:
                heroId = tmpHeroId
                break
    exp = database.select("tblUserHeros", ["iExp"], {"iHeroId":heroId, "sUid":userId})
    if exp == 0:
        return 1
    else:
        for level in range(len(gameConfig.GAME_EXP_LIST)):
            if exp < gameConfig.GAME_EXP_LIST[level]:
                break
        return level - 1

# level: 需要设置的等级
# exp: >0    多出多少经验
#      <0    缺少多少经验
# heroIdL: =0    主将
def setLevel(level, exp=0, heroId=0, userId=config.USER_ID):
    if level <= 0 or exp + gameConfig.GAME_EXP_LIST[level] < 0:
        log.writeErrorLog("level must more than zero")
        return False
    if heroId == 0:
        for tmpHeroId in gameConfig.GAME_MAIN_HERO_ID:
            if database.select("tblUserHeros", ["iHeroId"], {"iHeroId":tmpHeroId, "sUid":userId}) != None:
                heroId = tmpHeroId
                break
        if heroId == 0:
            log.writeErrorLog("Not Found main hero")
            return False
    exp += gameConfig.GAME_EXP_LIST[level]
    oldExp = database.select("tblUserHeros", ["iExp"], {"iHeroId":heroId, "sUid":userId})
    oldLevel = 1
    if oldExp != 0:
        for oldLevel in range(len(gameConfig.GAME_EXP_LIST)):
            if oldExp < gameConfig.GAME_EXP_LIST[oldLevel]:
                break
        oldLevel = oldLevel - 1
    database.update("tblUserHeros", {"iExp":exp}, {"iHeroId":heroId, "sUid":userId})
    database.update("tblUsers" , {"iCalcLevel":level}, {"sUid":userId})
    #unlock building
    for building in gameConfig.GAME_BUILDING_LIST:
        # add
        if level > building["unlockLevel"]:
            if database.select("tblUserBuildingLevel", ["iBuildingId"], {"sUid":userId, "iBuildingId" : building["buildingId"]}, 1 , False) == None:
                database.insert("tblUserBuildingLevel", ["sUid", "iBuildingId", "IBuildingLevel"], [userId, building["buildingId"], 1])
        # delete
        if oldLevel > building["unlockLevel"] and level < building["unlockLevel"]:
            database.delete("tblUserBuildingLevel", {"sUid":userId, "iBuildingId":building["buildingId"]})
    #unlock Farm
    for farm in gameConfig.GAME_FARM_LIST:
        if farm["farmType"] != 1:
            continue
        # add
        if level > farm["heroLevel"]:
            if database.select("tblUserFarms", ["iFarmId"], {"sUid":userId, "iFarmId" : farm["farmId"]}, 1 , False) == None:
                database.insert("tblUserFarms", ["sUid", "iFarmId"], [userId, farm["farmId"]])
        # delete
        if oldLevel > farm["heroLevel"] and level < farm["heroLevel"]:
            database.delete("tblUserFarms", {"sUid":userId, "iFarmId":farm["farmId"]})
    #match
    if oldLevel >= 20 and level < 20:
        database.delete("tblMatchGroupList", {"sUid":userId})
    if oldLevel < 20 and level >= 20:
        database.insert("tblMatchGroupList", ["sUid", "iRobot"], [userId, 2])

def getBagSlotCount(userId=config.USER_ID):
    return int(database.select("tblUserInfos", ["iPropOpacity"], {"sUid":userId}))

# count: 设置背包已使用的格子数
def setBagSlotCount(count=20, userId=config.USER_ID):
    if count % 5 != 0:
        log.writeErrorLog("bag Slot must is a multiple of 5")
        return False
    return database.update("tblUserInfos", {"iPropOpacity": count}, {"sUid":userId})

def getHistoryContribution(userId=config.USER_ID):
    return int(database.select("tblUsers", ["iHistoryContribution"], {"sUid":userId}))

def setHistoryContribution(contribution, userId=config.USER_ID):
    return database.update("tblUsers", {"iHistoryContribution":contribution}, {"sUid":userId})

# vipType: 1    非VIP
#          2    体验卡
#          3    三天卡
#          4    周卡
#          5    月卡
#          6    季卡
#          7    半年卡
#          8    年卡
def getVip(userId=config.USER_ID):
    return database.select("tblUserVipInfos", ["sUid", "iVipType", "iVipPoint", "iVipNtime", "iVipChargeTime", "sVipReceiveBox"], {"sUid":userId})      

def setVip(vipType, vipPoint=0, vipTime=0, vipChargeTime=0, vipReceiveBox="", userId=config.USER_ID):
    oldVipType = database.select("tblUserVipInfos", ["iVipType"], {"sUid":userId}, 1 , False) 
    database.update("tblUserVipInfos", {"iVipPoint":vipPoint, "iVipType":vipType, "iVipNtime":vipTime, "iVipChargeTime":vipChargeTime, "sVipReceiveBox":vipReceiveBox}, {"sUid":userId})
    # add vip farm
    if (oldVipType != 1 and vipType == 1) or (oldVipType == 1 and vipType != 1):
        for farm in gameConfig.GAME_FARM_LIST:
            if farm["farmType"] == 3:
                database.delete("tblUserFarms", {"sUid": userId, "iFarmId": farm["farmId"]})
                if (oldVipType == 1 and vipType != 1):
                    database.insert("tblUserFarms", ["sUid", "iFarmId", "iSeedId", "iNTime", "SFriendHelp"], [userId, farm["farmId"], 0, 0, ""])

def setYearVip(userId=config.USER_ID):
    serverTime = getServerTime()
    setVip(8, 1000, serverTime - 60, serverTime + (86400 * 365))

def getFarm(farmId=0, userId=config.USER_ID):
    if farmId == 0:
        return database.select("tblUserFarms", ["sUid", "iFarmId", "iSeedId", "iNTime", "SFriendHelp"], {"sUid": userId}, -1)
    else:
        return database.select("tblUserFarms", ["sUid", "iFarmId", "iSeedId", "iNTime", "SFriendHelp"], {"sUid": userId, "iFarmId": farmId})        

# farmId = 0: 清除所有农田的种植作物
# farmId = -1: 删除所有农田
def setFarm(farmId, seedId=0, time=0, userId=config.USER_ID):
    if farmId == 0:
        database.update("tblUserFarms", {"iSeedId":0, "iNTime":0, "SFriendHelp":""}, {"sUid": userId})
    elif farmId == -1:
        database.delete("tblUserFarms", {"sUid": userId})
    else:
        isIncorrect = True
        for farm in gameConfig.GAME_FARM_LIST:
            if farm["farmId"] == farmId:
                database.delete("tblUserFarms", {"sUid": userId, "iFarmId": farmId})
                database.insert("tblUserFarms", ["sUid", "iFarmId", "iSeedId", "iNTime", "SFriendHelp"], [userId, farmId, seedId, time, ""])
                isIncorrect = False
                break
        if isIncorrect:
            log.writeErrorLog("incorrect farm id" + str(farmId))

def getUserGuild(userId=config.USER_ID):
    return int(database.select("tblUsers", ["iGuildId"], {"sUid":userId}))

def setUserGuild(guildId, role, userId=config.USER_ID):
    oldGuildId = database.select("tblUsers", ["iGuildId"], {"sUid":userId}, 1 , False)
    # user in this guild
#    if oldGuildId == guildId:
#        log.writeErrorLog("user not in a guild")
#        return False
    # guild id not exist
    if database.select("tblGuild", ["iGuildId"], {"iGuildId":guildId}) == ():
        log.writeErrorLog("guild not exist in database: " + str(guildId))
        return False
    if oldGuildId != 0:
        oldGuildMemberCount = database.select("tblGuild", ["iMemberCount"], {"iGuildId":oldGuildId}, 1, False)
        oldGuildEmployeeCount = len(database.select("tblGuildEmployee", ["sEmployeeId"], {"iGuildId":oldGuildId}, -1, False))        
        if oldGuildEmployeeCount != oldGuildMemberCount:
            oldGuildMemberCount = oldGuildEmployeeCount
            database.update("tblGuild", {"iMemberCount":oldGuildMemberCount}, {"iGuildId":oldGuildId})
        if oldGuildMemberCount != 1:
            database.update("tblGuild", {"iMemberCount":oldGuildMemberCount - 1}, {"iGuildId":oldGuildId})
        else:
            database.delete("tblGuild", {"iGuildId": oldGuildId})
            database.delete("tblGuildTechnology", {"iGuildId": oldGuildId})
        database.delete("tblGuildEmployee", {"sEmployeeId": userId, "iGuildId": oldGuildId})
    if guildId != 0:
        # guild member
        memberCount = database.select("tblGuild", ["iMemberCount"], {"iGuildId":guildId}, 1, False)
        if  memberCount >= config.getMaxMemberCountByGuildLevel(int(database.select("tblGuild", ["iGuildLevel"], {"iGuildId":guildId}))):
            log.writeErrorLog("guild member is max: " + str(memberCount))
            return False
        employeeCount = len(database.select("tblGuildEmployee", ["sEmployeeId"], {"iGuildId":guildId}, -1, False))
        if employeeCount != memberCount:
            memberCount = employeeCount
            database.update("tblGuild", {"iMemberCount":memberCount}, {"iGuildId":guildId})
        database.insert("tblGuildEmployee", ["iGuildId", "sEmployeeId", "iRole", "iContribution"], [guildId, userId, role, getHistoryContribution(userId)])
        database.update("tblGuild", {"iMemberCount":memberCount + 1}, {"iGuildId":guildId})
    database.update("tblUsers", {"iGuildId":guildId}, {"sUid":userId})

def getGuildInfo(guildId):
    return database.select("tblGuild", ["iGuildId", "sUid", "iCreateAt", "sMVPId", "iMemberCount", "iFightCount", "iWinCount", "iDestroyCount", "iBindEnemy", "iRank", "iHistoryRank", "iGuildLevel", "iLogoBg", "iLogo", "sGuildName", "sGuildIntro"], {"iGuildId":guildId})

def setGuildInfo(guildId, **guildInfo):
    newGuildInfo = {}
    for arg in guildInfo:
        if arg == "mvpId":
            newGuildInfo["sMVPId"] = guildInfo[arg]
            continue
        if arg == "memberCount":
            newGuildInfo["iMemberCount"] = guildInfo[arg]
            continue
        if arg == "fightCount":
            newGuildInfo["iFightCount"] = guildInfo[arg]
            continue
        if arg == "winCount":
            newGuildInfo["iWinCount"] = guildInfo[arg]
            continue
        if arg == "destroyCount":
            newGuildInfo["iDestroyCount"] = guildInfo[arg]
            continue
        if arg == "bindEnemy":
            newGuildInfo["iBindEnemy"] = guildInfo[arg]
            continue
        if arg == "rank":
            newGuildInfo["iRank"] = guildInfo[arg]
            continue
        if arg == "historyRank":
            newGuildInfo["iHistoryRank"] = guildInfo[arg]
            continue
        if arg == "guildLevel":
            newGuildInfo["iGuildLevel"] = guildInfo[arg]
            continue
        if arg == "logo":
            newGuildInfo["iLogo"] = guildInfo[arg]
            continue
        if arg == "logoBg":
            newGuildInfo["iLogoBg"] = guildInfo[arg]
            continue
        if arg == "guildName":
            if database.select("tblGuild", ["iGuildId"], {"sGuildName":arg}) == None:
                newGuildInfo["sGuildName"] = guildInfo[arg]
                continue
            else:
                log.writeErrorLog("guild name is exist: '" + arg + "'")
                return False
        if arg == "guildIntro":
            newGuildInfo["sGuildIntro"] = guildInfo[arg]
            continue
    return database.update("tblGuild", newGuildInfo, {"iGuildId":guildId})
    
def getGuildRole(userId=config.USER_ID):
    return database.select("tblGuildEmployee", ["iRole"], {"sEmployeeId":userId, "iGuildId":getUserGuild(userId)})

def setGuildRole(role, userId=config.USER_ID):
    # no guild
    if database.select("tblGuildEmployee", ["iRole"], {"sEmployeeId":userId, "iGuildId":getUserGuild(userId)}, 1, False) == 0:
        log.writeErrorLog("user not in a guild")
        return False
    guildId = database.select("tblUsers", ["iGuildId"], {"sUid":userId}, 1, False)
    if not(role in (gameConfig.GAME_GUILD_ROLE_MEMBER, gameConfig.GAME_GUILD_ROLE_ELITE, gameConfig.GAME_GUILD_ROLE_SENATOR, gameConfig.GAME_GUILD_ROLE_MASTER)):
        log.writeErrorLog("role id is error: " + str(role))
        return False
    if role != gameConfig.GAME_GUILD_ROLE_MASTER:
        oldMaster = database.select("tblGuild", ["sUid"], {"iGuildId": guildId})
        database.update("tblGuildEmployee", {"iRole": gameConfig.GAME_GUILD_ROLE_MEMBER}, {"sEmployeeId":oldMaster, "iGuildId": guildId})
    return database.update("tblGuildEmployee", {"iRole":role}, {"sEmployeeId":userId, "iGuildId": guildId})    

def getGuildIdByGuildName(guildName):
    return database.select("tblGuild", ["iGuildId"], {"sGuildName":guildName})

def delGuild(guildId, userId=config.USER_ID):
    database.delete("tblGuild", {"iGuildId":guildId})
    database.delete("tblGuildEmployee", {"iGuildId":guildId})
    database.delete("tblGuildTechnology", {"iGuildId":guildId})
    database.update("tblUsers", {"iGuildId":0}, {"iGuildId":guildId})

def getGuildEmployeeList(guildId):
    return database.select("tblGuildEmployee", ["iGuildId", "sEmployeeId", "iRole", "iContribution", "iJoinTime", "iBattleCount"], {"iGuildId":guildId}, -1)

def getGuildList():
    return database.select("tblGuild", ["iGuildId"], {}, -1)
