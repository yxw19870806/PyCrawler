import random
import time
BOARD_LENTH = 20
BOARD_BLANK = "."
PIECE_PLAYER1 = "X"
PIECE_PLAYER2 = "O"
import math

def init(x):
    board = [[BOARD_BLANK for i in range(x)] for j in range(x)]
    return board

def showBoard(board):
    string = "    "
    for i in range(len(board)):
        if i < 10:
            string = string + "0" + str(i) + " "
        else:
            string = string + str(i) + " "
    string += "\n"
    num = 0
    for i in board:
        if num < 10:
            string = string + "0" + str(num) + "  "
        else:
            string = string + str(num) + "  "
        for j in i:
            string = string + j + "  "
        string += "\n"
        num += 1
    print string

def changePlayer(nowPlayer, players):
    for player in players:
        if player != nowPlayer:
            return player

def isWin(board, x, y, player):
    x += 4
    y += 4
    boardCopy = [[BOARD_BLANK for i in range(BOARD_LENTH + 8)] for j in range(BOARD_LENTH + 8)]
    for i in range(BOARD_LENTH):
        for j in range(BOARD_LENTH):
            boardCopy[i + 4][j + 4] = board[i][j]
    piece = player["piece"] * 5
    if (boardCopy[x - 4][y] + boardCopy[x - 3][y] + boardCopy[x - 2][y] + boardCopy[x - 1][y] + boardCopy[x][y] + boardCopy[x + 1][y] + boardCopy[x + 2][y] + boardCopy[x + 3][y] + boardCopy[x + 4][y]).find(piece) == -1:
        if (boardCopy[x][y - 4] + boardCopy[x][y - 3] + boardCopy[x][y - 2] + boardCopy[x][y - 1] + boardCopy[x][y] + boardCopy[x][y + 1] + boardCopy[x][y + 2] + boardCopy[x][y + 3] + boardCopy[x][y + 4]).find(piece) == -1:
            if (boardCopy[x - 4][y - 4] + boardCopy[x - 3][y - 3] + boardCopy[x - 2][y - 2] + boardCopy[x - 1][y - 1] + boardCopy[x][y] + boardCopy[x + 1][y + 1] + boardCopy[x + 2][y + 2] + boardCopy[x + 3][y + 3] + boardCopy[x + 4][y + 4]).find(piece) == -1:
                if (boardCopy[x + 4][y - 4] + boardCopy[x + 3][y - 3] + boardCopy[x + 2][y - 2] + boardCopy[x + 1][y - 1] + boardCopy[x][y] + boardCopy[x - 1][y + 1] + boardCopy[x - 2][y + 2] + boardCopy[x - 3][y + 3] + boardCopy[x - 4][y + 4]).find(piece) == -1:
                    return False
    return True

def AI(board, player):
    #left to right, up to down
    # -
    boardRowString = " "
    for i in board:
        for j in i:
            boardRowString += j
        boardRowString += " "
    
    # |
    boardCopy = map(list, zip(*board)) 
    boardColString = " "
    for i in boardCopy:
        for j in i:
            boardColString += j
        boardColString += " "
    result = []
    
    # \
    boardDiagonalString1 = " "
#    for i in range(1 - BOARD_LENTH, BOARD_LENTH + 1):
    for i in range(BOARD_LENTH - 1, -BOARD_LENTH, -1):
        for j in range(BOARD_LENTH):
            if 0 <= j < BOARD_LENTH and 0 <= j - i < BOARD_LENTH:
                boardDiagonalString1 += board[j][j - i]
        boardDiagonalString1 += " "
    
    # /
    boardDiagonalString2 = " "
    for i in range(2 * BOARD_LENTH - 1):
        for j in range(i + 1):
            if 0 <= j < BOARD_LENTH and 0 <= i - j < BOARD_LENTH:
                boardDiagonalString2 += board[j][i - j]
        boardDiagonalString2 += " "
    
    
    # mine: O ; other: X
    # step 1
    # find "OOOO "
    piece = player["piece"] * 4 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find " OOOO"
    piece = BOARD_BLANK + player["piece"] * 4
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find "O OOO"
    piece = player["piece"] + BOARD_BLANK + player["piece"] * 3 
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find "OOO O"
    piece = player["piece"] * 3 + BOARD_BLANK + player["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find "OO OO"
    piece = player["piece"] * 2 + BOARD_BLANK + player["piece"] * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    if result != []:
#        print "OOOO:" + str(result)
        return result

    # step 2
    # find "XXXX "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] * 4 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find " XXXX"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] * 4
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find "X XXX"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] + BOARD_BLANK + p["piece"] * 3
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find "XXX X"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] * 3 + BOARD_BLANK + p["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find "XX XX"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] * 2 + BOARD_BLANK + p["piece"] * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    if result != []:
#        print "XXXX:" + str(result)
        return result

    # step 3
    # find "OOO  "
    piece = player["piece"] * 3 + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find "  OOO"
    piece = BOARD_BLANK * 2 + player["piece"] * 3
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])    
    # find " OOO "
    piece = BOARD_BLANK + player["piece"] * 3 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find " OO O"
    piece = BOARD_BLANK + player["piece"] * 2 + BOARD_BLANK + player["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
    # find "OO O "
    piece = player["piece"] * 2 + BOARD_BLANK + player["piece"] + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find " O OO"
    piece = BOARD_BLANK + player["piece"] + BOARD_BLANK + player["piece"] * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
    # find "O OO "
    piece = player["piece"] + BOARD_BLANK + player["piece"] * 2 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find "O O O"
    piece = player["piece"] + BOARD_BLANK + player["piece"] + BOARD_BLANK + player["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    if result != []:
#        print "OOO:" + str(result)
        return result
    
    # step 4
    # find "XXX  "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] * 3 + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find "  XXX"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK * 2 + p["piece"] * 3
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])  
    # find " XXX "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] * 3 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    # find " XX X"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] * 2 + BOARD_BLANK + p["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
    # find "XX X "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] * 2 + BOARD_BLANK + p["piece"] + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find " X XX"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] + BOARD_BLANK + p["piece"] * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
    # find "X XX "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] + BOARD_BLANK + p["piece"] * 2 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find "X X X"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] + BOARD_BLANK + p["piece"] + BOARD_BLANK + p["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece)
    if result != []:
