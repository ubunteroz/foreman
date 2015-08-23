# python imports
from datetime import datetime
import hashlib
from os import path, rename, remove
import shutil
import calendar
# library imports
from sqlalchemy import Table, Column, Integer, Boolean, Unicode, ForeignKey, DateTime, asc, desc, and_, or_, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import backref, relation
from qrcode import *
from werkzeug.exceptions import Forbidden
# local imports
from models import Base, Model, HistoryModel
from generalModel import ForemanOptions, TaskCategory, TaskType, CasePriority
from userModel import UserTaskRoles, User, UserCaseRoles
from ..utils.utils import session, ROOT_DIR, config, upload_file

hash_algorithm = config.get('forensics', 'hash_type').lower()
if hash_algorithm not in hashlib.algorithms:
    raise Exception('\n\nUnknown hash algorithm: {} in your config file.\n\n Please choose from: \n{}'.format(
        hash_algorithm, hashlib.algorithms))
hash_library = getattr(hashlib, hash_algorithm)


class CaseAuthorisation(Base, Model):
    __tablename__ = 'case_auth'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    reason = Column(Unicode)
    date_time = Column(DateTime)
    auth_id = Column(Integer, ForeignKey('users.id'))
    case_authorised = Column(Unicode)

    STATUS = {'AUTH': {'description': 'Authorised'},
              'NOAUTH': {'description': 'Rejected'},
              'PENDING': {'description': 'Pending'}, }

    case = relation('Case', backref=backref('authorisations', order_by=desc(date_time)))
    authoriser = relation('User', backref=backref('cases_authorised'))

    def __init__(self, authoriser, case, authorised, reason):
        self.authoriser = authoriser
        self.case = case
        self.case_authorised = authorised
        self.reason = reason
        self.date_time = datetime.now()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @staticmethod
    def get_changes(case):
        history_list = session.query(CaseAuthorisation).filter_by(case_id=case.id)

        change_log = []
        for entry in history_list.all():
            if entry.case_authorised == "NOAUTH":
                change_log.append({'date': entry.date,
                                   'date_time': entry.date_time,
                                   'user': entry.authoriser,
                                   'object': ("Case", entry.case.case_name, entry.case.id),
                                   'change_log': {'Case': ('NOAUTH', entry.reason)}})
            elif entry.case_authorised == "AUTH":
                change_log.append({'date': entry.date,
                                   'date_time': entry.date_time,
                                   'user': entry.authoriser,
                                   'object': ("Case", entry.case.case_name, entry.case.id),
                                   'change_log': {'Case': ('AUTH', entry.reason)}})
        return change_log


class LinkedCase(Base, HistoryModel):
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

    history_backref = "linked"
    comparable_fields = {}
    object_name = "Case"
    history_name = ("Case", "case_name", "case_linker_id")

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

    @property
    def previous(self):
        q = session.query(LinkedCase)
        q = q.filter_by(case_linker_id=self.case_linker_id).filter(LinkedCase.id < self.id)
        q = q.order_by(desc(LinkedCase.id))
        q1 = q.count()
        if q1 == 0:
            return self
        else:
            return q.first()

    def difference(self, link_history):
        differences = HistoryModel.difference(self, link_history)
        if link_history.removed is False:
            differences['Case Link'] = ("LINK", Case.get(link_history.case_linkee_id).case_name)
        else:
            differences['Case Link'] = ("UNLINK", Case.get(link_history.case_linkee_id).case_name)
        return differences

    @property
    def case_name(self):
        return Case.get(self.case_linker_id).case_name


