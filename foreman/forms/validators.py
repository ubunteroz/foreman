#python imports
from os import path
import datetime
# #library imports
from formencode import validators as v, Invalid
from formencode.compound import CompoundValidator
# local imports
from foreman.model import Evidence
from ..model import User, UserTaskRoles, UserRoles, Task, Case, ForemanOptions, TaskType
from ..model import CaseType, CaseClassification, TaskCategory, CasePriority, Department, Team, EvidenceType
from ..model import EvidenceStatus
from ..utils.utils import ROOT_DIR


class CheckUniqueEdit(v.FormValidator):
    __unpackargs__ = ('name', 'edit_obj')
    validate_partial_form = True
    object_type = ""
    object_class = None
    attribute_to_compare = ''

    def validate_partial(self, vals, state):
        if not self.check_duplicate(vals.get(self.name), vals.get(self.edit_obj)):
            errors = {
                self.name: 'This {} already exists'.format(self.object_type),
            }
            raise Invalid('', vals, state, error_dict=errors)

    def validate_python(self, vals, state):
        self.validate_partial(vals, state)

    def check_duplicate(self, value, obj_id):
        comparer = {self.attribute_to_compare: value}
        result = self.object_class.get_filter_by(**comparer).first()
        if result is None:
            return True
        elif obj_id.isdigit() and result.id == int(obj_id):
            return True
        else:
            return False


class CheckUnique(v.UnicodeString):
    messages = {'duplicate': 'This value already exists'}
    object_class = None
    attribute_to_compare = ''

    def _to_python(self, value, state):
        comparer = {self.attribute_to_compare: value}
        obj = self.object_class.get_filter_by(**comparer).first()
        if obj is None:
            return value
        else:
            raise Invalid(self.message('duplicate', state), value, state)


class CheckUniqueCaseEdit(CheckUniqueEdit):
    object_type = "case"
    object_class = Case
    attribute_to_compare = 'case_name'


class CheckUniqueCase(CheckUnique):
    messages = {'duplicate': 'This case name already exists'}
    object_class = Case
    attribute_to_compare = 'case_name'


class CheckUniqueTaskEdit(CheckUniqueEdit):
    object_type = "task"
    object_class = Task
    attribute_to_compare = 'task_name'


class CheckUniqueTask(CheckUnique):
    messages = {'duplicate': 'This task name already exists'}
    object_class = Task
    attribute_to_compare = 'task_name'


class CheckUniqueTeamEdit(CheckUniqueEdit):
    object_type = "team"
    object_class = Team
    attribute_to_compare = 'team'


class CheckUniqueTeam(CheckUnique):
    messages = {'duplicate': 'This team name already exists'}
    object_class = Team
    attribute_to_compare = 'team'


class CheckUniqueDepartmentEdit(CheckUniqueEdit):
    object_type = "department"
    object_class = Department
    attribute_to_compare = 'department'


class CheckUniqueDepartment(CheckUnique):
    messages = {'duplicate': 'This department name already exists'}
    object_class = Department
    attribute_to_compare = 'department'


class CheckUniqueUsernameEdit(CheckUniqueEdit):
    object_type = "username"
    object_class = User
    attribute_to_compare = 'username'


class CheckUniqueUsername(CheckUnique):
    messages = {'duplicate': 'This username already exists'}
    object_class = User
    attribute_to_compare = 'username'


class CheckUniqueEmailEdit(CheckUniqueEdit):
    object_type = "email address"
    object_class = User
    attribute_to_compare = 'email'


class CheckUniqueEmail(CheckUnique):
    messages = {'duplicate': 'This email address already exists'}
    object_class = User
    attribute_to_compare = 'email'


class CheckUniqueReferenceEdit(CheckUniqueEdit):
    object_type = "evidence reference"
    object_class = Evidence
    attribute_to_compare = 'reference'


class CheckUniqueReference(CheckUnique):
    messages = {'duplicate': 'This evidence reference already exists'}
    object_class = Evidence
    attribute_to_compare = 'reference'


class Match(v.FormValidator):
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


class NotEmptyUpload(v.FormValidator):
    """ Checks that there has been a file uploaded if the option was selected to upload a file """
    __unpackargs__ = ('names', 'uploads')
    validate_partial_form = True

    def validate_partial(self, vals, state):
        if not self.check_upload(vals.get(self.names), vals.get(self.uploads)):
            errors = {
                self.names: 'Please upload a file or choose a different option',
                self.uploads: 'Please upload a file or choose a different option',
            }
            raise Invalid('', vals, state, error_dict=errors)

    def validate_python(self, vals, state):
        self.validate_partial(vals, state)

    def check_upload(self, option, upload):
        if option == "FromList" and not upload:
            return False
        else:
            return True


