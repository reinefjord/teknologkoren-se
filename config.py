import os


# flask secret key
SECRET_KEY = 'super secret string'

BASEDIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = 'sqliteext:///' + os.path.join(BASEDIR, 'app.db')

TEMPLATES_AUTO_RELOAD = True

UPLOADS_DEFAULT_DEST = 'app/static/uploads/'
UPLOADS_DEFAULT_URL = '/static/uploads/'

IMAGES_PATH = ['static/images', 'static/uploads/images']
IMAGES_URL = '/img'
