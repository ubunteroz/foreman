# python imports
from datetime import datetime
import shutil
from os import path
# library imports
from sqlalchemy import Table, Column, Integer, DateTime, Boolean, Unicode, ForeignKey, asc, desc
from sqlalchemy.orm import backref, relation
from werkzeug.exceptions import InternalServerError
# local imports
from models import Base, Model
from ..utils.utils import session, ROOT_DIR


class ForemanOptions(Base, Model):
    __tablename__ = 'options'

    id = Column(Integer, primary_key=True)
    date_format = Column(Unicode)
    default_location = Column(Unicode)
    case_names = Column(Unicode)
    c_increment = Column(Integer)
    c_leading_zeros = Column(Integer)
    c_leading_date = Column(Unicode)
    c_list_name = Column(Unicode)
    task_names = Column(Unicode)
    t_increment = Column(Integer)
    t_leading_zeros = Column(Integer)
    t_list_name = Column(Unicode)
    company = Column(Unicode)
    department = Column(Unicode)
    date_created = Column(DateTime)
    over_limit_case = Column(Boolean)
    over_limit_task = Column(Boolean)
    auth_view_tasks = Column(Boolean)
    auth_view_evidence = Column(Boolean)
    manager_inherit = Column(Boolean)
    evidence_retention_period = Column(Integer)
    evidence_retention = Column(Boolean)
    email_alert_all_inv_task_queued = Column(Boolean)
    email_alert_inv_assigned_task = Column(Boolean)
    email_alert_qa_assigned_task = Column(Boolean)
    email_alert_caseman_inv_self_assigned = Column(Boolean)
    email_alert_caseman_qa_self_assigned = Column(Boolean)
    email_alert_req_task_completed = Column(Boolean)
    email_alert_case_man_task_completed = Column(Boolean)
    email_alert_all_caseman_new_case = Column(Boolean)
    email_alert_all_caseman_case_auth = Column(Boolean)
    email_alert_req_case_caseman_assigned = Column(Boolean)
    email_alert_req_case_opened = Column(Boolean)
    email_alert_req_case_closed = Column(Boolean)
    email_alert_req_case_archived = Column(Boolean)
    email_alert_caseman_requester_add_task = Column(Boolean)

    CASE_NAME_OPTIONS = ['NumericIncrement', 'DateNumericIncrement', 'FromList']
    TASK_NAME_OPTIONS = ['NumericIncrement', 'FromList', 'TaskTypeNumericIncrement']

    def __init__(self, date_format, default_location, case_names, task_names, company, department, c_list_location=None,
                 c_leading_zeros=3, t_list_location=None, t_leading_zeros=3, auth_view_tasks=True,
                 auth_view_evidence=True, manager_inherit=False):
        self.date_format = date_format
        self.default_location = default_location
        self.case_names = case_names
        self.c_increment = -1
        self.c_leading_zeros = c_leading_zeros
        self.c_leading_date = datetime.now().strftime("%Y%m%d")
        self.c_list_name = self.import_list(c_list_location)
        self.task_names = task_names
        self.t_increment = -1
        self.t_leading_zeros = t_leading_zeros
        self.t_list_name = self.import_list(t_list_location)
        self.company = company
        self.department = department
        self.date_created = datetime.now()
        self.over_limit_case = False
        self.over_limit_task = False
        self.auth_view_evidence = auth_view_evidence
        self.auth_view_tasks = auth_view_tasks
        self.manager_inherit = manager_inherit
        self.evidence_retention = False
        self.evidence_retention_period = None

        TaskCategory.populate_default()
        TaskType.populate_default()
        EvidenceType.populate_default()
        CaseClassification.populate_default()
        CaseType.populate_default()
        CasePriority.populate_default()

        self.email_alert_all_inv_task_queued = False
        self.email_alert_inv_assigned_task = False
        self.email_alert_qa_assigned_task = False
        self.email_alert_caseman_inv_self_assigned = False
        self.email_alert_caseman_qa_self_assigned = False
        self.email_alert_req_task_completed = False
        self.email_alert_case_man_task_completed = False
        self.email_alert_all_caseman_new_case = False
        self.email_alert_all_caseman_case_auth = False
        self.email_alert_req_case_caseman_assigned = False
        self.email_alert_req_case_opened = False
        self.email_alert_req_case_closed = False
        self.email_alert_req_case_archived = False
        self.email_alert_caseman_requester_add_task = False

        session.commit()

    @staticmethod
    def import_list(list_location):
        if list_location is not None:
            unique = datetime.now().strftime("%H%M%S-%d%m%Y-%f")
            filename, ext = path.splitext(path.basename(list_location))
            full_filename = "{}_{}{}".format(filename, unique, ext)
            destination = path.join(ROOT_DIR, 'files', full_filename)
            shutil.copy(list_location, destination)
            return destination

    @staticmethod
    def import_names(type_list, list_location):
        options = session.query(ForemanOptions).first()
        count = options.check_list_valid(list_location)
        if count:
            dest = options.import_list(list_location)
            # reset
            if type_list == "case":
                options.c_increment = -1
                options.c_list_name = dest
                options.over_limit_case = False
            elif type_list == "task":
                options.t_increment = -1
                options.t_list_name = dest
                options.over_limit_task = False
        return count

    @staticmethod
    def check_list_valid(list_location):
        try:
            with open(list_location, "r") as names:
                contents = names.readlines()
            return len(contents)
        except Exception:
            # catch all!
            return None

    @staticmethod
    def get_date(date):
        options = session.query(ForemanOptions).first()
        date_format = options.date_format
        return date.strftime(date_format)

    @staticmethod
    def get_default_location():
        options = session.query(ForemanOptions).first()
        return options.default_location

    @staticmethod
    def get_date_created():
        options = session.query(ForemanOptions).first()
        return options.date_created

    @staticmethod
    def get_evidence_retention_period():
        options = session.query(ForemanOptions).first()
        return options.evidence_retention, options.evidence_retention_period

    @staticmethod
    def run_out_of_names():
        options = session.query(ForemanOptions).first()
        return [options.over_limit_task and options.task_names == "FromList",
                options.over_limit_case and options.case_names == "FromList"]

    @staticmethod
    def get_next_case_name(test=False):
        options = session.query(ForemanOptions).first()
        if options.case_names == 'NumericIncrement':
            options.c_increment += 1
            return '{num:0{width}}'.format(num=options.c_increment, width=options.c_leading_zeros)
        elif options.case_names == "DateNumericIncrement":
            now = datetime.now().strftime("%Y%m%d")
            if now == options.c_leading_date:
                options.c_increment += 1
                return '{now}{num:0{width}}'.format(now=now, num=options.c_increment, width=options.c_leading_zeros)
            else:
                options.c_increment = 1
                options.c_leading_date = now
                return '{now}{num:0{width}}'.format(now=now, num=options.c_increment, width=options.c_leading_zeros)
        elif options.case_names == "FromList":
            options.c_increment += 1
            return ForemanOptions.get_next_case_name_from_list(options.c_list_name, options.c_increment,
                                                               options, "c", test)

    @staticmethod
    def get_next_task_name(case, tasktype=None, test=False):
        options = session.query(ForemanOptions).first()
        if case is not None:
            options.t_increment = len(case.tasks)
        else:
            options.t_increment = -1
        if options.task_names == 'NumericIncrement':
            options.t_increment += 1
            return '{case}_{num1:0{width1}}'.format(case=case.case_name, num1=options.t_increment,
                                                    width1=options.t_leading_zeros)
        elif options.task_names == "FromList":
            options.t_increment += 1
            return ForemanOptions.get_next_case_name_from_list(options.t_list_name, options.t_increment,
                                                               options, "t", test)
        elif options.task_names == "TaskTypeNumericIncrement":
            options.t_increment += 1
            return '{task}_{num1:0{width1}}'.format(task=tasktype, num1=options.t_increment,
                                                    width1=options.t_leading_zeros)

    @staticmethod
    def get_next_case_name_from_list(filename, increment, options, content_type, test):

        if filename is None:
            results = '{num:0{width}}'.format(num=options.c_increment, width=options.c_leading_zeros)
            if content_type == "t":
                options.over_limit_task = True
            elif content_type == "c":
                options.over_limit_case = True
            return results

        with open(filename, 'r') as contents:
            all_content = contents.readlines()
            try:
                results = all_content[increment].strip()
                if test is True:
                # if it's a test, and there is actually a next one; then reverse the increment otherwise
                # using one for no reason
                    if content_type == "t":
                        options.t_increment -= 1
                    elif content_type == "c":
                        options.c_increment -= 1
            except IndexError:
                results = '{num:0{width}}'.format(num=options.c_increment, width=options.c_leading_zeros)
                if content_type == "t":
                    options.over_limit_task = True
                elif content_type == "c":
                    options.over_limit_case = True
        return results

    @staticmethod
    def get_options():
        return session.query(ForemanOptions).first()

    @staticmethod
    def set_options(company, department, folder, date_display, case_names, task_names):
        opt = ForemanOptions.get_options()
        opt.company = company
        opt.department = department
        opt.default_location = folder
        opt.date_format = date_display
        opt.case_names = case_names
        opt.task_names = task_names


