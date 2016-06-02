#!/usr/bin/python
#coding=utf-8
#__author__ = 'CY'
import httplib, urllib,urllib2,json
from ftplib import FTP
import os,time,sys
import hashlib,zipfile
api_url = '$apiurl'
api_path = '$apipath'
api_port = '$apiport'

mysql_dump = '$mysql_dump'
mysql_host = '$mysql_host'
mysql_port = '$mysql_port'
mysql_user = '$mysql_user'
mysql_pass = '$mysql_pass'
database_name = '$database_name'
backup_dir = '$backup_dir'

customers_user = '$customers_user'
customers_pass = '$customers_pass'

CorpID = "$CorpID"
Secret='$Secret'

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

def request_api(params_dict):
    httpClient = None
    try:
        params = urllib.urlencode(params_dict)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        httpClient = httplib.HTTPConnection(api_url, int(api_port), timeout=5)
        httpClient.request("POST", api_path, params, headers)
        response = httpClient.getresponse()
        status = response.status
        if str(status) != '200':
            data = {'status':500,'auth':'failed'}
        else:
            data = eval(response.read())
            data['status'] = status
        return data
    except Exception, e:
        print e
        data = {'status':500,'auth':'failed'}
        return data
    finally:
        if httpClient:
            httpClient.close()

def md5sum(file):
    m = hashlib.md5()
    n = 1024*4
    inp = open(file,'rb')
    while True:
        buf = inp.read(n)
        if buf:
            m.update(buf)
        else:
            break
    return m.hexdigest()

def backup_mysql():
    try:
        back_file_name = database_name+time.strftime("%Y%m%d_%H%M%S", time.localtime())
        back_file_path = os.path.join(backup_dir,back_file_name)
        backup_command= '%s -h%s -P%d -u%s  -p%s --default-character-set=utf8 %s  > %s'\
                        %(mysql_dump,mysql_host,int(mysql_port),mysql_user,mysql_pass,database_name,back_file_path)
        if os.system(backup_command) == 0:
            zip_file_path = back_file_path+'.zip'
            f = zipfile.ZipFile(zip_file_path, 'w' ,zipfile.ZIP_DEFLATED,allowZip64=True)
            f.write(back_file_path,back_file_name)
            f.close()
            md5_num = str(md5sum(zip_file_path))
            md5_file_path = zip_file_path+'_'+md5_num
            back_file_new_path = os.path.join(backup_dir,md5_file_path)
            os.rename(zip_file_path,back_file_new_path)
            os.remove(back_file_path)
            data = {'status':'back_success','file_path':back_file_new_path,'md5':md5_num}
            return data
        else:
            data = {'status':'back_failed'}
            return data
    except Exception, e:
        print e
        data = {'status':'back_failed'}
        return data


def upload_ftp(customer_name,ftp_ip,ftp_user,ftp_pass,ftp_dir,ftp_port,timeout,localfile):
    ftp = FTP()
    try:
        ftp.connect(ftp_ip,ftp_port,timeout)
        ftp.login(ftp_user,ftp_pass)
    except:
        print 'login error'
        message = u'%s MySQLDB %s FTP login failed!' %(ftp_dir,database_name)
        message = message.encode("utf8")
        Token = GetToken()
        SendMessage(Token,message)
        sys.exit()
    date_dir = time.strftime("%Y-%m-%d", time.localtime())
    date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    upload_dir = os.path.join(ftp_dir,date_dir)
    dir_list = ftp.nlst()
    try:
        if ftp_dir in dir_list:
            ftp.cwd(ftp_dir)
        else:
            ftp.mkd(ftp_dir)
            ftp.cwd(ftp_dir)
        date_dir_list = ftp.nlst()
        if date_dir in date_dir_list:
            ftp.cwd(date_dir)
        else:
            ftp.mkd(date_dir)
            ftp.cwd(date_dir)
    except Exception, e:
        print 'U have no authority to make dir'
        message = u'%s MySQLDB %s FTP dir Error!' %(ftp_dir,database_name)
        message = message.encode("utf8")
        Token = GetToken()
        SendMessage(Token,message)
        sys.exit()
    try:
        bufsize = 1024
        file_handler = open(localfile,'rb')
        ftp.storbinary('STOR %s' % os.path.basename(localfile),file_handler,bufsize)
        file_handler.close()
        ftp.quit()
        data = {'status':'upload_success','ftp_ip':ftp_ip,'upload_path':upload_dir,
                'file_name':os.path.basename(localfile),'upload_time':date_time}
        return data
    except Exception, e:
        print e.message
        message = u'%s MySQLDB %s FTP upload failed!' %(ftp_dir,database_name)
        message = message.encode("utf8")
        Token = GetToken()
        SendMessage(Token,message)
        sys.exit()


def main():
    print 'start backup mysql...'
    back_result = backup_mysql()

    params_dict = {'operation':'auth','user':customers_user,'pass':customers_pass}
    auth_result = request_api(params_dict)
    print 'Auth ftp server...'
    #print auth_result
    if auth_result['auth'] != 'ok':
        print 'auth failed! Exit...'
        sys.exit()
    print 'Auth success!'

    if back_result['status'] != 'back_success':
        message = u'%s MySQLDB %s backup failed!' %(str(auth_result['ftp_dir']),database_name)
        message = message.encode("utf8")
        Token = GetToken()
        SendMessage(Token,message)
        sys.exit()
    print 'backup mysql success,uploading backup ftp server...'

    local_back_file = back_result['file_path']
    upload_result = upload_ftp(str(auth_result['customer_name']),str(auth_result['ftp_ip']),str(auth_result['ftp_user'])
                               ,str(auth_result['ftp_pass']),str(auth_result['ftp_dir']),str(auth_result['ftp_port'])
                               ,timeout=30,localfile=str(local_back_file))
    if upload_result and upload_result['status'] == 'upload_success':
        print 'uploading ftp success,uploading backup info to API.'
        upload_file_size = '%.2f' %(os.path.getsize(local_back_file)/1024/1024.00)
        if str(auth_result['local_save']) == "1":
            os.remove(local_back_file)
        params_dict['operation'] = 'upload_info'
        params_dict['name'] = auth_result['ftp_dir']
        params_dict['md5'] = back_result['md5']
        params_dict['upload_file_size'] =upload_file_size
        params_dict['upload_ip'] = upload_result['ftp_ip']
        params_dict['upload_path'] = upload_result['upload_path']
        params_dict['upload_name'] = upload_result['file_name']
        params_dict['upload_time'] = upload_result['upload_time']
        archive_result = request_api(params_dict)
        print archive_result


if __name__ == '__main__':
    main()
