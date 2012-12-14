from com.shinezone.case.common import communication, common, gameConfig

# ["Package","openSilverCoinBox","[$itemid]"]
GOLD_CHEST = 10
GOLD_PACK_ITEM_ID = 610072
GOLD_PACK_REWARD = 20

itemList = []
for item in gameConfig.GAME_ITEM_LIST:
    if item["itemType"] == GOLD_CHEST:
        if item["itemId"] == GOLD_PACK_ITEM_ID:
            item["itemReward"] = GOLD_PACK_REWARD
        itemList.append(item)

def sendPackage(itemId, count):
    data = '["Package","openGoldCoinBox",[%d,%d]]' % (itemId, count)
    return communication.request(data)

def init(itemId, count=1):
    common.setItemCount(itemId, count)
    common.clearCache()

def getStatus(itemId):
    itemCount = common.getItemCount(itemId)
    goldCoin = common.getGoldCoin()
    return itemCount, goldCoin

def getRandomRange(itemReward):
    if len(itemReward) == 3:
        return int(itemReward[0]), int(itemReward[1]), int(itemReward[2])
    else:
        return itemReward[0]