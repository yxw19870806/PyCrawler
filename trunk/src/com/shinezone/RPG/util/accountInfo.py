#####################################
#				ACCOUNT				#
#####################################
#check account name valid
def isAccountNameValid(accName_str):
	if accName_str == "1":
		return 1
	if accName_str == "2":
		return 1
	if accName_str == "3":
		return 1
	if accName_str is None:
		return 1
	return 0

#check account password valid
def isAccountPwdValid(accPwd_str):
	if accPwd_str is None:
		return 1
	return 0

#attr:
#	accList    {USERNAME_1: PASSWORD_1,USERNAME_2: PASSWORD_2, ...}
#return
#	0: account exist
#	1: account not exist
def isAccountNameExist(accName_str, accList_dict):
	if accName_str in accList_dict:
		return 0
	else:
		return 1

#attr:
#	accList    {USERNAME_1: PASSWORD_1,USERNAME_2: PASSWORD_2, ...}
#return
#	0: password correct
#	1: password incorrect
def checkAccountPassword(accName_str, accPwd_str, accList_dict):
	if accPwd_str == accList_dict[accName_str]:
		return 0
	else:
		return 1

#attr:
#	accList    {USERNAME_1: PASSWORD_1,USERNAME_2: PASSWORD_2, ...}
#return
#	0: account exist
#	1: account invalid
#	2: account not exist
def login(accName_str, accList_dict):
	#account invalid
	if isAccountNameValid(accName_str) == 1:
		return 1
	#account exist
	if isAccountNameExist(accName_str, accList_dict) == 0:
		return 0
	else:
		return 2

#return
#	0: password twice consistent
#	1: password twice inconsistent
def signUp(accPwd_str, rePwd_str):
	if accPwd_str == rePwd_str:
		return 0
	else:
		return 1
