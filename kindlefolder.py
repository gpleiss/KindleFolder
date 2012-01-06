from __future__ import with_statement
import sys, os, string, random, MySQLdb, sendemail
import dropbox, oauth
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing


# Get configuration variables
from config import *


# Setup flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('KINDLEFOLDER_SETTINGS', silent=True)


def connect_db():
	return MySQLdb.connect(host=HOST, user=USERNAME, passwd=PASSWORD, db=DATABASE)


def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql') as f:
			db.cursor().executescript(f.read())
			
		
def dropbox_error(person_id=None):
	if person_id is not None:
		sql = '''delete from accounts
			where id='%s' ''' % (person_id)
		g.cur.execute(sql)
	return redirect(url_for('failure'))
	
	
def id_generator(size=30, chars=string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for i in range(size))
	

@app.before_request		
def before_request():
	g.db = connect_db()
	g.cur = g.db.cursor()
	
@app.teardown_request
def teardown_request(exception):
	g.db.close()
	



@app.route('/')
def index():
	return render_template('index.html')


@app.route('/add', methods=['POST'])
def add():
	global APP_KEY, APP_SECRET, ACCESS_TYPE
	
	# Add kindle email, personal email to the database - to add dropbox keys later
	kindle_email = request.form['kindle_email']
	personal_email = request.form['personal_email'] 
	sql = '''INSERT INTO accounts
		(app_key, app_secret, kindle_email, personal_email)
		VALUES ('%s', '%s', '%s', '%s');
		''' % (APP_KEY, APP_SECRET, kindle_email, personal_email)
	g.cur.execute(sql)
	g.cur.execute("SELECT @@IDENTITY")
	(person_id,) = g.cur.fetchone()
	
	
	# Get dropbox requtest token/url, redirect to confirm page
	try:
		sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
		request_token = sess.obtain_request_token()
		db_auth_url = sess.build_authorize_url(request_token)
		return redirect(url_for('confirm', person_id=person_id, request_token=request_token, db_auth_url=db_auth_url))
		
		
	except dropbox.rest.ErrorResponse:
		return dropbox_error(person_id)
	except dropbox.rest.RESTSocketError:
		return dropbox_error(person_id)
		
	
	
@app.route('/confirm', methods=['GET'])
def confirm():
	person_id = request.args.get('person_id')
	request_token = request.args.get('request_token')
	db_auth_url = request.args.get('db_auth_url')
	
	if (person_id or request_token or db_auth_url) is None:
		abort(400)
	else:
		return render_template('confirm.html', person_id=person_id, request_token=request_token, db_auth_url=db_auth_url)




@app.route('/confirm_add', methods=['POST'])
def confirm_add():
	global APP_KEY, APP_SECRET
	print "confirmed clicked"
	
	#read input
	person_id=request.form['person_id']
	request_token=request.form['request_token']
	
	try:
		sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, 'app_folder')
		request_token = oauth.oauth.OAuthToken.from_string(request_token)
		full_access_token = sess.obtain_access_token(request_token)
		access_secret = full_access_token.__str__()[19:34]
		access_token = full_access_token.__str__()[47:62]		
		
		sql = '''update accounts
			set access_secret='%s', access_token='%s'
			where id='%s'
			''' % (access_secret, access_token, person_id)
		g.cur.execute(sql)
		sql = '''select kindle_email, personal_email
			from accounts where id='%s'
			''' % (person_id)
		g.cur.execute(sql)
		(kindle_email, personal_email) = g.cur.fetchone()
		
		
		return redirect(url_for('success', kindle_email=kindle_email, personal_email=personal_email))
		
	except dropbox.rest.ErrorResponse:
		return dropbox_error(person_id)
	except dropbox.rest.RESTSocketError:
		return dropbox_error(person_id)
	
	
	
