from com.shinezone.case.common import communication, common

# ["Guild","addGuild",[$logo, $logoBG, $guildName, $guildIntroduction]]

def sendPackage(logo, logoBg, guildName, guildIntroduction):
    data = '["Guild","addGuild",[%d,%d,"%s","%s"]]' % (logo, logoBg, guildName, guildIntroduction)
    return communication.request(data)

def init(level=15, silver=10000, guildName="Test Guild"):
    common.setLevel(level)
    common.setSliverCoin(silver)
    guildId = common.getUserGuild()
    if guildId != 0:
        common.delGuild(guildId)
    guildId = common.getGuildIdByGuildName(guildName)
    if guildId != None:
        common.delGuild(guildId)
    common.clearCache()

def getStatus():
    silver = common.getSliverCoin()
    level = common.getLevel()
    guildId = common.getUserGuild()
    if guildId != 0:
        guild = common.getGuildInfo(guildId)
        guildInfo = {}
        guildInfo["guildId"] = int(guild[0])
        guildInfo["guildMasterId"] = str(guild[1])
        guildInfo["createTime"] = int(guild[2])
        guildInfo["mvpId"] = str(guild[3])
        guildInfo["memberCount"] = int(guild[4])
        guildInfo["fightCount"] = int(guild[5])
        guildInfo["winCount"] = int(guild[6])
        guildInfo["lostCount"] = int(guild[7])
        guildInfo["bindEnemy"] = int(guild[8])
        guildInfo["rank"] = int(guild[10])
        guildInfo["historyRank"] = int(guild[10])
        guildInfo["guildLevel"] = int(guild[11])
        guildInfo["logo"] = int(guild[13])
        guildInfo["logoBg"] = int(guild[12])
        guildInfo["guildName"] = str(guild[14])
        guildInfo["guildIntro"] = str(guild[15])
    else:
        guildInfo = {"guildId":guildId}
    employeeLists = common.getGuildEmployeeList(guildId)
    employeeList = []
    for employee in employeeLists:
        tmpEmployee = {}
        tmpEmployee["guildId"] = int(employee[0])
        tmpEmployee["employeeId"] = str(employee[1])
        tmpEmployee["role"] = int(employee[2])
        tmpEmployee["contribution"] = int(employee[3])
        tmpEmployee["joinTime"] = int(employee[4])
        tmpEmployee["battleCount"] = int(employee[5])
        employeeList.append(tmpEmployee)
    return silver, level, guildInfo, employeeList