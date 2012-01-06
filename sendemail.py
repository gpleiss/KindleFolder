import smtplib
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os




def mail(to, subject, text, attach):
   msg = MIMEMultipart()

   msg['From'] = gmail_user
   msg['To'] = to
   msg['Subject'] = subject

   msg.attach(MIMEText(text))

   part = MIMEBase('application', 'octet-stream')
   part.set_payload(open(attach, 'rb').read())
   Encoders.encode_base64(part)
   part.add_header('Content-Disposition',
           'attachment; filename="%s"' % os.path.basename(attach))
   msg.attach(part)

   mailServer = smtplib.SMTP("smtp.gmail.com", 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(gmail_user, gmail_pwd)
   mailServer.sendmail(gmail_user, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
   mailServer.close()

def mail_without_attach(to, subject, text):
   #fromaddr = 'unicorns@kindlefolder.us'
   #to = to
   #print 'to:'
   #print to
   #print '================'
   #
   ## Credentials (if needed)  
   #username = 'unicorns@kindlefolder.us'  
   #password = 'fuckcalvin'  
   #  
   ## The actual mail send  
   #server = smtplib.SMTP('smtp.gmail.com:587')  
   #server.starttls()  
   #server.login(username,password)  
   #server.sendmail(fromaddr, to, text)  
   #server.quit()
   
   SMTP_SERVER = 'smtp.gmail.com'
   SMTP_PORT = 587
    
   sender = 'unicorns@kindlefolder.us'
   password = 'fuckcalvin'
   recipient = to
   body = text
   subject = subject
   body = "" + body + ""
   headers = ["From: " + sender,
              "Subject: " + subject,
              "To: " + recipient,
              "MIME-Version: 1.0",
              "Content-Type: text/html"]
   headers = "\r\n".join(headers)
   session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    
   session.ehlo()
   session.starttls()
   session.ehlo
   session.login(sender, password)
   
   session.sendmail(sender, recipient, headers + "\r\n\r\n" + body)
   session.quit()


def main(name):	
	gmail_user = "kindleboxsender@gmail.com"
	gmail_pwd = "fuckingcalvin"
	mail("chrisgallello@gmail.com","Hello from python! We have a gmail account a kindleboxsender@gmail.com. Passwod is fuckingcalvin","This is a email sent with python. Hopefully you get the attachement! None of this is automated, just trying out an email sending script.","authenticate.py")

if __name__ == '__main___':
	main(*sys.argv)