#        print "XXX:" + str(result)
        return result
    
    # step 5
    # find "OO   "
    piece = player["piece"] * 2 + BOARD_BLANK * 3
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [3, 4])
    # find " OO  "
    piece = BOARD_BLANK + player["piece"] * 2 + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find "  OO "
    piece = BOARD_BLANK * 2 + player["piece"] * 2 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
    # find "   OO"
    piece = BOARD_BLANK * 3 + player["piece"] * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1])
#    print result
    # find "O O  "
    piece = player["piece"] + BOARD_BLANK + player["piece"] + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [3, 4])
#    print result
    # find " O O "
    piece = BOARD_BLANK + player["piece"] + BOARD_BLANK + player["piece"] + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 4])
#    print result
    # find "  O O"
    piece = BOARD_BLANK * 2 + player["piece"] + BOARD_BLANK + player["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1])
#    print result
    # find " O  O"
    piece = BOARD_BLANK + player["piece"] + BOARD_BLANK * 2 + player["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
#    print result
    # find "O  O "
    piece = player["piece"] + BOARD_BLANK * 2 + player["piece"] + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
#    print result
    # find "O   O"
    piece = player["piece"] + BOARD_BLANK * 3 + player["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [2])
    if result != []:
#        print "OO:" + str(result)
        return result
        
    # step 6
    # find "XX   "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] * 2 + BOARD_BLANK * 3
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [3, 4])
    # find " XX  "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] * 2 + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])
    # find "  XX "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK * 2 + p["piece"] * 2 + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
    # find "   XX"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK * 3 + p["piece"] * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1])
    # find "X X  "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] + BOARD_BLANK + p["piece"] + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [3, 4])
    # find " X X "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] + BOARD_BLANK + p["piece"] + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 4])
    # find "  X X"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK * 2 + p["piece"] + BOARD_BLANK + p["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1])
    # find " X  X"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] + BOARD_BLANK * 2 + p["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0])
    # find "X  X "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] + BOARD_BLANK * 2 + p["piece"] + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [4])  
    # find "X   X"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] + BOARD_BLANK * 3 + p["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [2])    
    if result != []:
#        print "XX:" + str(result)
        return result
    
    # step 7
    # find "O    "
    piece = player["piece"] + BOARD_BLANK * 4
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [2, 3, 4])
    # find " O   "
    piece = BOARD_BLANK + player["piece"] + BOARD_BLANK * 3
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [3, 4])
    # find "  O  "
    piece = BOARD_BLANK * 2 + player["piece"] + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 4])
    # find "   O "
    piece = BOARD_BLANK * 3 + player["piece"] + BOARD_BLANK
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1])
    # find "    O"
    piece = BOARD_BLANK * 4 + player["piece"]
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1, 2])
    if result != []:
#        print "O:" + str(result)
        return result

    # step 8
    # find "X    "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = p["piece"] + BOARD_BLANK * 4
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [2, 3, 4])
    # find " X   "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK + p["piece"] + BOARD_BLANK * 3
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [3, 4])
    # find "  X  "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK * 2 + p["piece"] + BOARD_BLANK * 2
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 4])
    # find "   X "
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK * 3 + p["piece"] + BOARD_BLANK 
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1])
    # find "    X"
    for p in players:
        if p["piece"] != player["piece"]:
            piece = BOARD_BLANK * 4 + p["piece"] 
    result += getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, [0, 1, 2])  
    if result != []:
#        print "X:" + str(result)
        return result
    
    # step 9
    print "start!!!"
    return [[BOARD_LENTH / 2, BOARD_LENTH / 2]]
    
    
