import random
from com.shinezone.case.item import useEnergyProp, openSilverCoinChest, equipMerge, openGoldCoinChest
from com.shinezone.case.common import communication, config, log, gameConfig

# energy prop
class EnergyProp():
    REQUEST_SUCCEED = '[1,[1]]'
    # not enough item
    REQUEST_FAILED_NOT_ENOUG_ITEM = '[1,[-1004]]'
    # item count incorrect
    REQUEST_FAILED_INCORRECT_ITEM_COUNT = '[1,-4003]'
    # item id incorrect
    REQUEST_FAILED_INCORRECT_ITEM_ID = '[1,[-1]]'
       
    def __init__(self):
        log.writeResultLog("start use energy prop")
    
    def useItem(self, itemId, count):
        #get status before test
        itemCount1 , energy1 = useEnergyProp.getStatus(itemId)
        log.writeBeforeStatus([{"item id":itemId}, {"item count":itemCount1}, {"energy":energy1}])
        response = useEnergyProp.sendPackage(itemId, count)
        log.write("use item:\t\titem id: " + str(itemId) + ", item count: " + str(count))
        #get status after test
        itemCount2 , energy2 = useEnergyProp.getStatus(itemId)
        log.writeAfterStatus([{"item id":itemId}, {"item count":itemCount2}, {"energy":energy2}])
        return itemCount1, energy1, response, itemCount2, energy2
    
    def itemEffect(self, count=random.randint(1, 10)):
        log.writeResultLog("\tCheck item effect, count: " + str(count))
        for item in useEnergyProp.itemList:
            itemId = item["itemId"]
            useEnergyProp.init(itemId, count)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            energy1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            energy2 = result[4]
            if itemCount1 < count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if response == self.REQUEST_SUCCEED and (energy2 - energy1) == count * item["itemReward"] and (itemCount1 - itemCount2) == count:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")

    # use item count more than in your storage
    def useMoreThanHave(self, count=random.randint(2, 10)):
        log.writeResultLog("\tUse item count more than have")
        initItemCount = 1
        # each item
        for item in useEnergyProp.itemList:
            itemId = item["itemId"]
            useEnergyProp.init(itemId, initItemCount)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            energy1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            energy2 = result[4]
            if itemCount1 >= count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if response != self.REQUEST_SUCCEED and itemCount2 == itemCount1 and energy2 == energy1:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")

    # use item count less than zero
    def useNegativeNumber(self, count= -1):
        log.writeResultLog("\tUse item count less than zero")
        initItemCount = 1
        # each item
        for item in useEnergyProp.itemList:
            itemId = item["itemId"]
            useEnergyProp.init(itemId, initItemCount)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            energy1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            energy2 = result[4]
            if response == self.REQUEST_FAILED_INCORRECT_ITEM_COUNT and itemCount2 == itemCount1 and energy2 == energy1:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")

    # use other item
    def useIncorrectItemId(self, itemId=0, count=1):
        log.writeResultLog("\tUse incorrect item id")
        item = random.choice(gameConfig.GAME_ITEM_LIST)
        while item["itemType"] == useEnergyProp.ENERGY_PROP:
            item = random.choice(gameConfig.GAME_ITEM_LIST)
        itemId = item["itemId"]
        useEnergyProp.init(itemId, count)
        result = self.useItem(itemId, count)
        itemCount1 = result[0]
        energy1 = result[1]
        response = result[2]
        itemCount2 = result[3]
        energy2 = result[4]
        if itemCount1 < count:
            log.writeResultLog("\t\tIniterror")
            return
        if response == self.REQUEST_FAILED_INCORRECT_ITEM_ID and itemCount2 == itemCount1 or energy2 == energy1:
            log.writeResultLog("\t\tPassed")
        else:
            log.writeResultLog("\t\tFailed")
            