class CaseStatus(Base, HistoryModel):
    __tablename__ = 'case_statuses'

    CREATED = 'Created'
    PENDING = 'Awaiting authorisation'
    REJECTED = 'Rejected'
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
    all_statuses = [CREATED, OPEN, CLOSED, ARCHIVED, PENDING, REJECTED]
    approved_statuses = [CREATED, OPEN, CLOSED, ARCHIVED]
    active_statuses = [CREATED, PENDING, REJECTED, OPEN]
    workable_statuses = [CREATED, OPEN]

    history_backref = "statuses"
    comparable_fields = {'Status': 'status'}
    object_name = "Case"
    history_name = ("Case", "case_name", "case_id")

    def __init__(self, case_id, status, user):
        self.status = status
        self.date_time = datetime.now()
        self.case_id = case_id
        self.user = user

    @property
    def previous(self):
        q = session.query(CaseStatus)
        q = q.filter_by(case_id=self.case_id).filter(CaseStatus.id < self.id)
        q = q.order_by(desc(CaseStatus.id))
        q1 = q.count()
        if q1 == 0:
            return False
        else:
            return q.first()

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
    case_priority = Column(Unicode)
    case_priority_colour = Column(Unicode)

    case = relation('Case', backref=backref('history', order_by=asc(date_time)))
    user = relation('User', backref=backref('case_history_changes'))

    comparable_fields = {'Case Name': 'case_name', 'Reference': 'reference', 'Background': 'background',
                         "Case Files Location": 'location', 'Classification': 'classification',
                         'Case Type:': 'case_type', 'Justification': 'justification', "Case Priority": 'case_priority'}
    history_name = ("Case", "case_name", "case_id")

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
        self.case_priority = case.case_priority
        self.case_priority_colour = case.case_priority_colour

    @property
    def previous(self):
        q = session.query(CaseHistory)
        q = q.filter_by(case_id=self.case_id).filter(CaseHistory.id < self.id).order_by(desc(CaseHistory.id))
        return q.first()

    @property
    def object_id(self):
        return self.case_id

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
    case_priority = Column(Unicode)
    case_priority_colour = Column(Unicode)

    def __init__(self, case_name, user, background=None, reference=None, private=False, location=None,
                 classification=None, case_type=None, justification=None, priority=None):
        self.case_name = case_name
        self.reference = reference
        self.set_status(CaseStatus.PENDING, user)
        self.private = private
        self.background = background
        self.classification = classification
        self.case_type = case_type
        self.justification = justification
        if priority is None:
            priority = CasePriority.default_value()
        self.case_priority = priority.case_priority
        self.case_priority_colour = priority.colour

        if location is None:
            self.location = ForemanOptions.get_default_location()
        else:
            self.location = location
        self.creation_date = datetime.now()

    def authorise(self, authoriser, reason, authorisation):
        auth = CaseAuthorisation(authoriser, self, authorisation, reason)
        session.add(auth)
        session.commit()

        if self.authorised.case_authorised == "AUTH":
            self.set_status(CaseStatus.CREATED, authoriser)
        elif self.authorised.case_authorised == "NOAUTH":
            self.set_status(CaseStatus.REJECTED, authoriser)

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

    def get_links(self, perm_checker=None, user=None):
        links = LinkedCase.get_links(self)
        output = []
        for link in links:
            try:
                if perm_checker and user:
                    perm_checker(user, link, "view")
                output.append(link)
            except Forbidden:
                pass
        return output

    def get_from_links(self, perm_checker=None, user=None):
        links = LinkedCase.get_from_links(self)
        output = []
        for link in links:
            try:
                if perm_checker and user:
                    perm_checker(user, link, "view")
                output.append(link)
            except Forbidden:
                pass
        return output

    @property
    def authorised(self):
        if len(self.authorisations) == 0:
            return None
        return self.authorisations[0]

    @staticmethod
    def get_num_cases_opened_on_date(date_required, on_status, case_type=None, by_month=False):
        if by_month:
            month = date_required.month
            year = date_required.year
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, calendar.monthrange(year, month)[1])
            q = session.query(func.count(Case.id))
            if on_status == CaseStatus.OPEN:
                q = q.filter(and_(Case.creation_date >= first_day, Case.creation_date <= last_day))
            else:
                q = q.join(CaseStatus).filter(
                    and_(CaseStatus.status == on_status, CaseStatus.date_time >= first_day,
                         CaseStatus.date_time <= last_day))
            if case_type is not None:
                q = q.filter(Case.case_type == case_type)
            return q.scalar()

    @staticmethod
    def cases_with_user_involved(user_id, active=False):
        q_case_roles = session.query(Case).join('case_roles').filter_by(user_id=user_id)
        q_task_roles = session.query(Case).join('tasks').join(Task.task_roles).filter_by(user_id=user_id)
        if active:
            q_case_roles = q_case_roles.filter(Case.currentStatus.in_(CaseStatus.active_statuses))
            q_task_roles = q_task_roles.filter(Case.currentStatus.in_(CaseStatus.active_statuses))
        q = q_case_roles.union(q_task_roles)
        return q.all()

    def get_user_roles(self, user_id):
        return session.query(UserCaseRoles).filter_by(case_id=self.id, user_id=user_id).all()

    @staticmethod
    def _check_perms(case_manager, cases, case_perm_checker):
        output = []
        for case in cases:
            try:
                case_perm_checker(case_manager, case, "view")
                output.append(case)
            except Forbidden:
                pass
        return output

    @staticmethod
    def get_completed_cases(case_manager, case_perm_checker, current_user):
        q = session.query(Case)
        q = q.join(UserCaseRoles).filter(UserCaseRoles.user_id == case_manager.id).filter(or_(
            UserCaseRoles.role == UserCaseRoles.PRINCIPLE_CASE_MANAGER,
            UserCaseRoles.role == UserCaseRoles.SECONDARY_CASE_MANAGER))
        q = q.filter(or_(Case.currentStatus == CaseStatus.CLOSED, Case.currentStatus == CaseStatus.ARCHIVED))
        return Case._check_perms(current_user, q, case_perm_checker)

    @staticmethod
    def get_current_cases(case_manager, case_perm_checker, current_user):
        q = session.query(Case)
        q = q.join(UserCaseRoles).filter(UserCaseRoles.user_id == case_manager.id).filter(or_(
            UserCaseRoles.role == UserCaseRoles.PRINCIPLE_CASE_MANAGER,
            UserCaseRoles.role == UserCaseRoles.SECONDARY_CASE_MANAGER))
        q = q.filter(or_(Case.currentStatus == CaseStatus.OPEN, Case.currentStatus == CaseStatus.CREATED))
        return Case._check_perms(current_user, q, case_perm_checker)

    @staticmethod
    def get_cases_requested(requester, case_perm_checker, current_user, statuses):
        q = session.query(Case)
        q = q.join(UserCaseRoles).filter(UserCaseRoles.user_id == requester.id). \
            filter(UserCaseRoles.role == UserCaseRoles.REQUESTER)
        q = q.filter(Case.currentStatus.in_(statuses))
        return Case._check_perms(current_user, q, case_perm_checker)

    @staticmethod
    def get_cases_authorised(authoriser, case_perm_checker, current_user, statuses):
        q = session.query(Case)
        q = q.join(UserCaseRoles).filter(UserCaseRoles.user_id == authoriser.id). \
            filter(UserCaseRoles.role == UserCaseRoles.AUTHORISER)
        q = q.filter(Case.currentStatus.in_(statuses))
        return Case._check_perms(current_user, q, case_perm_checker)

    @staticmethod
    def get_cases(status, current_user, user=False, QA=False, case_perm_checker=None, case_man=False):
        q = session.query(Case)
        if status != 'All' and status != "Queued" and status != "Workable":
            q = q.filter_by(currentStatus=status)
        elif status == "Queued":
            q = q.filter_by(currentStatus=CaseStatus.OPEN).join('tasks').filter(Task.currentStatus == TaskStatus.QUEUED)
        elif status == "Workable":
            q = q.filter(Case.currentStatus.in_(CaseStatus.workable_statuses))
        if user is True:
            q = q.join('tasks').join(Task.task_roles)
            if QA:
                q = q.filter(
                    and_(UserTaskRoles.user_id == current_user.id, UserTaskRoles.role.in_(UserTaskRoles.qa_roles)))
            else:
                q = q.filter(
                    and_(UserTaskRoles.user_id == current_user.id, UserTaskRoles.role.in_(UserTaskRoles.inv_roles)))
            return q.order_by(desc(Case.creation_date)).all()
        else:
            cases = q.order_by(desc(Case.creation_date)).all()
            output = []
            for case in cases:
                if (case_man is True and case.principle_case_manager is None and case.secondary_case_manager is None) \
                        or case_man is False:
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

    @property
    def authoriser(self):
        return User.get_user_with_role(UserCaseRoles.AUTHORISER, case_id=self.id)


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
            new_directory = path.join(ROOT_DIR, 'files', 'evidence_custody_receipts')
            file_name = upload_file(custody_receipt, new_directory)
            self.custody_receipt = file_name
            self.custody_receipt_label = label
            return file_name
        else:
            return None

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_recorded)

    @property
    def custody_date(self):
        return ForemanOptions.get_date(self.date_of_custody)

    @staticmethod
    def get_changes_for_user(user):
        q_checkin = session.query(ChainOfCustody).filter_by(user_id=user.id, check_in=True)
        q_checkout = session.query(ChainOfCustody).filter_by(user_id=user.id, check_in=False)

        change_log = []
        for entry in q_checkin.all():
            cr = ". Custody receipt uploaded" if entry.custody_receipt is not None else ""
            change_log.append({'date': entry.date,
                               'date_time': entry.date_recorded,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id,
                                          entry.evidence.case.id),
                               'change_log': "Evidence checked in{}".format(cr)})
        for entry in q_checkout.all():
            cr = ". Custody receipt uploaded" if entry.custody_receipt is not None else ""
            change_log.append({'date': entry.date,
                               'date_time': entry.date_recorded,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id,
                                          entry.evidence.case.id),
                               'change_log': "Evidence checked out{}".format(cr)})
        return change_log

    @staticmethod
    def get_changes(evidence):
        q_checkin = session.query(ChainOfCustody).filter_by(evidence_id=evidence.id, check_in=True)
        q_checkout = session.query(ChainOfCustody).filter_by(evidence_id=evidence.id, check_in=False)

        change_log = []
        for entry in q_checkin.all():
            cr = ". Custody receipt uploaded" if entry.custody_receipt is not None else ""
            change_log.append({'date': entry.date,
                               'date_time': entry.date_recorded,
                               'user': entry.user,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id,
                                          entry.evidence.case.id),
                               'change_log': "Evidence checked in{}".format(cr)})
        for entry in q_checkout.all():
            cr = ". Custody receipt uploaded" if entry.custody_receipt is not None else ""
            change_log.append({'date': entry.date,
                               'date_time': entry.date_recorded,
                               'user': entry.user,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id,
                                          entry.evidence.case.id),
                               'change_log': "Evidence checked out{}".format(cr)})
        return change_log


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
    evidence_bag_number = Column(Unicode)
    location = Column(Unicode)

    evidence = relation('Evidence', backref=backref('history', order_by=asc(date_time)))
    user = relation('User', backref=backref('evidence_history_changes'))

    object_name = "Evidence"
    comparable_fields = {'Type': 'type',
                         'Reference': 'reference',
                         'Location': 'location',
                         'Evidence Bag Number': 'evidence_bag_number',
                         'Originator': 'originator',
                         'Associated Case': 'case_id'}
    history_name = ("Evidence", "reference", "evidence_id", "case_id")

    def __init__(self, evidence, user):
        self.evidence = evidence
        if evidence.case:
            self.case_id = evidence.case.id
        else:
            self.case_id = None
        self.type = evidence.type
        self.qr_code = evidence.qr_code
        self.qr_code_text = evidence.qr_code_text
        self.comment = evidence.comment
        self.originator = evidence.originator
        self.evidence_bag_number = evidence.evidence_bag_number
        self.location = evidence.location
        self.reference = evidence.reference
        self.date_time = datetime.now()
        self.user = user

    @property
    def previous(self):
        q = session.query(EvidenceHistory)
        q = q.filter_by(evidence_id=self.evidence_id).filter(EvidenceHistory.id < self.id).order_by(
            desc(EvidenceHistory.id))
        return q.first()

    @property
    def object_id(self):
        return self.evidence_id

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    def difference(self, evidence_history):
        differences = HistoryModel.difference(self, evidence_history)
        if self.qr_code != evidence_history.qr_code:
            differences['QR Code'] = ("has QR Code", "has no QR Code") if self.qr_code else (
                "has no QR Code", "has QR Code")
        if self.comment != evidence_history.comment:
            differences['Comment'] = ("'" + self.comment + "'", "'" + evidence_history.comment + "'")
        if self.qr_code_text != evidence_history.qr_code_text:
            differences['QR Code Text'] = ("'" + self.qr_code_text + "'", "'" + evidence_history.qr_code_text + "'")
        if self.case_id != evidence_history.case_id:
            if self.case_id is None:
                differences['Associated Case'] = ("None", Case.get(evidence_history.case_id))
            else:
                differences['Associated Case'] = (Case.get(self.case_id), "None")
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
    evidence_bag_number = Column(Unicode)
    location = Column(Unicode)
    date_added = Column(DateTime)

    case = relation('Case', backref=backref('evidence', order_by=asc(reference)))
    user = relation('User', backref=backref('evidence_added', order_by=asc(reference)))

    def __init__(self, case, reference, evidence_type, comment, originator, location, user_added,
                 evidence_bag_number=None, qr=True):
        self.case = case
        self.reference = reference
        self.type = evidence_type
        self.comment = comment
        self.originator = originator
        self.evidence_bag_number = evidence_bag_number
        self.location = location
        self.date_added = datetime.now()
        self.user = user_added

        if qr:
            self.qr_code = True
            self.qr_code_text = self.generate_qr_code_text()
        else:
            self.qr_code = False
            self.qr_code_text = ""

    def generate_qr_code_text(self):
        if self.case is not None:
            return "Case: {} | Ref: {} | Date Added: {} | Added by: {}".format(self.case.case_name, self.reference,
                                                                               self.date_added, self.user.fullname)
        else:
            return "Case: None Assigned | Ref: {} | Date Added: {} | Added by: {}".format(self.reference,
                                                                                          self.date_added,
                                                                                          self.user.fullname)

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

        qr_image_location = path.abspath(path.join(ROOT_DIR, 'files', 'evidence_QR_codes', str(self.id) + '.png'))
        img.save(qr_image_location, "PNG")

    def disassociate(self):
        self.case = None
        session.flush()

    def associate(self, case):
        self.case = case
        session.flush()

    @property
    def current_status(self):
        q = session.query(ChainOfCustody).filter_by(evidence_id=self.id).order_by(desc(ChainOfCustody.id)).first()
        return q

    @property
    def icon(self):
        return self.type.replace(" ", "").lower()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_added)

    @staticmethod
    def get_all_evidence(user, case_perm_checker):
        q = session.query(Evidence)
        output = []
        for evi in q:
            try:
                case_perm_checker(user, evi, "view")
                output.append(evi)
            except Forbidden:
                pass
        return output


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
    case_id = Column(Integer, ForeignKey('cases.id'))
    date_time = Column(DateTime)
    status = Column(Unicode)
    note = Column(Unicode)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relation('User', backref=backref('task_status_changes'))
    task = relation('Task', backref=backref('statuses', order_by=asc(date_time)))

    history_backref = "statuses"
    comparable_fields = {'Status': 'status'}
    object_name = "Task"
    history_name = ("Task", "task_name", "task_id", "case_id")

    def __init__(self, task_id, status, user, case=None):
        self.status = status
        self.date_time = datetime.now()
        self.task_id = task_id
        if case:
            self.case_id = case.id
        else:
            self.case_id = Task.get(task_id).case.id
        self.user = user

    @property
    def previous(self):
        q = session.query(TaskStatus)
        q = q.filter_by(task_id=self.task_id).filter(TaskStatus.id < self.id).order_by(desc(TaskStatus.id))
        q1 = q.count()
        if q1 == 0:
            return False
        else:
            return q.first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @property
    def task_name(self):
        return self.task.task_name


