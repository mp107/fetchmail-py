#!/usr/bin/python

import base64, errno, os, sqlite3, sys, tempfile

# Database config
# It might be specified also as command arguments, f.e.
# python fetchmail-py.py sqlite.db fetchmail
sqlite_file_path = 'sqlite.db'
sqlite_db_name = 'fetchmail'

run_dir = '/var/lock'

dovecot_deliver = '/usr/lib/dovecot/deliver'

# TODO - Allow to import values from file

##### CODE #####

lock_file_path = run_dir + '/fetchmail-py-all.lock'

def connect_to_sqlite_db(dburi):
    if sys.version_info >= (3, 0):
        db = sqlite3.connect(dburi, uri=True)
    else:
        if not os.access(sqlite_file_path, os.R_OK | os.W_OK):
            print('Error: DB file {} does not exist or is not writeable' \
                .format(sqlite_file_path))
            return None

        # TODO - Better check as sqlite file may become unaccessible until now
        db = sqlite3.connect(sqlite_file_path)
    return db


def lockfile(filename):
    # Source: https://stackoverflow.com/a/39097188
    try:
        file = os.open(filename, os.O_CREAT | os.O_EXCL)
        return file
    except OSError as e:
        if e.errno == errno.EEXIST:
            return None
        else:
            raise

def unlockfile(file):
    os.remove(lock_file_path)
    os.close(file)

def exit_me(status, lock = None):
    if lock:
        unlockfile(lock)
    sys.exit(status)

# DB file path and DB name may be set also as command line arguments
if (len(sys.argv) == 3):
    sqlite_file_path = sys.argv[1]
    sqlite_db_name = sys.argv[2]

print('DB file path: ' + sqlite_file_path)
print('DB name: ' + sqlite_db_name)

# Lock
lock = lockfile(lock_file_path)

if not lock:
    print('Error: Fetchmail-py is already working. Stopping.')
    exit_me(1)

file_handler = None

try:
    # Connect to the DB
    dburi = 'file:{}?mode=rw'.format(sqlite_file_path)

    with connect_to_sqlite_db(dburi) as db:

        if not db:
            exit_me(1, lock)

        # Select only mailboxes for which time for update has come
        sql_cond = "active = 1 AND strftime('%s', 'now') - strftime(date)"

        # Get mentioned mailboxes' details
        sql = 'SELECT date,id,mailbox,src_server,src_auth,src_user,' \
            'src_password,src_folder,fetchall,keep,protocol,mda,' \
            'extra_options,usessl,sslcertck,sslcertpath,sslfingerprint ' \
            'FROM fetchmail WHERE %s  > poll_time*60'

        # Get row as dict, not tuple
        # Source: https://stackoverflow.com/a/48789604
        db.row_factory = lambda c, r: \
            dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])

        result = db.execute(sql % sql_cond)


    # Run fetchmail separate for every mailbox
    # so that one failure will not abort all current updates

    for row in result:
        try:
            print('Fetching %s@%s for %s' \
                % (row.get('src_user'), row.get('src_server'), \
                    row.get('mailbox')))

            cmd = "user '%s' there with password '%s'" \
                % (row.get('src_user'), \
                    base64.b64decode(row.get('src_password')).decode('utf-8'))

            # Construct fetchmail configuration file content
            if row.get('src_folder'):
                cmd += " folder '%s'" % row.get('src_folder')

            cmd += ' mda "%s -d %s" ' % (dovecot_deliver, row.get('mailbox'))

            cmd += " is '%s' here" % row.get('mailbox')

            if row.get('keep'): cmd += ' keep'
            if row.get('fetchall'): cmd += ' fetchall'
            if row.get('usessl'): cmd += ' ssl'
            if row.get('sslcertck'): cmd += ' sslcertck'

            if row.get('sslcertpath'): 
                cmd += ' sslcertpath %s' % row.get('sslcertpath')

            if row.get('sslfingerprint'): 
                cmd += ' sslfingerprint "%s"' % row.get('sslfingerprint')

            if row.get('extra_options'): 
                cmd += ' extra_options' % row.get('extra_options')

            text = 'set postmaster "postmaster"\nset nobouncemail\n' \
                'set no spambounce\nset properties ""\nset syslog\n'

            text += 'poll %s with proto %s' \
                % (row.get('src_server'), row.get('protocol') )

            if row.get('src_port'):
                text += ' service %s' % row.get('src_port')

            text += '\n  %s' % cmd

            # Create temporary fetchmail configuration file
            file_handler = tempfile.NamedTemporaryFile(delete=False)
            filename = file_handler.name
            file_handler.write(text.encode())
            file_handler.close()

            # Run fetchmail
            stream = os.popen(
                '/usr/bin/fetchmail -f "%s" -i %s/fetchmail.pid 2>&1' \
                % (filename, run_dir))

            output = stream.read()
            print('Fetchmail result: ' + output)
            os.remove(filename)

        except Exception as e:
            emsg = ''
            if hasattr(e, 'message'):
                emsg = e.message
            elif hasattr(e, '__traceback__'): 
                emsg = e.__traceback__
            output = 'Exception level 2: ' + str(emsg)

        # Update fetching status
        sql = 'UPDATE fetchmail ' \
            "SET returned_text='%s'," % output + \
            "date=strftime('%s', 'now') " \
            'WHERE id=' + '%d;' % row.get('id')

        with connect_to_sqlite_db(dburi) as db:

            if not db:
                exit_me(1, lock)

            result = db.execute(sql)
            db.commit()

except Exception as e:
    emsg = ''
    if hasattr(e, 'message'):
        emsg = e.message
    elif hasattr(e, '__traceback__'): 
        emsg = e.__traceback__
    print('Exception level 1: ' + str(emsg))

# Unlock and exit
exit_me(0, lock)