# silver coin box
class SilverCoinChest():
#    REQUEST_SUCCEED = '[1,[1,$silver]]'
    REQUEST_SUCCEED = '[1,[1,%d]]'
    # not enough item
    REQUEST_FAILED_NOT_ENOUG_ITEM = '[1,[-1004]]'
    # item count incorrect
    REQUEST_FAILED_INCORRECT_ITEM_COUNT = '[1, [-4003]]'
    # item id incorrect
    REQUEST_FAILED_INCORRECT_ITEM_ID = '[1,[-1]]'
    
    def __init__(self):
        log.writeResultLog("start open silver coin chest")
    
    def useItem(self, itemId, count):
        #get status before test
        itemCount1, silverCoint1 = openSilverCoinChest.getStatus(itemId)
        log.writeBeforeStatus([{"item id":itemId}, {"item count":itemCount1}, {"silver coin":silverCoint1}])
        #send package
        response = openSilverCoinChest.sendPackage(itemId, count)
        log.write("use item:\t\titem id: " + str(itemId) + ", item count: " + str(count))
        #get status after test
        itemCount2, silverCoin2 = openSilverCoinChest.getStatus(itemId)
        log.writeAfterStatus([{"item id":itemId}, {"item count":itemCount2}, {"silver coin":silverCoin2}])
        return itemCount1, silverCoint1, response, itemCount2, silverCoin2
    
    def itemEffect(self, count=random.randint(1, 10)):
        for item in openSilverCoinChest.itemList:
            itemId = item["itemId"]
            openSilverCoinChest.init(itemId, count)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            silverCoint1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            silverCoin2 = result[4]
            if itemCount1 < count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if response == (self.REQUEST_SUCCEED % (silverCoin2 - silverCoint1)) and itemCount1 - itemCount2 == count:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")
    
    # use item count more than in your storage
    def useMoreThanHave(self, count=random.randint(2, 10)):
        log.writeResultLog("\tUse item count more than have")
        initItemCount = 1
        # each item
        for item in openSilverCoinChest.itemList:
            itemId = item["itemId"]
            openSilverCoinChest.init(itemId, initItemCount)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            silverCoint1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            silverCoin2 = result[4]
            if itemCount1 >= count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if response == self.REQUEST_FAILED_NOT_ENOUG_ITEM and itemCount1 == itemCount2 and silverCoint1 == silverCoin2:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")

    # use item count less than zero
    def useNegativeNumber(self, count= -1):
        log.writeResultLog("\tUse item count less than zero")
        initItemCount = 1
        # each item
        for item in openSilverCoinChest.itemList:
            itemId = item["itemId"]
            openSilverCoinChest.init(itemId, initItemCount)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            silverCoint1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            silverCoin2 = result[4]
            if response == self.REQUEST_FAILED_INCORRECT_ITEM_COUNT and itemCount1 == itemCount2 and silverCoint1 == silverCoin2:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                print response == self.REQUEST_FAILED_INCORRECT_ITEM_COUNT , itemCount1 == itemCount2 , silverCoint1 == silverCoin2
                log.writeResultLog("\t\t" + str(itemId) + " Failed")
    
    def useIncorrectItemId(self, itemId=0, count=1):
        log.writeResultLog("\tUse incorrect item id")
        item = random.choice(gameConfig.GAME_ITEM_LIST)
        while item["itemType"] == openSilverCoinChest.SILVER_CHEST:
            item = random.choice(gameConfig.GAME_ITEM_LIST)
        itemId = item["itemId"]
        openSilverCoinChest.init(itemId, count)
        result = self.useItem(itemId, count)
        itemCount1 = result[0]
        silverCoint1 = result[1]
        response = result[2]
        itemCount2 = result[3]
        silverCoin2 = result[4]
        if itemCount1 < count:
            log.writeResultLog("\t\t" + str(itemId) + " Init error")
            return
        if response == self.REQUEST_FAILED_INCORRECT_ITEM_ID and itemCount1 == itemCount2 and silverCoint1 == silverCoin2:
            log.writeResultLog("\t\t" + str(itemId) + " Passed")
        else:
            log.writeResultLog("\t\t" + str(itemId) + " Failed")
    
    def checkEffectRange(self):
        log.writeResultLog("\tCheck item effect range")
        count = config.RANGE_TEST_COUNT
        # random one item
        item = random.choice(openSilverCoinChest.itemList)
        itemId = item["itemId"]
        openSilverCoinChest.init(itemId, count)
        for number in range(count):
            result = self.useItem(itemId, 1)
            silverCoint1 = result[1]
            silverCoin2 = result[4]
            itemReward = openSilverCoinChest.getRandomRange(item["itemReward"])
            if not(itemReward[0] <= (silverCoin2 - silverCoint1) <= itemReward[1] or (silverCoin2 - silverCoint1) == itemReward[2]):
                log.writeResultLog("\t\t" + str(itemId) + " Failed")
                break
        if number == count - 1:
            log.writeResultLog("\t\t" + str(itemId) + " Passed")
    
    def checkEffectRate(self):
        count = config.RANGE_TEST_COUNT
        log.writeResultLog("\tCheck item effect rate")
        # random one item
        item = random.choice(openSilverCoinChest.itemList) 
        itemId = item["itemId"]
        openSilverCoinChest.init(itemId, count)
        range1 = 0
        range2 = 0
        for number in range(count):
            result = self.useItem(itemId, 1)
            silverCoint1 = result[1]
            silverCoin2 = result[4]
            itemReward = openSilverCoinChest.getRandomRange(item["itemReward"])
            if (silverCoin2 - silverCoint1) == itemReward[2]:
                range2 += 1
            elif itemReward[0] <= (silverCoin2 - silverCoint1) <= itemReward[1]:
                range1 += 1
        if number == count - 1 and range1 + range2 == count:
            log.writeResultLog("\t\t" + str(itemId) + " range 1: " + str(range1) + ", range 2: " + str(range2))
        else:
            log.writeResultLog("\t\t" + str(itemId) + " Failed")