class UploadModel(Model):
    id = Column(Integer, primary_key=True)

    date_time = Column(DateTime)
    file_note = Column(Unicode)
    file_hash = Column(Unicode)

    @declared_attr
    def uploader_id(cls):
        return Column(Integer, ForeignKey('users.id'))

    file_name = Column(Unicode)
    upload_location = Column(Unicode)
    file_title = Column(Unicode)
    deleted = Column(Boolean)
    date_deleted = Column(DateTime)

    @declared_attr
    def deleter_id(cls):
        return Column(Integer, ForeignKey('users.id'))

    ROOT = path.join(ROOT_DIR, 'files')

    def __init__(self, uploader_id, file_name, file_note, title):
        self.uploader_id = uploader_id
        self.date_time = datetime.now()
        self.file_name = file_name
        self.file_note = file_note
        self.file_title = title
        self.file_hash = self.compute_hash()
        self.deleted = False

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    @property
    def deleted_date(self):
        return ForemanOptions.get_date(self.date_deleted)

    @property
    def file_path(self):
        return path.join(self.upload_location, self.file_name)

    def check_hash(self):
        return self.file_hash == self.compute_hash()

    def compute_hash(self):
        f = open(path.join(self.ROOT, self.upload_location, self.file_name), "rb")
        d = hash_library()
        for buf in f.read(128):
            d.update(buf)
        return d.hexdigest()

    def delete(self, user):
        if path.exists(path.join(self.ROOT, self.upload_location, self.file_name)):
            remove(path.join(self.ROOT, self.upload_location, self.file_name))
        self.deleted = True
        self.deleter = user
        self.date_deleted = datetime.now()


