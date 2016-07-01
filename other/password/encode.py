import random

randomList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '_', '@']

a = ""
b = ""
c = ""
d = ""
e = ""
f = ""
g = ""
h = ""


for old in [a, b, c, d, e, f, g, h]:
    new = ""
    for i in old:
        temp = ord(i) 
        if 33 <= temp <= 79:
            temp = temp * 2 - 33
        else:
            temp = temp * 2 - 128
        new = str(random.choice(randomList)) + str(chr(temp)) + new
    print new
