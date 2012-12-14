from com.shinezone.case.common import communication, common

# ["Package","unlockPropGrid",[]]
GOLD_CPIN_COST_LESS_THAN_LIMIT_SLOTS = 10
GOLD_CPIN_COST_MORE_THAN_LIMIT_SLOTS = 50
BAG_SLOTS_COST_LIMIT = 45
EXPAND_ADD_SLOT_COUNTS = 5


def sendPackage():
    data = '["Package","unlockPropGrid",[]]'
    return communication.request(data)

def init(goldCoin, bagSlotCount):
    common.setGoldCoin(goldCoin)
    common.setBagSlotCount(bagSlotCount)
    common.clearCache()

def getStatus():
    goldCoin = common.getGoldCoin()
    bagSlotCount = common.getBagSlotCount()
    return goldCoin, bagSlotCount
    
