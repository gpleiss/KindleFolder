import sys, os, sendemail, time
from dropbox import client, rest, session
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from person import Person


# Get all variables
from config import *


kindle_mime_types = ['application/pdf', 'application/msword', 
					 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
					 'text/html', 'text/rtf', 'image/jpeg', 'application/mobi', 'application/azw',
					 'image/gif', 'image/png', 'image/bmp', 'application/zip']

sent_files_foldername = "/Files Sent" # Folder containing files sent to kindle


def send_files_to_kindle(account, kindle_email):
	''' Looks in app folder and emails all valid files to kindle
		 A valid file is one with a valid mime-type, and one that has not
			been sent before.
		 Sent files will be sent to the sent files folder.
		 NOTE: App folderis not viewed recursivly. Only files at the base
			level of the folder will be sent
	'''
	files_sent = []
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
				files_sent.append(path)
				
	return files_sent


def main(name):

	i = 1
		
	if not os.path.exists('log/sent_files_log.txt'):
		os.popen('touch log/sent_files_log.txt')
	f = open('log/sent_files_log.txt', 'a')
	
	Person.connect_db()
	ps = Person.find_all()
	print ps
		
	for p in ps:
		try:
			
			# With retrieved access strings, accesses dropbox account
			print (p.access_token, p.access_secret, p.kindle_email)
			if not p.can_send_files_to_kindle():
				continue
			try: 
				sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
				sess.set_token(p.access_token, p.access_secret)
				account = client.DropboxClient(sess)
				
				files_sent = send_files_to_kindle(account, p.kindle_email)
				print "files_sent:", files_sent
				f.write("Call #" + i.__str__() + ", ")
				f.write(p.kindle_email + "\n")
				f.write("files_sent: " + files_sent.__str__() + "\n")
				i += 1
			except:
				print "something went wrong"
		except:
			#sendemail.mail_without_attach("chrisgallello@gmail.com", "KindleFolder Error: authenticate_paths for loop error","There was an issue with one of the for loop things in authenticate_paths.py.<br /><br />")
			#sendemail.mail_without_attach("gpleiss@gmail.com", "KindleFolder Error: authenticate_paths for loop error","There was an issue with one of the for loop things in authenticate_paths.py.<br /><br />")
			pass
			
	f.write("\n")
	f.close()
	Person.close_db()


	
	
if __name__ == '__main__':
	main(*sys.argv)
