# python imports
from datetime import datetime
from hashlib import sha256
from os import path, rename
import shutil
# library imports
from sqlalchemy import Table, Column, Integer, Boolean, Unicode, ForeignKey, DateTime, asc, desc, and_, or_
from sqlalchemy.orm import backref, relation
from qrcode import *
from werkzeug.exceptions import Forbidden
# local imports
from models import Base, Model, HistoryModel
from generalModel import ForemanOptions
from userModel import UserTaskRoles, User, UserCaseRoles
from ..utils.utils import session, ROOT_DIR


class LinkedCase(Base, Model):
    __tablename__ = 'linked_cases'

    id = Column(Integer, primary_key=True)
    case_linker_id = Column(Integer, ForeignKey('cases.id'), primary_key=True)
    case_linkee_id = Column(Integer, ForeignKey('cases.id'), primary_key=True)
    reason = Column(Unicode)
    date_time = Column(DateTime)
    removed = Column(Boolean)
    user_id = Column(Integer, ForeignKey('users.id'))

    case_linkers = relation('Case', backref=backref('linked'), foreign_keys=case_linker_id)
    case_linkees = relation('Case', backref=backref('linkees'), foreign_keys=case_linkee_id)
    user = relation('User', backref=backref('case_link_changes'))

    def __init__(self, linker, linkee, reason, user, removed=False):
        self.case_linker_id = linker.id
        self.case_linkee_id = linkee.id
        self.date_time = datetime.now()
        self.reason = reason
        self.removed = removed
        self.user = user

    def bidirectional(self, link, direction):
        # swap the linker and linkee
        if direction == "linkee":
            linker_id = link.id
            linkee_id = self.case_linker_id
        else:
            linker_id = self.case_linkee_id
            linkee_id = link.id

        q = session.query(LinkedCase).filter_by(case_linker_id=linker_id, case_linkee_id=linkee_id). \
            order_by(desc(LinkedCase.date_time)).all()

        if len(q) == 0 or q[0].removed is True or self.link_removed(link.id) is True:
            return False
        else:
            return True

    @staticmethod
    def get_links(case):
        results = []
        for link in case.linked:
            if link.case_linkees not in results and link.link_removed(link.case_linkees.id) is False:
                results.append(link.case_linkees)
        return results

    @staticmethod
    def get_from_links(case):
        results = []
        for link in case.linkees:
            if link.case_linkers not in results and link.link_removed(case.id) is False:
                results.append(link.case_linkers)
        return results

    def link_removed(self, with_link):
        q = session.query(LinkedCase).filter_by(case_linker_id=self.case_linker_id, case_linkee_id=with_link). \
            order_by(desc(LinkedCase.id)).first()
        if q and q.removed is True:
            return True
        else:
            return False

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)


class CaseStatus(Base, HistoryModel):
    __tablename__ = 'case_statuses'

    CREATED = 'Created'
    OPEN = 'Open'
    CLOSED = 'Closed'
    ARCHIVED = 'Archived'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    date_time = Column(DateTime)
    status = Column(Unicode)
    user_id = Column(Integer, ForeignKey('users.id'))

    case = relation('Case', backref=backref('statuses', order_by=asc(date_time)))
    user = relation('User', backref=backref('case_status_changes'))

    closedStatuses = [CLOSED, ARCHIVED]
    all_statuses = [CREATED, OPEN, CLOSED, ARCHIVED]

    history_backref = "statuses"
    comparable_fields = {'Status': 'status'}
    object_name = "Case"
    history_name = ("Case", "case_name")

    def __init__(self, case_id, status, user):
        self.status = status
        self.date_time = datetime.now()
        self.case_id = case_id
        self.user = user

    @property
    def previous(self):
        q = session.query(CaseStatus)
        q = q.filter_by(case_id=self.case_id).filter(CaseStatus.id < self.id)
        return q.order_by(desc(CaseStatus.id)).first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @property
    def case_name(self):
        return self.case.case_name


