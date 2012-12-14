from com.shinezone.case.common import communication, common

# ["Farm","planting",[$farmId, $seedId]]

def sendPackage(farmId, seedId):
    data = '["Farm","planting",[%d, %d]]' % (farmId, seedId)
    return communication.request(data)

def init(level, seedId, seedCount, farmId=0):
    common.setLevel(level)
    common.setYearVip()
    common.setFarm(farmId)
    common.setItemCount(seedId, seedCount)
    common.clearCache()

def getStatus(farmId=0):
    farmList = common.getFarm(farmId)
    if farmList == None:
        return None
    if farmId == 0:
        farmInfo = []
        for farm in farmList:
            fa = {}
            fa["farmId"] = int(farm[1])
            fa["seedId"] = int(farm[2])
            fa["time"] = int(farm[3])
            fa["friendHelp"] = str(farm[4])
            farmInfo.append(fa)
    else:
        farmInfo = {}
        farmInfo["farmId"] = int(farmList[1])
        farmInfo["seedId"] = int(farmList[2])
        farmInfo["time"] = int(farmList[3])
        farmInfo["friendHelp"] = str(farmList[4])
    return farmInfo
    
def plant(farmId, seedId):
    common.setFarm(farmId, seedId, common.getServerTime())
