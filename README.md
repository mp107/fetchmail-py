# fetchmail-py
Partial [fetchmail.pl](https://github.com/postfixadmin/postfixadmin/blob/master/ADDITIONS/fetchmail.pl) reimplementation in Python language, using sqlite database. It uses fetchmail package to periodically synchronize e-mails from external mailboxes into currently selected mailbox.

It may be used for example with [fetchmail plugin for RoundCube](https://plugins.roundcube.net/#/packages/pf4public/fetchmail).

### Set up
The script requires sqlite database to be initialized with [init_sqlite.sql](init_sqlite.sql) script.

`sqlite3 /path/to/database.sqlite < init_sqlite.sql`

This SQL script performs necessary DDL operations - it removes table named "fetchmail" if already existed and redefines it.

### Using
It is possible to specify the database location and the table name either directly at the beginning of the fetchmail-py.py script or run this script with command line parameters, like below:

`python fetchmail-py.py /path/to/database.sqlite table_name`

In order to execute the Python script periodically in automated way one can add it as a cron job. It may be defined for example by putting [fetchmail-py-cron](fetchmail-py-cron) file in /etc/cron.d/ directory.
