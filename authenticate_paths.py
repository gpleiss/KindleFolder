import sys, os, MySQLdb, sendemail, time
from dropbox import client, rest, session
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders


# Get all variables
from config import *


kindle_mime_types = ['application/pdf', 'application/msword', 
					 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
					 'text/html', 'text/rtf', 'image/jpeg', 'application/mobi', 'application/azw',
					 'image/gif', 'image/png', 'image/bmp', 'application/zip']

sent_files_foldername = "/Files Sent" # Folder containing files sent to kindle


def send_files_to_kindle(account, kindle_email, files_sent):
	''' Looks in app folder and emails all valid files to kindle
		 A valid file is one with a valid mime-type, and one that has not
			been sent before.
		 Sent files will be sent to the sent files folder.
		 NOTE: App folderis not viewed recursivly. Only files at the base
			level of the folder will be sent
	'''
	
	metadata = account.metadata('', list=True)
	files = metadata['contents']
	print files
	# Go thru each file in app folder, send vaild files to kindle
	for file in files:
		
		# Only send files w/ vaild mimetypes, don't send the "Sent files" folder
		if not file['path'] == sent_files_foldername:	
			if file['mime_type'] in kindle_mime_types:	
				path = file['path'] # Path to file on Dropbox
				print path
				
				# Make a local copy of the file - will be emailed to Kindle
				path_no_slash = path.replace('/','',1)
				path_local = path_no_slash.replace(' ','') # Path to local copy of file
				download = account.get_file(path).read()
				file = open(path_local, "w")
				file.write(download)
				file.close()
				
				# Send local copy of file to kindle, and then remove local copy
				sendemail.mail(kindle_email,"Files","Here's your file!", path_local)
				account.file_move(path, sent_files_foldername+path)
				os.remove(path_local)
				
	return files_sent


def main(name):
	
	# From accounts database, get account access strings
	db =  MySQLdb.connect(host=HOST, user=USERNAME, passwd=PASSWORD, db=DATABASE)
	cur = db.cursor()

	i = 1
	files_sent = 0
		
	sql = "SELECT id FROM accounts" 
	# Selecting first id right now	
	cur.execute(sql)
	id_list = list(cur.fetchall()) # Returns a tuple (access_token, access_secret)
		
	for item in id_list:
		length = len(item)
		itemm = filter(lambda x: x.isdigit(), item.__str__())
		sql = "select app_key, app_secret, access_token, access_secret, kindle_email from accounts where id=" + itemm.__str__()
		# Selecting first id right now	
		cur.execute(sql)
		# Returns a tuple (access_token, access_secret)
		access_strings = cur.fetchone() 
		if access_strings is None:
			continue
			
		app_key = access_strings[0]
		app_secret = access_strings[1]
		access_token = access_strings[2]
		access_secret = access_strings[3]
		kindle_email = access_strings[4]

		# With retrieved access strings, accesses dropbox account
		if (access_token or access_secret or kindle_email) is None:
			continue
		try: 
			sess = session.DropboxSession(app_key, app_secret, "app_folder")
			sess.set_token(access_token, access_secret)
			account = client.DropboxClient(sess)
			
			print "Call #", i.__str__()
			print kindle_email
			files_sent = send_files_to_kindle(account, kindle_email, files_sent)
			i += 1
			print "files_sent:", files_sent
		except:
			pass


	
	
if __name__ == '__main__':
	main(*sys.argv)
