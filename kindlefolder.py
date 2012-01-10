from __future__ import with_statement
import sys, os, sendemail
import dropbox, oauth
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing
from person import Person

# Get configuration variables
from config import *


# Setup flask
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('KINDLEFOLDER_SETTINGS', silent=True)


			
	

@app.before_request		
def before_request():
	g.db = Person.connect_db()
	
	
@app.teardown_request
def teardown_request(exception):
	g.db.close()
	

def dropbox_error(person_id=None):
	if person_id is not None:
		Person.find(person_id).destroy()
	return redirect(url_for('failure'))
	
	



@app.route('/')
def index():
	return render_template('index.html')


@app.route('/add', methods=['POST'])
def add():
	global APP_KEY, APP_SECRET, ACCESS_TYPE
	
	# Add kindle email, personal email to the database - to add dropbox keys later
	kindle_email = request.form['kindle_email']
	personal_email = request.form['personal_email'] 
	p = Person.new(kindle_email=kindle_email, personal_email=personal_email)
	
	# Get dropbox requtest token/url, redirect to confirm page
	try:
		sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
		request_token = sess.obtain_request_token()
		db_auth_url = sess.build_authorize_url(request_token)
		return redirect(url_for('confirm', person_id=p.person_id, request_token=request_token, db_auth_url=db_auth_url))
		
	# If an error occured with dropbox, remove new entry from database, prompt user to try again
	except dropbox.rest.ErrorResponse:
		return dropbox_error(p.person_id)
	except dropbox.rest.RESTSocketError:
		return dropbox_error(p.person_id)
		
	
@app.route('/confirm', methods=['GET'])
def confirm():
	# Make sure necessary parameters are in url
	person_id = request.args.get('person_id')
	request_token = request.args.get('request_token')
	db_auth_url = request.args.get('db_auth_url')
	if person_id is None or request_token is None or db_auth_url is None:
		abort(400)
		
	else:
		return render_template('confirm.html', person_id=person_id, request_token=request_token, db_auth_url=db_auth_url)
		

@app.route('/confirm_add', methods=['POST'])
def confirm_add():
	global APP_KEY, APP_SECRET
	person_id = int(request.form['person_id'])
	request_token = request.form['request_token']
	
	# Obtain access tokens from dropbox, and add them to the associated account in the database
	try:
		sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, 'app_folder')
		request_token = oauth.oauth.OAuthToken.from_string(request_token)
		full_access_token = sess.obtain_access_token(request_token)
		
		p = Person.find(person_id)
		p.access_secret = full_access_token.__str__()[19:34]
		p.access_token = full_access_token.__str__()[47:62]		
		p.save()
		
		# Send success notification email to newly added user
		sendemail.mail_without_attach(p.personal_email, "Welcome to KindleFolder!","Welcome to KindleFolder's free service!<br /><br />Please complete the following instructions to complete setup. <ol><li>Go to Manage Your Kindle on Amazon.com or <a href='https://www.amazon.com/gp/digital/fiona/manage?ie=UTF8&ref_=ya_14&'>click here</a>.</li><li>Go to &quot;Personal Document Settings&quot;, then under the &quot;Approved Personal Document E-mail List&quot;, click &quot;Add a new approved e-mail address&quot;.</li><li>Enter &quot;unicorns@kindlefolder.us&quot; and then click &quot;Add Address&quot;. We like unicorns.</li><li>Within the &quot;Apps&quot; folder of your Dropbox, a new folder will appear called &quot;KindleFolder&quot;. Any file that a Kindle can open will automatically be sent to your Kindle! Please note that this service uses Amazon's Kindle Personal Document Service - as a result, it may take up to 5 minutes for your file to be sent to your Kindle. Charges may apply for use over 3G.</li></ol><br />If you followed these directions, you should be good to go! Feel free to unsubscribe at any point by visiting <a href='http://www.kindlefolder.us/unsubscribe'>http://www.kindlefolder.us/unsubscribe</a>.<br /><br />Thanks!<br /><br />Chris and Geoff from KindleFolder")
		
		return redirect(url_for('success', kindle_email=p.kindle_email, personal_email=p.personal_email))
	
	# If an error occured with dropbox, remove associated account from database, prompt user to try again from beginning
	except dropbox.rest.ErrorResponse:
		return dropbox_error(person_id)
	except dropbox.rest.RESTSocketError:
		return dropbox_error(person_id)
	
	
@app.route('/success', methods=['GET'])
def success():
	# Make sure necessary parameters are in url
	kindle_email = request.args.get('kindle_email')
	personal_email = request.args.get('personal_email')	
	if kindle_email is None or personal_email is None:
		abort(400)
		
	# Make sure email addresses sent as parameters are in the database
	ps = Person.find_many("kindle_email='%s' AND personal_email='%s'" % (kindle_email, personal_email))
	if (ps is None) or (len(ps) == 0):
		abort(400)
	
	else:
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
	
	# If submitted email is not found in the database, return an error
	ps = Person.find_many("personal_email='%s'" % personal_email)
	if len(ps) < 1:
		flash('Email was not found in our database', 'error')
		return render_template("unsubscribe.html")
	
	# Generate unsubscribe token for an account with the personal email, send it in an email to the user
	unsubscribe_token = ps[0].generate_unsubscribe_token()
	sendemail.mail_without_attach(personal_email, "Unsubscribe","Hello!<br /><br />You have requested to be unsubscribed from KindleFolder's service. Please click the link below to confirm. <br /><br />%s<br /><br />If you did not request to be unsubscribed, please ignore this email. If you keep receiving this email, please contact support@kindlefolder.us.<br /><br />Thanks!<br /><br />Chris and Geoff from KindleFolder" % (ROOT + url_for('remove', personal_email=personal_email, unsubscribe_token=unsubscribe_token)))
	return redirect(url_for("unsubscribe_email_sent", personal_email=personal_email))
	

@app.route('/unsubscribe_email_sent', methods=['GET'])
def unsubscribe_email_sent():
	# Make sure necessary parameters are in url
	personal_email = request.args.get('personal_email')	
	if personal_email is None:
		abort(400)
		
	else:
		return render_template("unsubscribe_email_sent.html", personal_email=personal_email)
		
	
@app.route('/remove', methods=['GET'])
def remove():
	# Make sure necessary parameters are in url
	personal_email = request.args.get('personal_email')
	unsubscribe_token = request.args.get('unsubscribe_token')
	if personal_email is None or unsubscribe_token is None:
		abort(400)
		
	# Find accounts to be removed (accounts that match the personal email)
	ps = Person.find_many("personal_email='%s'" % personal_email)
	
	# Abort if no accounts exist, or if unsubscribe token is invalid
	if (ps is None) or (len(ps) == 0) or (ps[0].unsubscribe_token != unsubscribe_token):
		abort(400)
		
	# Otherwise, remove accounts
	else:	
		for p in ps:
			p.destroy()	
		return redirect(url_for("unsubscribe_confirm", personal_email=personal_email))

	
@app.route('/unsubscribe_confirm', methods=['GET'])
def unsubscribe_confirm():
	# Make sure necessary parameters are in url
	personal_email = request.args.get('personal_email')	
	if personal_email is None:
		abort(400)
		
	else:
		return render_template("unsubscribe_confirm.html", personal_email=personal_email)
				
				
@app.route('/about', methods=['GET'])
def setup():
	return render_template("about.html");
	

@app.route('/support', methods=['GET'])
def support():
	return render_template("support.html");
	
	
@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400
				
				
				
				

if __name__ == "__main__":
	app.run()
