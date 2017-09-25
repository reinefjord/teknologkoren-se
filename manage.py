from flask_script import Manager, prompt, prompt_pass

from teknologkoren_se import app, db
from teknologkoren_se.models import Tag, User

manager = Manager(app)


@manager.command
def create_db():
    """Create database and all tables."""
    db.create_all()


@manager.command
def full_setup():
    """First time setup of database."""
    print('Creating database...')
    create_db()
    print('Done, setup complete.')


if __name__ == "__main__":
    manager.run()
