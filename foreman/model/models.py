# library imports
from sqlalchemy import asc, desc
from sqlalchemy.ext.declarative import declarative_base
# local imports
from ..utils.utils import session


class Model(object):
    @classmethod
    def get(cls, id):
        return session.query(cls).get(id)

    @classmethod
    def get_filter_by(cls, **vars):
        return session.query(cls).filter_by(**vars)

    @classmethod
    def get_all(cls, descending=False):
        if descending:
            return session.query(cls).order_by(desc(cls.id))
        else:
            return session.query(cls).order_by(asc(cls.id))

    @classmethod
    def get_amount(cls):
        return session.query(cls).count()


class HistoryModel(Model):
    comparable_fields = {}
    history_backref = 'history'
    object_name = None  # override this to add an entry for "<object_name> created"
    history_name = (None, None)  # override this for user history of this object

    @classmethod
    def get_changes(cls, current_obj):
        change_log = []
        history_list = getattr(current_obj, cls.history_backref)
        for new_obj, old_obj in zip(history_list, history_list[1:]):
            change_log.append({'date': old_obj.date,
                               'user': old_obj.user,
                               'current': current_obj,
                               'date_time': old_obj.date_time,
                               'change_log': new_obj.difference(old_obj)})

        if cls.object_name is not None:
            try:
                oldest_entry = history_list[0]
                change_log.append({'date': oldest_entry.date,
                               'user': oldest_entry.user,
                               'current': current_obj,
                               'date_time': oldest_entry.date_time,
                               'change_log': cls.object_name + " created"})
            except IndexError:
                # no entries
                pass

        return change_log

    def difference(self, previous_object):
        differences = {}

        for field_name, field in self.comparable_fields.iteritems():
            current_value = getattr(self, field)
            old_value = getattr(previous_object, field)
            if current_value != old_value:
                if current_value == "":
                    current_value = "None"
                elif old_value == "":
                    old_value = "None"
                differences[field_name] = (current_value, old_value)
        return differences

    @classmethod
    def get_changes_for_user(cls, user):
        change_log = []
        q = session.query(cls).filter_by(user=user).all()
        for i in xrange(0, len(q)):
            entry = q[i]
            previous_entry_list = entry.previous
            if previous_entry_list is None:
                change_log.append({'date': entry.date,
                                   'date_time': entry.date_time,
                                   'object': (entry.history_name[0], getattr(entry, entry.history_name[1])),
                                   'change_log': entry.history_name[0] + " created"})
            else:
                change_log.append({'date': entry.date,
                                   'date_time': entry.date_time,
                                   'object': (entry.history_name[0], getattr(entry, entry.history_name[1])),
                                   'change_log': previous_entry_list.difference(entry)})
        return change_log

    def __repr__(self):
        return "<{} History id {}>".format(self.history_name[0], self.id)


class UserHistoryModel(Model):
    history_name = (None, None)  # override this for user history of this object

    @classmethod
    def get_changes(cls, current_obj, role):
        change_log = []
        history_list = cls.get_roles_for_obj(current_obj, role)

        for new_obj, old_obj in zip(history_list, history_list[1:]):
            change_log.append({'date': old_obj.date,
                               'user': old_obj.changes_user,
                               'current': current_obj,
                               'date_time': old_obj.date_time,
                               'change_log': new_obj.difference(old_obj, role)})

        try:
            oldest_entry = history_list[0]
            if oldest_entry.removed is False:
                change_log.append({'date': oldest_entry.date,
                                   'user': oldest_entry.changes_user,
                                   'current': current_obj,
                                   'date_time': oldest_entry.date_time,
                                   'change_log': {role: ("ADD", oldest_entry.user.fullname)}})
        except IndexError:
            # no entries
            pass
        return change_log

    @classmethod
    def get_changes_for_user(cls, user):
        change_log = []
        q = session.query(cls).filter_by(changes_user=user).all()
        for i in xrange(0, len(q)):
            entry = q[i]
            previous_entry_list = entry.previous
            if previous_entry_list is None:
                change_log.append({'date': entry.date,
                                   'date_time': entry.date_time,
                                   'object': (entry.history_name[0], getattr(entry, entry.history_name[1])),
                                   'change_log': {entry.role: ("ADD", entry.user.fullname)}})
            else:
                change_log.append({'date': entry.date,
                                   'date_time': entry.date_time,
                                   'object': (entry.history_name[0], getattr(entry, entry.history_name[1])),
                                   'change_log': previous_entry_list.difference(entry, entry.role)})
        return change_log

    def difference(self, previous_object, role_name):
        differences = {}
        if previous_object.removed:
            differences[role_name] = ("DEL", previous_object.user.fullname)
        elif self.removed:
            differences[role_name] = ("ADD", previous_object.user.fullname)
        return differences

    @classmethod
    def change_user(cls, role_for_user, new_user, changes_made_by_user):
        current_user_id = role_for_user.user.id
        if new_user is True:
            old_removed = cls(role_for_user, changes_made_by_user, True)
            session.add(old_removed)
            session.delete(role_for_user)
            session.flush()
        elif new_user is not None and new_user.id != current_user_id:
            old_removed = cls(role_for_user, changes_made_by_user, True)
            session.add(old_removed)

            role_for_user.user = new_user
            new_added = cls(role_for_user, changes_made_by_user)
            session.add(new_added)
        else:
            new_added = cls(role_for_user, changes_made_by_user)
            session.add(new_added)
            session.flush()

    def __repr__(self):
        return "<{} History id {}>".format(self.history_name[0], self.id)


Base = declarative_base()