class TaskType(Base, Model):
    __tablename__ = 'task_types'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('task_category.id'))
    task_type = Column(Unicode)

    category = relation('TaskCategory', backref=backref('task_types', order_by=desc(id)), order_by=asc(task_type))

    def __init__(self, task_type, category):
        self.task_type = task_type
        self.category = category

    @staticmethod
    def populate_default():
        task_types = [('Email Search', 'Communications Retrieval'),
                      ('Email Archive Search', 'Communications Retrieval'),
                      ('Instant Messenger Search', 'Communications Retrieval'),
                      ('Chat Room Search', 'Communications Retrieval'),
                      ('Fax Search', 'Communications Retrieval'),
                      ('Text Message Search', 'Communications Retrieval'),
                      ('PST File Recovery', 'Communications Retrieval'),
                      ('User Browser History', 'Internet Logs'),
                      ('Proxy Logs', 'Internet Logs'),
                      ('Firewall / DHCP logs', 'Internet Logs'),
                      ('Machine Image', 'Computer Forensics'),
                      ('Machine Remote Image', 'Computer Forensics'),
                      ('Machine Analysis', 'Computer Forensics'),
                      ('Mobile Image', 'Mobile & Tablet Forensics'),
                      ('Tablet Image', 'Mobile & Tablet Forensics'),
                      ('Mobile Analysis', 'Mobile & Tablet Forensics'),
                      ('Tablet Analysis', 'Mobile & Tablet Forensics'),
                      ('User Personal Drive Search', 'Networked Data'),
                      ('User Personal Drive Capture', 'Networked Data'),
                      ('Networked Drive Search', 'Networked Data'),
                      ('Networked Drive Capture', 'Networked Data'),
                      ('Windows Event Log Analysis', 'Log file Analysis'),
                      ('Printer Log Analysis', 'Log file Analysis'),
                      ('SIEM Log Analysis', 'Log file Analysis'),
                      ('Malware Analysis', 'Specialist Tasks'),
                      ('Undefined', 'Other')]

        for tt, cat in task_types:
            t = TaskType(tt, TaskType.get_category(cat))
            session.add(t)
            session.flush()

    @staticmethod
    def get_category(cat):
        return session.query(TaskCategory).filter_by(category=cat).first()

    @staticmethod
    def undefined():
        return "Undefined"

    def __str__(self):
        return "{} > {}".format(self.category, self.task_type)


