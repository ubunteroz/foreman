# python imports
from os import path, mkdir
from ConfigParser import ConfigParser
import random
import string
# library imports
from werkzeug import Local, LocalManager
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

    print "Binding to database."


def init_database():
    from ..model import Base

    Base.metadata.create_all(db)
    print "Database initialised."


def drop_database():
    from ..model import Base

    Base.metadata.reflect(db)
    Base.metadata.drop_all(db)


def create_admin_user():
    from population import create_admin_user
    create_admin_user()
    print "Admin user created."


def load_initial_values():
    from population import load_initial_values
    load_initial_values()
    print "Initial data added to database!"


def populate_database():
    from population import create_test_data
    create_test_data()
    print "Example data populated!"


def populate_test_database():
    from test_population import create_test_data
    create_test_data()
    print "Example data populated!"


def multidict_to_dict(md):
    d = {}
    for k, a in md.iterlists():
        if len(a) == 1:
            d[k] = a[0]
        else:
            d[k] = a
    return d


def upload_file(f, new_directory, rand=15):
    unused_file_name, file_ext = path.splitext(f.filename.split(path.sep)[-1])
    # make random file name that is 15 characters/numbers long to prevent 2 users uploading same
    # file at same time
    file_name = ''.join(random.SystemRandom().choice(
        string.ascii_uppercase + string.digits) for _ in range(rand)) + file_ext

    new_location = path.join(new_directory, file_name)

    if not path.exists(new_directory):
        mkdir(new_directory)
    f.save(new_location)
    f.close()

    return file_name