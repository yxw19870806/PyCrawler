from com.shinezone.case.common import common, communication, config, gameConfig, log
from com.shinezone.case.guild import addGuild, leaveGuild
import random

# energy prop
class AddGuild():
    REQUEST_SUCCEED = '[1,[1,$guildData,$guildEmployee,$guildTechnology]]'
    REQUEST_FAILED_HAVE_GUILD = '[1,[-1]]'
    REQUEST_FAILED_NOT_ENOUG_SILVER = '[1,[-2]]'
    REQUEST_FAILED_NOT_ENOUG_LEVEL = '[1,[-3]]'
    
    GUILD_TEST_LOGO = 1
    GUILD_TEST_LOGO_BG = 1
    GUILD_TEST_NAME = "Test Guild"
    GUILD_TEST_INTRO = "This is test information"
    
    def __init__(self):
        log.writeResultLog("start guild testing")
    
    def addGuild(self, logo=GUILD_TEST_LOGO, logoBG=GUILD_TEST_LOGO_BG, guildName=GUILD_TEST_NAME, guildIntro=GUILD_TEST_INTRO):
        silver1, level1, guildInfo1, employeeList1 = addGuild.getStatus()
        log.writeBeforeStatus([{"silver coin":silver1}, {"level":level1}, {"guild info":guildInfo1}])
        result = addGuild.sendPackage(logo, logoBG, guildName, guildIntro)
        log.write("add guild:\t\titem logo: " + str(logo) + ", logoBG: " + str(logoBG) + ", guild name: " + guildName + ", guild intro: " + guildIntro)
        silver2, level2, guildInfo2, employeeList2 = addGuild.getStatus()
        log.writeAfterStatus([{"silver coin":silver2}, {"level":level2}, {"guild info":guildInfo2}])
        return silver1, level1, guildInfo1, employeeList1, result, silver2, level2, guildInfo2, employeeList2
    
    # create guild with enough level and silver coin and other conditions
    def normalAddGuild(self):
        level = gameConfig.GAME_GUILD_REQUIRE_LEVEL
        silverCoin = gameConfig.GAME_GUILD_REQUIRE_SILVER
        log.writeResultLog("\tcreate guild with level: " + str(level) + ", silver coin: " + str(silverCoin))
        addGuild.init(level, silverCoin, self.GUILD_TEST_NAME)
        silver1, level1, guildInfo1, employeeList1, result, silver2, level2, guildInfo2, employeeList2 = self.addGuild()
        isPass = True
        if guildInfo1["guildId"] != 0:
            log.write("user is in a guild: " + str(guildInfo1["guildId"]) + " before add guild")
            isPass = False
        elif guildInfo2["guildId"] == 0:
            log.write("user not in a guild after add guild")
            isPass = False
        else:
            if silver1 - silver2 != gameConfig.GAME_GUILD_REQUIRE_SILVER:
                log.write("add guild cost silver coin error: " + str(silver1 - silver2))
                isPass = False 
            responseGuildInfo = communication.toJson(result)[1][1]
            guildId = guildInfo2["guildId"]
            if responseGuildInfo["iGuildId"] != guildInfo2["guildId"]:
                log.write("guild id is not match in response: " + str(responseGuildInfo["iGuildId"]) + " and database: " + guildInfo2["guildId"])
                isPass = False
            if responseGuildInfo["sUid"] != config.USER_ID:
                log.write("guild master user id is error in response: " + responseGuildInfo["sUid"])
                isPass = False
            if guildInfo2["guildMasterId"] != config.USER_ID:
                log.write("guild master user id is error in database: " + responseGuildInfo["sUid"])
                isPass = False
            if responseGuildInfo["iCreateAt"] != guildInfo2["createTime"]:
                log.write("guild create time is not match in response: " + str(responseGuildInfo["iCreateAt"]) + " and database: " + guildInfo2["createTime"])
                isPass = False
            if responseGuildInfo["sMVPId"] != guildInfo2["mvpId"]:
                log.write("guild MVP user id is not match in response: " + responseGuildInfo["sMVPId"] + " and database: " + guildInfo2["mvpId"])
                isPass = False
            if responseGuildInfo["iMemberCount"] != guildInfo2["memberCount"]:
                log.write("guild member count is not match in response: " + str(responseGuildInfo["iMemberCount"]) + " and database: " + guildInfo2["memberCount"])
                isPass = False
            if responseGuildInfo["iFightCount"] != guildInfo2["fightCount"]:
                log.write("guild fight count is not match in response: " + str(responseGuildInfo["iFightCount"]) + " and database: " + guildInfo2["fightCount"])
                isPass = False
            if responseGuildInfo["iWinCount"] != guildInfo2["winCount"]:
                log.write("guild win count is not match in response: " + str(responseGuildInfo["iWinCount"]) + " and database: " + guildInfo2["winCount"])
                isPass = False
            if responseGuildInfo["iDestroyCount"] != guildInfo2["lostCount"]:
                log.write("guild destroy count is not match in response: " + str(responseGuildInfo["iDestroyCount"]) + " and database: " + guildInfo2["lostCount"])
                isPass = False
            if responseGuildInfo["iBindEnemy"] != guildInfo2["bindEnemy"]:
                log.write("guild bind enemy is not match in response: " + str(responseGuildInfo["iBindEnemy"]) + " and database: " + guildInfo2["bindEnemy"])
                isPass = False
            if responseGuildInfo["iRank"] != guildInfo2["rank"]:
                log.write("guild rank is not match in response: " + str(responseGuildInfo["iRank"]) + " and database: " + guildInfo2["rank"])
                isPass = False
            if responseGuildInfo["iHistoryRank"] != guildInfo2["historyRank"]:
                log.write("guild history rank is not match in response: " + str(responseGuildInfo["iHistoryRank"]) + " and database: " + guildInfo2["historyRank"])
                isPass = False
            if responseGuildInfo["iGuildLevel"] != guildInfo2["guildLevel"]:
                log.write("guild level is not match in response: " + str(responseGuildInfo["iGuildLevel"]) + " and database: " + guildInfo2["guildLevel"])
                isPass = False
            if responseGuildInfo["iLogo"] != self.GUILD_TEST_LOGO:
                log.write("guild logo is error in response: " + str(responseGuildInfo["iLogo"]))
                isPass = False
            if guildInfo2["logo"] != self.GUILD_TEST_LOGO:
                log.write("guild logo is error in database: " + str(guildInfo2["logo"]))
                isPass = False
            if responseGuildInfo["iLogoBg"] != self.GUILD_TEST_LOGO_BG:
                log.write("guild iLogoBg is error in response: " + str(responseGuildInfo["iLogoBg"]))
                isPass = False
            if guildInfo2["logoBg"] != self.GUILD_TEST_LOGO_BG:
                log.write("guild logobg is error in database: " + str(guildInfo2["logoBg"]))
                isPass = False
            if responseGuildInfo["sGuildName"] != self.GUILD_TEST_NAME:
                log.write("guild logobg is error in response: " + responseGuildInfo["sGuildName"])
                isPass = False
            if guildInfo2["guildName"] != self.GUILD_TEST_NAME:
                log.write("guild logo is error in database: " + guildInfo2["guildName"])
                isPass = False
            if responseGuildInfo["sGuildIntro"] != self.GUILD_TEST_INTRO:
                log.write("guild logo is error in response: " + responseGuildInfo["sGuildIntro"])
                isPass = False
            if guildInfo2["guildIntro"] != self.GUILD_TEST_INTRO:
                log.write("guild logo is error in database: " + guildInfo2["guildIntro"])
                isPass = False
            responseGuildEmployeeInfo = communication.toJson(result)[1][2]
            if responseGuildEmployeeInfo["iGuildId"] != guildId:
                log.write("guild employee's guild id is error in response: " + str(responseGuildEmployeeInfo["iGuildId"]))
                isPass = False
            if responseGuildEmployeeInfo["sEmployeeId"] != config.USER_ID:
                log.write("guild employee's user id is error in response: " + responseGuildEmployeeInfo["sEmployeeId"])
                isPass = False
            if responseGuildEmployeeInfo["iRole"] != gameConfig.GAME_GUILD_ROLE_MASTER:
                log.write("guild employee's role id is error in response: " + str(responseGuildEmployeeInfo["iRole"]))
                isPass = False
            if responseGuildEmployeeInfo["iCalcLevel"] != common.getLevel():
                log.write("guild employee's level is error in response: " + str(responseGuildEmployeeInfo["iCalcLevel"]))
                isPass = False
            if responseGuildEmployeeInfo["iContribution"] != common.getHistoryContribution():
                log.write("guild employee's contribution is error in response: " + str(responseGuildEmployeeInfo["iContribution"]))
                isPass = False
            if responseGuildEmployeeInfo["iBattleCount"] != 0:
                log.write("guild employee's battle count is error in response: " + str(responseGuildEmployeeInfo["iBattleCount"]))
                isPass = False
            if len(employeeList2) != 1:
                log.write("guild employee count is error in database: " + str(len(employeeList2)))
                isPass = False
            else:
                if employeeList2[0]["employeeId"] != config.USER_ID:
                    log.write("guild employee's user id is error in database: " + str(employeeList2["employeeId"]))
                    isPass = False
                if employeeList2[0]["role"] != gameConfig.GAME_GUILD_ROLE_MASTER:
                    log.write("guild employee's role id is error in database: " + str(employeeList2["role"]))
                    isPass = False
                if employeeList2[0]["contribution"] != common.getHistoryContribution():
                    log.write("guild employee's contribution is error in database: " + str(employeeList2["contribution"]))
                    isPass = False
                if responseGuildEmployeeInfo["iJoinTime"] != employeeList2[0]["joinTime"]:
                    log.write("guild employee's join time is not match in response: " + str(responseGuildEmployeeInfo["iJoinTime"]) + " and database: " + employeeList2["joinTime"])
                    isPass = False
                if employeeList2[0]["battleCount"] != 0:
                    log.write("guild employee's contribution is error in database: " + str(employeeList2["battleCount"]))
                    isPass = False
            responseGuildTechnology = communication.toJson(result)[1][3]
            for guildTech in responseGuildTechnology:
                if guildTech["iGuildId"] != guildInfo2["guildId"] or guildTech["iExp"] != 0 or not(guildTech["iTechnologyId"] in gameConfig.GAME_GUILD_TECHNOLOGY_LIST):
                    log.write("guild technology info is error in response: " + str(guildTech))
                    isPass = False
        if isPass:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    # create guild with not enough level
    def noLevelAddGuild(self, level=random.randint(1, gameConfig.GAME_GUILD_REQUIRE_LEVEL - 1)):
        silverCoin = gameConfig.GAME_GUILD_REQUIRE_SILVER
        log.writeResultLog("\tcreate guild with level: " + str(level) + ", silver coin: " + str(silverCoin))
        addGuild.init(level, silverCoin, self.GUILD_TEST_NAME)
        silver1, level1, guildInfo1, employeeList1, result, silver2, level2, guildInfo2, employeeList2 = self.addGuild()
        if result == self.REQUEST_FAILED_NOT_ENOUG_LEVEL and silver1 == silver2 and guildInfo2["guildId"] == 0:
            log.writeResultLog("\t\t Passed, not created")
        else:
            log.writeResultLog("\t\t Failed")
        isPass = True
        if result != self.REQUEST_FAILED_NOT_ENOUG_LEVEL:
            log.write("response error: " + str(result))
            isPass = False
        if silver1 != silver2:
            log.write("silver coin not match before: " + str(silver1) + ", after: " + str(silver2))
            isPass = False
        if guildInfo2["guildId"] != 0:
            log.write("guild id error: " + str(guildInfo2["guildId"]))
            isPass = False
        if isPass:
            log.writeResultLog("\t\t Passed, not created")
        else:
            log.writeResultLog("\t\t Failed")

    # create guild with not enough silver
    def noSilvercoinAddGuild(self, silverCoin=random.randint(1, gameConfig.GAME_GUILD_REQUIRE_SILVER - 1)):
        level = gameConfig.GAME_GUILD_REQUIRE_LEVEL
        log.writeResultLog("\tcreate guild with level: " + str(level) + ", silver coin: " + str(silverCoin))
        addGuild.init(level, silverCoin, self.GUILD_TEST_NAME)
        silver1, level1, guildInfo1, employeeList1, result, silver2, level2, guildInfo2, employeeList2 = self.addGuild()
        if result == self.REQUEST_FAILED_NOT_ENOUG_SILVER and silver1 == silver2 and guildInfo2["guildId"] == 0:
            log.writeResultLog("\t\t Passed, not created")
        else:
            log.writeResultLog("\t\t Failed")

    # create guild with in other guild
    def haveGuildAddGuild(self):
        level = gameConfig.GAME_GUILD_REQUIRE_LEVEL
        silverCoin = gameConfig.GAME_GUILD_REQUIRE_SILVER
        log.writeResultLog("\tcreate guild with in other guild")
        addGuild.init(level, silverCoin, self.GUILD_TEST_NAME)
        common.setUserGuild(random.choice(common.getGuildList()))
        silver1, level1, guildInfo1, employeeList1, result, silver2, level2, guildInfo2, employeeList2 = self.addGuild()
        if result == self.REQUEST_FAILED_HAVE_GUILD and silver1 == silver2 and guildInfo1["guildId"] == guildInfo2["guildId"]:
            log.writeResultLog("\t\t Passed, not created")
        else:
            log.writeResultLog("\t\t Failed")
        
