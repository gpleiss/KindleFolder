import MySQLdb
from person import Person


class EmailQueue():

	@staticmethod
	def push(e):
		if type(e) != EmailObj:
			raise Exception("Not an email object")
		sql = """ INSERT INTO emailqueue
			(person_id, filename) VALUES ('%s', '%s')
			""" % (e.person.person_id, e.filename)
		Person.cur.execute(sql)
			
	@staticmethod		
	def pop():
		sql = """ SELECT TOP 1 
			person_id, filename FROM emailqueue
			ORDER BY id DESC """
		Person.cur.execute(sql)
		(person_id, filename) = Person.cur.fetchone()
		return Person(Person.find(person_id), filename)
		
	@staticmethod
	def is_empty():
		sql = """ SELECT id FROM emailqueue """
		return Person.cur.execute(sql) is None
		


class EmailObj():
		
	def __init__(self, person_id, filename):
		self.person_id = person_id
		self.filename = filename
		
	def send_email(self):
		pass
		


if __name__ == "__main__":
	# For testing purposes
	Person.connect_db()
	# Put test code here
	print EmailQueue.is_empty()
	Person.close_db()
