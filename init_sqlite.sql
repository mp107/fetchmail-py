DROP TABLE IF EXISTS fetchmail;
CREATE TABLE IF NOT EXISTS fetchmail (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT '1',
  src_server TEXT NOT NULL,
  src_auth TEXT NOT NULL DEFAULT 'password',
  src_user TEXT NOT NULL,
  src_password TEXT NOT NULL,
  src_folder TEXT NOT NULL,
  poll_time INTEGER unsigned NOT NULL DEFAULT '10',
  fetchall INTEGER unsigned NOT NULL DEFAULT '0',
  keep INTEGER unsigned NOT NULL DEFAULT '1',
  protocol TEXT NOT NULL DEFAULT 'IMAP',
  usessl INTEGER unsigned NOT NULL DEFAULT '1',
  sslcertck INTEGER NOT NULL DEFAULT '0',
  sslcertpath TEXT /*!40100 CHARACTER SET utf8 */ DEFAULT '',
  sslfingerprint TEXT /*!40100 CHARACTER SET latin1 */ DEFAULT '',
  extra_options TEXT,
  returned_text TEXT,
  mda TEXT NOT NULL DEFAULT '',
  domain TEXT,
  date TIMESTAMP NOT NULL DEFAULT 0
);