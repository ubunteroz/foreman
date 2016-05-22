#python imports
from os import path
import datetime
# #library imports
from formencode import validators as v, Invalid
from formencode.compound import CompoundValidator
# local imports
from ..model import User, UserTaskRoles, UserRoles, TaskStatus, Task, CaseStatus, Case, ForemanOptions, TaskType
from ..model import CaseType, CaseClassification, TaskCategory, CasePriority, Department, Team, EvidenceType
from ..model import EvidenceStatus
from ..utils.utils import ROOT_DIR


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


class NotEmptyCaseUpload(v.FancyValidator):
    """ Checks that there has been a file uploaded if the option was selected to upload a file """
    validate_partial_form = False

    def validate_python(self, vals, state):
        if not self.check_upload(vals['case_names'], vals['upload_case_names']):
            errors = {
                'case_names': 'Please upload a file or choose a different option',
                'upload_case_names': 'Please upload a file or choose a different option',
            }
            raise Invalid('', vals, state, error_dict=errors)

    def check_upload(self, option, upload):
        if option == "FromList" and not upload:
            return False
        else:
            return True


class NotEmptyTaskUpload(v.FancyValidator):
    """ Checks that there has been a file uploaded if the option was selected to upload a file """
    validate_partial_form = False

    def validate_python(self, vals, state):
        if not self.check_upload(vals['task_names'], vals['upload_task_names']):
            errors = {
                'task_names': 'Please upload a file or choose a different option',
                'upload_task_names': 'Please upload a file or choose a different option',
            }
            raise Invalid('', vals, state, error_dict=errors)

    def check_upload(self, option, upload):
        if option == "FromList" and not upload:
            return False
        else:
            return True


class PositiveNumberAboveZero(v.Number):
    messages = {
        'negative': 'Please enter a positive number',
        'zero': 'Please enter a positive number greater than zero',
        'invalid': 'Please enter a number'
    }

    def _to_python(self, value, state):
        try:
            value = int(value)
        except ValueError:
            raise Invalid(self.message('invalid', state), value, state)
        if value > 0:
            return value
        elif value == 0:
            raise Invalid(self.message('zero', state), value, state)
        else:
            raise Invalid(self.message('negative', state), value, state)


class TimeSheetDateTime(v.UnicodeString):
    messages = {
        'invalid': 'The date was not entered in the correct format',
    }
    allow_null = False

    def _to_python(self, value, state):
        try:
            dt = datetime.datetime.strptime(value, "%d%m%Y")
            return datetime.date(dt.year, dt.month, dt.day)
        except ValueError:
            raise Invalid(self.message('invalid', state), value, state)


class ValidDate(v.UnicodeString):
    messages = {
        'invalid': 'The date was not entered in the correct format DD MMMM YYYY',
    }
    allow_null = False

    def _to_python(self, value, state):
        try:
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


class AddIcon(v.UnicodeString):
    messages = {
        'empty': 'Please select an icon.',
        'invalid': 'This icon does not exist.',
    }
    allow_null = False

    def _to_python(self, value, state):
        icon_path = path.join(ROOT_DIR, 'static', 'images', 'siteimages', 'evidence_icons_unique', value)
        if path.exists(icon_path):
            return icon_path
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