class GoldCoinChest():
#    REQUEST_SUCCEED = '[1,[1,$gold]]'
    REQUEST_SUCCEED = '[1,[1,%d]]'
    # not enough item
    REQUEST_FAILED_NOT_ENOUG_ITEM = '[1,[-1004]]'
    # item count incorrect
    REQUEST_FAILED_INCORRECT_ITEM_COUNT = '[1,[-4003]]'
    # item id incorrect
    REQUEST_FAILED_INCORRECT_ITEM_ID = '[1,[-1]]'
    
    def __init__(self):
        log.writeResultLog("start open gold coin chest")
    
    def useItem(self, itemId, count):
        #get status before test
        itemCount1, goldCoin1 = openGoldCoinChest.getStatus(itemId)
        log.writeBeforeStatus([{"item id":itemId}, {"item count":itemCount1}, {"gold coin":goldCoin1}])
        #send package
        response = openGoldCoinChest.sendPackage(itemId, count)
        log.write("use item:\t\titem id: " + str(itemId) + ", item count: " + str(count))
        #get status after test
        itemCount2, goldCoin2 = openGoldCoinChest.getStatus(itemId)
        log.writeAfterStatus([{"item id":itemId}, {"item count":itemCount2}, {"gold coin":goldCoin2}])
        return itemCount1, goldCoin1, response, itemCount2, goldCoin2
    
    def itemEffect(self, count=random.randint(1, 10)):
        log.writeResultLog("\tCheck item effect, count:" + str(count))
        for item in openGoldCoinChest.itemList:
            itemId = item["itemId"]
            openGoldCoinChest.init(itemId, count)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            goldCoin1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            goldCoin2 = result[4]
            if itemCount1 < count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if response == (self.REQUEST_SUCCEED % (goldCoin2 - goldCoin1)) and itemCount1 - itemCount2 == count:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")
    
    # use item count more than in your storage
    def useMoreThanHave(self, count=random.randint(2, 10)):
        log.writeResultLog("\tUse item count more than have")
        initItemCount = 1
        # each item
        for item in openGoldCoinChest.itemList:
            itemId = item["itemId"]
            openGoldCoinChest.init(itemId, initItemCount)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            goldCoin1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            goldCoin2 = result[4]
            if itemCount1 >= count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if response == self.REQUEST_FAILED_NOT_ENOUG_ITEM and itemCount1 == itemCount2 and goldCoin1 == goldCoin2:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")

    # use item count less than zero
    def useNegativeNumber(self, count= -1):
        log.writeResultLog("\tUse item count less than zero")
        initItemCount = 1
        # each item
        for item in openGoldCoinChest.itemList:
            itemId = item["itemId"]
            openGoldCoinChest.init(itemId, initItemCount)
            result = self.useItem(itemId, count)
            itemCount1 = result[0]
            goldCoin1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            goldCoin2 = result[4]
            if response == self.REQUEST_FAILED_INCORRECT_ITEM_COUNT and itemCount1 == itemCount2 and goldCoin1 == goldCoin2:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")
    
    def useIncorrectItemId(self, itemId=0, count=1):
        log.writeResultLog("\tUse incorrect item id")
        item = random.choice(gameConfig.GAME_ITEM_LIST)
        while item["itemType"] == openGoldCoinChest.GOLD_CHEST:
            item = random.choice(gameConfig.GAME_ITEM_LIST)
        itemId = item["itemId"]
        openGoldCoinChest.init(itemId, count)
        result = self.useItem(itemId, count)
        itemCount1 = result[0]
        goldCoin1 = result[1]
        response = result[2]
        itemCount2 = result[3]
        goldCoin2 = result[4]
        if itemCount1 < count:
            log.writeResultLog("\t\t" + str(itemId) + " Init error")
            return
        if response == self.REQUEST_FAILED_INCORRECT_ITEM_ID and itemCount1 == itemCount2 and goldCoin1 == goldCoin2:
            log.writeResultLog("\t\t" + str(itemId) + " Passed")
        else:
            log.writeResultLog("\t\t" + str(itemId) + " Failed")
    
    def checkEffectRange(self):
        log.writeResultLog("\tCheck item effect range")
        count = config.RANGE_TEST_COUNT
        # random one item
        for item in openGoldCoinChest.itemList:
            itemId = item["itemId"]
            if itemId == openGoldCoinChest.GOLD_PACK_ITEM_ID:
                continue
            openGoldCoinChest.init(itemId, count)
            for number in range(count):
                result = self.useItem(itemId, 1)
                goldCoin1 = result[1]
                goldCoin2 = result[4]
                itemReward = openGoldCoinChest.getRandomRange(item["itemReward"])
                if not(itemReward[0] <= (goldCoin2 - goldCoin1) <= itemReward[1] or (goldCoin2 - goldCoin1) == itemReward[2]):
                    log.writeResultLog("\t\t" + str(itemId) + " Failed")
                    break
            if number == count - 1:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
    
    def checkEffectRate(self):
        count = config.RANGE_TEST_COUNT
        log.writeResultLog("\tCheck item effect rate")
        # random one item
        for item in openGoldCoinChest.itemList:
            itemId = item["itemId"]
            if itemId == openGoldCoinChest.GOLD_PACK_ITEM_ID:
                continue
            openGoldCoinChest.init(itemId, count)
            range1 = 0; range2 = 0
            for number in range(count):
                result = self.useItem(itemId, 1)
                goldCoin1 = result[1]
                goldCoin2 = result[4]
                itemReward = openGoldCoinChest.getRandomRange(item["itemReward"])
                if (goldCoin2 - goldCoin1) == itemReward[2]:
                    range2 += 1
                elif itemReward[0] <= (goldCoin2 - goldCoin1) <= itemReward[1]:
                    range1 += 1
            if number == count - 1 and range1 + range2 == count:
                log.writeResultLog("\t\t" + str(itemId) + " range 1: " + str(range1) + ", range 2: " + str(range2))
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")

