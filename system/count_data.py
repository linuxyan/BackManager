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

    try:
        #预设每个平台每天备份5个文件为成功
        everyday_back_file = 5

        #count_day_status
        back_file_success = 0
        back_customers_success = 0
        back_file_failed = 0
        back_customers_failed = 0

        #count_mon_status
        back_customers_mon = 0
        back_customers_stop_mon = 0
        back_file_cur_mon = 0

        cur_mon = str(time.strftime('%Y-%m',time.localtime(time.time())))
        yesterday = str(datetime.date.today()-datetime.timedelta(days=1))

        db=DB('127.0.0.1',3306,'backmanage','backmanage_pass','backmanage')
        back_file_success = db.query("select count(*) from backarchives where DATE_FORMAT(back_time,'%%Y-%%m-%%d')='%s'" %yesterday)[0][0]
        #print back_file_success

        customer_id_list = db.query("select id from customers where customers_status = 0")
        for customer_id in customer_id_list:
            sql = "select count(*) from backarchives where customer_id=%s and DATE_FORMAT(back_time,'%%Y-%%m-%%d')='%s'" %(customer_id[0],yesterday)
            yesterday_back_file = db.query(sql)[0][0]
            if yesterday_back_file < everyday_back_file:
                cur_day_backfailed = everyday_back_file-yesterday_back_file
                back_file_failed = back_file_failed+cur_day_backfailed
                customer_name = db.query("select * from customers where id=%s"%customer_id[0])[0][1]
                sql = "insert into backfailed(count_date,customer_name,back_success,back_failed) values('%s','%s','%s','%s')" %(yesterday,customer_name,yesterday_back_file,cur_day_backfailed)
                #print sql
                db.update(sql)
            else:
                back_customers_success = back_customers_success+1

        sql = "select count(*) from backfailed where count_date = '%s'" %yesterday
        #print sql
        back_customers_failed = db.query(sql)[0][0]
        sql = "insert into count_day_status(count_date,back_file_success,back_customers_success,back_file_failed,back_customers_failed) " \
              "values('%s',%s,%s,%s,%s)" %(yesterday,back_file_success,back_customers_success,back_file_failed,back_customers_failed)
        #print sql
        db.update(sql)

        back_customers_mon = db.query("select count(*) from customers where customers_status=0")[0][0]
        back_customers_stop_mon = db.query("select count(*) from customers where customers_status=1")[0][0]
        back_file_cur_mon = db.query("select count(*) from backarchives where DATE_FORMAT(back_time,'%%Y-%%m')='%s'" %cur_mon)[0][0]

        cur_mon_count = db.query("select id from count_mon_status where count_date='%s'" %cur_mon)
        if cur_mon_count:
            cur_mon_id = cur_mon_count[0][0]
            sql = "update count_mon_status set back_customers=%s,back_customers_stop=%s,back_file=%s where id=%s" %(back_customers_mon,back_customers_stop_mon,back_file_cur_mon,cur_mon_id)
            #print sql
            db.update(sql)
        else:
            sql = "insert into count_mon_status(count_date,back_customers,back_customers_stop,back_file) " \
                  "values('%s',%s,%s,%s)" %(cur_mon,back_customers_mon,back_customers_stop_mon,back_file_cur_mon)
            #print sql
            db.update(sql)

        db.close()
    except Exception as e:
        message = u'备份管理系统(BackManage)数据统计失败！错误信息：'+e.message
        message = message.encode("utf8")
        Token = GetToken()
        SendMessage(Token,message)