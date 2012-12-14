from com.shinezone.case.common import communication, common, gameConfig

# ["Package","equipmerge",[%itemId]]
EQUIP_FRAGMENT = 5
itemList = []
for item in gameConfig.GAME_ITEM_LIST:
    if item["itemType"] == EQUIP_FRAGMENT:
        item["itemId"] = int(item["itemId"])
        for equipMerge in gameConfig.GAME_EQUIP_MERGE_LIST:
            if equipMerge["itemId"] == item["itemId"]:
                item["count"] = int(equipMerge["count"])
                item["equipId"] = int(equipMerge["equipId"]) 
        itemList.append(item)
#[{'itemId': 610042, 'count': 5, 'equipId': 210014, 'itemType': 5}, {'itemId': 610043, 'count': 5, 'equipId': 215007, 'itemType': 5}, {'itemId': 610044, 'count': 5, 'equipId': 230014, 'itemType': 5}, {'itemId': 610045, 'count': 5, 'equipId': 220014, 'itemType': 5}, {'itemId': 610046, 'count': 10, 'equipId': 210018, 'itemType': 5}, {'itemId': 610047, 'count': 10, 'equipId': 215011, 'itemType': 5}, {'itemId': 610048, 'count': 10, 'equipId': 230018, 'itemType': 5}, {'itemId': 610049, 'count': 10, 'equipId': 220018, 'itemType': 5}, {'itemId': 610050, 'count': 10, 'equipId': 210022, 'itemType': 5}, {'itemId': 610051, 'count': 10, 'equipId': 215015, 'itemType': 5}, {'itemId': 610052, 'count': 10, 'equipId': 230022, 'itemType': 5}, {'itemId': 610053, 'count': 10, 'equipId': 220022, 'itemType': 5}, {'itemId': 610054, 'count': 15, 'equipId': 210026, 'itemType': 5}, {'itemId': 610055, 'count': 15, 'equipId': 215019, 'itemType': 5}, {'itemId': 610056, 'count': 15, 'equipId': 230026, 'itemType': 5}, {'itemId': 610057, 'count': 15, 'equipId': 220026, 'itemType': 5}, {'itemId': 610058, 'count': 15, 'equipId': 210030, 'itemType': 5}, {'itemId': 610059, 'count': 15, 'equipId': 215023, 'itemType': 5}, {'itemId': 610060, 'count': 15, 'equipId': 230030, 'itemType': 5}, {'itemId': 610061, 'count': 15, 'equipId': 220030, 'itemType': 5}, {'itemId': 610062, 'count': 20, 'equipId': 210034, 'itemType': 5}, {'itemId': 610063, 'count': 20, 'equipId': 215027, 'itemType': 5}, {'itemId': 610064, 'count': 20, 'equipId': 230034, 'itemType': 5}, {'itemId': 610065, 'count': 20, 'equipId': 220034, 'itemType': 5}, {'itemId': 610066, 'count': 20, 'equipId': 210038, 'itemType': 5}, {'itemId': 610067, 'count': 20, 'equipId': 215031, 'itemType': 5}, {'itemId': 610068, 'count': 20, 'equipId': 230038, 'itemType': 5}, {'itemId': 610069, 'count': 20, 'equipId': 220038, 'itemType': 5}]

def sendPackage(itemId):
    data = '["Package","equipmerge",[%d]]' % (itemId)
    return communication.request(data)

def init(itemId, count, equipId=0):
    if equipId != 0:
        common.delEquip(0, equipId)
    common.setItemCount(itemId, count)
    common.clearCache()

def getStatus(itemId, equipId):
    itemCount = common.getItemCount(itemId)
    equipList = common.getEquipInfo(equipId)
    equipInfo = []
    if equipList != None:
        for equip in equipList:
            eq = {}
            eq["UID"] = int(equip[0])
            eq["heroId"] = int(equip[1])
            eq["equipId"] = int(equip[2])
            eq["strengthenLevel"] = int(equip[3])
            eq["grooveCount"] = int(equip[4])
            equipInfo.append(eq)
    return itemCount, equipInfo
