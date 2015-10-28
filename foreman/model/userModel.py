# python imports
from datetime import datetime
import random
import hashlib
import string
from os import path
# library imports
from sqlalchemy import Table, Column, Integer, Boolean, Float, Unicode, MetaData, ForeignKey, DateTime, CheckConstraint, \
    asc, desc, func, and_, Date
from sqlalchemy.orm import backref, relation
# local imports
from models import Base, Model, UserHistoryModel, HistoryModel
from ..utils.utils import session, ROOT_DIR
from generalModel import ForemanOptions


class Department(Base, Model):
    __tablename__ = 'department'

    id = Column(Integer, primary_key=True)
    department = Column(Unicode)

    def __init__(self, department):
        self.department = department

    def __str__(self):
        return self.department


class Team(Base, Model):
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True)
    team = Column(Unicode)
    department_id = Column(Integer, ForeignKey('department.id'))

    department = relation('Department', backref=backref('teams'))

    def __init__(self, team, department):
        self.team = team
        self.department = department

    def __str__(self):
        return self.team


class UserMessage(Base, Model):
    __tablename__ = 'user_messages'

    id = Column(Integer, primary_key=True)
    recipient_id = Column(Integer, ForeignKey('users.id'))
    sender_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(Unicode)
    body = Column(Unicode)
    date_time = Column(DateTime)

    recipient = relation('User', backref=backref('messages_received'), foreign_keys=recipient_id)
    sender = relation('User', backref=backref('messages_sent'), foreign_keys=sender_id)

    def __init__(self, sender, recipient, subject, body):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.date_time = datetime.now()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)


class UserHistory(Base, HistoryModel):
    __tablename__ = 'user_history'

    id = Column(Integer, primary_key=True)
    original_user_id = Column(Integer, ForeignKey('users.id'))
    forename = Column(Unicode)
    surname = Column(Unicode)
    middle = Column(Unicode)
    username = Column(Unicode)
    email = Column(Unicode)
    date_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    telephone = Column(Unicode)
    alt_telephone = Column(Unicode)
    fax = Column(Unicode)
    job_title = Column(Unicode)
    team = Column(Unicode)
    department = Column(Unicode)
    photo = Column(Unicode)
    manager = Column(Unicode)

    original_user = relation('User', backref=backref('history', order_by=asc(date_time)), foreign_keys=original_user_id)
    user = relation('User', backref=backref('user_history_changes'), foreign_keys=user_id)

    comparable_fields = {'Forename': 'forename', 'Surname': 'surname', 'Middle Name': 'middle', 'Username': 'username',
                         'Email address': 'email', 'Telephone Number': 'telephone', 'Alternative Telephone Number':
                         'alt_telephone', 'Fax number': 'fax', 'Job Title': 'job_title', "Profile photo": 'photo',
                         'Team': 'team', 'Department': 'department', "Manager": 'manager'}

    history_name = ("User", "username", "original_user_id")
    object_name = "User"

    def __init__(self, original_user, user_who_made_changes):
        self.original_user_id = original_user.id
        self.forename = original_user.forename
        self.surname = original_user.surname
        self.middle = original_user.middle
        self.username = original_user.username
        self.email = original_user.email
        self.date_time = datetime.now()
        self.user = user_who_made_changes
        self.telephone = original_user.telephone
        self.alt_telephone = original_user.alt_telephone
        self.fax = original_user.fax
        self.job_title = original_user.job_title
        self.photo = original_user.photo
        if original_user.team is not None:
            self.team = original_user.team.team
            self.department = original_user.team.department.department
        else:
            self.team = None
            self.department = None
        if original_user.manager is not None:
            self.manager = original_user.manager.fullname
        else:
            self.manager = None

    @property
    def previous(self):
        q = session.query(UserHistory)
        q = q.filter_by(original_user_id=self.original_user_id).filter(UserHistory.id < self.id).order_by(
            desc(UserHistory.id))
        return q.first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)


