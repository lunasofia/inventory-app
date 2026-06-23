# Use PyMySQL as the MySQL driver (pure-Python; Cloud SQL MySQL in production).
# Harmless when DATABASE_URL points at SQLite/Postgres — it just registers a
# MySQLdb-compatible module. The version override satisfies Django's MySQL
# backend, which requires the reported driver version to be >= 1.4.
import pymysql

pymysql.version_info = (1, 4, 6, 'final', 0)
pymysql.install_as_MySQLdb()
