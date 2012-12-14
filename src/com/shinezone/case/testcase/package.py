from com.shinezone.case.common import common, config, gameConfig, log
import random
from com.shinezone.case.package import expanding, saleBook

class PackageExpand():
    REQUEST_SUCCEED = '[1,[1]]'
    # not enough gold
    REQUEST_FAILED_NOT_ENOUGH_GOLD = '[1,[-1001]]'

    def __init__(self):
        log.writeResultLog("start expand package")   

    def expand(self):
        #get status before test
        goldCoin1, bagSlotCount1 = expanding.getStatus()
        log.writeBeforeStatus([{"gold coin":goldCoin1}, {"bag slot count":bagSlotCount1}])
        response = expanding.sendPackage()
        #get status after test        
        goldCoin2, bagSlotCount2 = expanding.getStatus()
        log.writeBeforeStatus([{"gold coin":goldCoin2}, {"bag slot count":bagSlotCount2}])
        return goldCoin1, bagSlotCount1, response, goldCoin2, bagSlotCount2

    def expandPackageLessThanLimitSlots(self):
        log.writeResultLog("\tExpanding package slots less than " + str(expanding.BAG_SLOTS_COST_LIMIT))
        goldCoin = 100
        for bagSlotCount in range(20, expanding.BAG_SLOTS_COST_LIMIT, 5):
            expanding.init(goldCoin, bagSlotCount)
            result = self.expand()
            goldCoin1 = result[0]
            bagSlotCount1 = result[1]
            response = result[2]
            goldCoin2 = result[3]
            bagSlotCount2 = result[4]
            if goldCoin < expanding.GOLD_CPIN_COST_LESS_THAN_LIMIT_SLOTS or bagSlotCount1 >= expanding.BAG_SLOTS_COST_LIMIT or bagSlotCount1 != bagSlotCount:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Init error")
                continue
            if response == self.REQUEST_SUCCEED and goldCoin1 - goldCoin2 == expanding.GOLD_CPIN_COST_LESS_THAN_LIMIT_SLOTS and bagSlotCount2 - bagSlotCount1 == expanding.EXPAND_ADD_SLOT_COUNTS and bagSlotCount2 < expanding.BAG_SLOTS_COST_LIMIT:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Failed")

    def expandPackageMoreThanLimitSlots(self):
        log.writeResultLog("\tExpanding package slots more than " + str(expanding.BAG_SLOTS_COST_LIMIT))
        goldCoin = 100
        for bagSlotCount in range(expanding.BAG_SLOTS_COST_LIMIT, 100, 5):
            expanding.init(goldCoin, bagSlotCount)
            result = self.expand()
            goldCoin1 = result[0]
            bagSlotCount1 = result[1]
            response = result[2]
            goldCoin2 = result[3]
            bagSlotCount2 = result[4]
            if goldCoin < expanding.GOLD_CPIN_COST_MORE_THAN_LIMIT_SLOTS or bagSlotCount1 < expanding.BAG_SLOTS_COST_LIMIT or bagSlotCount1 != bagSlotCount:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Init error")
                continue
            if response == self.REQUEST_SUCCEED and goldCoin1 - goldCoin2 == expanding.GOLD_CPIN_COST_MORE_THAN_LIMIT_SLOTS and bagSlotCount2 - bagSlotCount1 == expanding.EXPAND_ADD_SLOT_COUNTS and bagSlotCount2 >= expanding.BAG_SLOTS_COST_LIMIT:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Failed")
                
    def expandNotEnoughGoldLessThanLimitSlots(self):
        log.writeResultLog("\tExpanding package not enough gold coin when slots less than " + str(expanding.BAG_SLOTS_COST_LIMIT))
        for bagSlotCount in range(20, expanding.BAG_SLOTS_COST_LIMIT, 5):
            goldCoin = random.randint(0, expanding.GOLD_CPIN_COST_LESS_THAN_LIMIT_SLOTS - 1)
            expanding.init(goldCoin, bagSlotCount)
            result = self.expand()
            goldCoin1 = result[0]
            bagSlotCount1 = result[1]
            response = result[2]
            goldCoin2 = result[3]
            bagSlotCount2 = result[4]
            if goldCoin >= expanding.GOLD_CPIN_COST_LESS_THAN_LIMIT_SLOTS or bagSlotCount1 >= expanding.BAG_SLOTS_COST_LIMIT or bagSlotCount1 != bagSlotCount:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Init error")
                continue
            if response == self.REQUEST_FAILED_NOT_ENOUGH_GOLD and goldCoin1 == goldCoin2 and bagSlotCount2 == bagSlotCount1 and bagSlotCount2 < expanding.BAG_SLOTS_COST_LIMIT:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Failed")

    def expandNotEnoughGoldMoreThanLimitSlots(self):
        log.writeResultLog("\tExpanding package not enough gold coin when slots more than " + str(expanding.BAG_SLOTS_COST_LIMIT))
        for bagSlotCount in range(expanding.BAG_SLOTS_COST_LIMIT, 100, 5):
            goldCoin = random.randint(0, expanding.GOLD_CPIN_COST_MORE_THAN_LIMIT_SLOTS - 1)
            expanding.init(goldCoin, bagSlotCount)
            result = self.expand()
            goldCoin1 = result[0]
            bagSlotCount1 = result[1]
            response = result[2]
            goldCoin2 = result[3]
            bagSlotCount2 = result[4]
            if goldCoin >= expanding.GOLD_CPIN_COST_MORE_THAN_LIMIT_SLOTS or bagSlotCount1 < expanding.BAG_SLOTS_COST_LIMIT or bagSlotCount1 != bagSlotCount:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Init error")
                continue
            if response == self.REQUEST_FAILED_NOT_ENOUGH_GOLD and goldCoin1 == goldCoin2 and bagSlotCount2 == bagSlotCount1 and bagSlotCount2 >= expanding.BAG_SLOTS_COST_LIMIT:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(bagSlotCount) + " Failed")