class EvidencePhotoUpload(UploadModel, Base):
    __tablename__ = 'evidence_photo_uploads'

    evidence_id = Column(Integer, ForeignKey('evidence.id'))
    evidence = relation('Evidence', backref=backref('evidence_photos'))
    uploader = relation('User', backref=backref('evidence_photos_uploaded'),
                        foreign_keys='EvidencePhotoUpload.uploader_id')
    deleter = relation('User', backref=backref('evidence_photos_deleted'),
                       foreign_keys='EvidencePhotoUpload.deleter_id')
    DEFAULT_FOLDER = 'evidence_photos'

    def __init__(self, uploader_id, evidence_id, file_name, file_note, title):
        self.evidence_id = evidence_id
        self.upload_location = path.join(EvidencePhotoUpload.DEFAULT_FOLDER, str(evidence_id))
        UploadModel.__init__(self, uploader_id, file_name, file_note, title)

    @staticmethod
    def get_changes_for_user(user):
        q_added = session.query(EvidencePhotoUpload).filter_by(uploader_id=user.id)
        q_removed = session.query(EvidencePhotoUpload).filter_by(deleter_id=user.id)
        change_log = []
        for entry in q_added.all():
            change_log.append({'date': entry.date,
                               'date_time': entry.date_time,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id),
                               'change_log': "File '{}' was uploaded".format(entry.file_title)})

        for entry in q_removed.all():
            change_log.append({'date': entry.deleted_date,
                               'date_time': entry.date_deleted,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id),
                               'change_log': "File '{}' was deleted".format(entry.file_title)})
        return change_log

    @staticmethod
    def get_changes(evidence):
        q_added = session.query(EvidencePhotoUpload).filter_by(evidence_id=evidence.id)
        q_removed = session.query(EvidencePhotoUpload).filter_by(evidence_id=evidence.id, deleted=True)

        change_log = []
        for entry in q_added.all():
            change_log.append({'date': entry.date,
                               'date_time': entry.date_time,
                               'current': entry,
                               'user': entry.uploader,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id),
                               'change_log': "File '{}' was uploaded".format(entry.file_title)})

        for entry in q_removed.all():
            change_log.append({'date': entry.deleted_date,
                               'date_time': entry.date_deleted,
                               'current': entry,
                               'user': entry.deleter,
                               'object': ("Evidence", entry.evidence.reference, entry.evidence.id),
                               'change_log': "File '{}' was deleted".format(entry.file_title)})
        return change_log


