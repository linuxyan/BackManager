#coding=utf-8
from flask import render_template, redirect, request, url_for, flash,abort
from . import auth
from ..models import users
from .. import db
from .forms import LoginForm,UserEditForm
from flask.ext.login import login_user, logout_user,current_user
from flask.ext.login import login_required

@auth.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = users.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('login.html',form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/upuser/<int:userid>', methods=['GET','POST'])
@login_required
def upuser(userid):
    if current_user.id == userid or current_user.role == '0':
        form = UserEditForm()
        if form.validate_on_submit():
            user = users.query.filter_by(id=userid).first()
            if user is not None and user.verify_password(form.oldpassword.data):
                user.password = form.password.data
                db.session.add(user)
                db.session.commit()
                flash(u'密码更改成功!')
                return render_template('useredit.html',form=form)

        user = users.query.filter_by(id=userid).first()
        form.username.data = user.username
        form.name.data = user.name
        return render_template('useredit.html',form=form)
    else:
        abort(403)