class SpecialText(Base, Model):
    __tablename__ = 'special_text'

    id = Column(Integer, primary_key=True)
    model = Column(Unicode)
    text = Column(Unicode)

    def __init__(self, model, text):
        self.model = model
        self.text = text

    @staticmethod
    def get_text(model):
        return session.query(SpecialText).filter_by(model=model).first()


class TaskCategory(Base, Model):
    __tablename__ = 'task_category'

    id = Column(Integer, primary_key=True)
    category = Column(Unicode)

    def __init__(self, category):
        self.category = category

    @staticmethod
    def populate_default():
        cats = ['Communications Retrieval', 'Internet Logs', 'Computer Forensics', 'Mobile & Tablet Forensics', 'Networked Data',
                'Log file Analysis', 'Specialist Tasks', 'Other']

        for cat in cats:
            c = TaskCategory(cat)
            session.add(c)
            session.flush()

    @staticmethod
    def get_categories():
        q = session.query(TaskCategory).all()
        return [c.category for c in q]

    def __str__(self):
        return self.category

    @staticmethod
    def get_empty_categories():
        return session.query(TaskCategory).outerjoin('task_types').filter(TaskType.task_type==None)


class CaseClassification(Base, Model):
    __tablename__ = 'case_classification'

    id = Column(Integer, primary_key=True)
    classification = Column(Unicode)

    def __init__(self, classification):
        self.classification = classification

    @staticmethod
    def populate_default():
        classifications = ['Public', 'Secret', 'Confidential', 'Internal', 'Undefined']

        for classification in classifications:
            c = CaseClassification(classification)
            session.add(c)
            session.flush()

    @staticmethod
    def get_classifications():
        q = session.query(CaseClassification).all()
        return [c.classification for c in q if c.classification != "Undefined"]

    def __str__(self):
        return self.classification

    @staticmethod
    def undefined():
        return "Undefined"