@app.route('/success', methods=['GET'])
def success():
	kindle_email = request.args.get('kindle_email')
	personal_email = request.args.get('personal_email')	
	if (kindle_email or personal_email) is None:
		abort(400)
	else:
		sendemail.mail_without_attach(personal_email, "Welcome to KindleFolder!","Welcome to KindleFolder's free service!<br /><br />Please complete the following instructions to complete setup. <ol><li>Go to Manage Your Kindle on Amazon.com or <a href='https://www.amazon.com/gp/digital/fiona/manage?ie=UTF8&ref_=ya_14&'>click here</a>.</li><li>Go to &quot;Personal Document Settings&quot;, then under the &quot;Approved Personal Document E-mail List&quot;, click &quot;Add a new approved e-mail address&quot;.</li><li>Enter &quot;unicorns@kindlefolder.us&quot; and then click &quot;Add Address&quot;. We like unicorns.</li><li>Within the &quot;Apps&quot; folder of your Dropbox, a new folder will appear called &quot;KindleFolder&quot;. Any file that a Kindle can open will automatically be sent to your Kindle! Please note that this service uses Amazon's Kindle Personal Document Service. Charges may apply for use over 3G.</li></ol><br />If you followed these directions, you should be good to go! Feel free to unsubscribe at any point by visiting <a href='http://www.kindlefolder.us/unsubscribe'>http://www.kindlefolder.us/unsubscribe</a>.<br /><br />Thanks!<br /><br />Chris and Geoff from KindleFolder")

		return render_template("success.html", kindle_email=kindle_email, personal_email=personal_email)
			
			
@app.route('/failure', methods=['GET'])
def failure():
	return render_template("failure.html");
			

@app.route('/unsubscribe', methods=['GET'])
def unsubscribe():
	return render_template("unsubscribe.html")
	
	
@app.route('/send_unsubscribe_email', methods=['POST'])
def send_unsubscribe_email():
	global ROOT
	personal_email = request.form['personal_email']
	
	sql = """ select id from accounts where personal_email='%s' """ % personal_email
	g.cur.execute(sql)
	results = g.cur.fetchall()
	if len(results) < 1:
		flash('Email was not found in our database', 'error')
		return render_template("unsubscribe.html")
	
	unsubscribe_token = id_generator()
	sql = """ update accounts set unsubscribe_token='%s' where personal_email='%s' """ % (unsubscribe_token, personal_email)
	g.cur.execute(sql)

	
	print url_for("remove", personal_email=personal_email, unsubscribe_token=unsubscribe_token)
	sendemail.mail_without_attach(personal_email, "Unsubscribe","Hello!<br /><br />You have requested to be unsubscribed from KindleFolder's service. Please click the link below to confirm. <br /><br />%s<br /><br />If you did not request to be unsubscribed, please ignore this email. If you keep receiving this email, please contact support@kindlefolder.us.<br /><br />Thanks!<br /><br />Chris and Geoff from KindleFolder" % (ROOT + url_for('remove', personal_email=personal_email, unsubscribe_token=unsubscribe_token)))
	return redirect(url_for("unsubscribe_email_sent", personal_email=personal_email))
	

@app.route('/unsubscribe_email_sent', methods=['GET'])
def unsubscribe_email_sent():
	personal_email = request.args.get('personal_email')	
	if personal_email is None:
		abort(400)
	else:
		return render_template("unsubscribe_email_sent.html", personal_email=personal_email)
	
	
@app.route('/remove', methods=['GET'])
def remove():
	personal_email = request.args.get('personal_email')
	unsubscribe_token = request.args.get('unsubscribe_token')
	if (personal_email or unsubscribe_token) is None:
		abort(400)
		
	sql = ''' select unsubscribe_token from accounts where personal_email='%s' ''' % personal_email
	g.cur.execute(sql)
	res = g.cur.fetchone()
	if (res is None) or (res[0] != unsubscribe_token):
		abort(400)
		
	sql = '''delete from accounts
			where personal_email='%s' ''' % (personal_email)
	g.cur.execute(sql)

	
	return redirect(url_for("unsubscribe_confirm", personal_email=personal_email))

	
@app.route('/unsubscribe_confirm', methods=['GET'])
def unsubscribe_confirm():
	personal_email = request.args.get('personal_email')	
	if personal_email is None:
		abort(400)
	else:
		return render_template("unsubscribe_confirm.html", personal_email=personal_email)
				

if __name__ == "__main__":
	app.run()
