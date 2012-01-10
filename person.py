import MySQLdb, string, random
from config import *


class Person():
	
	db = None
	cur = None


	@staticmethod
	def connect_db():
		Person.db = MySQLdb.connect(host=HOST, user=USERNAME, passwd=PASSWORD, db=DATABASE)
		Person.cur = Person.db.cursor()
		return Person.db
		
		
	@staticmethod
	def init_db():
		with closing(connect_db()) as db:
			with app.open_resource('db/schema.sql') as f:
				db.cursor().executescript(f.read())
				
				
	@staticmethod
	def close_db():
		Person.db.close()
		
		
	
	def __init__(self, person_id=None, access_token=None, access_secret=None, kindle_email=None,
	personal_email=None, unsubscribe_token=None, created=None):
		self.person_id = person_id
		self.personal_email = personal_email
		self.kindle_email = kindle_email
		self.access_token = access_token
		self.access_secret = access_secret
		self.unsubscribe_token = unsubscribe_token
		self.created = created
	
		

	@staticmethod
	def new(personal_email, kindle_email, access_token=None, access_secret=None):
		sql_personal_email = "'" + personal_email + "'"
		sql_kindle_email = "'" + kindle_email + "'"
		sql_access_token = "'" + access_token + "'" if access_token is not None else "NULL"
		sql_access_secret = "'" + access_secret + "'" if access_secret is not None else "NULL"
		sql = '''INSERT INTO accounts
			(access_token, access_secret, kindle_email, personal_email)
			VALUES (%s, %s, %s, %s)
			''' % (sql_access_token, sql_access_secret, sql_kindle_email, sql_personal_email)
		Person.cur.execute(sql)
		
		sql = '''SELECT @@IDENTITY'''
		Person.cur.execute(sql)
		(person_id,) = Person.cur.fetchone()
		
		sql = '''SELECT created FROM accounts WHERE id=%i''' % person_id
		Person.cur.execute(sql)
		(created,) = Person.cur.fetchone()
		
		return Person(person_id=person_id, personal_email=personal_email, kindle_email=kindle_email,
			access_token=access_token, access_secret=access_secret, created=created)
		
		
			
	@staticmethod	
	def find(person_id):
		sql = '''SELECT * FROM accounts WHERE id=%i''' % person_id
		Person.cur.execute(sql)
		res = Person.cur.fetchone()
		return Person(*res) if res is not None else None
		
		
	
	@staticmethod	
	def find_many(sql_cmpr):
		sql = '''SELECT * FROM accounts WHERE %s''' % sql_cmpr
		Person.cur.execute(sql)
		res = Person.cur.fetchall()
		return [Person(*account_params) for account_params in res] if res is not None else None
		
		
		
	@staticmethod	
	def find_all():
		sql = '''SELECT * FROM accounts'''
		Person.cur.execute(sql)
		res = Person.cur.fetchall()
		return [Person(*account_params) for account_params in res] if res is not None else None
	
	
		
	def save(self):
		sql_personal_email = "'" + self.personal_email + "'"
		sql_kindle_email = "'" + self.kindle_email + "'"
		sql_access_token = "'" + self.access_token + "'" if self.access_token is not None else "NULL"
		sql_access_secret = "'" + self.access_secret + "'" if self.access_secret is not None else "NULL"
		sql_unsubscribe_token = "'" + self.unsubscribe_token + "'" if self.unsubscribe_token is not None else "NULL"
		sql = '''UPDATE accounts
			SET access_token=%s, access_secret=%s, kindle_email=%s, 
			personal_email=%s, unsubscribe_token=%s WHERE id=%i
			''' % (sql_access_token, sql_access_secret, sql_kindle_email,
			sql_personal_email, sql_unsubscribe_token, self.person_id)
		Person.cur.execute(sql)
		
		
		
	def destroy(self):
		sql = '''DELETE FROM accounts WHERE id=%i''' % self.person_id
		Person.cur.execute(sql)
		
		
	
	def generate_unsubscribe_token(self):
		chars = string.ascii_letters + string.digits
		size = 30
		
		self.unsubscribe_token = ''.join(random.choice(chars) for i in range(size))
		self.save()
		return self.unsubscribe_token
		
		
	
	def can_send_files_to_kindle(self):
		if self.access_token is None: 
			return False
		elif self.access_secret is None: 
			return False
		elif self.kindle_email is None: 
			return False
		else: 
			return True
	
	
	
	def __str__(self):
		string = "Person: "
		string += "id = %i, " % self.person_id
		string += "personal email = %s, " % self.personal_email
		string += "kindle_email = %s, " % self.kindle_email
		string += "access token = %s, " % self.access_token if self.access_token else ""
		string += "secret token = %s, " % self.access_secret if self.access_secret else ""
		string += "unsubscribe token = %s, " % self.unsubscribe_token if self.unsubscribe_token else ""
		string += "created on %s" % self.created
		return string
		


if __name__ == "__main__":
	# For testing purposes
	Person.connect_db()
	# Put test code here
	Person.close_db()
