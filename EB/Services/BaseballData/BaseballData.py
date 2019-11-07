import pymysql
from operator import itemgetter
import json
from Context.Context import Context
import DataAccess.DataAdaptor as data_adaptor

_context = Context.get_default_context()
connect_info = _context.get_context("lahman_db_connect_info")
cnx, cur = data_adaptor.get_connection_and_cursor(connect_info=connect_info)
# cnx = pymysql.connect(host='localhost',
#                               user='dbuser',
#                               password='dbuser',
#                               db='lahman2017',
#                               charset='utf8mb4',
#                               cursorclass=pymysql.cursors.DictCursor)


def run_q(q, args, fetch=False):
    global cur
    global cnx
    cur.execute(q, args)
    if fetch:
        result = cur.fetchall()
    else:
        result = None
    cnx.commit()
    return result

def get_key_columns(table):
    # This is MySQL specific and relies on the fact that MySQL returns the keys in
    # based on seq_in_index
    q = "show keys from " + table + " WHERE Key_name = 'PRIMARY'"

    result = run_q(q, None, True)
    keys = [(r['Column_name'], r['Seq_in_index']) for r in result]
    keys = sorted(keys, key=itemgetter(1))
    keys = [k[0] for k in keys]
    return keys


def find_by_related_resource(table, rel_table, primary_key, in_args=None, fields=None):
    keys = primary_key.split('_')
    cnt = 0
    for k in keys:
        keys[cnt] = [k]
        cnt += 1

    key_columns = get_key_columns(table)
    key_columns2= get_key_columns(rel_table)
    tmp = dict(zip(key_columns, keys))

    for key in list(tmp.keys()):
        if key not in key_columns2:

            del(tmp[key])

    tmp1=tmp
    if in_args is not None:
        tmp.update(in_args)


    result= find_by_template(rel_table, tmp, fields)
    return result, tmp1


def find_by_primary_key(table, primary_key, fields=None):
    keys = primary_key.split('_')
    cnt = 0
    for k in keys:
        keys[cnt] = [k]
        cnt += 1

    key_columns = get_key_columns(table)

    tmp = dict(zip(key_columns, keys))

    result= find_by_template(table, tmp, fields)
    return result, tmp

def find_by_template(table, template, fields=None):
    WC = template_to_where_clause(template)
    if fields is not None:
        q = "select "+ fields[0] +" from " + table + " " + WC
    else:
        q = "select * from " + table + " " + WC

    result = run_q(q, None, True)
    return result


def template_to_where_clause(t):
        s = ""

        if t is None:
            return s

        for (k, v) in t.items():
            if s != "":
                s += " AND "
            s += k + "='" + v[0] + "'"

        if s != "":
            s = "WHERE " + s;

        return s


def insert(table, row):
    keys = row.keys()
    q = "INSERT into " + table + " "
    s1 = list(keys)
    s1 = ",".join(s1)

    q += "(" + s1 + ") "

    v = ["%s"] * len(keys)
    v = ",".join(v)

    q += "values(" + v + ")"

    params = tuple(row.values())

    result = run_q(q, params, False)

def delete(table, template):
    # I did not call run_q() because it commits after each statement.
    # I run the second query to get row_count, then commit.
    # I should move some of this logic into run_q to handle getting
    # row count, running multiple statements, etc.
    where_clause = template_to_where_clause(template)
    q1 = "delete from " + table + " " + where_clause + ";"
    q2 = "select row_count() as no_of_rows_deleted;"
    cursor = cnx.cursor()
    cursor.execute(q1)
    cursor.execute(q2)
    result = cursor.fetchone()
    cnx.commit()


    return result

