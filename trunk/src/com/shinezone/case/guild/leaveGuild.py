from com.shinezone.case.common import communication, common, gameConfig

# ["Guild","addGuild",[$logo, $logoBG, $guildName, $guildIntroduction]]

def sendPackage(guildId):
    data = '["Guild","leaveGuild",[%d]]' % (guildId)
    return communication.request(data)

def init(guildId, role=gameConfig.GAME_GUILD_ROLE_MEMBER):
    common.setUserGuild(guildId, role)
    common.setLevel(15)
    if guildId !=0:
        common.setGuildRole(role)
        memberCount = len(common.getGuildEmployeeList(guildId))
        if memberCount != common.getGuildInfo(guildId)[4]:
            common.setGuildInfo(guildId, memberCount=memberCount)
    common.clearCache()

def getStatus(guildId):
    if guildId != 0:
        guild = common.getGuildInfo(guildId)
        guildInfo = {}
        guildInfo["guildId"] = guildId
        guildInfo["memberCount"] = int(guild[4])
        employeeLists = common.getGuildEmployeeList(guildId)
        employeeList = []
        for employee in employeeLists:
            employeeList.append(str(employee[1]))
    else:
        guildInfo = {"guildId":guildId}
        employeeList = []
    return guildInfo, employeeList