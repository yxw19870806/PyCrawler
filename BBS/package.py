# -*- coding:utf-8  -*-
'''
Created on 2013-6-30

@author: rena
'''
import codecs
import random
# 
# count = 402
# 
# reward1 = "高级礼包"
# reward2 = "初级礼包"
# reward3 = "实物奖励"
# reward4 = ""
# reward5 = "梦想"
# reward6 = "剧场门票"
# reward7 = "应援"
# 
# count1 = 1
# count2 = 11
# count3 = 11
# count4 = 11
# count5 = 11
# count6 = 11
# 
# rewardList = []
# for i in range(count1):
#     rewardList.append(reward1)
# for i in range(count2):
#     rewardList.append(reward2)
# for i in range(count3):
#     rewardList.append(reward3)
# for i in range(count4):
#     rewardList.append(reward4)
# for i in range(count5):
#     rewardList.append(reward5)
#     
# print rewardList
#
# for i in rewardList:
#     resultFile.write(str(i))
# resultFile.close()
# for i in range(count):
#     pass

resultFile = codecs.open("result", 'w', 'utf8')
for i in range(1, 201):
    p = random.randint(1, 10000)
    if p < 4500:
        reward = "+" + str(random.choice([48, 68, 88, 168, 188, 268, 288, 368, 388, 468, 488, 568, 588, 668, 688, 768, 788, 868, 888])) + "梦想"
    elif p < 9000:
        reward = "+" + str(random.randint(1, 10)) + "剧场门票"
    else:
        reward = "+" + str(random.choice([48, 68, 88, 168, 188, 268, 288, 368, 388, 468, 488, 568, 588, 668, 688, 768, 788, 868, 888])) + "梦想"
        reward += " +" + str(random.randint(1, 10)) + "剧场门票"
    resultFile.write(str(i) + " " + reward + "\n")
resultFile.close()