class CaseHistory(HistoryModel, Base):
    __tablename__ = 'case_history'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    case_name = Column(Unicode)
    reference = Column(Unicode)
    background = Column(Unicode)
    private = Column(Boolean)
    date_time = Column(DateTime)
    location = Column(Unicode)
    user_id = Column(Integer, ForeignKey('users.id'))
    classification = Column(Unicode)
    case_type = Column(Unicode)
    justification = Column(Unicode)

    case = relation('Case', backref=backref('history', order_by=asc(date_time)))
    user = relation('User', backref=backref('case_history_changes'))

    comparable_fields = {'Case Name': 'case_name', 'Reference': 'reference', 'Background': 'background',
                         "Case Files Location": 'location', 'Classification': 'classification',
                         'Case Type:': 'case_type', 'Justification': 'justification'}
    history_name = ("Case", "case_name")

    def __init__(self, case, user):
        self.case_id = case.id
        self.case_name = case.case_name
        self.reference = case.reference
        self.private = case.private
        self.background = case.background
        self.date_time = datetime.now()
        self.user = user
        self.location = case.location
        self.classification = case.classification
        self.case_type = case.case_type
        self.justification = case.justification

    @property
    def previous(self):
        q = session.query(CaseHistory)
        q = q.filter_by(case_id=self.case_id).filter(CaseHistory.id != self.id)
        return q.order_by(desc(CaseHistory.id)).first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    def difference(self, case_history):
        differences = HistoryModel.difference(self, case_history)
        if self.private != case_history.private:
            differences['Private Setting'] = ("On", "Off") if self.private else ("Off", "On")
        return differences


class Case(Base, Model):
    __tablename__ = 'cases'

    id = Column(Integer, primary_key=True)
    case_name = Column(Unicode)
    reference = Column(Unicode)
    currentStatus = Column(Unicode)
    private = Column(Boolean)
    background = Column(Unicode)
    location = Column(Unicode)
    creation_date = Column(DateTime)
    classification = Column(Unicode)
    justification = Column(Unicode)
    case_type = Column(Unicode)

    def __init__(self, case_name, user, background=None, reference=None, private=False, location=None,
                 classification=None, case_type=None, justification=None):
        self.case_name = case_name
        self.reference = reference
        self.set_status(CaseStatus.CREATED, user)
        self.private = private
        self.background = background
        self.classification = classification
        self.case_type = case_type
        self.justification = justification
        if location is None:
            self.location = ForemanOptions.get_default_location()
        else:
            self.location = location
        self.creation_date = datetime.now()

    @property
    def date_created(self):
        return ForemanOptions.get_date(self.creation_date)

    def set_status(self, status, user):
        self.currentStatus = status
        self.statuses.append(CaseStatus(self.id, status, user))
        session.flush()

    def get_status(self):
        return session.query(CaseStatus).filter_by(case_id=self.id).order_by(desc(CaseStatus.id)).first()

    def add_change(self, user):
        change = CaseHistory(self, user)
        session.add(change)
        session.flush()

    @property
    def status(self):
        return self.currentStatus

    def open_case(self):
        self.set_status(CaseStatus.OPEN)

    def close_case(self):
        self.set_status(CaseStatus.CLOSED)

    def archive_case(self):
        self.set_status(CaseStatus.ARCHIVED)

    def get_links(self):
        return LinkedCase.get_links(self)

    def get_from_links(self):
        return LinkedCase.get_from_links(self)

    @staticmethod
    def cases_with_user_involved(user_id):
        q_case_roles = session.query(Case).join('case_roles').filter_by(user_id=user_id)
        q_task_roles = session.query(Case).join('tasks').join(Task.task_roles).filter_by(user_id=user_id)
        q = q_case_roles.union(q_task_roles)
        return q.all()

    def get_user_roles(self, user_id):
        return session.query(UserCaseRoles).filter_by(case_id=self.id, user_id=user_id).all()

    @staticmethod
    def get_cases(status, current_user, user=False, QA=False, current_user_perms=False, case_perm_checker=None):
        q = session.query(Case)
        if status != 'All' and status != "Queued":
            q = q.filter_by(currentStatus=status)
        elif status == "Queued":
            q = q.filter_by(currentStatus=CaseStatus.OPEN).join('tasks').filter(Task.currentStatus == TaskStatus.QUEUED)
        if user is True:
            q = q.join('tasks').join(Task.task_roles)
            if QA:
                q = q.filter(and_(UserTaskRoles.user_id == current_user.id, UserTaskRoles.role.in_(UserTaskRoles.qa_roles)))
            else:
                q = q.filter(and_(UserTaskRoles.user_id == current_user.id, UserTaskRoles.role.in_(UserTaskRoles.inv_roles)))
            return q.all()
        else:
            cases = q.all()
            output = []
            for case in cases:
                try:
                    case_perm_checker(current_user, case, "view")
                    output.append(case)
                except Forbidden:
                    pass
            return output

    def __repr__(self):
        return "<Case Object[{}] '{}' [{}]>".format(self.id, self.case_name, self.status)

    def __str__(self):
        return "{}".format(self.case_name)

    @property
    def principle_case_manager(self):
        return User.get_user_with_role(UserCaseRoles.PRINCIPLE_CASE_MANAGER, case_id=self.id)

    @property
    def secondary_case_manager(self):
        return User.get_user_with_role(UserCaseRoles.SECONDARY_CASE_MANAGER, case_id=self.id)

    @property
    def case_managers(self):
        return [self.principle_case_manager, self.secondary_case_manager]

    @property
    def requester(self):
        return User.get_user_with_role(UserCaseRoles.REQUESTER, case_id=self.id)