class RequiredFieldEvidence(v.FormValidator):
    __unpackargs__ = ('field', 'required_field')
    validate_partial_form = True

    def validate_partial(self, vals, state):
        if not self.check_required(vals.get(self.field), vals.get(self.required_field)):
            errors = {
                self.required_field: 'Please enter a value',
            }
            raise Invalid('', vals, state, error_dict=errors)

    def validate_python(self, vals, state):
        self.validate_partial(vals, state)

    def check_required(self, field, field_req):
        if field == "True" and not field_req:
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
        if value == "":
            return value

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
    now = datetime.datetime.now()
    messages = {
        'invalid': 'The date was not entered in the correct format DD/MM/YYYY, e.g. {}'.format(now.strftime("%d/%m/%Y")),
    }
    allow_null = False

    def _to_python(self, value, state):
        try:
            date = datetime.datetime.strptime(value, "%d/%m/%Y")
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


class TestDateFormat(v.UnicodeString):
    messages = {
        'invalid': 'The date formatter is invalid.',
    }
    allow_null = False

    def _to_python(self, value, state):
        try:
            now = datetime.datetime.now()
            date = now.strftime(value)
            if date == value:
                raise Invalid(self.message('invalid', state), value, state)
            return value
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


class IsPrincipleQA(v.UnicodeString):
    messages = {
        'null': 'Please select an option.',
        'invalid': 'This item does not exist.',
    }
    allow_null = False

    def _to_python(self, value, state):
        if value == UserTaskRoles.PRINCIPLE_QA:
            return True
        elif value == UserTaskRoles.SECONDARY_QA:
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
    null_value = None

    def getObject(self, user_id):
        if user_id.isdigit():
            user = User.get(int(user_id))
            if user is not None:
                if user.roles is not None:
                    for role in user.roles:
                        if role.role == UserRoles.INV:
                            return user
                return None
            return None
        else:
            return None


class GetQA(GetUser):
    null_value = None

    def getObject(self, user_id):
        if user_id.isdigit():
            user = User.get(int(user_id))
            if user is not None:
                if user.roles is not None:
                    for role in user.roles:
                        if role.role == UserRoles.QA:
                            return user
                return None
            return None
        else:
            return None


class GetCaseManager(GetUser):
    null_value = None

    def getObject(self, user_id):
        if user_id.isdigit():
            user = User.get(int(user_id))
            if user is not None:
                if user.roles is not None:
                    for role in user.roles:
                        if role.role == UserRoles.CASE_MAN:
                            return user
                return None
            return None
        else:
            return None


class GetAuthoriser(GetUser):
    allow_null = False
    
    def getObject(self, user_id):
        if user_id.isdigit():
            user = User.get(int(user_id))
            if user is not None:
                if user.roles is not None:
                    for role in user.roles:
                        if role.role == UserRoles.AUTH:
                            return user
                return None
            return None
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
        if classification.isdigit():
            return CaseClassification.get(int(classification))
        return None


class GetPriority(GetObject):
    messages = {
        'invalid': 'Priority is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, priority):
        if priority.isdigit():
            return CasePriority.get(int(priority))
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
        if case_type.isdigit():
            return CaseType.get(int(case_type))
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
        if department.isdigit():
            return Department.get(int(department))
        else:
            return None


class GetTeam(GetObject):
    messages = {
        'invalid': 'Team is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, team):
        if team.isdigit():
            return Team.get(int(team))
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
        if task_type.isdigit():
            return TaskType.get(int(task_type))
        else:
            return None


class GetTaskCategory(GetObject):
    messages = {
        'invalid': 'Task Category is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, category):
        if category.isdigit():
            return TaskCategory.get(int(category))
        else:
            return None


class GetEvidenceType(GetObject):
    messages = {
        'invalid': 'Task Type is invalid.',
        'null': 'Please select an option.'
    }

    allow_new = False
    allow_null = False

    def getObject(self, evidence_type):
        if evidence_type.isdigit():
            return EvidenceType.get(int(evidence_type))
        else:
            return None


class GetEvidenceStatus(v.UnicodeString):
    messages = {
        'null': 'Please select an option.',
        'invalid': 'Please select a valid status.',
    }

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
        if User.get_filter_by(username=username.lower()).first() is None:
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


class Upload(v.FancyValidator):
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
        try:
            value.seek(0)
        except AttributeError:
            raise Invalid(self.message('empty', state), value, state)

        uploaded_file = value
        if self.type is None or self.type in uploaded_file.content_type or self.type in \
                uploaded_file.filename.split(path.sep)[-1].split('.', 1)[1] or self.type in value.mimetype:
            new = path.join(self.folder, self.file_name(uploaded_file))
            uploaded_file.save(new)
        else:
            raise Invalid(self.message('invalid', state), value, state)
        return uploaded_file.filename

    def file_name(self, file):
        # make sure filename is just [name].[extension]
        return file.filename.split(path.sep)[-1]


class UploadWithoutStorage(v.FancyValidator):
    """ Class to upload things  - override this class """

    accept_iterator = True

    def _to_python(self, value, state):
        if not value:
            if self.not_empty is True:
                raise Invalid(self.message('empty', state), value, state)
            else:
                return None

        # FormEncode annoyingly checks whether the value is iterable by trying to iterate over it, which consumes
        # the first line of the file. Rewind it again.
        try:
            value.seek(0)
        except AttributeError:
            raise Invalid(self.message('empty', state), value, state)

        if self.type is not None:
            if self.type in value.mimetype or self.type in value.content_type:
                return value
            else:
                raise Invalid(self.message('invalid', state), value, state)
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