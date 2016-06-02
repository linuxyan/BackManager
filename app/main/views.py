#!/usr/bin/python
# coding=utf-8
#__author__ = 'CY'
from flask import  render_template, request, flash,abort,redirect,url_for
from flask.ext.login import login_required, current_user
from . import main
from .. import db
from sqlalchemy import and_,desc,or_
from app.models import users,backhosts,customers,backarchives,config,backfailed,count_day_status,count_mon_status
from config import Config
import os,json,string,datetime
from random import choice
import py_compile

def GenPassword(length=8,chars=string.ascii_letters+string.digits):
    return ''.join([choice(chars) for i in range(length)])


@main.route('/',methods=['GET', 'POST'])
@login_required
def index():
    yesterday = str(datetime.date.today()-datetime.timedelta(days=1))
    day_count = count_day_status.query.filter_by(count_date=yesterday).first()
    if day_count:
        back_success_file =day_count.back_file_success
        back_customers_success =day_count.back_customers_success
        back_file_failed =day_count.back_file_failed
        back_customers_failed =day_count.back_customers_failed
    else:
        back_success_file =0
        back_customers_success =0
        back_file_failed =0
        back_customers_failed =0

    mon_count = count_mon_status.query.order_by(desc(count_mon_status.id)).limit(12).all()
    customer_count = []
    customer_count_customer = []
    customer_count_file = []
    for mon_item in mon_count:
        mon_dict = {'y':str(mon_item.count_date),'a':str(mon_item.back_customers),'b':str(mon_item.back_customers_stop)}
        mon_dict_customer = {'period':str(mon_item.count_date),'platform':str(mon_item.back_customers)}
        mon_dict_file = {'period':str(mon_item.count_date),'file':str(mon_item.back_file)}
        customer_count.append(mon_dict)
        customer_count_customer.append(mon_dict_customer)
        customer_count_file.append(mon_dict_file)
    customer_count = customer_count[::-1]
    customer_count_customer = customer_count_customer[::-1]
    customer_count_file = customer_count_file[::-1]

    yes_backfailed = backfailed.query.filter_by(count_date=yesterday).order_by(desc(backfailed.back_failed)).limit(4).all()
    for i in range(0,int(4-len(yes_backfailed))):
        yes_backfailed.append(0)
    return render_template('index.html',back_success_file=back_success_file,back_customers_success=back_customers_success,
                           back_file_failed=back_file_failed,back_customers_failed=back_customers_failed,
                           customer_count=str(customer_count),customer_count_customer=str(customer_count_customer),
                           customer_count_file=str(customer_count_file),yes_backfailed=yes_backfailed)


@main.route('/build_config/',methods=['GET', 'POST'])
@login_required
def build_config():
    if request.method == 'POST':
        customers_name = request.form['customers_name']
        customers_short = request.form['customers_short']
        mysqldump_path = request.form['mysqldump_path']
        local_back_dir = request.form['local_back_dir']
        local_save = request.form['local_save']
        db_ip = request.form['db_ip']
        db_port = request.form['db_port']
        db_user = request.form['db_user']
        db_pass = request.form['db_pass']
        db_name = request.form['db_name']

        customer = customers.query.filter(or_(customers.customers_name==customers_name,customers.customers_short==customers_short
                                                 ,customers.db_name==db_name)).all()
        if customer:
            flash(u'%s平台 添加记录失败,客户名称/数据库名称已存在!' %customers_name)
            backhost = backhosts.query.all()
            return render_template('customeradd.html',back_hosts=backhost)

        backhost_id = int(request.form['backhost_id'])
        random_pass = GenPassword()
        customer = customers(customers_name=customers_name,customers_short=customers_short,customers_user=customers_short,
                             customers_pass=random_pass,mysqldump_path=mysqldump_path,local_back_dir=local_back_dir,
                             db_ip=db_ip,db_port=db_port,db_user=db_user,db_pass=db_pass,db_name=db_name,
                             backhost_id=backhost_id,local_save=local_save)
        db.session.add(customer)
        db.session.commit()
        config_url = config.query.filter_by(key='apiurl').first()
        config_apipath = config.query.filter_by(key='apipath').first()
        config_apiport = config.query.filter_by(key='apiport').first()
        config_CorpID = config.query.filter_by(key='CorpID').first()
        config_Secret = config.query.filter_by(key='Secret').first()

        config_dict = {'apiurl':config_url.value,'apipath':config_apipath.value,'apiport':int(config_apiport.value),
                       'mysql_dump':mysqldump_path,'mysql_host':db_ip,'mysql_port':db_port,
                       'mysql_user':db_user,'mysql_pass':db_pass,'database_name':db_name,
                       'backup_dir':local_back_dir,'customers_user':customers_short,'customers_pass':random_pass,
                       'CorpID':config_CorpID.value,'Secret':config_Secret.value}
        print config_dict
        back_code = open(Config.back_script).read()
        code_string = string.Template(back_code)
        pro_code = code_string.substitute(config_dict)
        scripts_dir = Config.scripts_dir
        print scripts_dir,customers_short
        config_file_dir = os.path.join(scripts_dir,customers_short)
        if not os.path.exists(config_file_dir):
            os.mkdir(config_file_dir)
        customers_back_file = customers_short + '_Backup_Mysql.py'
        customers_back_file = os.path.join(config_file_dir,customers_back_file)
        output = open(customers_back_file,'w')
        output.write(pro_code)
        output.close()
        py_compile.compile(customers_back_file)
        return redirect(request.url_root+str(customers_back_file+'c').split('BackManage')[1])
    else:
        backhost = backhosts.query.all()
        return render_template('customeradd.html',back_hosts=backhost)