class User(Base, Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    forename = Column(Unicode)
    surname = Column(Unicode)
    middle = Column(Unicode)
    username = Column(Unicode)
    password = Column(Unicode)
    email = Column(Unicode)
    validated = Column(Boolean)
    telephone = Column(Unicode)
    alt_telephone = Column(Unicode)
    fax = Column(Unicode)
    team_id = Column(Integer, ForeignKey('team.id'))
    job_title = Column(Unicode)
    photo = Column(Unicode)
    active = Column(Boolean)
    manager_id = Column(Integer, ForeignKey('users.id'))

    team = relation('Team', backref=backref('team_members'))
    manager = relation('User', backref=backref('direct_reports'), remote_side=[id])
    PROFILE_PHOTO_FOLDER = path.join(ROOT_DIR, 'files', 'user_profile_photos')

    def __init__(self, username, password, forename, surname, email, validated=False, middle=None, photo='default.png'):
        self.username = username
        self.set_password(password)
        self.forename = forename
        self.surname = surname
        self.middle = middle
        self.email = email
        self.validated = validated
        self.photo = photo
        self.activate()

    def add_change(self, user):
        change = UserHistory(self, user)
        session.add(change)
        session.flush()

    def deactivate(self):
        self.active = False

    def activate(self):
        self.active = True

    def is_manager_of(self, user):
        return user.manager.id == self.id

    def is_a_manager(self):
        return len(self.direct_reports) > 0

    def is_investigator(self):
        return UserRoles.check_user_has_active_role(user=self, role=UserRoles.INV) or \
               UserRoles.check_user_has_active_role(user=self, role=UserRoles.ADMIN)

    def is_QA(self):
        return UserRoles.check_user_has_active_role(user=self, role=UserRoles.QA) or \
               UserRoles.check_user_has_active_role(user=self, role=UserRoles.ADMIN)

    def is_case_manager(self):
        return UserRoles.check_user_has_active_role(user=self, role=UserRoles.CASE_MAN) or \
               UserRoles.check_user_has_active_role(user=self, role=UserRoles.ADMIN)

    def is_requester(self):
        return UserRoles.check_user_has_active_role(user=self, role=UserRoles.REQUESTER) or \
               UserRoles.check_user_has_active_role(user=self, role=UserRoles.ADMIN)

    def is_worker(self):
        return self.is_case_manager() or self.is_investigator() or self.is_QA()

    def is_examiner(self):
        return self.is_investigator() or self.is_QA()

    def is_admin(self):
        return UserRoles.check_user_has_active_role(user=self, role=UserRoles.ADMIN)

    def is_authoriser(self):
        return UserRoles.check_user_has_active_role(user=self, role=UserRoles.AUTH) or \
               UserRoles.check_user_has_active_role(user=self, role=UserRoles.ADMIN)

    @property
    def department(self):
        return self.team.department.department

    @property
    def fullname(self):
        if self.middle is not None:
            return "{} {} {}".format(self.forename, self.middle, self.surname).title()
        else:
            return "{} {}".format(self.forename, self.surname).title()

    @staticmethod
    def is_valid_id(user_id):
        if session.query(User).filter_by(id=user_id).count() == 1:
            return True
        return False

    @staticmethod
    def get_user_with_role(role, case_id=None, task_id=None):
        if task_id is not None:
            return session.query(User).join('task_roles').filter(and_(UserTaskRoles.task_id == task_id,
                                                                      UserTaskRoles.role == role)).order_by(
                desc(UserTaskRoles.id)).first()
        elif case_id is not None:
            return session.query(User).join('case_roles').filter(and_(UserCaseRoles.case_id == case_id,
                                                                      UserCaseRoles.role == role)).order_by(
                desc(UserCaseRoles.id)).first()

    def __repr__(self):
        return "<User Object[{}] '{}'>".format(self.id, self.fullname)

    def set_password(self, raw_password):
        salt = str(random.random())[3:10]
        hash = hashlib.sha256('%s%s' % (salt, raw_password)).hexdigest()
        self.password = '%s$%s' % (salt, hash)

    @staticmethod
    def check_password(username, raw_password):
        user = User.get_user_with_username(username)
        salt, hash = user.password.split('$')
        return hash == hashlib.sha256('%s%s' % (salt, raw_password)).hexdigest()

    @staticmethod
    def make_random_password():
        return ''.join(
            random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(10))

    @staticmethod
    def get_user_with_username(username):
        return session.query(User).filter_by(username=username).first()

    @staticmethod
    def get_number_unvalidated():
        return session.query(User).filter_by(validated=False).count()


class UserTaskRolesHistory(Base, UserHistoryModel):
    __tablename__ = 'user_task_roles_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    case_id = Column(Integer, ForeignKey('cases.id'))
    role = Column(Unicode)
    date_time = Column(DateTime)
    user_change_id = Column(Integer, ForeignKey('users.id'))
    removed = Column(Boolean)

    user = relation('User', backref=backref('task_roles_history', order_by=desc(id)), foreign_keys=user_id)
    changes_user = relation('User', backref=backref('task_roles_change_history', order_by=desc(id)),
                            foreign_keys=user_change_id)
    task = relation('Task', backref=backref('task_roles_history', order_by=desc(id)))
    history_name = ("Task", "task", "task_id", "case_id")

    def __init__(self, user_task_role, user_change, removed=False):
        self.user = user_task_role.user
        self.task = user_task_role.task
        self.role = user_task_role.role
        self.changes_user = user_change
        self.date_time = datetime.now()
        self.removed = removed
        self.case_id = self.task.case.id

    @staticmethod
    def get_roles_for_obj(task, role):
        q = session.query(UserTaskRolesHistory).filter_by(task=task, role=role).all()
        return q

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @property
    def previous(self):
        q = session.query(UserTaskRolesHistory)
        q = q.filter_by(task_id=self.task_id, role=self.role).filter(UserTaskRolesHistory.id < self.id).order_by(
            desc(UserTaskRolesHistory.id))
        return q.first()


class UserTaskRoles(Base, Model):
    __tablename__ = 'user_task_roles'

    PRINCIPLE_INVESTIGATOR = 'Principle Investigator'
    SECONDARY_INVESTIGATOR = 'Secondary Investigator'
    PRINCIPLE_QA = 'Principle QA'
    SECONDARY_QA = 'Secondary QA'

    inv_roles = [PRINCIPLE_INVESTIGATOR, SECONDARY_INVESTIGATOR]
    qa_roles = [PRINCIPLE_QA, SECONDARY_QA]
    all_roles = inv_roles + qa_roles

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    role = Column(Unicode)

    user = relation('User', backref=backref('task_roles', order_by=desc(id)))
    task = relation('Task', backref=backref('task_roles', order_by=desc(id)))

    def __init__(self, user, task, role):
        self.user_id = user.id
        self.task_id = task.id
        self.role = role

    def add_change(self, change_user, new_user=None):
        UserTaskRolesHistory.change_user(self, new_user, change_user)

    @staticmethod
    def get_history(task, role):
        if role in UserTaskRoles.all_roles:
            return UserTaskRolesHistory.get_changes(task, role)
        return None

    @staticmethod
    def delete_if_already_exists(task_id, user_id, role):
        already = session.query(UserTaskRoles).filter_by(task_id=task_id, user_id=user_id, role=role).all()
        if len(already) > 0:
            for al in already:
                session.delete(al)


class UserCaseRolesHistory(Base, UserHistoryModel):
    __tablename__ = 'user_case_roles_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    case_id = Column(Integer, ForeignKey('cases.id'))
    role = Column(Unicode)
    date_time = Column(DateTime)
    user_change_id = Column(Integer, ForeignKey('users.id'))
    removed = Column(Boolean)

    user = relation('User', backref=backref('case_roles_history', order_by=desc(id)), foreign_keys=user_id)
    changes_user = relation('User', backref=backref('case_roles_change_history', order_by=desc(id)),
                            foreign_keys=user_change_id)
    case = relation('Case', backref=backref('case_roles_history', order_by=desc(id)))
    history_name = ("Case", "case", "case_id")

    def __init__(self, user_case_role, user_change, removed=False):
        self.user = user_case_role.user
        self.case = user_case_role.case
        self.role = user_case_role.role
        self.changes_user = user_change
        self.date_time = datetime.now()
        self.removed = removed

    @staticmethod
    def get_roles_for_obj(case, role):
        q = session.query(UserCaseRolesHistory).filter_by(case=case, role=role).all()
        return q

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @property
    def previous(self):
        q = session.query(UserCaseRolesHistory)
        q = q.filter_by(case_id=self.case_id, role=self.role).filter(UserCaseRolesHistory.id < self.id).order_by(
            desc(UserCaseRolesHistory.id))
        return q.first()

    def __repr__(self):
        return "<CaseRoleHist Object[{}] '{}'>".format(self.role, self.user.fullname)


class UserCaseRoles(Base, Model):
    __tablename__ = 'user_case_roles'

    PRINCIPLE_CASE_MANAGER = 'Principle Case Manager'
    SECONDARY_CASE_MANAGER = 'Secondary Case Manager'
    REQUESTER = 'Requester'
    AUTHORISER = 'Authoriser'

    case_managers = [PRINCIPLE_CASE_MANAGER, SECONDARY_CASE_MANAGER]
    authorisers = [AUTHORISER]

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    case_id = Column(Integer, ForeignKey('cases.id'))
    role = Column(Unicode)

    user = relation('User', backref=backref('case_roles', order_by=desc(id)))
    case = relation('Case', backref=backref('case_roles', order_by=desc(id)))

    def __init__(self, user, case, role):
        self.user = user
        self.case = case
        self.role = role

    def add_change(self, change_user, new_user=None):
        UserCaseRolesHistory.change_user(self, new_user, change_user)

    @staticmethod
    def get_history(case, role):
        if role in UserCaseRoles.case_managers or role in UserCaseRoles.authorisers:
            return UserCaseRolesHistory.get_changes(case, role)
        return None


class UserRolesHistory(Base, UserHistoryModel):
    __tablename__ = 'user_roles_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(Unicode)
    removed = Column(Boolean)
    date_time = Column(DateTime)
    changes_user_id = Column(Integer, ForeignKey('users.id'))

    user = relation('User', backref=backref('roles_history', order_by=asc(date_time)), foreign_keys=user_id)
    changes_user = relation('User', backref=backref('user_roles_history_changes'), foreign_keys=changes_user_id)

    history_name = ("Role", "role", "user_id")

    def __init__(self, user_role, user_who_made_changes):
        self.user_id = user_role.user_id
        self.role = user_role.role
        self.removed = user_role.removed
        self.date_time = datetime.now()
        self.changes_user = user_who_made_changes

    @property
    def previous(self):
        q = session.query(UserRolesHistory)
        q = q.filter_by(user_id=self.user_id, role=self.role).filter(UserRolesHistory.id < self.id).order_by(
            desc(UserRolesHistory.id))
        q1 = q.count()
        if q1 == 0:
            return False
        return q.first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @staticmethod
    def get_roles_for_obj(user, role):
        q = session.query(UserRolesHistory).filter_by(user=user, role=role).order_by(
            asc(UserRolesHistory.date_time)).all()
        return q

    def difference(self, previous_object, role_name):
        differences = {}
        if self.removed:
            differences[role_name] = ("ADD", self.user.fullname)
        else:
            differences[role_name] = ("DEL", previous_object.user.fullname)
        return differences


class UserRoles(Base, Model):
    __tablename__ = 'user_roles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(Unicode)
    removed = Column(Boolean)

    user = relation('User', backref=backref('roles', order_by=desc(id)))

    ADMIN = 'Administrator'
    CASE_MAN = 'Case Manager'
    REQUESTER = 'Requester'
    AUTH = 'Authoriser'
    INV = 'Investigator'
    QA = 'QA'

    roles = [ADMIN, CASE_MAN, REQUESTER, AUTH, INV, QA]

    def __init__(self, user, role, removed):
        self.user_id = user.id
        if role in self.roles:
            self.role = role
            self.removed = removed
        else:
            raise Exception("Invalid Role")

    def add_change(self, user):
        change = UserRolesHistory(self, user)
        session.add(change)
        session.flush()

    @staticmethod
    def check_user_has_active_role(user, role):
        q = session.query(UserRoles).filter_by(user=user, role=role).first()
        if q is None:
            return False
        elif q.removed is False:
            return True
        else:
            return False

    @staticmethod
    def edit_user_role(user, role, change_user):
        q = session.query(UserRoles).filter_by(user=user, role=role).first()
        q.removed = not q.removed
        session.flush()
        q.add_change(change_user)

    @staticmethod
    def check_if_user_is_QA_for_task(task, QA_user):
        if QA_user in task.investigators:
            return False
        return True

    @staticmethod
    def check_if_user_is_investigator_for_case(case, user):
        if user in case.case_managers:
            return False
        return True

    @staticmethod
    def get_role_names(user_id):
        q = session.query(UserRoles).filter_by(user_id=user_id, removed=False).all()
        if len(q) > 0:
            return [x.role for x in q]
        else:
            return []

    @staticmethod
    def get_investigators():
        q = session.query(User).join('roles').filter_by(role=UserRoles.INV, removed=False)
        return q.all()

    @staticmethod
    def get_managers():
        q = session.query(User).join('roles').filter_by(role=UserRoles.CASE_MAN, removed=False)
        return q.all()

    @staticmethod
    def get_authorisers():
        q = session.query(User).join('roles').filter_by(role=UserRoles.AUTH, removed=False)
        return q.all()

    @staticmethod
    def get_qas():
        q = session.query(User).join('roles').filter_by(role=UserRoles.QA, removed=False)
        return q.all()

    @staticmethod
    def get_admins():
        q = session.query(User).join('roles').filter_by(role=UserRoles.ADMIN, removed=False)
        return q.all()

    def __repr__(self):
        return "<Role Object[{}] '{}' ({})>".format(self.role, self.user.fullname, self.removed)


class TaskTimeSheets(Base, Model):
    __tablename__ = 'task_timesheets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    date = Column(Date)
    hours = Column(Float)

    user = relation('User', backref=backref('task_timesheet', order_by=desc(id)))
    task = relation('Task', backref=backref('task_timesheet', order_by=desc(id)))

    def __init__(self, user, task, date, hours):
        self.user = user
        self.task = task
        self.date = date
        self.hours = hours


class CaseTimeSheets(Base, Model):
    __tablename__ = 'case_timesheets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    case_id = Column(Integer, ForeignKey('cases.id'))
    date = Column(Date)
    hours = Column(Float)

    user = relation('User', backref=backref('case_timesheet', order_by=desc(id)))
    case = relation('Case', backref=backref('case_timesheet', order_by=desc(id)))

    def __init__(self, user, case, date, hours):

        self.user = user
        self.case = case
        self.date = date
        self.hours = hours