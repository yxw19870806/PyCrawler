from com.shinezone.case.common import communication, common

# ["Package","saleBook",[$bookId,$bookNum]]

def sendPackage(bookId, bookCount):
    data = '["Package","saleBook",[%d,%d]]' % (bookId, bookCount)
    return communication.request(data)

def init(bookId, bookCount):
    common.setItemCount(bookId, bookCount)
    common.clearCache()

def getStatus(bookId):
    silverCoin = common.getSliverCoin()
    bookCount = common.getItemCount(bookId)
    return silverCoin, bookCount