@main.route('/set_config/',methods=['GET', 'POST'])
@login_required
def set_config():
    if request.method == 'POST':
        try:
            apiurl = request.form['apiurl']
            apipath = request.form['apipath']
            apiport = request.form['apiport']
            CorpID = request.form['CorpID']
            Secret = request.form['Secret']
            apiurl_obj = config.query.filter_by(key='apiurl').first()
            apiurl_obj.value = apiurl
            apipath_obj = config.query.filter_by(key='apipath').first()
            apipath_obj.value = apipath
            apiport_obj = config.query.filter_by(key='apiport').first()
            apiport_obj.value = apiport
            CorpID_obj = config.query.filter_by(key='CorpID').first()
            CorpID_obj.value = CorpID
            Secret_obj = config.query.filter_by(key='Secret').first()
            Secret_obj.value = Secret
            db.session.add(apiurl_obj)
            db.session.add(apipath_obj)
            db.session.add(apiport_obj)
            db.session.add(CorpID_obj)
            db.session.add(Secret_obj)
            db.session.commit()
        except Exception as e:
            print e.message
            flash(u'系统设置更新失败!')
            return redirect(url_for('main.set_config'))
        flash(u'系统设置更新成功!')
        return redirect(url_for('main.set_config'))
    else:
        try:
            config_url = config.query.filter_by(key='apiurl').first().value
            config_apipath = config.query.filter_by(key='apipath').first().value
            config_apiport = config.query.filter_by(key='apiport').first().value
            config_CorpID = config.query.filter_by(key='CorpID').first().value
            config_Secret = config.query.filter_by(key='Secret').first().value
            return render_template('config.html',apiurl=config_url,apipath=config_apipath,apiport=config_apiport,
                                   CorpID=config_CorpID,Secret=config_Secret)
        except Exception as e:
            print e.message
            return render_template('config.html')


@main.route('/api/', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
       operation = request.form['operation']
       if operation == 'auth':
           auth_user = request.form['user']
           auth_pass = request.form['pass']
           customer = customers.query.filter(and_(customers.customers_user==auth_user,customers.customers_pass==auth_pass,customers.customers_status==0)).first()
           if customer:
               back_host = backhosts.query.filter_by(id=customer.backhost_id).first()
               data = {'auth':'ok','customer_name':customer.customers_name,'ftp_ip':back_host.ftp_ip,'ftp_port':int(back_host.ftp_port),'local_save':customer.local_save,
                       'ftp_user':back_host.ftp_user,'ftp_pass':back_host.ftp_pass,'ftp_dir':customer.customers_short}
               return json.dumps(data)
       elif operation == 'upload_info':
           md5 = request.form['md5']
           customer_short = request.form['name']
           upload_ip = request.form['upload_ip']
           upload_path = request.form['upload_path']
           upload_name = request.form['upload_name']
           upload_time = request.form['upload_time']
           upload_size = request.form['upload_file_size']
           customer = customers.query.filter_by(customers_short=customer_short).first()
           backarchive = backarchives(customer_id=customer.id,back_name=upload_name,back_ip=upload_ip,back_path=upload_path,
                                      back_time=upload_time,back_md5=md5,back_size=upload_size)
           db.session.add(backarchive)
           db.session.commit()
           data =  {'backup_info':'ok'}
           return json.dumps(data)
    else:
        data = {'status':'ok'}
        return json.dumps(data)


@main.route('/add_backnode/',methods=['GET', 'POST'])
@login_required
def add_backnode():
    if request.method == 'POST':
        node_name = request.form['node_name']
        ftp_ip = request.form['ftp_ip']
        ftp_port = request.form['ftp_port']
        ftp_user = request.form['ftp_user']
        ftp_pass = request.form['ftp_pass']
        back_node = backhosts.query.filter(or_(backhosts.host_node==node_name,backhosts.ftp_ip==ftp_ip)).all()
        if back_node:
            flash(u'%s 节点已经存在，请勿重复添加!' %node_name)
            return render_template('addbacknode.html')
        backhost = backhosts(host_node=node_name,ftp_ip=ftp_ip,ftp_port=ftp_port,ftp_user=ftp_user,ftp_pass=ftp_pass)
        db.session.add(backhost)
        db.session.commit()
        flash(u'%s 节点添加成功!' %node_name)
        return render_template('addbacknode.html')
    else:
        return render_template('addbacknode.html')

@main.route('/backnode/',methods=['GET', 'POST'])
def backnode():
    if request.method == 'POST':
        pass
    else:
        backnodes = backhosts.query.all()
        return render_template('backnode.html',backnodes=backnodes)

@main.route('/backmanage/',methods=['GET', 'POST'])
@login_required
def backmanage():
    if request.method == 'POST':
        pass
    else:
        backarchive_all = backarchives.query.order_by(desc(backarchives.id)).all()
        return render_template('backarchives.html',backarchives=backarchive_all)

@main.route('/customer/',methods=['GET', 'POST'])
@login_required
def customer():
    if request.method == 'POST':
        try:
            customer_id = request.form['customer_id']
            customer_oper = request.form['customer_oper']
            customer = customers.query.filter_by(id=customer_id).first()
            if customer_oper == 'stop_back':
                customer.customers_status = 1
            else:
                customer.customers_status = 0
            db.session.add(customer)
            db.session.commit()
            return u"更新状态成功！"
        except Exception, e:
            print e
            return u"更新状态失败！"
    else:
        customer_all = customers.query.all()
        return render_template('customers.html',customers=customer_all)

@main.route('/failed_customer/',methods=['GET', 'POST'])
@login_required
def failed_customer():
    backfaileds = backfailed.query.order_by(desc(backfailed.count_date)).all()
    return render_template('backfailed.html',backfaileds=backfaileds)

@main.route('/help/',methods=['GET', 'POST'])
@login_required
def help():
    return render_template('help.html')