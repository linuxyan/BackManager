from . import db
from flask.ext.login import UserMixin
from . import login_manager
from werkzeug.security import generate_password_hash, check_password_hash


class users(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    useremail = db.Column(db.String(64))
    role  = db.Column(db.String(64),default='1')
    createtime = db.Column(db.DateTime)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<user %r>' % self.username

@login_manager.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))


class backhosts(db.Model):
    __tablename__ = 'backhosts'
    id = db.Column(db.Integer, primary_key=True)
    host_node = db.Column(db.String(64), index=True)
    ftp_ip = db.Column(db.String(64))
    ftp_port = db.Column(db.Integer)
    ftp_user = db.Column(db.String(64))
    ftp_pass = db.Column(db.String(64))
    customers = db.relationship('customers', backref='backhosts',passive_deletes=True)
    def __repr__(self):
        return '<host_node %r>' %self.hostname

class customers(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customers_name = db.Column(db.String(64))
    customers_short = db.Column(db.String(64))
    customers_user = db.Column(db.String(64))
    customers_pass = db.Column(db.String(64))
    customers_status = db.Column(db.Integer,default=0)
    mysqldump_path = db.Column(db.String(64))
    local_back_dir = db.Column(db.String(64))
    local_save = db.Column(db.Integer,default=0)
    db_ip = db.Column(db.String(64))
    db_port = db.Column(db.String(64))
    db_user = db.Column(db.String(64))
    db_pass = db.Column(db.String(64))
    db_name = db.Column(db.String(64))
    backhost_id = db.Column(db.Integer,db.ForeignKey('backhosts.id',ondelete='CASCADE', onupdate='CASCADE'))
    backarchives = db.relationship('backarchives', backref='customers',passive_deletes=True)

    def __repr__(self):
        return 'customer_ID %r' %self.id


class backarchives(db.Model):
    __tablename__ = 'backarchives'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer,db.ForeignKey('customers.id',ondelete='CASCADE', onupdate='CASCADE'))
    back_name = db.Column(db.String(128))
    back_ip = db.Column(db.String(128))
    back_path = db.Column(db.String(128))
    back_size = db.Column(db.String(128))
    back_time = db.Column(db.String(64))
    back_md5 = db.Column(db.String(64))

    def __repr__(self):
        return '<backarchives_ID %r>' %self.id

class config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64))
    value = db.Column(db.String(64))

    def __repr__(self):
        return '<Key %r>' %self.key

class backfailed(db.Model):
    __tablename__ = 'backfailed'
    id = db.Column(db.Integer, primary_key=True)
    count_date = db.Column(db.String(64))
    customer_name = db.Column(db.String(64))
    back_success = db.Column(db.String(64))
    back_failed = db.Column(db.String(64))
    def __repr__(self):
        return '<count_date %r>' %self.count_date

class count_day_status(db.Model):
    __tablename__ = 'count_day_status'
    id = db.Column(db.Integer, primary_key=True)
    count_date = db.Column(db.String(64))
    back_file_success = db.Column(db.Integer,default=0)
    back_customers_success = db.Column(db.Integer,default=0)
    back_file_failed = db.Column(db.Integer,default=0)
    back_customers_failed = db.Column(db.Integer,default=0)

    def __repr__(self):
        return '<count_date %r>' %self.count_date

class count_mon_status(db.Model):
    __tablename__ = 'count_mon_status'
    id = db.Column(db.Integer, primary_key=True)
    count_date = db.Column(db.String(64))
    back_customers = db.Column(db.Integer,default=0)
    back_customers_stop = db.Column(db.Integer,default=0)
    back_file = db.Column(db.Integer,default=0)

    def __repr__(self):
        return '<count_date %r>' %self.count_date