class ChainOfCustody(Base, Model):
    __tablename__ = 'chain_custody'

    id = Column(Integer, primary_key=True)
    evidence_id = Column(Integer, ForeignKey('evidence.id'))
    date_recorded = Column(DateTime)  # date this entry was made, always "now"
    date_of_custody = Column(DateTime)  # date the evidence was checked in / out
    user_id = Column(Integer, ForeignKey('users.id'))
    check_in = Column(Boolean)
    comment = Column(Unicode)
    custody_receipt = Column(Unicode)
    custody_receipt_label = Column(Unicode)
    custodian = Column(Unicode)

    user = relation('User', backref=backref('evidence_handled', order_by=asc(date_recorded)))
    evidence = relation('Evidence', backref=backref('user_handled', order_by=asc(id)))

    def __init__(self, evidence, user, custodian, date_of_custody, check_in, comment):
        self.evidence = evidence
        self.user = user
        self.check_in = check_in
        self.date_recorded = datetime.now()
        self.date_of_custody = date_of_custody
        self.comment = comment
        self.custodian = custodian

    def upload_custody_receipt(self, custody_receipt, label):
        if custody_receipt is not None:
            old_file_name = path.split(custody_receipt)[-1]
            new_file_name = str(self.id) + "_" + old_file_name
            location = path.join(ROOT_DIR, 'static', 'evidence_custody_receipts', new_file_name)
            if path.dirname(path.abspath(custody_receipt)) == path.dirname(path.abspath(location)):
                rename(custody_receipt, location)
            else:
                shutil.copy(custody_receipt, location)
            self.custody_receipt = new_file_name
            self.custody_receipt_label = label
            return new_file_name
        else:
            return None

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_recorded)

    @property
    def custody_date(self):
        return ForemanOptions.get_date(self.date_of_custody)


