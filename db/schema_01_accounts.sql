DROP TABLE IF EXISTS accounts;
CREATE TABLE accounts (
	id INTEGER PRIMARY KEY AUTO_INCREMENT,
	access_token VARCHAR(15),
	access_secret VARCHAR(15),
	kindle_email VARCHAR(45) NOT NULL,
	personal_email VARCHAR(45) NOT NULL,
	unsubscribe_token VARCHAR(30),
	created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