def getResult(boardRowString, boardColString, boardDiagonalString1, boardDiagonalString2, piece, num=[]):
    result = []
    indexs = []
    index = piece.find(BOARD_BLANK, 0)
    # get blank index
    while index != -1:
        if not (index in num):
            indexs.append(index)
        index = piece.find(BOARD_BLANK, index + 1)
    # ROW(-)
    start = boardRowString.find(piece, 0)
    while start != -1:
        for index in indexs:
#            print "row:" + str(start)
            result.append([(start - 1) % (BOARD_LENTH + 1) + index, (start - 1) / (BOARD_LENTH + 1)])
        start = boardRowString.find(piece, start + 1)
    # COLUMN(|)
    start = boardColString.find(piece, 0)
    while start != -1:
        for index in indexs:
#            print "col:" + str(start)
            result.append([(start - 1) / (BOARD_LENTH + 1), (start - 1) % (BOARD_LENTH + 1) + index])
        start = boardColString.find(piece, start + 1)
    # test ####
#    result = []
    # diagonal(\) up to down
    start = boardDiagonalString1.find(piece, 0)
    while start != -1:
        for index in indexs:
#            print "diagonal(\):" + str(start)
            if start < (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2):
                # 1 + 2 * i + i * (i - 1) / 2 = index
                # (n+1)(n+2)=2*x
                # (n+3/2)**2-1/4 = 2*x
                i = int(math.ceil((2 * (start + 1) + 0.25) ** 0.5 - 1.5))
                j = start - (2 * (i - 1) + (i - 1) * ((i - 1) - 1) / 2)
                result.append([j - 1 + index, BOARD_LENTH - i + j - 1 + index])
            else:
                start2 = start - (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2) + 1
                # BOARD_LENTH * i - i * (i - 1) / 2 = index2
                i = int(math.ceil(0.5 * (2 * BOARD_LENTH + 1) - ((0.5 * (2 * BOARD_LENTH + 1)) * (0.5 * (2 * BOARD_LENTH + 1)) - 2 * start2) ** 0.5))
                j = start2 - (BOARD_LENTH * (i - 1) - (i - 1) * ((i - 1) - 1) / 2)
                result.append([i + j - 1 + index, j - 1 + index])
        start = boardDiagonalString1.find(piece, start + 1)
    # DIAGONAL(/) up to down
    start = boardDiagonalString2.find(piece, 0)
    while start != -1:
        for index in indexs:
#            print "diagonal(/):" + str(start)
            if start < (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2):
                # 1 + 2 * i + i * (i - 1) / 2 = index
                # (n+1)(n+2)=2*x
                # (n+3/2)**2-1/4 = 2*x
                i = int(math.ceil((2 * (start + 1) + 0.25) ** 0.5 - 1.5))
                j = start - (2 * (i - 1) + (i - 1) * ((i - 1) - 1) / 2)
                result.append([i - j - index, j - 1 + index])
            else:
                start2 = start - (1 + BOARD_LENTH * 2 + BOARD_LENTH * (BOARD_LENTH - 1) / 2) + 1
                # BOARD_LENTH * i - i * (i - 1) / 2 = index2
                i = int(math.ceil(0.5 * (2 * BOARD_LENTH + 1) - ((0.5 * (2 * BOARD_LENTH + 1)) * (0.5 * (2 * BOARD_LENTH + 1)) - 2 * start2) ** 0.5))
                j = start2 - (BOARD_LENTH * (i - 1) - (i - 1) * ((i - 1) - 1) / 2)
                result.append([BOARD_LENTH - j - index, i + j - 1 + index])
        start = boardDiagonalString2.find(piece, start + 1)
    return result



board = init(BOARD_LENTH)
#showBoard(board)
print "=====GAME START====="
players = [{"name":"1", "piece":PIECE_PLAYER1, "AI":True}, {"name":"2", "piece":PIECE_PLAYER2, "AI":True}]
player = players[0]
showBoard(board)

while True:
    x = 0;y = 0
    if player["AI"]:
        locations = AI(board, player)
        location = locations[random.randint(0, len(locations) - 1)]
        y = int(location[0])
        x = int(location[1])
        time.sleep(1)
    else:
        action = raw_input("PLAYER " + player["name"] + "'s round, input x,y: ")
        location = action.replace(" ", "").split(",")
        try:
            y = int(location[0])
            x = int(location[1])
        except Exception, e:
            print "Warning, the coordinates must be two digits and ',' connections, e.g: 15,15"
            continue
        if x < 0 or y < 0 or x > BOARD_LENTH or y > BOARD_LENTH:
            print "Warning, coordinate must smaller than " + str(BOARD_LENTH) + "!"
            continue
    if board[x][y] != BOARD_BLANK:
        print "Warning, this location is not empty " + str(x) + " " + str(y)
        continue
    board[x][y] = player["piece"]
    showBoard(board)
    if isWin(board, x, y, player):
        showBoard(board)
        print "PLAYER " + player["name"] + " is win!"
        break
    player = changePlayer(player, players)