class BookSaling():
    REQUEST_SUCCEED = '[1,[1]]'
    # not enough book
    REQUEST_FAILED_NOT_ENOUGH_BOOK = '[1,[-1004]]'
    # item count incorrect
    REQUEST_FAILED_INCORRECT_ITEM_COUNT = '[1,-4003]'
    # item id incorrect
    REQUEST_FAILED_INCORRECT_ITEM_ID = '[1,[-1004]]'

    def __init__(self):
        log.writeResultLog("start expand package")   

    def sale(self, bookId, bookCount):
        #get status before test
        silverCoin1, bookCount1 = saleBook.getStatus(bookId)
        log.writeBeforeStatus([{"silver coin":silverCoin1}, {"book count":bookCount1}])
        response = saleBook.sendPackage(bookId, bookCount)
        #get status after test        
        silverCoin2, bookCount2 = saleBook.getStatus(bookId)
        log.writeBeforeStatus([{"silver coin":silverCoin2}, {"book count":bookCount2}])
        return silverCoin1, bookCount1, response, silverCoin2, bookCount2

    def saleEachBook(self, count=random.randint(1, 10)):
        log.writeResultLog("\tSale book, count: " + str(count))
        for book in gameConfig.GAME_SKILL_BOOK_LIST + gameConfig.GAME_UPGRADE_BOOK_LIST:
            bookId = book["bookId"]
            saleBook.init(bookId, count)
            result = self.sale(bookId, count)
            silverCoin1 = result[0]
            bookCount1 = result[1]
            response = result[2]
            silverCoin2 = result[3]
            bookCount2 = result[4]
            if bookCount1 != count:
                log.writeResultLog("\t\t" + str(bookId) + " Init error")
                continue
            if response == self.REQUEST_SUCCEED and bookCount1 - bookCount2 == count and silverCoin2 - silverCoin1 == book["price"]:
                log.writeResultLog("\t\t" + str(bookId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(bookId) + " Failed")

    def saleMoreThanHave(self, count=random.randint(2, 10)):
        log.writeResultLog("\tSale book count more than have")
        initItemCount = 1
        for book in gameConfig.GAME_SKILL_BOOK_LIST + gameConfig.GAME_UPGRADE_BOOK_LIST:
            bookId = book["bookId"]
            saleBook.init(bookId, initItemCount)
            result = self.sale(bookId, count)
            silverCoin1 = result[0]
            bookCount1 = result[1]
            response = result[2]
            silverCoin2 = result[3]
            bookCount2 = result[4]
            if bookCount1 != initItemCount:
                log.writeResultLog("\t\t" + str(bookId) + " Init error")
                continue
            if response == self.REQUEST_FAILED_NOT_ENOUGH_BOOK and bookCount1 == bookCount2 and silverCoin2 == silverCoin1:
                log.writeResultLog("\t\t" + str(bookId) + " Passed")
            else:
                log.writeResultLog("\t\t" + str(bookId) + " Failed")

    def saleNegativeNumber(self, count= -1):
        log.writeResultLog("\tSale book count less than zero")
        initItemCount = 1
        book = random.choice(gameConfig.GAME_SKILL_BOOK_LIST + gameConfig.GAME_UPGRADE_BOOK_LIST)
        bookId = book["bookId"]
        saleBook.init(bookId, initItemCount)
        result = self.sale(bookId, count)
        silverCoin1 = result[0]
        bookCount1 = result[1]
        response = result[2]
        silverCoin2 = result[3]
        bookCount2 = result[4]
        if bookCount1 != initItemCount:
            log.writeResultLog("\t\t" + str(bookId) + " Init error")
            return
        if response == self.REQUEST_FAILED_INCORRECT_ITEM_COUNT and bookCount1 == bookCount2 and silverCoin2 == silverCoin1:
            log.writeResultLog("\t\t" + str(bookId) + " Passed")
        else:
            log.writeResultLog("\t\t" + str(bookId) + " Failed")











#pe = PackageExpand()
#pe.expandPackageLessThanLimitSlots()
#pe.expandPackageMoreThanLimitSlots()
#pe.expandNotEnoughGoldLessThanLimitSlots()
#pe.expandNotEnoughGoldMoreThanLimitSlots()

bs = BookSaling()
#bs.saleEachBook(1)
#bs.saleEachBook(5)
#bs.saleMoreThanHave()
bs.saleNegativeNumber()
