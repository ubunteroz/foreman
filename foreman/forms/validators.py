#python imports
from os import path
import datetime
# #library imports
from formencode import validators as v, Invalid
from formencode.compound import CompoundValidator
# local imports
from ..model import User, UserTaskRoles, UserRoles, TaskStatus, Task, CaseStatus, Case, ForemanOptions, TaskType
from ..model import CaseType, CaseClassification
from ..utils.utils import session, ROOT_DIR


class RemoveEmpties(v.FancyValidator):
    """ Removes empty items from a list """
    key = None

    def _to_python(self, value, state):
        if self.key is None:
            return [item for item in value if item]
        else:
            # If item is a dictionary, check the required dictionary key.
            return [item for item in value if item[self.key]]


class Match(v.FancyValidator):
    """ Checks the new passwords match """
    __unpackargs__ = ('pass1_field', 'pass2_field')
    validate_partial_form = False

    def validate_python(self, vals, state):
        if not self.check_password(vals.get(self.pass1_field), vals.get(self.pass2_field)):
            errors = {
                self.pass1_field: 'Passwords do not match',
                self.pass2_field: 'Passwords do not match'
            }
            raise Invalid('', vals, state, error_dict=errors)

    def check_password(self, new_password, new_password_2):
        if new_password == new_password_2:
            return True
        else:
            return False


class ValidDate(v.UnicodeString):
    messages = {
        'invalid': 'The date was not entered in the correct format DD MMMM YYYY',
    }
    allow_null = False

    def _to_python(self, value, state):
        try:
            print value
            date = datetime.datetime.strptime(value, "%d %B %Y")
            return datetime.date(date.year, date.month, date.day)
        except ValueError:
            raise Invalid(self.message('invalid', state), value, state)


class ValidTime(v.UnicodeString):
    messages = {
        'invalid': 'The time was not entered in the correct format HH:MM',
    }
    allow_null = False

    def _to_python(self, value, state):
        try:
            time = datetime.datetime.strptime(value, "%H:%M")
            return datetime.time(time.hour, time.minute, time.second)
        except ValueError:
            raise Invalid(self.message('invalid', state), value, state)


class QADecision(v.UnicodeString):
    messages = {
        'null': 'Please select an option.',
    }
    allow_null = False

    def _to_python(self, value, state):
        if value == "qa_pass":
            return True
        elif value == "qa_fail":
            return False
        else:
            raise Invalid(self.message('null', state), value, state)


class IsPrincipleInvestigator(v.UnicodeString):
    messages = {
        'null': 'Please select an option.',
        'invalid': 'This item does not exist.',
    }
    allow_null = False

    def _to_python(self, value, state):
        if value == UserTaskRoles.PRINCIPLE_INVESTIGATOR:
            return True
        elif value == UserTaskRoles.SECONDARY_INVESTIGATOR:
            return False
        else:
            raise Invalid(self.message('invalid', state), value, state)


class GetObject(v.UnicodeString):
    """ Override this - abstract class """
    messages = {
        'invalid': 'This item does not exist.',
        'null': 'Please select an option.',
        'new': 'You cannot add new items'
    }
    allow_new = True
    allow_null = False
    null_value = None

    def _to_python(self, value, state):
        if value == "new" and self.allow_new:
            return value
        elif value == "new" and not self.allow_new:
            raise Invalid(self.message('new', state), value, state)
        elif value == "null" and not self.allow_null:
            raise Invalid(self.message('null', state), value, state)
        elif value == "null" and self.allow_null:
            return self.null_value
        else:
            obj_id = v.UnicodeString._to_python(self, value, state)
            obj = self.getObject(obj_id)
            if obj is None:
                raise Invalid(self.message('invalid', state), value, state)
            return obj

    def getObject(self, obj_id):
        raise Exception('Should be implemented by subclass')


