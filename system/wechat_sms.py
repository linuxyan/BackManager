#!/usr/bin/python
#coding=utf-8
#__author__ = 'CY'

import datetime,MySQLdb,time
import json,urllib2

CorpID = "wx9b32a4b30268070a"
Secret='ZL74qB4Jd2L5fAC8lP4LdtXrshKj-vwCeWMawRSJjgKz00Gg_OGRsfhduNxo_4Ho'

def GetToken():
    tokenurl = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' %(CorpID,Secret)
    response = urllib2.urlopen(tokenurl)
    html = response.read().strip()
    ret = json.loads(html)
    if 'errcode' in ret.keys():
        print ret['errmsg']
        return 'Error'
    access_token = ret['access_token']
    return access_token

def SendMessage(Token,message):
    url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s' %Token
    values = {
       "touser": "",
       "toparty": "2",
       "totag": "",
       "msgtype": "text",
       "agentid": "2",
       "text": {
           "content": message
       },
       "safe":"0"
    }
    print values
    data = json.dumps(values,ensure_ascii=False)
    req = urllib2.Request(url, data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('encoding', 'utf-8')
    response = urllib2.urlopen(req)
    result = response.read().strip()
    print result
    result = json.loads(result)
    if result['errmsg'] == 'ok':
        return 'ok'
    else:
        return 'Error'

class DB():
    def __init__(self, DB_HOST, DB_PORT, DB_USER, DB_PWD, DB_NAME):
        self.DB_HOST = DB_HOST
        self.DB_PORT = DB_PORT
        self.DB_USER = DB_USER
        self.DB_PWD = DB_PWD
        self.DB_NAME = DB_NAME

        self.conn = self.getConnection()

    def getConnection(self):
        return MySQLdb.Connect(
                           host=self.DB_HOST,
                           port=self.DB_PORT,
                           user=self.DB_USER,
                           passwd=self.DB_PWD,
                           db=self.DB_NAME,
                           charset='utf8'
                           )

    def query(self, sqlString):
        cursor=self.conn.cursor()
        cursor.execute(sqlString)
        returnData=cursor.fetchall()
        cursor.close()
        return returnData

    def update(self, sqlString):
        cursor=self.conn.cursor()
        cursor.execute(sqlString)
        self.conn.commit()
        cursor.close()

    def close(self):
        self.conn.close()

if __name__=="__main__":
    cur_mon = str(time.strftime('%Y-%m',time.localtime(time.time())))
    yesterday = str(datetime.date.today()-datetime.timedelta(days=1))

    db=DB('127.0.0.1',3306,'backmanage','backmanage_pass','backmanage')
    yesterday_data = db.query("select * from count_day_status where count_date='%s'" %yesterday)
    cur_mon_file = db.query("select back_file from count_mon_status where count_date='%s'" %cur_mon)
    db.close()
    message = u'''备份管理平台每日统计
    -----------------------
    <a href="http://bk.rdops.top" color="#FF0000">http://bk.rdops.top</a>
    -----------------------
    昨日(%s)：
    备份成功文件数量：%s
    备份成功平台数量：%s
    <a color="#FF0000">备份失败文件数量：%s</a>
    <a color="#FF0000">备份失败平台数量：%s</a>
    -----------------------
    本月(%s)：
    备份备份文件总数：%s''' %(yesterday,yesterday_data[0][2],
                         yesterday_data[0][3],yesterday_data[0][4],yesterday_data[0][5],cur_mon,cur_mon_file[0][0])
    message = message.encode("utf8")
    Token = GetToken()
    SendMessage(Token,message)