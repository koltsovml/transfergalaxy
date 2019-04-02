import MySQLdb
import logging


class DBConnection(object):
    _db_connection = None
    _db_cursor = None
    _disconnected = False

    # init connection
    def __init__(self, host, port, user, password, database, autocommit=False):
        self._db_connection = MySQLdb.connect(user=user, passwd=password, db=database,
                                              host=host, port=int(port), charset="utf8", use_unicode=True)
        self._db_cursor = self._db_connection.cursor(MySQLdb.cursors.DictCursor)
        self._db_connection.autocommit(autocommit)
        logging.info("________________________________CONNECTION__INSTANTIATED________________________________")

    # execute query
    def query(self, query, params):
        result = self._db_cursor.execute(query, params)
        return result

    # get connection's cursor
    def get_cursor(self):
        return self._db_cursor

    def close_connection(self):
        self._db_connection.close()
        self._disconnected = True
        logging.info("_____________________________CONNECTION__CLOSED__MANUALLY_______________________________")

    def commit(self):
        self._db_connection.commit()

    # close connection
    def __del__(self):
        if not self._disconnected:
            self._db_connection.close()
            logging.info("_______________________CONNECTION__CLOSED__BY__DESTRUCTOR_______________________________")
