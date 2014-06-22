# python imports
from os import path
from ConfigParser import ConfigParser
# library imports
from werkzeug import Local, LocalManager, MultiDict
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# Useful variables
# ================
ROOT_DIR = path.join(path.dirname(__file__), '..')

# Local Manager Stuff
# ===================
local = Local()
local_manager = LocalManager([local])

db = None

# This creates a custom session class
sessionMaker = sessionmaker(autocommit=False)

# This is a wrapper that will always be the thread-local session
session = scoped_session(sessionMaker, local_manager.get_ident)

config = None


def setup(config_file):
    global config
    if not path.exists(config_file):
        raise Exception('Config file "%s" cannot be found' % config_file)

    config = ConfigParser()
    config.read(config_file)

    global db
    if config.get('database', 'database_type').lower() == "sqlite":
        db = create_engine('sqlite:///' + config.get('database', 'database_name'), echo=False)
    elif config.get('database', 'database_type').lower() == "postgres":
        db = create_engine('postgres://{}:{}@{}:{}/{}'.format(
            config.get('database', 'username'),
            config.get('database', 'password'),
            config.get('database', 'database_location'),
            config.get('database', 'port_number'),
            config.get('database', 'database_name')), echo=False)
    else:
        raise Exception('The database in the config file must be sqlite or postgres only')
    sessionMaker.configure(bind=db, autocommit=False, autoflush=False)

    print "Database setup"


def init_database():
    from ..model import Base

    Base.metadata.create_all(db)
    print "Database initialised"


def drop_database():
    from ..model import Base

    Base.metadata.reflect(db)
    Base.metadata.drop_all(db)


def create_admin_user():
    from population import create_admin_user
    create_admin_user()
    print "Admin user created"


def load_initial_values():
    from population import load_initial_values
    load_initial_values()
    print "Initial data added to database"


def populate_database():
    from example_populate import populate
    populate()
    print "Example data populated"


def multidict_to_dict(md):
    d = {}
    for k, a in md.iterlists():
        if len(a) == 1:
            d[k] = a[0]
        else:
            d[k] = a
    return d
