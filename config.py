import os


# flask secret key
SECRET_KEY = 'super secret string'

BASEDIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = 'sqliteext:///' + os.path.join(BASEDIR, 'app.db')


#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
#SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
#SQLALCHEMY_TRACK_MODIFICATIONS = False # Don't need it, suppress warning