class EvidenceHistory(HistoryModel, Base):
    __tablename__ = 'evidence_history'

    id = Column(Integer, primary_key=True)
    evidence_id = Column(Integer, ForeignKey('evidence.id'))
    date_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    case_id = Column(Integer, ForeignKey('cases.id'))
    reference = Column(Unicode)
    type = Column(Unicode)
    qr_code = Column(Boolean)
    qr_code_text = Column(Unicode)
    comment = Column(Unicode)
    originator = Column(Unicode)
    photographs = Column(Boolean)
    evidence_bag_number = Column(Unicode)
    location = Column(Unicode)

    evidence = relation('Evidence', backref=backref('history', order_by=asc(date_time)))
    user = relation('User', backref=backref('evidence_history_changes'))
    case = relation('Case', backref=backref('evidence_history', order_by=asc(reference)))

    object_name = "Evidence"
    comparable_fields = {'Type': 'type',
                         'Reference': 'reference',
                         'Location': 'location',
                         'Evidence Bag Number': 'evidence_bag_number',
                         'Originator': 'originator'}
    history_name = ("Evidence", "reference")

    def __init__(self, evidence, user):
        self.evidence = evidence
        self.case = evidence.case
        self.type = evidence.type
        self.qr_code = evidence.qr_code
        self.qr_code_text = evidence.qr_code_text
        self.comment = evidence.comment
        self.originator = evidence.originator
        self.photographs = evidence.photographs
        self.evidence_bag_number = evidence.evidence_bag_number
        self.location = evidence.location
        self.reference = evidence.reference
        self.date_time = datetime.now()
        self.user = user

    @property
    def previous(self):
        q = session.query(EvidenceHistory)
        q = q.filter_by(evidence_id=self.evidence_id).filter(EvidenceHistory.id != self.id)
        return q.order_by(desc(EvidenceHistory.id)).first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    def difference(self, evidence_history):
        differences = HistoryModel.difference(self, evidence_history)
        if self.photographs != evidence_history.photographs:
            differences['Private Setting'] = ("having photographs", "no photographs") if self.photographs else (
                "no photographs", "having photographs")
        if self.qr_code != evidence_history.qr_code:
            differences['QR Code'] = ("has QR Code", "has no QR Code") if self.qr_code else (
                "has no QR Code", "has QR Code")
        if self.comment != evidence_history.comment:
            differences['Comment'] = ("'" + self.comment + "'", "'" + evidence_history.comment + "'")
        if self.qr_code_text != evidence_history.qr_code_text:
            differences['QR Code Text'] = ("'" + self.qr_code_text + "'", "'" + evidence_history.qr_code_text + "'")
        if self.case_id != evidence_history.case_id:
            if self.case_id is None:
                differences['Case'] = ("ADD", self.case.case_name)
            else:
                differences['Case'] = ("DEL", evidence_history.case.case_name)
        return differences


