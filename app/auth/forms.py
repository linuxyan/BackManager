# -*- coding: UTF-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,validators
from wtforms.validators import DataRequired, Length,EqualTo, Email, DataRequired

class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField(u'记住我')

class UserEditForm(Form):
    username = StringField('username', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    oldpassword = PasswordField('oldpassword', validators=[DataRequired()])
    password = PasswordField('password', [validators.DataRequired(), EqualTo('password2', message=u'两次密码不一致')])
    password2 = PasswordField('Confirm password',validators=[DataRequired()])