import MySQLdb
import config, log

def createConnection():
    return MySQLdb.connect(host=config.DATABASE_IP, port=3306, db=config.DATABASE_DB_NAME, user=config.DATABASE_USER, passwd=config.DATABASE_PASSWORD)

def _insert(sql, isLog):
    try:
        if isLog:
            log.writeSQLLog(sql)
        conn = createConnection()
        cursor = conn.cursor()
        result = cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        if isLog:
            log.writeDbResultLog(result)
        return result
    except:
        log.writeErrorLog("SQL: " + sql)
        log.writeExceptionLog()
        return False

def _delete(sql, isLog):
    try:
        if isLog:
            log.writeSQLLog(sql)
        conn = createConnection()
        cursor = conn.cursor()
        result = cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        if isLog:
            log.writeDbResultLog(result)
        return result
    except:
        log.writeErrorLog("SQL: " + sql)
        log.writeExceptionLog()
        return False

def _update(sql, isLog):
    try:
        if isLog:
            log.writeSQLLog(sql)
        conn = createConnection()
        cursor = conn.cursor()
        result = cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        if isLog:
            log.writeDbResultLog(result)
        return result
    except:
        log.writeErrorLog("SQL: " + sql)
        log.writeExceptionLog()
        return False

def _select(sql, count, isLog):
    try:
        if isLog:
            log.writeSQLLog(sql)
        conn = createConnection()
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        if isLog:
            log.writeDbResultLog(result)
        if count == 1:
            if result != ():
                return result[0]
            else:
                return result
        elif count == -1:
            return result
        else:
            return result[0:count]
    except:
        log.writeErrorLog("SQL: " + sql)
        log.writeExceptionLog()
        return False

def insert(tbl_name, columns=[], values=[], isLog=True, userId=config.USER_ID):
    tbl_name = config.getDBName(tbl_name, userId)
    columnString = ""
    if columns != []:
        columnString = columns[0]
        for col in columns[1:]:
            columnString += ", " + col
    valueString = ""
    if values != []:
        val = values[0]
        if type(val) == str:
            val = "'" + val + "'"
        valueString += str(val)
        for val in values[1:]:
            if type(val) == str:
                val = "'" + val + "'"
            valueString += ", " + str(val)
    # SQL
    sql = "INSERT INTO " + tbl_name + "(" + columnString + ") VALUES(" + valueString + ")"
    return _insert(sql, isLog)

def delete(tbl_name, where={}, isLog=True, userId=config.USER_ID):
    tbl_name = config.getDBName(tbl_name, userId)
    whereString = ""
    if where != {}:
        columns = where.keys()
        value = where[columns[0]]
        if type(value) != list:
            if type(value) == str:
                value = "'" + value + "'"
            whereString += columns[0] + "=" + str(value)
        else:
            val = value[0]
            if type(val) == str:
                val = "'" + val + "'"
            valstring = str(val)
            for val in value[1:]:
                if type(val) == str:
                    val = "'" + val + "'"
                valstring += ", " + str(val)
            whereString += columns[0] + " in (" + valstring + ")"
        for col in columns[1:]:
            value = where[col]
            if type(value) != list:
                if type(value) == str:
                    value = "'" + value + "'"
                whereString += " and " + col + "=" + str(value)
            else:
                val = value[0]
                if type(val) == str:
                    val = "'" + val + "'"
                valstring = str(val)
                for val in value[1:]:
                    if type(val) == str:
                        val = "'" + val + "'"
                    valstring += ", " + str(val)
                whereString += " and " + col + " in (" + valstring + ")"
    # SQL
    sql = "DELETE FROM " + tbl_name
    if where != {}:
        sql += " WHERE " + whereString
    return _delete(sql, isLog)
#delete("test1", {"tid":[333, 222], "text":"ttt2"})

def update(tbl_name, set={}, where={}, isLog=True, userId=config.USER_ID):
    tbl_name = config.getDBName(tbl_name, userId)
    setString = ""
    if set != {}:
        columns = set.keys()
        value = set[columns[0]]
        if type(value) == str:
            if value == "":
                value = "''"
            else:
                value = "'" + str + "'"
        setString = columns[0] + "=" + str(value)
        for col in columns[1:]:
            value = set[col]
            if type(value) == str:
                value = "'" + value + "'"
            setString += ", " + col + "=" + str(value) 
    whereString = ""
    if where != {}:
        columns = where.keys()
        value = where[columns[0]]
        if type(value) != list:
            if type(value) == str:
                value = "'" + value + "'"
            whereString += columns[0] + "=" + str(value)
        else:
            val = value[0]
            if type(val) == str:
                val = "'" + val + "'"
            valstring = str(val)
            for val in value[1:]:
                if type(val) == str:
                    val = "'" + val + "'"
                valstring += ", " + str(val)
            whereString += columns[0] + " in (" + valstring + ")"
        for col in columns[1:]:
            value = where[col]
            if type(value) != list:
                if type(value) == str:
                    value = "'" + value + "'"
                whereString += " and " + col + "=" + str(value)
            else:
                val = value[0]
                if type(val) == str:
                    val = "'" + val + "'"
                valstring = str(val)
                for val in value[1:]:
                    if type(val) == str:
                        val = "'" + val + "'"
                    valstring += ", " + str(val)
                whereString += " and " + col + " in (" + valstring + ")"
    # SQL
    sql = "UPDATE " + tbl_name + " SET " + setString
    if where != {}:
        sql += " WHERE " + whereString
#    print sql
    return _update(sql, isLog)
#update("test1", {"tid":"900", "text":"test"}, {"tid":200, "id":200})

def select(tbl_name, columns=[], where={}, count=1, isLog=True, userId=config.USER_ID):
    tbl_name = config.getDBName(tbl_name, userId)
    columnString = ""
    if columns != []:
        columnString = columns[0]
        for col in columns[1:]:
            columnString += ", " + col
    else:
        columnString = "*"
    whereString = ""
    if where != {}:
        cols = where.keys()
        value = where[cols[0]]
        if type(value) != list:
            if type(value) == str:
                value = "'" + value + "'"
            whereString += cols[0] + "=" + str(value)
        else:
            val = value[0]
            if type(val) == str:
                val = "'" + val + "'"
            valstring = str(val)
            for val in value[1:]:
                if type(val) == str:
                    val = "'" + val + "'"
                valstring += ", " + str(val)
            whereString += cols[0] + " in (" + valstring + ")"
        for col in cols[1:]:
            value = where[col]
            if type(value) != list:
                if type(value) == str:
                    value = "'" + value + "'"
                whereString += " and " + col + "=" + str(value)
            else:
                val = value[0]
                if type(val) == str:
                    val = "'" + val + "'"
                valstring = str(val)
                for val in value[1:]:
                    if type(val) == str:
                        val = "'" + val + "'"
                    valstring += ", " + str(val)
                whereString += " and " + col + " in (" + valstring + ")"
    sql = "SELECT " + columnString + " FROM " + tbl_name
    if where != {}:
        sql += " WHERE " + whereString
    if len(columns) == 1:
        result = _select(sql, count, isLog)
        if result == ():
            return None
        if result:
            if count == 1:
                return result[0]
            else:
                tmpResult = []
                for re in result:
                    tmpResult.append(re[0])
                return tuple(tmpResult)
        else:
            return False
    else:
        result = _select(sql, count, isLog)
        if result == ():
            return None
        else:
            return result