class GetUsers(GetObject):
    messages = {
        'invalid': 'User does not exist.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, user_id):
        if user_id.isdigit():
            return session.query(User).get(int(user_id))
        if user_id == "both":
            return "both"
        else:
            return None


class GetUser(GetObject):
    messages = {
        'invalid': 'User does not exist.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = True

    def getObject(self, user_id):
        if user_id.isdigit():
            return session.query(User).get(int(user_id))
        else:
            return None


class GetInvestigator(GetUser):
    null_value = True

    def getObject(self, user_id):
        print user_id, "^"*99
        if user_id.isdigit():
            user = session.query(User).get(int(user_id))
            if user is not None:
                for role in user.roles:
                    if role.role == UserRoles.INV:
                        return user
                return None
            return None
        else:
            return None


class GetQA(GetUser):
    null_value = True

    def getObject(self, user_id):
        if user_id.isdigit():
            user = session.query(User).get(int(user_id))
            if user is not None:
                for role in user.roles:
                    if role.role == UserRoles.QA:
                        return user
                return None
            return None
        else:
            return None


class GetCaseManager(GetUser):
    null_value = True

    def getObject(self, user_id):
        if user_id.isdigit():
            user = session.query(User).get(int(user_id))
            if user is not None:
                for role in user.roles:
                    if role.role == UserRoles.CASE_MAN:
                        return user
                return None
            return None
        else:
            return None


class GetTaskStatus(GetObject):
    messages = {
        'invalid': 'Status is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, status_text):
        if status_text in TaskStatus.all_statuses:
            return status_text
        else:
            return None


class GetCaseClassification(GetObject):
    messages = {
        'invalid': 'Classification is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, classification):
        for ct in CaseClassification.get_classifications():
            if classification == ct.replace(" ", "").lower():
                return ct
        else:
            return None


class GetCaseType(GetObject):
    messages = {
        'invalid': 'Case Type is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, case_type):
        print case_type
        for ct in CaseType.get_case_types():
            print ct
            if case_type == ct.replace(" ", "").lower():
                return ct
        else:
            return None


class GetCaseStatus(GetObject):
    messages = {
        'invalid': 'Status is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, status_text):
        if status_text in CaseStatus.all_statuses:
            return status_text
        else:
            return None


class GetTask(GetObject):
    messages = {
        'invalid': 'Task does not exist.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, task_id):
        if task_id.isdigit():
            return session.query(Task).get(int(task_id))
        else:
            return None


class GetCase(GetObject):
    messages = {
        'invalid': 'Case does not exist.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, case_id):
        if case_id.isdigit():
            return session.query(Case).get(int(case_id))
        else:
            return None


class GetTaskTypes(GetObject):
    messages = {
        'invalid': 'Task Type is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, task_type):
        return TaskType.get_type_from_list(task_type)



class GetEvidenceType(GetObject):
    messages = {
        'invalid': 'Task Type is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, evidence_type):
        evidence_types = {}
        for evi in ForemanOptions.get_evidence_types():
            evidence_types[evi.evidence_type.replace(" ","").lower()] = evi.evidence_type

        if evidence_type in evidence_types.keys():
            return evidence_types[evidence_type]
        else:
            return None

class GetBooleanYesNo(v.UnicodeString):
    messages = {
        'null': 'Please select an option.',
        'invalid': 'Please select Yes or No.',
    }
    allow_null = False

    def _to_python(self, value, state):
        if value == "yes":
            return True
        elif value == "no":
            return False
        else:
            raise Invalid(self.message('invalid', state), value, state)


class PasswordCheck(v.FormValidator):
    __unpackargs__ = ('username_field', 'pass_field')
    validate_partial_form = False

    def validate_python(self, vals, state):
        if not self.check_pass(vals.get(self.username_field), vals.get(self.pass_field)):
            errors = {
                self.username_field: 'Wrong username or password',
                self.pass_field: 'Wrong username or password'
            }
            raise Invalid('', vals, state, error_dict=errors)

    def check_pass(self, username, password):
        if len(User.get_filter_by(username=username.lower()).all()) == 0:
            return False
        else:
            return User.check_password(username.lower(), password)


class Upload(v.FieldStorageUploadConverter):
    """ Class to upload things """
    folder = ''  # upload destination
    type = ''   # type of file e.g. css or image

    def _to_python(self, value, state):
        if not value:
            if self.not_empty is True:
                raise Invalid(self.message('empty', state), value, state)
            else:
                return None
        file = v.FieldStorageUploadConverter._to_python(self, value, state)
        if self.type is None or self.type in file.content_type or self.type in \
                file.filename.split(path.sep)[-1].split('.', 1)[1]:
            new = path.join(self.folder, self.file_name(file))
            file.save(new)
        else:
            raise Invalid(self.message('invalid', state), value, state)
        return file.filename

    def file_name(self, file):
        # make sure filename is just [name].[extension]
        return file.filename.split(path.sep)[-1]


class UploadCustodyAttachment(Upload):
    messages = {
        'invalid': 'An invalid file was uploaded.'
    }
    folder = path.join(ROOT_DIR, 'static', 'evidence_custody_receipts')
    type = None  # allow all types


class UploadEvidencePhoto(Upload):
    messages = {
        'invalid': 'An invalid image file was uploaded.'
    }
    folder = path.join(ROOT_DIR, 'static', 'evidence_photos')
    type = 'image'