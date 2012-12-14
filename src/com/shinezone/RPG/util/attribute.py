import raising
import sys

#public
#return
# 0:    role
# 1:    monster
def getType(targetInfo_dict):
    if targetInfo_dict["type"] == "role":
        return 0
    elif targetInfo_dict["type"] == "monster":
        return 1
    else:
        return (-1)

# return:
#    0: succeed
#    1: error
def setName(name_str, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["username"] = name_str
    elif type == 1:
        targetInfo_dict["name"] = name_str
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getName(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["username"]
    elif type == 1:
        return targetInfo_dict["name"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setAttack(atk_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["atk"] = atk_int
    elif type == 1:
        targetInfo_dict["atk"] = atk_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getAttack(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["atk"]
    elif type == 1:
        return targetInfo_dict["atk"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setDefense(def_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["def"] = def_int
    elif type == 1:
        targetInfo_dict["def"] = def_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getDefense(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["def"]
    elif type == 1:
        return targetInfo_dict["def"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setMaxHP(maxHP_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["maxHP"] = maxHP_int
    elif type == 1:
        targetInfo_dict["maxHP"] = maxHP_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getMaxHP(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["maxHP"]
    elif type == 1:
        return targetInfo_dict["maxHP"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setMaxMP(maxMP_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["maxMP"] = maxMP_int
    elif type == 1:
        targetInfo_dict["maxMP"] = maxMP_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getMaxMP(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["maxMP"]
    elif type == 1:
        return targetInfo_dict["maxMP"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setHP(HP_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["HP"] = HP_int
    elif type == 1:
        targetInfo_dict["HP"] = HP_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getHP(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["HP"]
    elif type == 1:
        return targetInfo_dict["HP"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setMP(MP_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["MP"] = MP_int
    elif type == 1:
        targetInfo_dict["MP"] = MP_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getMP(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["MP"]
    elif type == 1:
        return targetInfo_dict["MP"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setGold(gold_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["gold"] = gold_int
    elif type == 1:
        targetInfo_dict["gold"] = gold_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getGold(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["gold"]
    elif type == 1:
        return targetInfo_dict["gold"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setLevel(level_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["level"] = level_int
    elif type == 1:
        targetInfo_dict["level"] = level_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getLevel(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["level"]
    elif type == 1:
        return targetInfo_dict["level"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setExp(exp_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["exp"] = exp_int
    elif type == 1:
        targetInfo_dict["exp"] = exp_int
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getExp(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["exp"]
    elif type == 1:
        return targetInfo_dict["exp"]
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def setMap(map_int, targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        targetInfo_dict["map"] = targetInfo_dict
    elif type == 1:
        raise raising.GetObjectTypeException, "object type not support in " + sys._getframe().f_code.co_name + "()"
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"

def getMap(targetInfo_dict):
    type = getType(targetInfo_dict)
    if type == 0:
        return targetInfo_dict["map"]
    elif type == 1:
        raise raising.GetObjectTypeException, "object type not support in " + sys._getframe().f_code.co_name + "()"
    else:
        raise raising.GetObjectTypeException, "get object type error in " + sys._getframe().f_code.co_name + "()"
