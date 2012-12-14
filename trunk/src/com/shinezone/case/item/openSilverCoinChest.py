from com.shinezone.case.common import communication, common, gameConfig

# ["Package","openSilverCoinBox","[$itemid]"]
SILVER_CHEST = 9
itemList = []
for item in gameConfig.GAME_ITEM_LIST:
    if item["itemType"] == SILVER_CHEST:
        itemList.append(item)
# [{'itemId': 610009, 'itemReward': ['5', '50', '500']}, {'itemId': 610010, 'itemReward': ['20', '200', '2000']}, {'itemId': 610011, 'itemReward': ['50', '500', '5000']}, {'itemId': 610012, 'itemReward': ['100', '1000', '10000']}, {'itemId': 610013, 'itemReward': ['150', '1500', '15000']}, {'itemId': 610014, 'itemReward': ['200', '2000', '20000']}, {'itemId': 610015, 'itemReward': ['300', '3000', '30000']}, {'itemId': 610016, 'itemReward': ['400', '4000', '40000']}, {'itemId': 610017, 'itemReward': ['500', '5000', '50000']}]

def sendPackage(itemId, count):
    data = '["Package","openSilverCoinBox","[%d,%d]"]' % (itemId, count)
    return communication.request(data)

def init(itemId, count=1):
    common.setItemCount(itemId, count)
    common.clearCache()

def getStatus(itemId):
    itemCount = common.getItemCount(itemId)
    silverCoin = common.getSliverCoin()
    return itemCount, silverCoin

def getRandomRange(itemReward):
    return int(itemReward[0]), int(itemReward[1]), int(itemReward[2]) 
