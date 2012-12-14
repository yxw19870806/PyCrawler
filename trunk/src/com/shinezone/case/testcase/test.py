from com.shinezone.case.common import common, communication, config, json
# init
common.setHeroStrong(110000, 200)
common.setHeroIntelligence(110000, 200)
common.setHeroAgility(110000, 200)
common.setHeroEndurance(110000, 200)
common.setAchievement(100000)

# before status
strong = common.getHeroStrong(110000)
intelligence = common.getHeroIntelligence(110000)
agility = common.getHeroAgility(110000)
endurance = common.getHeroEndurance(110000)
all = strong + intelligence + agility + endurance
print "start test:", strong, intelligence, agility, endurance, " all: ", all

for i in range(100):
    data = '["UserHero","develop","[110000,1]"]'
    re = communication.toJson(communication.request(data))
    newStrong = re[1][1]["iStrong"]
    newIntelligence = re[1][1]["iIntelligence"]
    newAgility = re[1][1]["iAgility"]
    newEndurance = re[1][1]["iEndurance"]
    newAll = newStrong + newIntelligence + newAgility + newEndurance
    if newAll != all:
        print newStrong, newIntelligence, newAgility, newEndurance, " all: ", newAll
        all = newAll
    data = '["UserHero","makeSureDevelop","[110000]"]'
    re = communication.request(data)

# after status
strong = common.getHeroStrong(110000)
intelligence = common.getHeroIntelligence(110000)
agility = common.getHeroAgility(110000)
endurance = common.getHeroEndurance(110000)
all = strong + intelligence + agility + endurance
print "stop test:", strong, intelligence, agility, endurance, " all: ", all
