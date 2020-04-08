from flask import current_app, Blueprint, redirect, render_template, request, flash, session, url_for
from datetime import timedelta
from modules.User.Login import *


urlUser = Blueprint('user', __name__)


@urlUser.route('/', methods=['GET', 'POST'])
def userIndexRedirect():
	return redirect('/User/User')


@urlUser.route('/download/<path:url>')
def userDownload(url):
	url2 = url.replace('/', '-')
	return redirect('/download/{}'.format(url2))


@urlUser.route('/login/', methods=['GET', 'POST'])
def userLogin():
	session.permanent = True
	# 设置session过期时间
	current_app.permanent_session_lifetime = timedelta(days=2)

	token = session.get('token')

	if request.method == 'GET':
		login = Login(token=token, ip=request.remote_addr, mode=request.method)
		if not login.tokenExist:
			session['token'] = login.token
			return render_template('urlUser/login.html', imgPath=login.checkCodeImgPath)
		else:
			if login.login:
				return redirect('/main/index')
			else:
				return render_template('urlUser/login.html', imgPath=login.checkCodeImgPath)

	elif request.method == 'POST':
		login = Login(token=token, ip=request.remote_addr, mode=request.method)
		login.judgeUser(user=request.form.get('user'), pwd=request.form.get('pwd'),
		                checkCode=request.form.get('checkCode'))
		if login.login:
			return redirect('/main/index')
		else:
			flash(login.errStr)
			if login.checkCodeErr:
				return render_template('urlUser/login.html', imgPath=login.checkCodeImgPath,
				                       user=request.form.get('user'), pwd=request.form.get('pwd'))
			else:
				return render_template('urlUser/login.html', imgPath=login.checkCodeImgPath,
				                       user=request.form.get('user'))

	else:
		return 'Not Found! '