def add_limit_offset(result,url,limit,offset,fields,in_args):
    L=len(result)
    data={'data':result[offset:(offset+limit)]}
    q=''
    if in_args is not None:
        q='?'
        for key in list(in_args.keys()):
            q=q+key+'='+in_args[key][0]+'&'
    if fields is not None:
        if q=='':
            q='?fields='+fields[0]+'&'
        else:
            q=q+'fields='+fields[0]+'&'
    if q=='':
        off='?offset='
    else:
        off='offset='
    url=url+q
    if offset==0:
        prelink={'previous':'None'}
    elif offset-limit<0:
        offsetp=0
        limitp=offset-1
        prelink={'previous': url + off + str(offsetp) + '&limit=' + str(limitp)}
    elif offset - limit > 0:
        offsetp = offset-limit
        prelink = {'previous': url + off + str(offsetp) + '&limit=' + str(limit)}
    elif offset-limit==0:
        offsetp=0
        limitp=limit
        prelink={'previous': url + off + str(offsetp) + '&limit=' + str(limitp)}
    if offset+limit>L:
        nexlink = {'next':'None'}
    else:
        nexlink={'next': url + off + str(offset+limit) + '&limit=' + str(limit)}
    links={'links':[{'current':url + off +str(offset)+'&limit='+str(limit)},nexlink,prelink]}

    data.update(links)

    return data


def find_teammates(playerID):
    q1 = "select distinct teamID,yearID from appearances where playerID='" + playerID + "'"
    tny = run_q(q1, None, True)

    WC =''
    for row in tny:
        WC = WC +" or (teamID='" + row['teamID']+"' and yearID='"+str(row['yearID'])+"')"
    WC =WC[3:]
    WC ="where"+WC
    q2="SELECT playerID,(SELECT People.nameFirst FROM People WHERE people.playerID=appearances.playerID) as first_name,\
    (SELECT People.nameLast FROM People WHERE people.playerID=appearances.playerID) as last_name,\
    min(yearID) as first_year,max(yearID) as last_year,COUNT(*) as count FROM appearances "+WC+" GROUP BY playerID ORDER BY playerID ASC;"

    print(q2)
    result = run_q(q2, None, True)
    return result
    #     years=years+","+str(row['yearID'])
    #     teams=teams+",'"+row['teamID']+"'"
    # years=years[1:]
    # teams = teams[1:]
    # print(years)
    # print(teams)

def find_career_stats(playerID):
    q1 = "select distinct teamID,yearID from appearances where playerID='" + playerID + "';"
    tny = run_q(q1, None, True)

    WC = ''
    for row in tny:
        WC = WC + " or (appearances.teamID='" + row['teamID'] + "' and appearances.yearID='" + str(row['yearID']) +\
             "' and batting.teamID='" + row['teamID'] + "' and batting.yearID='" + str(row['yearID'])+\
             "' and fielding.teamID='" + row['teamID'] + "' and fielding.yearID='" + str(row['yearID'])+"')"
    WC = WC[3:]

    q="SELECT fielding.playerID,fielding.teamID,fielding.yearID,G_all, H, AB, A, E, pos from appearances,fielding,batting where appearances.playerID='"\
      +playerID+"' and fielding.playerID='"+playerID+"' and batting.playerID='"+playerID+"' and ("+WC+")ORDER BY pos;"
    print(q)
    result = run_q(q, None, True)
    return result


def find_roster(in_args):
    team=in_args['teamID'][0]
    year=in_args['yearID'][0]
    q1="SELECT DISTINCT playerID from appearances where teamID='"+team+"' and yearID='"+year+"';"
    tny = run_q(q1, None, True)
    WC = ''
    for row in tny:
        WC = WC + " or (appearances.playerID='" + row['playerID'] + "' and batting.playerID='" + row['playerID'] + \
             "' and fielding.playerID='" + row['playerID'] + "')"
    WC = WC[3:]

    q="SELECT (SELECT People.nameFirst FROM People WHERE people.playerID=appearances.playerID) as first_name,\
    (SELECT People.nameLast FROM People WHERE people.playerID=appearances.playerID) as last_name,\
    appearances.playerID,appearances.teamID,appearances.yearID,G_all,H,AB,A,E,pos \
    from appearances,fielding,batting where appearances.teamID='"+team+"' and appearances.yearID='"+year+"'\
     and fielding.teamID='"+team+"' and fielding.yearID='"+year+"'and batting.teamID='"+team+"' and batting.yearID='"+year+"' and ("+WC+") ORDER BY last_name ASC;"

    print(q)
    result = run_q(q, None, True)
    return result