class GetForemanCaseNameOptions(GetObject):
    messages = {
        'invalid': 'Automatic case name option does not exist.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, str):
        if str in ForemanOptions.CASE_NAME_OPTIONS:
            return str
        else:
            return None


class GetForemanTaskNameOptions(GetObject):
    messages = {
        'invalid': 'Automatic task name option does not exist.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, str):
        if str in ForemanOptions.TASK_NAME_OPTIONS:
            return str
        else:
            return None


class GetUsers(GetObject):
    messages = {
        'invalid': 'User does not exist.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, user_id):
        if user_id.isdigit():
            return User.get(int(user_id))
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
            return User.get(int(user_id))
        else:
            return None



class GetInvestigator(GetUser):
    null_value = True

    def getObject(self, user_id):
        if user_id.isdigit():
            user = User.get(int(user_id))
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
            user = User.get(int(user_id))
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
            user = User.get(int(user_id))
            if user is not None:
                for role in user.roles:
                    if role.role == UserRoles.CASE_MAN:
                        return user
                return None
            return None
        else:
            return None


class GetAuthoriser(GetUser):
    null_value = True

    def getObject(self, user_id):
        if user_id.isdigit():
            user = User.get(int(user_id))
            if user is not None:
                for role in user.roles:
                    if role.role == UserRoles.AUTH:
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
        return CaseClassification.get(classification)


class GetPriority(GetObject):
    messages = {
        'invalid': 'Priority is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, priority):
        for cp in CasePriority.get_all():
            if priority == cp.case_priority:
                return cp
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
        return CaseType.get(case_type)


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
            return Task.get(int(task_id))
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
            return Case.get(int(case_id))
        else:
            return None

class GetDepartment(GetObject):
    messages = {
        'invalid': 'Department is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, department):
        try:
            return Department.get(int(department))
        except ValueError:
            return None


class GetTeam(GetObject):
    messages = {
        'invalid': 'Team is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, team):
        try:
            return Team.get(int(team))
        except ValueError:
            return None


class GetTaskTypes(GetObject):
    messages = {
        'invalid': 'Task Type is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, task_type):
        try:
            return TaskType.get(int(task_type))
        except ValueError:
            return None


class GetTaskCategory(GetObject):
    messages = {
        'invalid': 'Task Category is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, category):
        try:
            return TaskCategory.get(int(category))
        except ValueError:
            return None


class GetEvidenceType(GetObject):
    messages = {
        'invalid': 'Task Type is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, evidence_type):
        try:
            return EvidenceType.get(int(evidence_type))
        except ValueError:
            return None


class GetEvidenceStatus(v.UnicodeString):
    messages = {
        'null': 'Please select an option.',
        'invalid': 'Please select a valid status.',
    }
    allow_null = False

    def _to_python(self, value, state):
        if value in EvidenceStatus.statuses:
            return value
        else:
            raise Invalid(self.message('invalid', state), value, state)


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


class GetBooleanAuthReject(v.UnicodeString):
    messages = {
        'null': 'Please select an option.',
        'invalid': 'Please select Authorised or Rejected.',
    }
    allow_null = False

    def _to_python(self, value, state):
        if value == "Authorised":
            return True
        elif value == "Rejected":
            return False
        else:
            raise Invalid(self.message('invalid', state), value, state)


class CheckHex(v.UnicodeString):
    messages = {
        'null': 'Please select a colour.',
        'invalid': 'Please select a valid colour',
        }
    allow_null = False

    def _to_python(self, value, state):
        try:
            hex = value[1:]
            if value[0] != "#" or len(hex) != 6:
                raise Invalid(self.message('null', state), value, state)

            int(hex, 16)
            return value
        except ValueError:
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


class ManagerCheck(v.FormValidator):
    __unpackargs__ = ('user_field', 'manager_field')
    validate_partial_form = False

    def validate_python(self, vals, state):
        if not self.check_pass(vals.get(self.user_field), vals.get(self.manager_field)):
            errors = {
                self.manager_field: "The manager cannot be the user or one of the user's direct reports"
            }
            raise Invalid('', vals, state, error_dict=errors)

    def check_pass(self, user, manager):
        # check that the manager inputted for the user is not a direct report of the user, or the user themselves
        if manager is None:
            return True

        if user.id == manager.id:
            return False
        elif manager in user._manager_loop_checker():
            return False
        else:
            return True


class Upload(v.FieldStorageUploadConverter):
    """ Class to upload things """
    folder = ''  # upload destination
    type = ''   # type of file e.g. css or image
    accept_iterator = True

    def _to_python(self, value, state):
        if not value:
            if self.not_empty is True:
                raise Invalid(self.message('empty', state), value, state)
            else:
                return None

        # FormEncode annoyingly checks whether the value is iterable by trying to iterate over it, which consumes
        # the first line of the file. Rewind it again.
        value.seek(0)
        uploaded_file = value
        if self.type is None or self.type in uploaded_file.content_type or self.type in \
                uploaded_file.filename.split(path.sep)[-1].split('.', 1)[1]:
            new = path.join(self.folder, self.file_name(uploaded_file))
            uploaded_file.save(new)
        else:
            raise Invalid(self.message('invalid', state), value, state)
        return uploaded_file.filename

    def file_name(self, file):
        # make sure filename is just [name].[extension]
        return file.filename.split(path.sep)[-1]


class UploadWithoutStorage(v.FieldStorageUploadConverter):
    """ Class to upload things """

    accept_iterator = True

    def _to_python(self, value, state):
        if not value:
            if self.not_empty is True:
                raise Invalid(self.message('empty', state), value, state)
            else:
                return None

        # FormEncode annoyingly checks whether the value is iterable by trying to iterate over it, which consumes
        # the first line of the file. Rewind it again.
        value.seek(0)
        return value


class UploadCustodyAttachment(UploadWithoutStorage):
    messages = {
        'invalid': 'An invalid file was uploaded.'
    }
    type = None  # allow all types


class UploadTaskFiles(UploadWithoutStorage):
    messages = {
        'invalid': 'An invalid file was uploaded.'
    }
    type = None  # allow all types


class UploadEvidencePhoto(UploadWithoutStorage):
    messages = {
        'invalid': 'An invalid image file was uploaded.'
    }
    type = 'image'


class UploadNames(Upload):
    messages = {
        'invalid': 'An invalid text file was uploaded.'
    }
    folder = path.join(ROOT_DIR, 'static', 'case_names')
    type = 'txt'


class UploadProfilePhoto(UploadWithoutStorage):
    messages = {
        'invalid': 'An invalid image file was uploaded.'
    }
    type = 'image'