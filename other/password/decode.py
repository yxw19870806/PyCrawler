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
    count = len(old)
    for i in range(count / 2):
        temp = old[count - i * 2 - 1]
        temp = ord(temp[0])
        if temp % 2 == 0:
            temp = (temp + 128) / 2
        else:
            temp = (temp + 33) / 2
        new += chr(temp)
        
    print new