class Evidence(Base, Model):
    __tablename__ = 'evidence'

    id = Column(Integer, primary_key=True)
    reference = Column(Unicode)
    type = Column(Unicode)
    case_id = Column(Integer, ForeignKey('cases.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    qr_code = Column(Boolean)
    qr_code_text = Column(Unicode)
    comment = Column(Unicode)
    originator = Column(Unicode)
    photographs = Column(Boolean)
    evidence_bag_number = Column(Unicode)
    location = Column(Unicode)
    date_added = Column(DateTime)

    case = relation('Case', backref=backref('evidence', order_by=asc(reference)))
    user = relation('User', backref=backref('evidence_added', order_by=asc(reference)))

    def __init__(self, case, reference, evidence_type, comment, originator, location, user_added,
                 evidence_bag_number=None, photographs=False, qr=True):
        self.case = case
        self.reference = reference
        self.type = evidence_type
        self.comment = comment
        self.originator = originator
        self.photographs = photographs
        self.evidence_bag_number = evidence_bag_number
        self.location = location
        self.date_added = datetime.now()
        self.user = user_added

        if qr:
            self.qr_code = True
            self.qr_code_text = self.generate_qr_code_text()
            self.create_qr_code()
        else:
            self.qr_code = False
            self.qr_code_text = ""

    def generate_qr_code_text(self):
        return "Case: {} | Ref: {} | Date Added: {} | Added by: {}".format(self.case.case_name, self.reference,
                                                                           self.date_added, self.user.fullname)

    def check_in(self, custodian, user, date, comment, attachment=None, label=None):
        chain = ChainOfCustody(self, user, custodian, date, True, comment)
        session.add(chain)
        session.flush()
        chain.upload_custody_receipt(attachment, label)

    def check_out(self, custodian, user, date, comment, attachment=None, label=None):
        chain = ChainOfCustody(self, user, custodian, date, False, comment)
        session.add(chain)
        session.flush()
        chain.upload_custody_receipt(attachment, label)

    def add_change(self, user):
        change = EvidenceHistory(self, user)
        session.add(change)
        session.flush()

    def create_qr_code(self):
        qr = QRCode(error_correction=ERROR_CORRECT_L)
        qr.add_data(self.qr_code_text)
        qr.make()
        img = qr.make_image()

        qr_image_location = path.join(ROOT_DIR, 'static', 'evidence_QR_codes', str(self.id) + '.png')
        img.save(qr_image_location, "PNG")

    def disassociate(self):
        self.case_id = None

    def associate(self, case):
        self.case = case

    @property
    def current_status(self):
        q = session.query(ChainOfCustody).filter_by(evidence_id=self.id).order_by(desc(ChainOfCustody.id)).first()
        return q

    @property
    def icon(self):
        return self.type.replace(" ", "").lower()


class TaskStatus(Base, HistoryModel):
    __tablename__ = 'task_statuses'

    CREATED = 'Created'
    QUEUED = 'Queued'
    ALLOCATED = 'Allocated'
    PROGRESS = 'Forensics in Process'
    QA = 'QA'
    DELIVERY = 'Delivery'
    COMPLETE = 'Complete'
    CLOSED = 'Closed'

    openStatuses = [CREATED, QUEUED, ALLOCATED, PROGRESS, QA, DELIVERY]
    notStarted = [QUEUED]
    preInvestigation = [QUEUED, ALLOCATED]
    notesAllowed = [PROGRESS, QA, DELIVERY, COMPLETE]
    closedStatuses = [COMPLETE, CLOSED]
    invRoles = [ALLOCATED, PROGRESS, DELIVERY, COMPLETE]
    qaRoles = [QA]
    all_statuses = [CREATED, QUEUED, ALLOCATED, PROGRESS, QA, DELIVERY, COMPLETE, CLOSED]

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    date_time = Column(DateTime)
    status = Column(Unicode)
    note = Column(Unicode)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relation('User', backref=backref('task_status_changes'))
    task = relation('Task', backref=backref('statuses', order_by=asc(date_time)))

    history_backref = "statuses"
    comparable_fields = {'Status': 'status'}
    object_name = "Task"
    history_name = ("Task", "task_name")

    def __init__(self, task_id, status, user):
        self.status = status
        self.date_time = datetime.now()
        self.task_id = task_id
        self.user = user

    @property
    def previous(self):
        q = session.query(TaskStatus)
        q = q.filter_by(task_id=self.task_id).filter(TaskStatus.id != self.id)
        return q.order_by(desc(TaskStatus.id)).first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @property
    def task_name(self):
        return self.task.task_name


class TaskNotes(Base, Model):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    date_time = Column(DateTime)
    note = Column(Unicode)
    hash = Column(Unicode)
    author_id = Column(Integer, ForeignKey('users.id'))

    task = relation('Task', backref=backref('notes', order_by=asc(date_time)))
    author = relation('User', backref=backref('notes', order_by=asc(id)))

    def __init__(self, note, author_id, task_id):
        self.note = note
        self.author_id = author_id
        self.task_id = task_id
        self.date_time = datetime.now()
        self.hash = sha256(self.note.encode("utf-8")).hexdigest()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    def check_hash(self):
        return self.hash == sha256(self.note.encode("utf-8")).hexdigest()


class TaskHistory(Base, HistoryModel):
    __tablename__ = 'task_history'

    id = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task_type_id = Column(Integer, ForeignKey('task_types.id'))
    task_name = Column(Unicode)
    location = Column(Unicode)
    background = Column(Unicode)

    task = relation('Task', backref=backref('history', order_by=asc(date_time)))
    user = relation('User', backref=backref('task_history_changes', order_by=asc(id)))
    task_type = relation('TaskType', backref=backref('task_history', order_by=desc(task_type_id)))

    comparable_fields = {'Task Name': 'task_name', 'Background': 'background', "Task Files Location": 'location'}
    history_name = ("Task", "task_name")

    def __init__(self, task, user):
        self.task_id = task.id
        self.task_name = task.task_name
        self.task_type = task.task_type
        self.background = task.background
        self.location = task.location
        self.date_time = datetime.now()
        self.user = user

    @property
    def previous(self):
        q = session.query(TaskHistory)
        q = q.filter_by(task_id=self.task_id).filter(TaskHistory.id != self.id)
        return q.order_by(desc(TaskHistory.id)).first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    def difference(self, previous_object):
        self.difference(previous_object)
        differences = HistoryModel.difference(self, previous_object)
        if self.task_type.task_type != previous_object.task_type.task_type:
            differences['Task Type'] = (self.task_type.task_type, previous_object.task_type.task_type)
        if self.task_type.category.category != previous_object.task_type.category.category:
            differences['Task Category'] = (self.task_type.category.category,
                                            previous_object.task_type.category.category)
        return differences


class Task(Base, Model):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    task_name = Column(Unicode)
    case_id = Column(Integer, ForeignKey('cases.id'))
    task_type_id = Column(Integer, ForeignKey('task_types.id'))
    background = Column(Unicode)
    princQA = Column(Boolean)
    seconQA = Column(Boolean)
    currentStatus = Column(Unicode)
    location = Column(Unicode)
    creation_date = Column(DateTime)

    case = relation('Case', backref=backref('tasks', order_by=desc(id)))
    task_type = relation('TaskType', backref=backref('tasks', order_by=desc(task_type_id)))

    def __init__(self, case, task_type, task_name, user, background=None, location=None):
        self.task_name = task_name
        self.case = case
        self.task_type = task_type
        self.background = background
        if location is None:
            self.location = self.case.location
        else:
            self.location = location
        self.set_status(TaskStatus.CREATED, user)
        self.princQA = False
        self.seconQA = False
        self.creation_date = datetime.now()

    @property
    def date_created(self):
        return ForemanOptions.get_date(self.creation_date)

    def add_change(self, user):
        change = TaskHistory(self, user)
        session.add(change)
        session.flush()

    def set_status(self, status, user):
        self.currentStatus = status
        self.statuses.append(TaskStatus(self.id, status, user))
        session.flush()

    def get_status(self):
        return session.query(TaskStatus).filter_by(task_id=self.id).order_by(desc(TaskStatus.id)).first()

    def get_user_roles(self, user_id):
        return session.query(UserTaskRoles).filter_by(task_id=self.id, user_id=user_id).all()

    @property
    def status(self):
        return session.query(TaskStatus).filter_by(task_id=self.id).order_by(desc(TaskStatus.id)).first().status

    def add_note(self, note, author):
        self.notes.append(TaskNotes(note, author.id, self.id))

    def assign_task(self, investigator, principle=True, manager=None):
        if principle:
            inv_type = "Principle"
            role_type = UserTaskRoles.PRINCIPLE_INVESTIGATOR
            self.set_status(TaskStatus.ALLOCATED, investigator)
        else:
            self.set_status(TaskStatus.QUEUED, investigator)
            role_type = UserTaskRoles.SECONDARY_INVESTIGATOR
            inv_type = "Secondary"
        session.flush()

        UserTaskRoles.delete_if_already_exists(self.id, investigator.id, role_type)

        u = UserTaskRoles(investigator, self, role_type)
        session.add(u)
        session.flush()
        if manager is None:
            u.add_change(investigator)
        else:
            u.add_change(manager)
        session.flush()

    def assign_QA(self, principle_qa, secondary_qa, assignee, single=False):
        self.set_status(self.get_status().status, assignee)
        currentStatus = self.get_status()

        if single is True and self.principle_QA is not None:
            role = UserTaskRoles.SECONDARY_QA
            role_name = "secondary"
        else:
            role = UserTaskRoles.PRINCIPLE_QA
            role_name = "primary"

        if single is True:
            currentStatus.note = "{} has assigned {} as {} QA".format(assignee.fullname, principle_qa.fullname,
                                                                      role_name)
        else:
            secondary = ""
            if secondary_qa:
                secondary = " and {} as secondary QA".format(secondary_qa.fullname)
            currentStatus.note = "{} has assigned {} as primary QA {}".format(assignee.fullname, principle_qa.fullname,
                                                                              secondary)

        UserTaskRoles.delete_if_already_exists(self.id, principle_qa.id, role)

        u = UserTaskRoles(principle_qa, self, role)
        session.add(u)
        session.flush()
        u.add_change(assignee)

        if secondary_qa:
            UserTaskRoles.delete_if_already_exists(self.id, secondary_qa.id, UserTaskRoles.SECONDARY_QA)
            u2 = UserTaskRoles(secondary_qa, self, UserTaskRoles.SECONDARY_QA)
            session.add(u2)
            session.flush()
            u2.add_change(assignee)


    def start_work(self, investigator):
        self.set_status(TaskStatus.PROGRESS, investigator)
        session.flush()

        currentStatus = self.get_status()
        currentStatus.note = "{} has started work on this task".format(investigator.fullname)
        session.flush()

    def pass_QA(self, note, author):
        self.notes.append(TaskNotes(note, author.id, self.id))
        currentStatus = self.get_status()

        if author.id == self.principle_QA.id:
            self.princQA = True
        elif self.secondary_QA is not None and author.id == self.secondary_QA.id:
            self.seconQA = True

        if self.secondary_QA is not None and self.princQA and self.seconQA:
            # QA complete, both QA pass
            self.set_status(TaskStatus.DELIVERY, author)
            currentStatus.note = currentStatus.note + " and by {}".format(author.fullname)
        elif self.secondary_QA is None and self.princQA:
            # QA complete and only one QA
            self.set_status(TaskStatus.DELIVERY, author)
            currentStatus.note = "QA passed by {}".format(author.fullname)
        elif self.secondary_QA is not None and not (self.princQA and self.seconQA):
            # one out of two has completed QA. No QA complete
            currentStatus.note = "QA passed by {}".format(author.fullname)

    def fail_QA(self, note, author):
        self.notes.append(TaskNotes(note, author.id, self.id))
        currentStatus = self.get_status()

        if author.id == self.principle_QA.id:
            self.princQA = True
        elif self.secondary_QA is not None and author.id == self.secondary_QA.id:
            self.seconQA = True
        currentStatus.note = "QA failed by {}".format(author.fullname)

        if self.secondary_QA is not None and not (self.princQA and self.seconQA):
            # one out of two has failed the QA
            currentStatus.note = "QA failed by {}".format(author.fullname)
            self.set_status(TaskStatus.PROGRESS, author)
        elif self.secondary_QA is None and self.princQA:
            # QA failed and only one QA
            self.set_status(TaskStatus.PROGRESS, author)
            currentStatus.note = "QA failed by {}".format(author.fullname)

        # reset the QAs
        self.princQA = False
        self.seconQA = False

    def request_QA(self, user):
        self.set_status(TaskStatus.QA, user)

    def close_task(self, user):
        self.set_status(TaskStatus.CLOSED, user)

    def deliver_task(self, user):
        self.set_status(TaskStatus.COMPLETE, user)

    @staticmethod
    def get_queued_tasks():
        q = session.query(Task).join('case').filter(Task.currentStatus == TaskStatus.QUEUED).filter(
            Case.currentStatus == CaseStatus.OPEN)
        return q.all()

    @staticmethod
    def _get_user_tasks(user=None, usergroups=None, statusgroups=None, case_perm_checker=None):
        q = session.query(Task)
        if statusgroups is not None:
            q = q.filter(Task.currentStatus.in_(statusgroups))
        if user is not None and usergroups is not None:
            q = q.join('task_roles').filter(and_(UserTaskRoles.user_id == user.id, UserTaskRoles.role.in_(usergroups)))
        q = q.join('case').filter(Case.currentStatus == CaseStatus.OPEN)
        if usergroups is None:
            tasks = q.all()
            output = []
            for task in tasks:
                try:

                    case_perm_checker(user, task, "view")
                    output.append(task)
                except Forbidden:
                    pass
            return output  # do now want to show private cases
        else:
            return q.all()

    @staticmethod
    def get_active_QAs(user=None, case_perm_checker=None):
        if not case_perm_checker:
            query = Task._get_user_tasks(user, UserTaskRoles.qa_roles, [TaskStatus.QA])
        else:
            query = Task._get_user_tasks(user, None, [TaskStatus.QA], case_perm_checker)
        return query

    @staticmethod
    def get_active_tasks(user=None, case_perm_checker=None):
        if not case_perm_checker:
            query = Task._get_user_tasks(user, UserTaskRoles.inv_roles, TaskStatus.openStatuses)
        else:
            query = Task._get_user_tasks(user, None, TaskStatus.openStatuses, case_perm_checker=case_perm_checker)
        return query

    @staticmethod
    def get_tasks_requiring_QA_by_user(user):
        principle = Task._get_user_tasks(user, [UserTaskRoles.PRINCIPLE_QA], [TaskStatus.QA])
        secondary = Task._get_user_tasks(user, [UserTaskRoles.SECONDARY_QA], [TaskStatus.QA])
        return principle, secondary

    @staticmethod
    def get_tasks_assigned_to_user(user):
        principle = Task._get_user_tasks(user, [UserTaskRoles.PRINCIPLE_INVESTIGATOR], TaskStatus.openStatuses)
        secondary = Task._get_user_tasks(user, [UserTaskRoles.SECONDARY_INVESTIGATOR], TaskStatus.openStatuses)
        return principle, secondary

    @property
    def principle_investigator(self):
        return User.get_user_with_role(UserTaskRoles.PRINCIPLE_INVESTIGATOR, task_id=self.id)

    @property
    def secondary_investigator(self):
        return User.get_user_with_role(UserTaskRoles.SECONDARY_INVESTIGATOR, task_id=self.id)

    @property
    def principle_QA(self):
        return User.get_user_with_role(UserTaskRoles.PRINCIPLE_QA, task_id=self.id)

    @property
    def secondary_QA(self):
        return User.get_user_with_role(UserTaskRoles.SECONDARY_QA, task_id=self.id)

    @property
    def investigators(self):
        query = session.query(User).join('task_roles').filter(and_(UserTaskRoles.task_id == self.id,
                                                                   or_(
                                                                       UserTaskRoles.role == UserTaskRoles.PRINCIPLE_INVESTIGATOR,
                                                                       UserTaskRoles.role == UserTaskRoles.SECONDARY_INVESTIGATOR)))
        return query.all()

    @property
    def QAs(self):
        query = session.query(User).join('task_roles').filter(and_(UserTaskRoles.task_id == self.id,
                                                                   or_(UserTaskRoles.role == UserTaskRoles.PRINCIPLE_QA,
                                                                       UserTaskRoles.role == UserTaskRoles.SECONDARY_QA)))
        return query.all()

    def __repr__(self):
        return "<Task Object[{}] '{}' for Case {} [{}]>".format(self.id, self.task_type, self.case.case_name,
                                                                self.get_status())

    def __str__(self):
        return "{}".format(self.task_name)