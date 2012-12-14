from com.shinezone.case.common import communication, common, gameConfig

# ["Package","useEnergyProp","[$itemid,$count]"]
ENERGY_PROP = 7
itemList = []
for item in gameConfig.GAME_ITEM_LIST:
    if item["itemType"] == ENERGY_PROP:
        item["itemId"] = int(item["itemId"])
        item["itemReward"] = int(item["itemReward"])
        itemList.append(item)
# itemList = [{'itemId': 610005, 'itemReward': 1}, {'itemId': 610006, 'itemReward': 3}, {'itemId': 610007, 'itemReward': 5}, {'itemId': 610008, 'itemReward': 10}]

def sendPackage(itemId, count):
    data = '["Package","useEnergyProp",[%d,%d]]' % (itemId, count)
    return communication.request(data)

def init(itemId, count=1):
    common.setItemCount(itemId, count)
    common.clearCache()

def getStatus(itemId):
    itemCount = common.getItemCount(itemId)
    energy = common.getEnergy()
    return itemCount, energy