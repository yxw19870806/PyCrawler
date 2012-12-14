def getAccountName():
    accName = raw_input("Please input your account: ")
    return accName

def getAccountPassword():
    accPwd = raw_input("Please input your password: ")
    return accPwd

def getAccountRePassword():
    accRePwd = raw_input("Please input your password again: ")
    return accRePwd

def getInputStatus(msg):
    status = raw_input(msg)
    return status

def showMsg(msg):
    print msg

def showExceptionMsg(msg):
    print msg

def showErrMsg(errNum):
    print "You have a big problem, Game over. Error number : " + str(errNum)

#return:
#    -1: error action
#    1: attack
#    2: defense
#    3: flee
#    4: item
#    5: skill
def getRoleFightAction():
    action = raw_input("ACTION: 1.Attack 2.Defense 3.Flee: ")
    if action == "1" or action.lower() == "a" or action.lower() == "attack":
        return 1
    elif action == "2" or action.lower() == "d" or action.lower() == "defense":
        return 2
    elif action == "3" or action.lower() == "f" or action.lower() == "flee":
        return 3
    elif action == "4" or action.lower() == "i" or action.lower() == "item":
        print "Error action"
        return (-1)
    elif action == "5" or action.lower() == "s" or action.lower() == "skill":
        print "Error action"
        return (-1)
    else:
        print "Error action"
        return (-1)

#return:
#    -1: error action
#    1: random enemy
#    2: heal
#    3: role information
#    4: save game
#    5: load game
def getRoleRestAction():
    action = raw_input("ACTION: 1.Move 2.Heal 3.Role 4.Save 5.Load: ")
    if action == "1" or action.lower() == "m" or action.lower() == "move":
        return 1
    elif action == "2" or action.lower() == "h" or action.lower() == "heal":
        return 2
    elif action == "3" or action.lower() == "r" or action.lower() == "role":
        return 3
    elif action == "4" or action.lower() == "s" or action.lower() == "save":
        return 4
    elif action == "5" or action.lower() == "l" or action.lower() == "load":
        return 5
    else:
        print "##Error action"
        return (-1)

def showRoleInf(roleInfo_dict):
    print "Role information: "
    print "mame: " + roleInfo_dict["name"] + " , level: " + roleInfo_dict["level"] + " , exp: " + roleInfo_dict["exp"] + " , gold: " + roleInfo_dict["gold"]
    print "attack: " + roleInfo_dict["atk"] + " , defense: " + roleInfo_dict["atk"] + " , HP: " + roleInfo_dict["HP"] + " , MP: " + roleInfo_dict["MP"] 

#return:
#    0: register
#    1: cancel
def isRegister():
    action = raw_input("Do you want to sign up? 1.Yes 2.No): ")
    if action == "1" or action.lower() == "y" or action.lower() == "yes":
        return 0
    elif action == "2" or action.lower() == "n" or action.lower() == "no":
        return 1
    else:
        print "error input"
        return (-1)

#return:
#    0: save game
#    1: cancel
def isSaveGame():
    action = raw_input("Do you want to save game? 1.Yes 2.No: ")
    if action == "1" or action.lower() == "m" or action.lower() == "move":
        return 1
    elif action == "2" or action.lower() == "h" or action.lower() == "heal":
        return 2
    elif action == "3" or action.lower() == "r" or action.lower() == "role":
        return 3
    elif action == "4" or action.lower() == "s" or action.lower() == "save":
        return 4
    elif action == "5" or action.lower() == "l" or action.lower() == "load":
        return 5
    else:
        print "Error action"
        return (-1)
