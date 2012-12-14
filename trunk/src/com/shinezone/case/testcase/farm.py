import random
from com.shinezone.case.farm import planting, harvesting
from com.shinezone.case.common import common, config, log, gameConfig, communication

# planting
class FarmPlanting():
    REQUEST_SUCCEED = '[1,[1,$farmInfo,$seedInfo,$time]]'
    # $farmInfo = {"sUid":$uid,"iFarmId":$farmId,"iSeedId":$seedId,"iNtime":$maturedTime}
    # $seedInfo = {"sUid":$uid,"iSeedId":$seedId,"iCount":$itemCount}
    # not found seed info
#    REQUEST_FAILED_NO_SEED = '[1,[-3009,$seedId]]'
    REQUEST_FAILED_NO_SEED = '[1,[-3009,%d]]'
    # not found farm info
#    REQUEST_FAILED_NO_FARM = '[1,[-3010,$farmId]]'
    REQUEST_FAILED_NO_FARM = '[1,[-3010,%d]]'
    # still have plant
    REQUEST_FAILED_HAVE_PLANTED_SEED = '[1,[-1]]'
    # not enough seed
#    REQUEST_FAILED_NOT_ENOUG_ITEM = '[1,[-3009,$seedId]]'
    REQUEST_FAILED_NOT_ENOUG_ITEM = '[1,[-3009,%d]]'
    # not VIP use VIP farm
    REQUEST_FAILED_NO_CONFIG = '[1,[-3]]'
    
    
    def __init__(self):
        log.writeResultLog("start planting")
    
    def plant(self, farmId, seedId):
        #get status before test
        farmInfo1 = planting.getStatus(farmId)
        log.writeBeforeStatus([{"farm info":farmInfo1}])
        plantingTime = common.getServerTime()
        response = planting.sendPackage(farmId, seedId)
        log.write("plant seed:\t\tseed id: " + str(seedId) + ", farm id: " + str(farmId))
        #get status after test
        farmInfo2 = planting.getStatus(farmId)
        log.writeAfterStatus([{"farm info":farmInfo2}])
        return farmInfo1, response, farmInfo2, plantingTime
    
    def plantingEachSeed(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tPlanting each seed")
        roleLevel = 99
        seedCount = random.randint(1, 100)
        for seed in gameConfig.GAME_SEED_LIST:
            seedId = seed["seedId"]
            planting.init(roleLevel, seedId, seedCount, farmId)
            result = self.plant(farmId, seedId)
            farmInfo1 = result[0]
            response = communication.toJson(result[1])
            farmInfo2 = result[2]
            if farmInfo1 == None or farmInfo1["seedId"] != 0:
                log.writeResultLog("\t\t" + str(seedId) + " Init error")
                continue
            if response[1][0] == 1 and farmInfo2["seedId"] == seedId:
                log.writeResultLog("\t\t" + str(seedId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(seedId) + " Failed")
    
    def plantingEachFarm(self, seedId=random.choice(gameConfig.GAME_SEED_LIST)["seedId"]):
        log.writeResultLog("\tPlanting each Farm")
        roleLevel = 99
        seedCount = 1
        for farm in gameConfig.GAME_FARM_LIST:
            farmId = farm["farmId"]
            planting.init(roleLevel, seedId, seedCount, farmId)
            result = self.plant(farmId, seedId)
            farmInfo1 = result[0]
            response = communication.toJson(result[1])
            farmInfo2 = result[2]
            if farmInfo1 == None or farmInfo1["seedId"] != 0:
                log.writeResultLog("\t\t" + str(farmId) + " Init error")
                continue
            if response[1][0] == 1 and farmInfo2["seedId"] == seedId:
                log.writeResultLog("\t\t" + str(farmId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(farmId) + " Failed")

    def plantingLessThanHave(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tPlanting less than have")
        roleLevel = 99
        seedCount = 0
        for seed in gameConfig.GAME_SEED_LIST:
            seedId = seed["seedId"]
            planting.init(roleLevel, seedId, seedCount, farmId)
            result = self.plant(farmId, seedId)
            farmInfo1 = result[0]
            response = result[1]
            farmInfo2 = result[2]
            if farmInfo1 == None or farmInfo1["seedId"] != 0:
                log.writeResultLog("\t\t" + str(seedId) + " Init error")
                continue
            if response == (self.REQUEST_FAILED_NOT_ENOUG_ITEM % seedId) and farmInfo2["seedId"] == 0:
                log.writeResultLog("\t\t" + str(seedId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(seedId) + " Failed")
    
    def checkSeedMatureTime(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tCheck seed mature time")
        roleLevel = 99
        seedCount = 1
        for seed in gameConfig.GAME_SEED_LIST:
            seedId = seed["seedId"]
            planting.init(roleLevel, seedId, seedCount, farmId)
            result = self.plant(farmId, seedId)
            farmInfo1 = result[0]
            farmInfo2 = result[2]
            plantingTime = result[3]
            matureTime = farmInfo2["time"]
            if farmInfo1 == None or farmInfo1["seedId"] != 0:
                log.writeResultLog("\t\t" + str(seedId) + " Init error")
                continue
            if (matureTime - plantingTime) - seed["matureTime"] <= config.TEST_TIME_MAX_PERMISSIBLE_ERROR:
                log.writeResultLog("\t\t" + str(seedId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(seedId) + " Failed")

    def plantingUnlockedFarm(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"], seedId=random.choice(gameConfig.GAME_SEED_LIST)["seedId"]):
        log.writeResultLog("\tPlanting unlocked farm")
        roleLevel = 99
        seedCount = 1
        planting.init(roleLevel, seedId, seedCount, -1)
        result = self.plant(farmId, seedId)
        farmInfo1 = result[0]
        response = result[1]
        farmInfo2 = result[2]
        if farmInfo1 != None:
            log.writeResultLog("\t\tInit error")
            return
        if response == (self.REQUEST_FAILED_NO_FARM % farmId) and farmInfo2 == None:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def plantingIncorrectSeedId(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tPlanting incorrect seed id")
        roleLevel = 99
        seedCount = 1
        item = random.choice(gameConfig.GAME_ITEM_LIST)
        seedId = item["itemId"]
        planting.init(roleLevel, seedId, seedCount, farmId)
        result = self.plant(farmId, seedId)
        farmInfo1 = result[0]
        response = result[1]
        farmInfo2 = result[2]
        if farmInfo1 == None or farmInfo1["seedId"] != 0:
            log.writeResultLog("\t\tInit error")
            return
        if response == (self.REQUEST_FAILED_NO_SEED % seedId) and farmInfo2["seedId"] == 0 and farmInfo2["time"] == 0:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def plantingIncorrectFarmId(self, seedId=random.choice(gameConfig.GAME_SEED_LIST)["seedId"]):
        log.writeResultLog("\tPlanting incorrect farm id")
        roleLevel = 99
        seedCount = 1
        randomFarmId = random.randint(1, 900000)
        planting.init(roleLevel, seedId, seedCount)
        result = self.plant(randomFarmId, seedId)
        farmInfo1 = result[0]
        response = result[1]
        farmInfo2 = result[2]
        if farmInfo1 != None:
            log.writeResultLog("\t\tInit error")
            return
        if response == (self.REQUEST_FAILED_NO_FARM % randomFarmId) and farmInfo2 == None:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def plantingExistsSeedFarm(self, existsSeedId=random.choice(gameConfig.GAME_SEED_LIST)["seedId"], seedId=random.choice(gameConfig.GAME_SEED_LIST)["seedId"], farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tPlanting exists seed farm")
        roleLevel = 99
        seedCount = 1
        planting.init(roleLevel, seedId, seedCount)
        planting.plant(farmId, existsSeedId)
        result = self.plant(farmId, seedId)
        farmInfo1 = result[0]
        response = result[1]
        farmInfo2 = result[2]
        if farmInfo1 == None or farmInfo1["seedId"] != existsSeedId:
            log.writeResultLog("\t\tInit error")
            return
        if response == self.REQUEST_FAILED_HAVE_PLANTED_SEED and farmInfo2["seedId"] == existsSeedId and farmInfo1["time"] == farmInfo2["time"]:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

# harvest
class FarmHarvesting():
    REQUEST_SUCCEED = '[1,[1,$seedType,$silver or $itemInfo,$farmInfo]]'
    # $itemInfo = {"sUid":$uid,"iItemId":$itemId,"iCount":$itemCoutn}
    # $farmInfo = {"sUid":$uid,"iFarmId":$farmId,"iSeedId":$seedId,"iNtime":$maturedTime}
    # not found farm info
    #REQUEST_FAILED_NO_FARM = '[1,[-3010,$farmId]]'
    REQUEST_FAILED_NO_FARM = '[1,[-3010,%d]]'
    # seed not mature
    REQUEST_FAILED_NOT_MATURE = '[1,[-1]]'
    # not planted seed
    REQUEST_FAILED_NO_SEED = '[1,[-2]]'

    def __init__(self):
        log.writeResultLog("start harvest")
    
    def harvest(self, farmId):
        #get status before test
        farmInfo1 = harvesting.getFarmStatus(farmId)
        seedId = 0
        if farmInfo1 != None:
            seedId = farmInfo1["seedId"]
        seedType, reward = harvesting.getSeedProduce(seedId)
        rewardItemId = 0
        if seedType == harvesting.CHEST_SEED or seedType == harvesting.STONE_SEED:
            rewardItemId = reward
        silver1, itemCount1 = harvesting.getStatus(rewardItemId)
        log.writeBeforeStatus([{"farm info":farmInfo1}, {"silver":silver1}, {"itemId":rewardItemId}, {"count":itemCount1}])
        response = harvesting.sendPackage(farmId)
        log.write("harvest farm:\t\tfarm id: " + str(farmId) + ", seed id: " + str(seedId))
        farmInfo2 = harvesting.getFarmStatus(farmId)
        silver2, itemCount2 = harvesting.getStatus(rewardItemId)
        log.writeAfterStatus([{"farm info":farmInfo2}, {"silver":silver2}, {"itemId":rewardItemId}, {"count":itemCount2}])
        return farmInfo1, silver1, itemCount1, response, farmInfo2, silver2, itemCount2
    
    def harvestingEachSeed(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tHarvesting each seed")
        roleLevel = 99
        for seed in gameConfig.GAME_SEED_LIST:
            seedId = seed["seedId"]
            harvesting.init(roleLevel, farmId, seedId, common.getServerTime())
            result = self.harvest(farmId)
            farmInfo1 = result[0]
            response = communication.toJson(result[3])
            farmInfo2 = result[4]
            if farmInfo1 == None and farmInfo1["seedId"] != seedId and farmInfo1["time"] > common.getServerTime():
                log.writeResultLog("\t\t" + str(seedId) + " Init error")
                continue
            if response[1][0] == 1 and farmInfo2["seedId"] == 0 and farmInfo2["time"] == 0:
                log.writeResultLog("\t\t" + str(seedId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(seedId) + " Failed")

    def harvestingEachFarm(self, seedId=random.choice(gameConfig.GAME_SEED_LIST)["seedId"]):
        log.writeResultLog("\tHarvesting each farm")
        roleLevel = 99
        for farm in gameConfig.GAME_FARM_LIST:
            farmId = farm["farmId"]          
            harvesting.init(roleLevel, farmId, seedId, common.getServerTime())
            result = self.harvest(farmId)
            farmInfo1 = result[0]
            response = communication.toJson(result[3])
            farmInfo2 = result[4]
            if farmInfo1 == None and farmInfo1["seedId"] != seedId and farmInfo1["time"] > common.getServerTime():
                log.writeResultLog("\t\t" + str(seedId) + " Init error")
                continue
            if response[1][0] == 1 and farmInfo2["seedId"] == 0 and farmInfo2["time"] == 0:
                log.writeResultLog("\t\t" + str(farmId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(farmId) + " Failed")

    def harvestingNotMatured(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tHarvesting hot matured seed")
        roleLevel = 99
        for seed in gameConfig.GAME_SEED_LIST:
            seedId = seed["seedId"]
            harvesting.init(roleLevel, farmId, seedId, common.getServerTime() + 60)
            result = self.harvest(farmId)
            farmInfo1 = result[0]
            response = result[3]
            farmInfo2 = result[4]
            if farmInfo1 == None and farmInfo1["seedId"] != seedId and farmInfo1["time"] <= common.getServerTime():
                log.writeResultLog("\t\t" + str(seedId) + " Init error")
                continue
            if response == self.REQUEST_FAILED_NOT_MATURE and farmInfo2["seedId"] == seedId and farmInfo2["time"] != 0:
                log.writeResultLog("\t\t" + str(seedId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(seedId) + " Failed")

    def harvestingUnlockedFarm(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tHarvesting unlocked farm")
        roleLevel = 1
        harvesting.init(roleLevel, -1, 0, 0, False)
        result = self.harvest(farmId)
        farmInfo1 = result[0]
        silver1 = result[1]
        response = result[3]
        farmInfo2 = result[4]
        silver2 = result[5]
        if farmInfo1 != None:
            log.writeResultLog("\t\tInit error")
            return
        if  response == (self.REQUEST_FAILED_NO_FARM % farmId) and farmInfo2 == None and silver1 == silver2:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def harvestingNoSeed(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tHarvesting no seed")
        roleLevel = 99
        harvesting.init(roleLevel, farmId, 0, 0)
        result = self.harvest(farmId)
        farmInfo1 = result[0]
        response = result[3]
        farmInfo2 = result[4]
        if farmInfo1 == None and farmInfo1["seedId"] != 0:
            log.writeResultLog("\t\tInit error")
            return
        if  response == self.REQUEST_FAILED_NO_SEED and farmInfo2["seedId"] == 0 and farmInfo2["time"] == 0:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def harvestingIncorrectFarmId(self, seedId=random.choice(gameConfig.GAME_SEED_LIST)["seedId"]):
        log.writeResultLog("\tHarvesting incorrect farm id")
        roleLevel = 99
        randomFarmId = random.randint(1, 900000)
        harvesting.init(roleLevel, 0, 0, 0)
        result = self.harvest(randomFarmId)
        farmInfo1 = result[0]
        silver1 = result[1]
        response = result[3]
        farmInfo2 = result[4]
        silver2 = result[5]
        if farmInfo1 != None:
            log.writeResultLog("\t\tInit error")
            return
        if  response == (self.REQUEST_FAILED_NO_FARM % randomFarmId) and farmInfo2 == None and silver1 == silver2:
            log.writeResultLog("\t\t Passed")
        else:
            log.writeResultLog("\t\t Failed")

    def checkProduce(self, farmId=random.choice(gameConfig.GAME_FARM_LIST)["farmId"]):
        log.writeResultLog("\tCheck seed produce")
        roleLevel = 99
        for seed in gameConfig.GAME_SEED_LIST:
            seedId = seed["seedId"]
            if seed["seedType"] == 1:
                continue
            harvesting.init(roleLevel, farmId, seedId, common.getServerTime())
            result = self.harvest(farmId)
            farmInfo1 = result[0]
            silver1 = result[1]
            itemCount1 = result[2]
            response = communication.toJson(result[3])
            farmInfo2 = result[4]
            silver2 = result[5]
            itemCount2 = result[6]
            if farmInfo1 == None and farmInfo1["seedId"] != seedId and farmInfo1["time"] > common.getServerTime():
                log.writeResultLog("\t\tInit error")
                continue
            isFailed = True
            if farmInfo2 != None and response[1][0] == 1 and farmInfo2["seedId"] == 0 and farmInfo2["time"] == 0:
                if seed["seedType"] == harvesting.SILVER_SEED:
                    if response[1][1] == harvesting.SILVER_SEED and response[1][2] == silver2 - silver1 and silver2 - silver1 == seed["reward"]:
                        isFailed = False
                elif seed["seedType"] == harvesting.STONE_SEED:
                    responseItemInfo = response[1][2]
                    if response[1][1] == harvesting.STONE_SEED and responseItemInfo["iStoneId"] == seed["reward"] and itemCount2 - itemCount1 == 1 and silver1 == silver2:
                        isFailed = False
                elif seed["seedType"] == harvesting.CHEST_SEED:
                    responseItemInfo = response[1][2]
                    if response[1][1] == harvesting.CHEST_SEED and responseItemInfo["iItemId"] == seed["reward"] and itemCount2 - itemCount1 == 1 and silver1 == silver2:
                        isFailed = False
            if isFailed:
                log.writeResultLog("\t\t" + str(seedId) + " Failed")
            else:
                log.writeResultLog("\t\t" + str(seedId) + " Passed")










fp = FarmPlanting()
fp.plantingEachSeed()
fp.plantingEachFarm()
fp.plantingLessThanHave()
fp.checkSeedMatureTime()
fp.plantingUnlockedFarm()
fp.plantingIncorrectSeedId()
fp.plantingIncorrectFarmId()
fp.plantingExistsSeedFarm()
fh = FarmHarvesting()
fh.harvestingEachSeed()
fh.harvestingEachFarm()
fh.harvestingNotMatured()
fh.harvestingUnlockedFarm()
fh.harvestingNoSeed()
fh.harvestingIncorrectFarmId()
fh.checkProduce()
