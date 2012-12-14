from com.shinezone.case.common import communication, common, gameConfig

# ["Farm","harvestFarm",[$farmId]]

SILVER_SEED = 1
STONE_SEED = 2
CHEST_SEED = 3

def sendPackage(farmId):
    data = '["Farm","harvestFarm",[%d]]' % (farmId)
    return communication.request(data)

# Remaining matureTime seconds seed will mature
# matureTime > 0: have matured
#            < 0: not matured
def init(level, farmId, seedId, matureTime, isVip=True):
    common.setLevel(level)
    if isVip:
        common.setYearVip()
    else:
        common.setVip(1)
    common.setFarm(farmId, seedId, matureTime)
    common.clearCache()

def getFarmStatus(farmId):
    farm = common.getFarm(farmId)
    if farm == None:
        return None
    farmInfo = {}
    farmInfo["farmId"] = int(farm[1])
    farmInfo["seedId"] = int(farm[2])
    farmInfo["time"] = int(farm[3])
    farmInfo["friendHelp"] = str(farm[4])
    return farmInfo

def getStatus(itemId=0):
    silverCoin = common.getSliverCoin()
    itemCount = 0
    if itemId != 0: 
        itemCount = common.getItemCount(itemId)
    return silverCoin, itemCount

def getSeedProduce(seedId):
    for seed in gameConfig.GAME_SEED_LIST:
        if seed["seedId"] == seedId:
            return seed["seedType"], seed["reward"]
    return 0, 0