class CaseType(Base, Model):
    __tablename__ = 'case_type'

    id = Column(Integer, primary_key=True)
    case_type = Column(Unicode)

    def __init__(self, case_type):
        self.case_type = case_type

    @staticmethod
    def populate_default():
        case_types = ['eDiscovery', 'Internal Investigation', 'Fraud Investigation', 'Incident Response',
                      'Security & Malware Investigation', 'Other', 'Undefined']

        for case_type in case_types:
            c = CaseType(case_type)
            session.add(c)
            session.flush()

    @staticmethod
    def get_case_types():
        q = session.query(CaseType).all()
        return [c.case_type for c in q if c.case_type != "Undefined"]

    @staticmethod
    def undefined():
        return "Undefined"

    def __str__(self):
        return self.case_type


class EvidenceType(Base, Model):
    __tablename__ = 'evidence_types'

    id = Column(Integer, primary_key=True)
    evidence_type = Column(Unicode)

    def __init__(self, evidence_type, icon=None):
        self.evidence_type = evidence_type

        if self.evidence_type != self.undefined():
            icon_path = self.evidence_type.replace(" ", "").lower() + ".png"
            new_icon = path.abspath(path.join(ROOT_DIR, 'static', 'images' ,'siteimages', 'evidence_icons', icon_path))

            if icon is None or not path.exists(icon):
                default_icon = path.abspath(path.join(ROOT_DIR, 'static', 'images', 'siteimages',
                                                      'evidence_icons', 'other.png'))
                if path.exists(default_icon) and not path.exists(new_icon):
                    shutil.copy(default_icon, new_icon)
            elif path.exists(icon) and not path.exists(new_icon):
                shutil.copy(icon, new_icon)

    @staticmethod
    def populate_default():
        evis = ['SATA Hard Drive', 'IDE Hard Drive', 'Other Hard Drive', 'USB Hard drive', 'Floppy Disk', 'CD', 'DVD',
                'Other Removable Media', 'Zip Drive', 'Mobile Phone', 'Smart Phone', 'Tablet', 'PDA', 'USB Media',
                'GPS Device', 'Digital Camera', 'Gaming System', 'Laptop', 'Whole Computer Tower', 'Inkjet Printer',
                'Laser Printer', 'Other Printer', 'Scanner', 'Multi-Functional Printer', 'Other', 'Music Player',
                "Undefined", 'Server']

        for evi in evis:
            e = EvidenceType(evi)
            session.add(e)
            session.flush()

    @staticmethod
    def get_evidence_types():
        evis = session.query(EvidenceType).order_by(asc(EvidenceType.evidence_type)).all()
        return [evi.evidence_type for evi in evis if evi.evidence_type != "Undefined"]

    def __str__(self):
        return self.evidence_type

    @staticmethod
    def undefined():
        return "Undefined"


class CasePriority(Base, Model):
    __tablename__ = 'case_priority'

    id = Column(Integer, primary_key=True)
    case_priority = Column(Unicode)
    colour = Column(Unicode)
    default = Column(Boolean)

    def __init__(self, case_priority, colour, default=False):
        self.case_priority = case_priority
        self.colour = colour
        self.default = self._check_default(default)

    @staticmethod
    def populate_default():
        case_priorities = [("Low", "#00CCFF", False),
                           ("Normal", "#009900", True),
                           ("High", "#FF9933", False),
                           ("Critical", "#CC0000", False)]

        for case_priority, colour, default in case_priorities:
            c = CasePriority(case_priority, colour, default)
            session.add(c)
            session.flush()

    @staticmethod
    def default_value():
        default = session.query(CasePriority).filter_by(default=True).first()
        if default is not None:
            return default
        else:
            # no default value, was somehow deleted - use the first on the list
            default = session.query(CasePriority).get(1)
            default.priority = True
            return default

    @staticmethod
    def _check_default(default):
        if default is False:
            return False
        if default is True:
            already_default = CasePriority.get_filter_by(default=True).all()
            if len(already_default) == 0:
                return True
            elif len(already_default) == 1:
                # we already have a default! We cannot have more than one default
                already_default[0].default = False
                return True
            else:
                # more than one default, something really not right!!
                raise InternalServerError


    def __str__(self):
        return self.case_priority
