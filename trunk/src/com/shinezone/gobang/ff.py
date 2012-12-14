'''
Created on 2012-8-14

@author: Administrator
''' 
import math
BOARD_LENTH = 5
num = 0
arr = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 'a', 'b'], ['c', 'd', 'e', 'f']]
brr = " 0 14 258 369c 7ad be f "
crr = "0123\n4567\n89ab\ncdef"

arr = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], ['a', 'b', 'c', 'd', 'e'], ['f', 'g', 'h', 'i', 'j'], ['k', 'l', 'm', 'n', 'o']]
#brr = " 0 15 26a 37bf 48cgk 9dhl oim jn o "
brr = " k fl agm 5bhn 06cio 17dj 28e 39 4 "
index = 33

#if index < (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2):
#    # 1 + 2 * i + i * (i - 1) / 2 = index
#    # (n+1)(n+2)=2*x
#    # (n+3/2)**2-1/4 = 2*x
##    print (2 * index + 0.25) ** 0.5 - 1.5
#    i = int(math.ceil((2 * (index + 1) + 0.25) ** 0.5 - 1.5))
#    j = index - (2 * (i - 1) + (i - 1) * ((i - 1) - 1) / 2)
#    print i, j
#    print brr[index]
#    x = j - 1
#    y = BOARD_LENTH - i + j - 1
#    print "x=" + str(x)
#    print "y=" + str(y)
#    print arr[y][x]
#else:
#    index2 = index - (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2) + 1
#    # BOARD_LENTH * i - i * (i - 1) / 2 = index2
#    i = int(math.ceil(0.5 * (2 * BOARD_LENTH + 1) - ((0.5 * (2 * BOARD_LENTH + 1)) * (0.5 * (2 * BOARD_LENTH + 1)) - 2 * index2) ** 0.5))
#    j = index2 - (BOARD_LENTH * (i - 1) - (i - 1) * ((i - 1) - 1) / 2)
#    print i, j
#    x = i + j - 1
#    y = j - 1
#    print brr[index]
#    print arr[y][x]

#if index < (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2):
#    # 1 + 2 * i + i * (i - 1) / 2 = index
#    # (n+1)(n+2)=2*x
#    # (n+3/2)**2-1/4 = 2*x
##    print (2 * index + 0.25) ** 0.5 - 1.5
#    i = int(math.ceil((2 * (index + 1) + 0.25) ** 0.5 - 1.5))
#    j = index - (2 * (i - 1) + (i - 1) * ((i - 1) - 1) / 2)
#    print i, j
#    print brr[index]
#    x=i-j
#    y=j-1
#    print "x=" + str(x)
#    print "y=" + str(y)
#    print arr[y][x]
#else:
#    index2 = index - (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2) + 1
#    # BOARD_LENTH * i - i * (i - 1) / 2 = index2
#    i = int(math.ceil(0.5 * (2 * BOARD_LENTH + 1) - ((0.5 * (2 * BOARD_LENTH + 1)) * (0.5 * (2 * BOARD_LENTH + 1)) - 2 * index2) ** 0.5))
#    j = index2 - (BOARD_LENTH * (i - 1) - (i - 1) * ((i - 1) - 1) / 2)
#    print i, j
#    print brr[index]
#    print arr[i + j - 1][BOARD_LENTH - j]
BOARD_BLANK = "."
board = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], ['a', 'b', 'c', 'd', 'e'], ['f', 'g', 'h', 'i', 'j'], ['k', 'l', 'm', 'n', 'o']]
boardDiagonalString1 = " "
for i in range(BOARD_LENTH - 1,  - BOARD_LENTH, -1):
#    print "a"
    for j in range(BOARD_LENTH):
#        print j
        if 0 <= j < BOARD_LENTH and 0 <= j - i < BOARD_LENTH:
            boardDiagonalString1 += str(board[j][j - i])
    boardDiagonalString1 += " "
boardDiagonalString2 = " "
for i in range(2 * BOARD_LENTH - 1):
    for j in range(i + 1):
        if 0 <= j < BOARD_LENTH and 0 <= i - j < BOARD_LENTH:
            boardDiagonalString2 += str(board[j][i - j])
    boardDiagonalString2 += " "
print board
print ":" + boardDiagonalString1 + ":"
print ":" + boardDiagonalString2 + ":"