class TaskUpload(UploadModel, Base):
    __tablename__ = 'task_uploads'

    task_id = Column(Integer, ForeignKey('tasks.id'))
    task = relation('Task', backref=backref('task_uploads'))
    uploader = relation('User', backref=backref('files_uploaded_to_tasks'), foreign_keys='TaskUpload.uploader_id')
    deleter = relation('User', backref=backref('files_deleted_from_tasks'), foreign_keys='TaskUpload.deleter_id')
    DEFAULT_FOLDER = 'task_uploads'

    def __init__(self, uploader_id, task_id, case_id, file_name, file_note, title):
        self.task_id = task_id
        self.upload_location = path.join(TaskUpload.DEFAULT_FOLDER, str(case_id) + "_" + str(task_id))
        UploadModel.__init__(self, uploader_id, file_name, file_note, title)

    @staticmethod
    def get_changes_for_user(user):
        q_added = session.query(TaskUpload).filter_by(uploader_id=user.id)
        q_removed = session.query(TaskUpload).filter_by(deleter_id=user.id)

        change_log = []
        for entry in q_added.all():
            change_log.append({'date': entry.date,
                               'date_time': entry.date_time,
                               'object': ("Task", entry.task.task_name, entry.task.id, entry.task.case.id),
                               'change_log': "File '{}' was uploaded".format(entry.file_title)})

        for entry in q_removed.all():
            change_log.append({'date': entry.deleted_date,
                               'date_time': entry.date_deleted,
                               'object': ("Task", entry.task.task_name, entry.task.id, entry.task.case.id),
                               'change_log': "File '{}' was deleted".format(entry.file_title)})
        return change_log

    @staticmethod
    def get_changes(task):
        q_added = session.query(TaskUpload).filter_by(task_id=task.id)
        q_removed = session.query(TaskUpload).filter_by(task_id=task.id, deleted=True)

        change_log = []
        for entry in q_added.all():
            change_log.append({'date': entry.date,
                               'date_time': entry.date_time,
                               'user': entry.uploader,
                               'current': entry,
                               'object': ("Task", entry.task.task_name, entry.task.id, entry.task.case.id),
                               'change_log': "File '{}' was uploaded".format(entry.file_title)})
        for entry in q_removed.all():
            change_log.append({'date': entry.deleted_date,
                               'date_time': entry.date_deleted,
                               'user': entry.deleter,
                               'current': entry,
                               'object': ("Task", entry.task.task_name, entry.task.id, entry.task.case.id),
                               'change_log': "File '{}' was deleted".format(entry.file_title)})
        return change_log


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
        self.hash = hash_library(self.note.encode("utf-8")).hexdigest()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    def check_hash(self):
        return self.hash == hash_library(self.note.encode("utf-8")).hexdigest()

    @staticmethod
    def get_changes_for_user(user):
        q_added = session.query(TaskNotes).filter_by(author_id=user.id)

        change_log = []
        for entry in q_added.all():
            change_log.append({'date': entry.date,
                               'date_time': entry.date_time,
                               'object': ("Task", entry.task.task_name, entry.task.id, entry.task.case.id),
                               'change_log': "Task notes were written"})
        return change_log

    @staticmethod
    def get_changes(task):
        q_added = session.query(TaskNotes).filter_by(task_id=task.id)

        change_log = []
        for entry in q_added.all():
            change_log.append({'date': entry.date,
                               'date_time': entry.date_time,
                               'user': entry.author,
                               'current': entry,
                               'object': ("Task", entry.task.task_name, entry.task.id, entry.task.case.id),
                               'change_log': "Task notes were written"})
        return change_log

