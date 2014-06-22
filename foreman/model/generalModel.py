# python imports
from datetime import datetime
import shutil
from os import path
from hashlib import sha256
# library imports
from sqlalchemy import Table, Column, Integer, Boolean, Float, Unicode, ForeignKey, asc, desc, func, and_, or_
from sqlalchemy.orm import backref, relation
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
    c_list_loc = Column(Unicode)
    c_list_name = Column(Unicode)
    task_names = Column(Unicode)
    t_increment = Column(Integer)
    t_leading_zeros = Column(Integer)
    t_leading_date = Column(Unicode)
    t_list_loc = Column(Unicode)
    t_list_name = Column(Unicode)
    company = Column(Unicode)
    department = Column(Unicode)

    CASE_NAME_OPTIONS = ['UserCreated', 'NumericIncrement', 'DateNumericIncrement', 'FromList']
    TASK_NAME_OPTIONS = ['UserCreated', 'NumericIncrement', 'FromList', 'TaskTypeNumericIncrement']

    def __init__(self, date_format, default_location, case_names, task_names, company, department, c_list_location=None, c_leading_zeros=None,
                 t_list_location=None, t_leading_zeros=None):
        self.date_format = date_format
        self.default_location = default_location
        self.case_names = case_names
        self.c_increment = 0
        self.c_leading_zeros = c_leading_zeros
        self.c_leading_date = datetime.now().strftime("%Y%m%d")
        self.c_list_name = self.import_list(c_list_location)
        self.task_names = task_names
        self.t_increment = 0
        self.t_leading_zeros = t_leading_zeros
        self.t_list_name = self.import_list(t_list_location)
        self.company = company
        self.department = department

        TaskCategory.populate_default()
        TaskType.populate_default()
        EvidenceType.populate_default()

    def import_list(self, list_location):
        if list_location is not None:
            shutil.copy(list_location, path.join(ROOT_DIR, 'files'))
            return path.join(ROOT_DIR, 'files', path.basename(list_location))

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
    def get_next_case_name():
        options = session.query(ForemanOptions).first()
        if options.case_names == 'UserCreated':
            return ""
        elif options.case_names == 'NumericIncrement':
            options.c_increment += 1
            return '{num:0{width}}'.format(num=options.c_increment, width=options.c_leading_zeros)
        elif options.case_names == "DateNumericIncrement":
            now = datetime.now().strftime("%Y%m%d")
            if now == options.c_leading_date:
                options.c_increment += 1
                return '{now}{num:0{width}}'.format(now=now, num=options.c_increment, width=options.c_leading_zeros)
            else:
                options.c_increment = 1
                return '{now}{num:0{width}}'.format(now=now, num=options.c_increment, width=options.c_leading_zeros)
        elif options.case_names == "FromList":
            options.c_increment += 1
            return ForemanOptions.get_next_case_name_from_list(options.c_list_name, options.c_increment)

    @staticmethod
    def get_next_task_name(tasktype, case):
        options = session.query(ForemanOptions).first()
        options.t_increment = len(case.tasks)
        if options.task_names == 'UserCreated':
            return "{}_".format(case.case_name)
        elif options.task_names == 'NumericIncrement':
            options.t_increment += 1
            return '{case}_{num1:0{width1}}'.format(case=case.case_name, num1=options.t_increment, width1=options.t_leading_zeros)
        elif options.task_names == "FromList":
            options.t_increment += 1
            return ForemanOptions.get_next_case_name_from_list(options.t_list_name, options.t_increment)
        elif options.task_names == "TaskTypeNumericIncrement":
            options.t_increment += 1
            return '{task}_{num1:0{width1}}'.format(task=tasktype, num1=options.t_increment, width1=options.t_leading_zeros)

    @staticmethod
    def get_next_case_name_from_list(filename, increment):
        with open(filename, 'r') as contents:
            all = contents.readlines()
            return all[increment].strip()

    @staticmethod
    def get_task_types():
        return session.query(TaskType).all()

    @staticmethod
    def get_evidence_types():
        return session.query(EvidenceType).order_by(asc(EvidenceType.evidence_type)).all()

    @staticmethod
    def get_options():
        return session.query(ForemanOptions).first()

    @staticmethod
    def set_options(company, department, folder, date_display):
        opt = ForemanOptions.get_options()
        opt.company = company
        opt.department = department
        opt.default_location = folder
        opt.date_format = date_display


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
                      ('Malware Analysis', 'Specialist Tasks')]

        for tt, cat in task_types:
            t = TaskType(tt, TaskType.get_category(cat))
            session.add(t)
            session.flush()

    @staticmethod
    def get_category(cat):
        return session.query(TaskCategory).filter_by(category=cat).first()

    @staticmethod
    def get_type_from_list(ttype):
        ttypes = session.query(TaskType).all()
        for task_type in ttypes:
            if ttype == task_type.task_type.replace(" ", "").lower():
                return task_type
        return None

    def __str__(self):
        return "{} > {}".format(self.category, self.task_type)


class TaskCategory(Base, Model):
    __tablename__ = 'task_category'

    id = Column(Integer, primary_key=True)
    category = Column(Unicode)

    def __init__(self, category):
        self.category = category

    @staticmethod
    def populate_default():
        cats = ['Communications Retrieval', 'Internet Logs', 'Computer Forensics', 'Mobile & Tablet Forensics', 'Networked Data',
                'Log file Analysis', 'Specialist Tasks']

        for cat in cats:
            c = TaskCategory(cat)
            session.add(c)
            session.flush()

    def __str__(self):
        return self.category


class EvidenceType(Base, Model):
    __tablename__ = 'evidence_types'

    id = Column(Integer, primary_key=True)
    evidence_type = Column(Unicode)

    def __init__(self, evidence_type, icon=None):
        self.evidence_type = evidence_type
        icon_path = self.evidence_type.replace(" ", "").lower() + ".png"
        new_icon = path.abspath(path.join(ROOT_DIR, 'static', 'images' ,'siteimages', 'evidence_icons', icon_path))

        if icon is None:
            default_icon = path.abspath(path.join(ROOT_DIR, 'static', 'images', 'siteimages',
                                                  'evidence_icons', 'other.png'))
            if path.exists(default_icon):
                shutil.copy(default_icon, new_icon)
        elif path.exists(icon):
            shutil.copy(icon, new_icon)

    @staticmethod
    def populate_default():
        evis = ['SATA Hard Drive', 'IDE Hard Drive', 'Other Hard Drive', 'USB Hard drive', 'Floppy Disk', 'CD', 'DVD',
                'Other Removable Media', 'Zip Drive', 'Mobile Phone', 'Smart Phone', 'Tablet', 'PDA', 'USB Media',
                'GPS Device', 'Digital Camera', 'Gaming System', 'Laptop', 'Whole Computer Tower', 'Inkjet Printer',
                'Laser Printer', 'Other Printer', 'Scanner', 'Multi-Functional Printer', 'Other' 'Music Player']

        for evi in evis:
            e = EvidenceType(evi)
            session.add(e)
            session.flush()

    @staticmethod
    def get_evidence_types():
        evis = session.query(EvidenceType).order_by(asc(EvidenceType.evidence_type)).all()
        return [evi.evidence_type for evi in evis]

    def __str__(self):
        return self.evidence_type