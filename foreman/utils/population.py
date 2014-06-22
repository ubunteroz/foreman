# foreman imports
from foreman.model import User, ForemanOptions, UserRoles
from utils import session, config


def create_admin_user():
    admin = User("administrator", "changeme", "The", "Administrator", config.get('admin', 'admin_email'),
                 validated=True)
    session.add(admin)
    session.flush()

    admin_role = UserRoles(admin, "Administrator", False)
    session.add(admin_role)
    session.flush()

    admin.add_change(admin)
    session.flush()

    session.commit()


def load_initial_values():
    opts = ForemanOptions("%d %b %Y %H:%M:%S", r"C:\Foreman", "FromList", "NumericIncrement", "A Large Company",
                          "Investigations")
    session.add(opts)
    session.flush()
    session.commit()