class TaskHistory(Base, HistoryModel):
    __tablename__ = 'task_history'

    id = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task_type_id = Column(Integer, ForeignKey('task_types.id'))
    case_id = Column(Integer, ForeignKey('cases.id'))
    task_name = Column(Unicode)
    location = Column(Unicode)
    background = Column(Unicode)

    task = relation('Task', backref=backref('history', order_by=asc(date_time)))
    user = relation('User', backref=backref('task_history_changes', order_by=asc(id)))
    task_type = relation('TaskType', backref=backref('task_history', order_by=desc(task_type_id)))

    comparable_fields = {'Task Name': 'task_name', 'Background': 'background', "Task Files Location": 'location'}
    history_name = ("Task", "task_name", "task_id", "case_id")

    def __init__(self, task, user):
        self.task_id = task.id
        self.task_name = task.task_name
        self.task_type = task.task_type
        self.background = task.background
        self.location = task.location
        self.date_time = datetime.now()
        self.user = user
        self.case_id = task.case.id

    @property
    def previous(self):
        q = session.query(TaskHistory)
        q = q.filter_by(task_id=self.task_id).filter(TaskHistory.id < self.id).order_by(desc(TaskHistory.id))
        return q.first()

    @property
    def date(self):
        return ForemanOptions.get_date(self.date_time)

    def difference(self, previous_object):

        differences = HistoryModel.difference(self, previous_object)
        if self.task_type.task_type != previous_object.task_type.task_type:
            differences['Task Type'] = (self.task_type.task_type, previous_object.task_type.task_type)
        if self.task_type.category.category != previous_object.task_type.category.category:
            differences['Task Category'] = (self.task_type.category.category,
                                            previous_object.task_type.category.category)
        if self.case_id != previous_object.case_id:
            differences['Case'] = (Case.get(self.case_id).case_name, Case.get(previous_object.case_id).case_name)
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
        self.statuses.append(TaskStatus(self.id, status, user, self.case))
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
            role_type = UserTaskRoles.PRINCIPLE_INVESTIGATOR
            self.set_status(TaskStatus.ALLOCATED, investigator)
        else:
            role_type = UserTaskRoles.SECONDARY_INVESTIGATOR

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
    def _check_perms(investigator, tasks, case_perm_checker):
        output = []
        for task in tasks:
            try:
                case_perm_checker(investigator, task, "view")
                output.append(task)
            except Forbidden:
                pass
        return output

    @staticmethod
    def get_completed_qas(investigator, case_perm_checker, current_user):
        q = session.query(Task)
        q = q.join(UserTaskRoles).filter(UserTaskRoles.user_id == investigator.id).filter(or_(
            UserTaskRoles.role == UserTaskRoles.PRINCIPLE_QA,
            UserTaskRoles.role == UserTaskRoles.SECONDARY_QA))
        q = q.join(TaskStatus).filter(TaskStatus.status == TaskStatus.DELIVERY)
        return Task._check_perms(current_user, q, case_perm_checker)

    @staticmethod
    def get_current_qas(investigator, case_perm_checker, current_user):
        return Task.get_active_QAs(investigator, case_perm_checker, True, current_user)

    @staticmethod
    def get_completed_investigations(investigator, case_perm_checker, current_user):
        q = session.query(Task)
        q = q.join(UserTaskRoles).filter(UserTaskRoles.user_id == investigator.id).filter(or_(
            UserTaskRoles.role == UserTaskRoles.SECONDARY_INVESTIGATOR,
            UserTaskRoles.role == UserTaskRoles.PRINCIPLE_INVESTIGATOR))
        q = q.join(TaskStatus).filter(TaskStatus.status == TaskStatus.COMPLETE)
        return Task._check_perms(current_user, q, case_perm_checker)

    @staticmethod
    def get_current_investigations(investigator, case_perm_checker, current_user):
        return Task.get_active_tasks(investigator, case_perm_checker, True, current_user)

    @staticmethod
    def get_num_tasks_by_user(investigator, category, date_required):
        month = date_required.month
        year = date_required.year
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])
        q = session.query(func.count(Task.id))
        q = q.filter(and_(Task.creation_date >= first_day, Task.creation_date <= last_day))
        if category is not None:
            q = q.join(TaskType).join(TaskCategory).filter(TaskCategory.category == category)
            q = q.join(UserTaskRoles).filter(UserTaskRoles.user_id == investigator.id).filter(or_(
                UserTaskRoles.role == UserTaskRoles.PRINCIPLE_INVESTIGATOR,
                UserTaskRoles.role == UserTaskRoles.SECONDARY_INVESTIGATOR))
        return q.scalar()

    @staticmethod
    def get_num_completed_qas(investigator, date_required):
        month = date_required.month
        year = date_required.year
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])
        q = session.query(func.count(Task.id))
        q = q.join(UserTaskRoles).filter(UserTaskRoles.user_id == investigator.id).filter(or_(
            UserTaskRoles.role == UserTaskRoles.PRINCIPLE_QA,
            UserTaskRoles.role == UserTaskRoles.SECONDARY_QA))
        q = q.join(TaskStatus).filter(and_(TaskStatus.status == TaskStatus.DELIVERY,
                                           TaskStatus.date_time >= first_day,
                                           TaskStatus.date_time <= last_day))
        return q.scalar()

    @staticmethod
    def get_queued_tasks():
        q = session.query(Task).join('case').filter(Task.currentStatus == TaskStatus.QUEUED).filter(
            Case.currentStatus == CaseStatus.OPEN)
        return q.all()

    @staticmethod
    def _get_user_tasks(user=None, usergroups=None, statusgroups=None, case_perm_checker=None, filter_check=None,
                        current_user=None):
        q = session.query(Task)
        if statusgroups is not None:
            q = q.filter(Task.currentStatus.in_(statusgroups))
        if filter_check is not None:
            q = q.join('task_roles').filter(and_(UserTaskRoles.user_id == user.id, UserTaskRoles.role.in_(usergroups)))
        q = q.join('case').filter(Case.currentStatus == CaseStatus.OPEN)
        if case_perm_checker is not None:
            if current_user is None:
                return Task._check_perms(user, q, case_perm_checker)  # do now want to show private cases
            else:
                return Task._check_perms(current_user, q, case_perm_checker)
        else:
            return q.all()

    @staticmethod
    def get_active_QAs(user=None, case_perm_checker=None, filter_check=None, current_user=None):
        if case_perm_checker is None:
            query = Task._get_user_tasks(user, UserTaskRoles.qa_roles, [TaskStatus.QA], filter_check=True)
        else:
            query = Task._get_user_tasks(user, UserTaskRoles.qa_roles, [TaskStatus.QA], case_perm_checker,
                                         filter_check=filter_check, current_user=current_user)
        return query

    @staticmethod
    def get_active_tasks(user=None, case_perm_checker=None, filter_check=None, current_user=None):
        if case_perm_checker is None:
            query = Task._get_user_tasks(user, UserTaskRoles.inv_roles, TaskStatus.openStatuses, filter_check=True)
        else:
            query = Task._get_user_tasks(user, UserTaskRoles.inv_roles, TaskStatus.openStatuses,
                                         case_perm_checker=case_perm_checker, filter_check=filter_check,
                                         current_user=current_user)
        return query

    @staticmethod
    def get_tasks_requiring_QA_by_user(user, all=False):
        if all:
            task_statuses = [TaskStatus.DELIVERY, TaskStatus.CLOSED, TaskStatus.COMPLETE]
        else:
            task_statuses = [TaskStatus.QA]
        principle = Task._get_user_tasks(user, [UserTaskRoles.PRINCIPLE_QA], task_statuses, filter_check=True)
        secondary = Task._get_user_tasks(user, [UserTaskRoles.SECONDARY_QA], task_statuses, filter_check=True)
        return principle, secondary

    @staticmethod
    def get_tasks_assigned_to_user(user):
        principle = Task._get_user_tasks(user, [UserTaskRoles.PRINCIPLE_INVESTIGATOR], TaskStatus.openStatuses,
                                         filter_check=True)
        secondary = Task._get_user_tasks(user, [UserTaskRoles.SECONDARY_INVESTIGATOR], TaskStatus.openStatuses,
                                         filter_check=True)
        return principle, secondary

    @staticmethod
    def get_tasks_with_type(task_type):
        q = session.query(Task).join('task_type').filter_by(task_type=task_type.task_type).all()
        return q

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