class MergeEquip():
    REQUEST_SUCCEED = '[1,[1,$itemInfo,$equipInfo]]'
    # $itemInfo = {"sUid":$uid,"iItemId":$itemId,"iCount":$itemCount}
    # $equipInfo = {"sUid":$uid,"iHeroId":$heroId,"iEquipId":$equipId,"iStrengthenLevel":$strengthenLevel,"iGrooveCount":$grooveCount,"sStones":$stoneInfo,"iUEid":$equipUid}
    # not enough item
    REQUEST_FAILED_NOT_ENOUG_ITEM = '[1,[-1]]'
    # item can't merge
    REQUEST_FAILED_INCORRECT_ITEM_ID = '[1,[-2]]'
    
    def __init__(self):
        log.writeResultLog("start merge equip")
    
    def useItem(self, itemId, equipId):
        #get status before test
        itemCount1, equipInfo1 = equipMerge.getStatus(itemId, equipId)
        log.writeBeforeStatus([{"item id":itemId}, {"item count":itemCount1}])
        #send package
        response = equipMerge.sendPackage(itemId)
        log.write("use item:\t\titem id: " + str(itemId))
        #get status after test
        itemCount2, equipInfo2 = equipMerge.getStatus(itemId, equipId)
        log.writeAfterStatus([{"item id":itemId}, {"item count":itemCount2}, {"equipInfo":equipInfo2}])
        return itemCount1, equipInfo1, response, itemCount2, equipInfo2

    def checkConfig(self):
        pass

    def itemEffect(self):
        log.writeResultLog("\tCheck equip id")
        for item in equipMerge.itemList:
            itemId = item["itemId"]
            count = item["count"]
            equipId = item["equipId"]
            equipMerge.init(itemId, count, equipId)
            result = self.useItem(itemId, equipId)
            itemCount1 = result[0]
            response = result[2]
            itemCount2 = result[3]
            equipInfo2 = result[4]
            responseItemInfo = communication.toJson(response)[1][1]
            responseEquipInfo = communication.toJson(response)[1][2]
            if itemCount1 < count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if responseItemInfo["iCount"] != itemCount2 or count != itemCount1 - itemCount2 or responseItemInfo["iItemId"] != itemId:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")
                continue
            isFailed = True
            for equip in equipInfo2:
                if equip["equipId"] == equipId and responseEquipInfo["iEquipId"] == equipId and equip["heroId"] == 0 and responseEquipInfo["iHeroId"] == 0 \
                 and equip["strengthenLevel"] == 0 and responseEquipInfo["iStrengthenLevel"] == 0 and equip["UID"] == responseEquipInfo["iUEid"] \
                 and responseEquipInfo["sStones"] == "":
                    log.writeResultLog("\t\t" + str(itemId) + " Passed")
                    isFailed = False
                    break
            if isFailed:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")

    def useLessThanWanted(self):
        log.writeResultLog("\tCheck count less than wanted")
        initShortageCount = 1
        for item in equipMerge.itemList:
            itemId = item["itemId"]
            count = item["count"]
            equipId = item["equipId"]
            equipMerge.init(itemId, count - initShortageCount, equipId)
            result = self.useItem(itemId, equipId)
            itemCount1 = result[0]
            equipInfo1 = result[1]
            response = result[2]
            itemCount2 = result[3]
            equipInfo2 = result[4]
            if itemCount1 >= count:
                log.writeResultLog("\t\t" + str(itemId) + " Init error")
                continue
            if response == self.REQUEST_FAILED_NOT_ENOUG_ITEM and len(equipInfo1) == len(equipInfo2) and itemCount1 == itemCount2:
                log.writeResultLog("\t\t" + str(itemId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(itemId) + " Failed")
    
    def useIncorrectItemId(self):
        log.writeResultLog("\tUse incorrect item id")
        initItemCount = 99
        item = random.choice(gameConfig.GAME_ITEM_LIST)
        while item["itemType"] == equipMerge.EQUIP_FRAGMENT:
            item = random.choice(gameConfig.GAME_ITEM_LIST)
        itemId = item["itemId"]        
        equipMerge.init(itemId, initItemCount)
        result = self.useItem(itemId, itemId)
        itemCount1 = result[0]
        equipInfo1 = result[1]
        response = result[2]
        itemCount2 = result[3]
        equipInfo2 = result[4]
        if response == self.REQUEST_FAILED_INCORRECT_ITEM_ID and len(equipInfo1) == len(equipInfo2) and itemCount1 == itemCount2:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")


#e = EnergyProp()
#e.itemEffect(1)
#e.itemEffect(5)
#e.useMoreThanHave()
#e.useNegativeNumber()
#e.useIncorrectItemId()
#
s = SilverCoinChest()
#s.itemEffect(1)
s.itemEffect(5)
#s.useMoreThanHave()
#s.useNegativeNumber()
#s.useIncorrectItemId()
#s.checkEffectRange()
#s.checkEffectRate()
#
#s = GoldCoinChest()
#s.itemEffect(1)
#s.itemEffect(2)
#s.useMoreThanHave()
#s.useNegativeNumber()
#s.useIncorrectItemId()
#s.checkEffectRange()
#s.checkEffectRate()
#
#m = MergeEquip()
#m.itemEffect()
#m.useLessThanWanted()
#m.useIncorrectItemId()