class LeaveGuild():
    REQUEST_SUCCEED = '[1,[1,$guildReloadTime]]'
    REQUEST_FAILED_NOT_MEMBER = '[1,[-1]]'
    REQUEST_FAILED_IS_GUILD_MASTER = '[1,[-2]]'
    
    def __init__(self):
        log.writeResultLog("start leave testing")
    
    def leaveGuild(self, guildId):
        guildInfo1, employeeList1 = leaveGuild.getStatus(guildId)
        log.writeBeforeStatus([{"guild info":guildInfo1}, {"employee list":employeeList1}])
        result = leaveGuild.sendPackage(guildId)
        guildInfo2, employeeList2 = leaveGuild.getStatus(guildId)
        log.writeAfterStatus([{"guild info":guildInfo1}, {"employee list":employeeList1}])
        return guildInfo1, employeeList1, result, guildInfo2, employeeList2

    def normalLeaveGuild(self, role=random.choice((gameConfig.GAME_GUILD_ROLE_MEMBER, gameConfig.GAME_GUILD_ROLE_ELITE, gameConfig.GAME_GUILD_ROLE_SENATOR)), guildId=random.choice(common.getGuildList())):
        log.writeResultLog("\tleave guild with role: " + str(role) + " in guild: " + str(guildId))
        leaveGuild.init(guildId, role)
        guildInfo1, employeeList1, result, guildInfo2, employeeList2 = self.leaveGuild(guildId)
        isPass = True
        result = communication.toJson(result)
        if result[1][0] != 1:
            log.write("result status in response error: " + str(result))
            isPass = False
        if not(config.USER_ID in employeeList1):
            log.write("user not in this guild employee list before leave guild: " + str(employeeList1))
            isPass = False
        if guildInfo1["memberCount"] - guildInfo2["memberCount"] != 1:
            log.write("guild member count not reduce: from " + str(guildInfo1["memberCount"]) + " to " + str(guildInfo2["memberCount"]))
            isPass = False
        if config.USER_ID in employeeList2:
            log.write("user still in this guild employee list: " + str(employeeList2))
            isPass = False
        if isPass:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def notMemberLeaveGuild(self, role=random.choice((gameConfig.GAME_GUILD_ROLE_MEMBER, gameConfig.GAME_GUILD_ROLE_ELITE, gameConfig.GAME_GUILD_ROLE_SENATOR)), guildId=random.choice(common.getGuildList()), otherGuildId=random.choice(common.getGuildList())):
        for i in range(3):
            if otherGuildId != guildId:
                break
            if i >= 2:
                log.write("can not random a different guild in all guilds: " + str)
                otherGuildId = 0
                break
            otherGuildId = random.choice(common.getGuildList())
        log.writeResultLog("\tleave other guild with role: " + str(role) + " in guild: " + str(guildId))
        leaveGuild.init(guildId, role)
        guildInfo1, employeeList1, result, guildInfo2, employeeList2 = self.leaveGuild(otherGuildId)
        isPass = True
        if result != self.REQUEST_FAILED_NOT_MEMBER:
            log.write("result status in response error: " + str(result))
            isPass = False
        if guildInfo1["memberCount"] != guildInfo2["memberCount"]:
            log.write("guild member count error from " + str(guildInfo1["memberCount"]) + " to " + str(guildInfo2["memberCount"]))
            isPass = False
        if len(employeeList1) != len(employeeList2):
            log.write("guild employee count error from " + str(employeeList1) + " to " + str(employeeList2))
            isPass = False
        if isPass:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def noGuildLeaveGuild(self, role=random.choice((gameConfig.GAME_GUILD_ROLE_MEMBER, gameConfig.GAME_GUILD_ROLE_ELITE, gameConfig.GAME_GUILD_ROLE_SENATOR)), otherGuildId=random.choice(common.getGuildList())):
        log.writeResultLog("\tleave other guild with role: " + str(role) + " in guild: 0")
        leaveGuild.init(0, role)
        guildInfo1, employeeList1, result, guildInfo2, employeeList2 = self.leaveGuild(otherGuildId)
        isPass = True
        if result != self.REQUEST_FAILED_NOT_MEMBER:
            log.write("result status in response error: " + str(result))
            isPass = False
        if guildInfo1["memberCount"] != guildInfo2["memberCount"]:
            log.write("guild member count error from " + str(guildInfo1["memberCount"]) + " to " + str(guildInfo2["memberCount"]))
            isPass = False
        if len(employeeList1) != len(employeeList2):
            log.write("guild employee count error from " + str(employeeList1) + " to " + str(employeeList2))
            isPass = False
        if isPass:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def guildMasterLeaveGuild(self, role=gameConfig.GAME_GUILD_ROLE_MASTER, guildId=random.choice(common.getGuildList())):
        log.writeResultLog("\tleave guild with role: " + str(role) + " in guild: " + str(guildId))
        leaveGuild.init(guildId, role)
        guildInfo1, employeeList1, result, guildInfo2, employeeList2 = self.leaveGuild(guildId)
        isPass = True
        result = communication.toJson(result)
        if result[1][0] != 1:
            log.write("result status in response error: " + str(result))
            isPass = False
        if not(config.USER_ID in employeeList1):
            log.write("user not in this guild employee list before leave guild: " + str(employeeList1))
            isPass = False
        if guildInfo1["memberCount"] - guildInfo2["memberCount"] != 1:
            log.write("guild member count not reduce: from " + str(guildInfo1["memberCount"]) + " to " + str(guildInfo2["memberCount"]))
            isPass = False
        if config.USER_ID in employeeList2:
            log.write("user still in this guild employee list: " + str(employeeList2))
            isPass = False
        if isPass:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")      

#a = AddGuild()
#a.normalAddGuild()
#a.noLevelAddGuild()
#a.noSilvercoinAddGuild()
#a.haveGuildAddGuild()

#l = LeaveGuild()
#l.normalLeaveGuild()
#l.notMemberLeaveGuild()
#l.noGuildLeaveGuild()
