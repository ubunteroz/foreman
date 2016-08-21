# python imports
from formencode import Invalid
from mock import patch, DEFAULT, Mock, MagicMock
from datetime import datetime, timedelta, date, time
from os import path

# local imports
import base_tester
from foreman.forms.validators import GetCaseManager, GetAuthoriser, GetCaseType, GetPriority, GetCaseClassification, \
    GetTeam, GetDepartment, GetQA, GetInvestigator, GetTaskTypes, GetUser, GetUsers, GetEvidenceType, GetTaskCategory, \
    GetCase, GetTask
from foreman.utils.utils import ROOT_DIR
from foreman.forms.forms import AddCaseForm, RequesterAddCaseForm, AuthoriseCaseForm, AddPriorityForm, \
    RemovePriorityForm, RemoveClassificationForm, RemoveCaseTypeForm, AddClassificationForm, AddCaseTypeForm, \
    AddTaskForm, RequesterAddTaskForm, LoginForm, PasswordChangeForm, AdminPasswordChangeForm, RegisterForm, \
    QACheckerForm, AddTaskNotesForm, DeactivateUser, ReactivateUser, AssignInvestigatorForm, AssignQAForm, \
    AssignQAFormSingle, AskForQAForm, ChainOfCustodyForm, EditEvidenceForm, EditEvidenceQRCodesForm, \
    AddEvidenceTypeForm, RemoveEvidenceTypeForm, MoveTaskTypeForm, AddTaskTypeForm, RemoveTaskTypeForm, \
    AddTaskCategoryForm, RemoveCategoryForm, AddEvidenceForm, AddEvidencePhotoForm, EvidenceAssociateForm, \
    EditTaskUsersForm, EditTaskForm, EditCaseForm, AddCaseLinkForm, RemoveCaseLinkForm, EditCaseManagersForm, \
    ReAssignTasksForm, EditUserForm, AddUserForm, EditRolesForm, OptionsForm, UploadTaskFile, AuthOptionsForm, \
    AddTeamForm, RenameTeamForm, RemoveTeamForm, AddDepartmentForm, RenameDepartmentForm, RemoveDepartmentForm, \
    TimeSheetCell, CaseHours, TaskHours, CaseTimeSheetForm, TaskTimeSheetForm, ManagersInheritForm, CloseCaseForm, \
    ChangeCaseStatusForm, EvidenceRetentionForm


INVALID_OBJECT_ID = '100'

class FormTestCaseBase(base_tester.UnitTestCase):

    getObjectPatches = (GetCaseManager, GetAuthoriser, GetCaseType, GetPriority, GetCaseClassification, GetTeam,
                        GetDepartment, GetInvestigator, GetQA, GetTaskTypes, GetUser, GetUsers, GetTaskCategory,
                        GetEvidenceType, GetCase, GetTask)

    def setUp(self):
        patchers = {}
        getObjectMocks = {}
        for toPatch in self.getObjectPatches:
            patcher = patch.object(toPatch, 'getObject')
            mock = patcher.start()

            # Set up the mock so it returns None when it gets an invalid object ID as an argument.
            def side_effect(id, _original_return_value=mock.return_value):
                if not id.isdigit() or id == INVALID_OBJECT_ID:
                    return None
                else:
                    return _original_return_value
            mock.side_effect = side_effect

            getObjectMocks[toPatch.__name__] = mock
            patchers[toPatch.__name__] = patcher

        self._patchers = patchers
        self.getObjectMocks = getObjectMocks

    def tearDown(self):
        for patcher in self._patchers.values():
            patcher.stop()

    def mock_storage(self, filename, *args, **kwargs):
        spec = ['__iter__','filename'] + [arg for arg in args]
        return MagicMock(spec=spec, filename=filename, **kwargs)


class AddCaseFormTestCase(FormTestCaseBase):
    future_date = datetime.now() + timedelta(days=30)
    original_class = AddCaseForm

    def make_input(self, **overrides):
        d = {'case_name': "Case Foo",
             'reference': "1234567",
             'private': None,
             'background': "Some background",
             'location': "London",
             'primary_case_manager': "17",
             'secondary_case_manager': "18",
             'classification': "2",
             'case_type': "2",
             'justification': "Some justification",
             'priority': "1",
             'authoriser': "40",
             'deadline': self.future_date.strftime("%d/%m/%Y")}
        d.update(overrides)
        return d

    def test_success(self):
        primary_case_manager_mock = MagicMock()
        secondary_case_manager_mock = MagicMock()
        def mock_case_manager_getobject(id):
            if id == '17':
                return primary_case_manager_mock
            if id == '18':
                return secondary_case_manager_mock
            return None

        self.getObjectMocks['GetCaseManager'].side_effect = mock_case_manager_getobject

        input = self.make_input()

        result = self.original_class().to_python(input)

        self.assertEqual(result['case_name'], 'Case Foo')
        self.assertEqual(result['reference'], '1234567')
        self.assertEqual(result['background'], 'Some background')
        self.assertEqual(result['location'], 'London')
        self.assertEqual(result['justification'], 'Some justification')
        self.assertEqual(result['private'], False)
        self.assertEqual(result['deadline'], self.future_date.date())
        self.assertTrue(result['deadline'] > datetime.now().date())
        self.assertIs(result['primary_case_manager'], primary_case_manager_mock)
        self.assertIs(result['secondary_case_manager'], secondary_case_manager_mock)
        self.assertIs(result['authoriser'], self.getObjectMocks['GetAuthoriser'].return_value)
        self.assertIs(result['case_type'], self.getObjectMocks['GetCaseType'].return_value)
        self.assertIs(result['priority'], self.getObjectMocks['GetPriority'].return_value)
        self.assertIs(result['classification'], self.getObjectMocks['GetCaseClassification'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, primary_case_manager="error")
        self._bad_field_tester(self.original_class, Invalid, secondary_case_manager="error")
        self._bad_field_tester(self.original_class, Invalid, authoriser="error")
        self._bad_field_tester(self.original_class, Invalid, case_type="error")
        self._bad_field_tester(self.original_class, Invalid, classification="error")
        self._bad_field_tester(self.original_class, Invalid, priority="error")
        self._bad_field_tester(self.original_class, Invalid, primary_case_manager="100")
        self._bad_field_tester(self.original_class, Invalid, secondary_case_manager="100")
        self._bad_field_tester(self.original_class, Invalid, authoriser="100")
        self._bad_field_tester(self.original_class, Invalid, case_type="100")
        self._bad_field_tester(self.original_class, Invalid, classification="100")
        self._bad_field_tester(self.original_class, Invalid, priority="100")
        self._bad_field_tester(self.original_class, Invalid, primary_case_manager=None)
        self._bad_field_tester(self.original_class, Invalid, secondary_case_manager=None)
        self._bad_field_tester(self.original_class, Invalid, authoriser=None)
        self._bad_field_tester(self.original_class, Invalid, case_type=None)
        self._bad_field_tester(self.original_class, Invalid, classification=None)
        self._bad_field_tester(self.original_class, Invalid, case_name=None)
        self._bad_field_tester(self.original_class, Invalid, background=None)
        self._bad_field_tester(self.original_class, Invalid, justification=None)
        self._bad_field_tester(self.original_class, Invalid, priority=None)


class RegisterFormTestCase(FormTestCaseBase):
    original_class = RegisterForm

    def make_input(self, **overrides):
        d = {'forename': "Foo",
             'middlename': None,
             'surname': "Bar",
             'username': "FooBar",
             'password': "pass",
             'password_2': "pass",
             'email': "foo@bar.com",
             'team': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['forename'], 'Foo')
        self.assertEqual(result['middlename'], '')
        self.assertIs(result['team'], self.getObjectMocks['GetTeam'].return_value)

    def test_password_mismatch(self):
        input = self.make_input(password_2="foo")

        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(input)

        invalid = cm.exception
        self.assertIn('password', invalid.error_dict)
        self.assertIn('password_2', invalid.error_dict)
        self.assertEqual(len(invalid.error_dict), 2)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, forename=None)
        self._bad_field_tester(self.original_class, Invalid, surname=None)
        self._bad_field_tester(self.original_class, Invalid, username=None)
        self._bad_field_tester(self.original_class, Invalid, password=None)
        self._bad_field_tester(self.original_class, Invalid, password_2=None)
        self._bad_field_tester(self.original_class, Invalid, email=None)
        self._bad_field_tester(self.original_class, Invalid, team=None)
        self._bad_field_tester(self.original_class, Invalid, team="Foo")
        self._bad_field_tester(self.original_class, Invalid, team="100")
        self._bad_field_tester(self.original_class, Invalid, team="-1")


class RequesterAddCaseFormTestCase(FormTestCaseBase):
    future_date = datetime.now() + timedelta(days=30)
    original_class = RequesterAddCaseForm

    def make_input(self, **overrides):
        d = {'reference': "1234567",
             'private': None,
             'background': "Some background",
             'classification': "2",
             'case_type': "2",
             'justification': "Some justification",
             'priority': "1",
             'authoriser': "40",
             'deadline': self.future_date.strftime("%d/%m/%Y")}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()

        result = self.original_class().to_python(input)

        self.assertEqual(result['reference'], '1234567')
        self.assertEqual(result['background'], 'Some background')
        self.assertEqual(result['justification'], 'Some justification')
        self.assertEqual(result['private'], False)
        self.assertEqual(result['deadline'], self.future_date.date())
        self.assertTrue(result['deadline'] > datetime.now().date())
        self.assertIs(result['authoriser'], self.getObjectMocks['GetAuthoriser'].return_value)
        self.assertIs(result['case_type'], self.getObjectMocks['GetCaseType'].return_value)
        self.assertIs(result['priority'], self.getObjectMocks['GetPriority'].return_value)
        self.assertIs(result['classification'], self.getObjectMocks['GetCaseClassification'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, authoriser="error")
        self._bad_field_tester(self.original_class, Invalid, case_type="error")
        self._bad_field_tester(self.original_class, Invalid, classification="error")
        self._bad_field_tester(self.original_class, Invalid, priority="error")
        self._bad_field_tester(self.original_class, Invalid, authoriser="100")
        self._bad_field_tester(self.original_class, Invalid, case_type="100")
        self._bad_field_tester(self.original_class, Invalid, classification="100")
        self._bad_field_tester(self.original_class, Invalid, priority="100")
        self._bad_field_tester(self.original_class, Invalid, authoriser=None)
        self._bad_field_tester(self.original_class, Invalid, case_type=None)
        self._bad_field_tester(self.original_class, Invalid, classification=None)
        self._bad_field_tester(self.original_class, Invalid, background=None)
        self._bad_field_tester(self.original_class, Invalid, justification=None)
        self._bad_field_tester(self.original_class, Invalid, priority=None)


class AuthoriseCaseFormTestCase(FormTestCaseBase):
    original_class = AuthoriseCaseForm

    def make_input(self, **overrides):
        d = {'reason': "Foo",
             'auth': "Authorised"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['reason'], 'Foo')
        self.assertEqual(result['auth'], True)

    def test_alternatives(self):
        input = self.make_input(auth="Rejected")
        result = self.original_class().to_python(input)
        self.assertEqual(result['auth'], False)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, auth=None)
        self._bad_field_tester(self.original_class, Invalid, reason=None)
        self._bad_field_tester(self.original_class, Invalid, auth="foo")


class AddPriorityFormTestCase(FormTestCaseBase):
    original_class = AddPriorityForm

    def make_input(self, **overrides):
        d = {'priority': "Foo",
             'default': "yes",
             'colour': "#FFFFFF"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['priority'], 'Foo')
        self.assertEqual(result['default'], True)
        self.assertEqual(result['colour'], '#FFFFFF')

    def test_alternatives(self):
        input = self.make_input(default="no")
        result = self.original_class().to_python(input)
        self.assertEqual(result['default'], False)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, priority=None)
        self._bad_field_tester(self.original_class, Invalid, default=None)
        self._bad_field_tester(self.original_class, Invalid, colour=None)
        self._bad_field_tester(self.original_class, Invalid, default="foo")
        self._bad_field_tester(self.original_class, Invalid, colour="FFFFFF")
        self._bad_field_tester(self.original_class, Invalid, colour="#foobar")


class RemovePriorityFormTestCase(FormTestCaseBase):
    original_class = RemovePriorityForm

    def make_input(self, **overrides):
        d = {'priority_remove': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['priority_remove'], self.getObjectMocks['GetPriority'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, priority_remove="100")
        self._bad_field_tester(self.original_class, Invalid, priority_remove="-1")
        self._bad_field_tester(self.original_class, Invalid, priority_remove=None)


class RemoveClassificationFormTestCase(FormTestCaseBase):
    original_class = RemoveClassificationForm

    def make_input(self, **overrides):
        d = {'classification': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['classification'], self.getObjectMocks['GetCaseClassification'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, classification="100")
        self._bad_field_tester(self.original_class, Invalid, classification="-1")
        self._bad_field_tester(self.original_class, Invalid, classification=None)


class RemoveCaseTypeFormTestCase(FormTestCaseBase):
    original_class = RemoveCaseTypeForm

    def make_input(self, **overrides):
        d = {'case_type': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['case_type'], self.getObjectMocks['GetCaseType'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, case_type="100")
        self._bad_field_tester(self.original_class, Invalid, case_type="-1")
        self._bad_field_tester(self.original_class, Invalid, case_type=None)


class AddClassificationFormTestCase(FormTestCaseBase):
    original_class = AddClassificationForm

    def make_input(self, **overrides):
        d = {'new_classification': "Foo",}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['new_classification'], 'Foo')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, new_classification=None)


class AddCaseTypeFormTestCase(FormTestCaseBase):
    original_class = AddCaseTypeForm

    def make_input(self, **overrides):
        d = {'new_case_type': "Foo",}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['new_case_type'], 'Foo')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, new_case_type=None)


class AddTaskFormTestCase(FormTestCaseBase):
    future_date = datetime.now() + timedelta(days=30)
    original_class = AddTaskForm

    def make_input(self, **overrides):
        d = {'task_name': "Case Foo",
             'task_type': "1",
             'background': "Some background",
             'location': "London",
             'primary_investigator': "2",
             'primary_qa': "4",
             'secondary_investigator': "3",
             'secondary_qa': "5",
             'deadline': self.future_date.strftime("%d/%m/%Y")}
        d.update(overrides)
        return d

    def test_success(self):
        primary_investigator_mock = MagicMock()
        secondary_investigator_mock = MagicMock()
        def mock_investigator_getobject(id):
            if id == '2':
                return primary_investigator_mock
            if id == '3':
                return secondary_investigator_mock
            return None

        primary_qa_mock = MagicMock()
        secondary_qa_mock = MagicMock()

        def mock_qa_getobject(id):
            if id == '4':
                return primary_qa_mock
            if id == '5':
                return secondary_qa_mock
            return None

        self.getObjectMocks['GetQA'].side_effect = mock_qa_getobject
        self.getObjectMocks['GetInvestigator'].side_effect = mock_investigator_getobject

        input = self.make_input()

        result = self.original_class().to_python(input)

        self.assertEqual(result['task_name'], 'Case Foo')
        self.assertEqual(result['task_type'], self.getObjectMocks['GetTaskTypes'].return_value)
        self.assertEqual(result['background'], 'Some background')
        self.assertEqual(result['location'], 'London')
        self.assertEqual(result['deadline'], self.future_date.date())
        self.assertTrue(result['deadline'] > datetime.now().date())
        self.assertIs(result['primary_investigator'], primary_investigator_mock)
        self.assertIs(result['primary_qa'], primary_qa_mock)
        self.assertIs(result['secondary_investigator'], secondary_investigator_mock)
        self.assertIs(result['secondary_qa'], secondary_qa_mock)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, primary_investigator="error")
        self._bad_field_tester(self.original_class, Invalid, secondary_investigator="error")
        self._bad_field_tester(self.original_class, Invalid, primary_investigator="100")
        self._bad_field_tester(self.original_class, Invalid, secondary_investigator="100")
        self._bad_field_tester(self.original_class, Invalid, primary_qa="error")
        self._bad_field_tester(self.original_class, Invalid, secondary_qa="error")
        self._bad_field_tester(self.original_class, Invalid, primary_qa="100")
        self._bad_field_tester(self.original_class, Invalid, secondary_qa="100")
        self._bad_field_tester(self.original_class, Invalid, task_name=None)
        self._bad_field_tester(self.original_class, Invalid, task_type=None)
        self._bad_field_tester(self.original_class, Invalid, background=None)


class RequesterAddTaskFormTestCase(FormTestCaseBase):
    future_date = datetime.now() + timedelta(days=30)
    original_class = RequesterAddTaskForm

    def make_input(self, **overrides):
        d = {'task_type': "1",
             'background': "Some background",}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()

        result = self.original_class().to_python(input)
        self.assertEqual(result['task_type'], self.getObjectMocks['GetTaskTypes'].return_value)
        self.assertEqual(result['background'], 'Some background')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, task_type=None)
        self._bad_field_tester(self.original_class, Invalid, task_type="100")
        self._bad_field_tester(self.original_class, Invalid, background=None)


class LoginFormTestCase(FormTestCaseBase):
    original_class = LoginForm

    def make_input(self, **overrides):
        d = {'username': "administrator",
             'password': "changeme"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['username'], 'administrator')
        self.assertEqual(result['password'], 'changeme')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, username=None)
        self._bad_field_tester(self.original_class, Invalid, password=None)


class PasswordChangeFormTestCase(FormTestCaseBase):
    original_class = PasswordChangeForm

    def make_input(self, **overrides):
        d = {'password': "pass",
             'new_password': "pass1",
             'new_password_2': "pass1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['password'], 'pass')
        self.assertEqual(result['new_password'], 'pass1')
        self.assertEqual(result['new_password_2'], 'pass1')

    def test_password_mismatch(self):
        input = self.make_input(new_password_2="foo")

        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(input)

        invalid = cm.exception
        self.assertIn('new_password', invalid.error_dict)
        self.assertIn('new_password_2', invalid.error_dict)
        self.assertEqual(len(invalid.error_dict), 2)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, new_password=None)
        self._bad_field_tester(self.original_class, Invalid, new_password_2=None)
        self._bad_field_tester(self.original_class, Invalid, password=None)


class AdminPasswordChangeFormTestCase(FormTestCaseBase):
    original_class = AdminPasswordChangeForm

    def make_input(self, **overrides):
        d = {'new_password': "pass1",
             'new_password_2': "pass1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['new_password'], 'pass1')
        self.assertEqual(result['new_password_2'], 'pass1')

    def test_password_mismatch(self):
        input = self.make_input(new_password_2="foo")

        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(input)

        invalid = cm.exception
        self.assertIn('new_password', invalid.error_dict)
        self.assertIn('new_password_2', invalid.error_dict)
        self.assertEqual(len(invalid.error_dict), 2)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, new_password=None)
        self._bad_field_tester(self.original_class, Invalid, new_password_2=None)


class QACheckerFormTestCase(FormTestCaseBase):
    original_class = QACheckerForm

    def make_input(self, **overrides):
        d = {'notes': "Foo",
             'qa_decision': "qa_pass"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['notes'], 'Foo')
        self.assertEqual(result['qa_decision'], True)

    def test_alternatives(self):
        input = self.make_input(qa_decision="qa_fail")
        result = self.original_class().to_python(input)
        self.assertEqual(result['qa_decision'], False)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, notes=None)
        self._bad_field_tester(self.original_class, Invalid, qa_decision=None)


class AddTaskNotesFormTestCase(FormTestCaseBase):
    original_class = AddTaskNotesForm

    def make_input(self, **overrides):
        d = {'notes': "Foo",}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['notes'], 'Foo')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, notes=None)


class DeactivateUserTestCase(FormTestCaseBase):
    original_class = DeactivateUser

    def make_input(self, **overrides):
        d = {'deactivate_user': "2"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['deactivate_user'], self.getObjectMocks['GetUser'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, deactivate_user="100")
        self._bad_field_tester(self.original_class, Invalid, deactivate_user="-1")
        self._bad_field_tester(self.original_class, Invalid, deactivate_user="foo")
        self._bad_field_tester(self.original_class, Invalid, deactivate_user=None)


class ReactivateUserTestCase(FormTestCaseBase):
    original_class = ReactivateUser

    def make_input(self, **overrides):
        d = {'reactivate_user': "2"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['reactivate_user'], self.getObjectMocks['GetUser'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, reactivate_user="100")
        self._bad_field_tester(self.original_class, Invalid, reactivate_user="-1")
        self._bad_field_tester(self.original_class, Invalid, reactivate_user="foo")
        self._bad_field_tester(self.original_class, Invalid, reactivate_user=None)


class AssignInvestigatorFormTestCase(FormTestCaseBase):
    original_class = AssignInvestigatorForm

    def make_input(self, **overrides):
        d = {'investigator': "2",
             'role': "Principle Investigator"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['investigator'], self.getObjectMocks['GetInvestigator'].return_value)
        self.assertEqual(result['role'], True)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, investigator="100")
        self._bad_field_tester(self.original_class, Invalid, investigator="-1")
        self._bad_field_tester(self.original_class, Invalid, investigator="foo")
        self._bad_field_tester(self.original_class, Invalid, role="foo")


class AssignQAFormTestCase(FormTestCaseBase):
    original_class = AssignQAForm

    def make_input(self, **overrides):
        d = {'investigator': "2",
             'investigator2': "3"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['investigator'], self.getObjectMocks['GetQA'].return_value)
        self.assertIs(result['investigator2'], self.getObjectMocks['GetQA'].return_value)

    def test_alternatives(self):
        input = self.make_input(investigator2="null")
        result = self.original_class().to_python(input)
        self.assertEqual(result['investigator2'], None)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, investigator="100")
        self._bad_field_tester(self.original_class, Invalid, investigator="-1")
        self._bad_field_tester(self.original_class, Invalid, investigator="foo")
        self._bad_field_tester(self.original_class, Invalid, investigator=None)
        self._bad_field_tester(self.original_class, Invalid, investigator2="100")
        self._bad_field_tester(self.original_class, Invalid, investigator2="-1")
        self._bad_field_tester(self.original_class, Invalid, investigator2="foo")


class AssignQAFormSingleTestCase(FormTestCaseBase):
    original_class = AssignQAFormSingle

    def make_input(self, **overrides):
        d = {'investigator': "2"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['investigator'], self.getObjectMocks['GetQA'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, investigator="100")
        self._bad_field_tester(self.original_class, Invalid, investigator="-1")
        self._bad_field_tester(self.original_class, Invalid, investigator="foo")
        self._bad_field_tester(self.original_class, Invalid, investigator=None)
        self._bad_field_tester(self.original_class, Invalid, investigator="null")


class AskForQAFormTestCase(FormTestCaseBase):
    original_class = AskForQAForm

    def make_input(self, **overrides):
        d = {'qa_partners': "2",
             'subject': "foo",
             'body': "foo1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['qa_partners'], self.getObjectMocks['GetUsers'].return_value)
        self.assertEqual(result['subject'], 'foo')
        self.assertEqual(result['body'], 'foo1')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, qa_partners="100")
        self._bad_field_tester(self.original_class, Invalid, qa_partners="-1")
        self._bad_field_tester(self.original_class, Invalid, qa_partners="foo")
        self._bad_field_tester(self.original_class, Invalid, subject=None)
        self._bad_field_tester(self.original_class, Invalid, body=None)
        self._bad_field_tester(self.original_class, Invalid, qa_partners="null")


class ChainOfCustodyFormTestCase(FormTestCaseBase):
    original_class = ChainOfCustodyForm

    def make_input(self, **overrides):
        d = {'date': "12 March 2016",
             'time': "14:15",
             'user': "Foo",
             'comments': "Foo",
             'attach': None,
             'label': None}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['user'], 'Foo')
        self.assertEqual(result['comments'], 'Foo')
        self.assertEqual(result['date'], date(2016, 3, 12))
        self.assertEqual(result['time'], time(14, 15, 0))

    def test_alternatives(self):
        mock_file_storage = self.mock_storage('test.txt', 'seek')
        input = self.make_input(attach=mock_file_storage, label="foo")
        result = self.original_class().to_python(input)
        mock_file_storage.seek.assert_called_once_with(0)
        self.assertEqual(result['label'], "foo")
        self.assertIs(result['attach'], mock_file_storage)

    def test_required_fields(self):
        input = self.make_input(attach=self.mock_storage('test.txt', 'seek'), label=None)
        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(input)
        invalid = cm.exception
        self.assertIn('label', invalid.error_dict)
        self.assertEqual(len(invalid.error_dict), 1)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, date=None)
        self._bad_field_tester(self.original_class, Invalid, date="35 March 2016")
        self._bad_field_tester(self.original_class, Invalid, date="foo")
        self._bad_field_tester(self.original_class, Invalid, time=None)
        self._bad_field_tester(self.original_class, Invalid, time="26:89")
        self._bad_field_tester(self.original_class, Invalid, time="foo")
        self._bad_field_tester(self.original_class, Invalid, user=None)
        self._bad_field_tester(self.original_class, Invalid, comments=None)


class EditEvidenceFormTestCase(FormTestCaseBase):
    original_class = EditEvidenceForm

    def make_input(self, **overrides):
        d = {'reference': "foo",
             'status': "Inactive",
             'bag_num': "foo1",
             'type': "1",
             'originator': "foo",
             'comments': "comment",
             'location': "loc"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['type'], self.getObjectMocks['GetEvidenceType'].return_value)
        self.assertEqual(result['reference'], 'foo')
        self.assertEqual(result['status'], 'Inactive')
        self.assertEqual(result['bag_num'], 'foo1')
        self.assertEqual(result['originator'], 'foo')
        self.assertEqual(result['comments'], 'comment')
        self.assertEqual(result['location'], 'loc')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, status="error")
        self._bad_field_tester(self.original_class, Invalid, status=None)
        self._bad_field_tester(self.original_class, Invalid, reference=None)
        self._bad_field_tester(self.original_class, Invalid, type="100")
        self._bad_field_tester(self.original_class, Invalid, type="-1")
        self._bad_field_tester(self.original_class, Invalid, type=None)
        self._bad_field_tester(self.original_class, Invalid, originator=None)
        self._bad_field_tester(self.original_class, Invalid, comments=None)
        self._bad_field_tester(self.original_class, Invalid, location=None)


class EditEvidenceQRCodesFormTestCase(FormTestCaseBase):
    original_class = EditEvidenceQRCodesForm

    def make_input(self, **overrides):
        d = {'qr_code_text': "Foo",
             'qr_code': None}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['qr_code_text'], 'Foo')
        self.assertEqual(result['qr_code'], False)

    def test_alternatives(self):
        input = self.make_input(qr_code="checked")
        result = self.original_class().to_python(input)
        self.assertEqual(result['qr_code'], True)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, qr_code_text=None)


class AddEvidenceTypeFormTestCase(FormTestCaseBase):
    original_class = AddEvidenceTypeForm

    def make_input(self, **overrides):
        d = {'evi_type_new': "Foo",
             'icon_input': "cd.png"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['evi_type_new'], 'Foo')
        self.assertEqual(result['icon_input'], path.join(ROOT_DIR, 'static', 'images', 'siteimages',
                                                           'evidence_icons_unique', "cd.png"))

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, evi_type_new=None)
        self._bad_field_tester(self.original_class, Invalid, icon_input=None)
        self._bad_field_tester(self.original_class, Invalid, icon_input="foo.png")


class RemoveEvidenceTypeFormTestCase(FormTestCaseBase):
    original_class = RemoveEvidenceTypeForm

    def make_input(self, **overrides):
        d = {'evi_type': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['evi_type'], self.getObjectMocks['GetEvidenceType'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, evi_type="100")
        self._bad_field_tester(self.original_class, Invalid, evi_type="-1")
        self._bad_field_tester(self.original_class, Invalid, evi_type="foo")
        self._bad_field_tester(self.original_class, Invalid, evi_type=None)


class MoveTaskTypeFormTestCase(FormTestCaseBase):
    original_class = MoveTaskTypeForm

    def make_input(self, **overrides):
        d = {'task_category': "1",
             'task_type': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['task_category'], self.getObjectMocks['GetTaskCategory'].return_value)
        self.assertIs(result['task_type'], self.getObjectMocks['GetTaskTypes'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, task_category="100")
        self._bad_field_tester(self.original_class, Invalid, task_category="-1")
        self._bad_field_tester(self.original_class, Invalid, task_category="foo")
        self._bad_field_tester(self.original_class, Invalid, task_category=None)
        self._bad_field_tester(self.original_class, Invalid, task_type="100")
        self._bad_field_tester(self.original_class, Invalid, task_type="-1")
        self._bad_field_tester(self.original_class, Invalid, task_type="foo")
        self._bad_field_tester(self.original_class, Invalid, task_type=None)


class AddTaskTypeFormTestCase(FormTestCaseBase):
    original_class = AddTaskTypeForm

    def make_input(self, **overrides):
        d = {'new_task_type': "foo",
             'change_task_category': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['change_task_category'], self.getObjectMocks['GetTaskCategory'].return_value)
        self.assertEqual(result['new_task_type'], 'foo')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, change_task_category="100")
        self._bad_field_tester(self.original_class, Invalid, change_task_category="-1")
        self._bad_field_tester(self.original_class, Invalid, change_task_category="foo")
        self._bad_field_tester(self.original_class, Invalid, change_task_category=None)
        self._bad_field_tester(self.original_class, Invalid, new_task_type=None)


class RemoveTaskTypeFormTestCase(FormTestCaseBase):
    original_class = RemoveTaskTypeForm

    def make_input(self, **overrides):
        d = {'remove_task_type': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['remove_task_type'], self.getObjectMocks['GetTaskTypes'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, remove_task_type="100")
        self._bad_field_tester(self.original_class, Invalid, remove_task_type="-1")
        self._bad_field_tester(self.original_class, Invalid, remove_task_type="foo")
        self._bad_field_tester(self.original_class, Invalid, remove_task_type=None)


class AddTaskCategoryFormTestCase(FormTestCaseBase):
    original_class = AddTaskCategoryForm

    def make_input(self, **overrides):
        d = {'new_task_category': "Foo"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['new_task_category'], 'Foo')

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, new_task_category=None)


class RemoveCategoryFormTestCase(FormTestCaseBase):
    original_class = RemoveCategoryForm

    def make_input(self, **overrides):
        d = {'remove_task_category': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['remove_task_category'], self.getObjectMocks['GetTaskCategory'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, remove_task_category="100")
        self._bad_field_tester(self.original_class, Invalid, remove_task_category="-1")
        self._bad_field_tester(self.original_class, Invalid, remove_task_category="foo")
        self._bad_field_tester(self.original_class, Invalid, remove_task_category=None)


class AddEvidenceFormTestCase(FormTestCaseBase):
    original_class = AddEvidenceForm

    def make_input(self, **overrides):
        d = {'reference': "foo",
             'status': "Inactive",
             'bag_num': "foo1",
             'type': "1",
             'originator': "foo",
             'comments': "comment",
             'location': "loc",
             'qr': "checked"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['type'], self.getObjectMocks['GetEvidenceType'].return_value)
        self.assertEqual(result['reference'], 'foo')
        self.assertEqual(result['status'], 'Inactive')
        self.assertEqual(result['bag_num'], 'foo1')
        self.assertEqual(result['originator'], 'foo')
        self.assertEqual(result['comments'], 'comment')
        self.assertEqual(result['location'], 'loc')
        self.assertEqual(result['qr'], True)

    def test_alternatives(self):
        input = self.make_input(qr=None)
        result = self.original_class().to_python(input)
        self.assertEqual(result['qr'], False)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, status="error")
        self._bad_field_tester(self.original_class, Invalid, status=None)
        self._bad_field_tester(self.original_class, Invalid, reference=None)
        self._bad_field_tester(self.original_class, Invalid, type="100")
        self._bad_field_tester(self.original_class, Invalid, type="-1")
        self._bad_field_tester(self.original_class, Invalid, type=None)
        self._bad_field_tester(self.original_class, Invalid, originator=None)
        self._bad_field_tester(self.original_class, Invalid, comments=None)
        self._bad_field_tester(self.original_class, Invalid, location=None)


class AddEvidencePhotoFormTestCase(FormTestCaseBase):
    original_class = AddEvidencePhotoForm

    def make_input(self, **overrides):
        self.mock = self.mock_storage('test.png', 'seek', 'mimetype', 'content_type', mimetype="image/text")
        d = {'file_title': "Foo",
             'comments': "Foo1",
             'file': self.mock}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.mock.seek.assert_called_once_with(0)
        self.assertEqual(result['file_title'], 'Foo')
        self.assertEqual(result['comments'], 'Foo1')
        self.assertEqual(result['file'], self.mock)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, file_title=None)
        self._bad_field_tester(self.original_class, Invalid, comments=None)
        self._bad_field_tester(self.original_class, Invalid, file=None)
        self._bad_field_tester(self.original_class, Invalid, file=self.mock_storage('test.txt', 'seek',
                                                                                    'mimetype', 'content_type',
                                                                                    mimetype="html/text"))


class EvidenceAssociateFormTestCase(FormTestCaseBase):
    original_class = EvidenceAssociateForm

    def make_input(self, **overrides):
        d = {'case_reassign': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['case_reassign'], self.getObjectMocks['GetCase'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, case_reassign="100")
        self._bad_field_tester(self.original_class, Invalid, case_reassign="-1")
        self._bad_field_tester(self.original_class, Invalid, case_reassign="foo")
        self._bad_field_tester(self.original_class, Invalid, case_reassign=None)


class EditTaskUsersFormTestCase(FormTestCaseBase):
    original_class = EditTaskUsersForm

    def make_input(self, **overrides):
        d = {'primary_investigator': "2",
             'primary_qa': "4",
             'secondary_investigator': "3",
             'secondary_qa': "5"}
        d.update(overrides)
        return d

    def test_success(self):
        primary_investigator_mock = MagicMock()
        secondary_investigator_mock = MagicMock()
        def mock_investigator_getobject(id):
            if id == '2':
                return primary_investigator_mock
            if id == '3':
                return secondary_investigator_mock
            return None

        primary_qa_mock = MagicMock()
        secondary_qa_mock = MagicMock()

        def mock_qa_getobject(id):
            if id == '4':
                return primary_qa_mock
            if id == '5':
                return secondary_qa_mock
            return None

        self.getObjectMocks['GetQA'].side_effect = mock_qa_getobject
        self.getObjectMocks['GetInvestigator'].side_effect = mock_investigator_getobject

        input = self.make_input()

        result = self.original_class().to_python(input)
        self.assertIs(result['primary_investigator'], primary_investigator_mock)
        self.assertIs(result['primary_qa'], primary_qa_mock)
        self.assertIs(result['secondary_investigator'], secondary_investigator_mock)
        self.assertIs(result['secondary_qa'], secondary_qa_mock)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, primary_investigator="error")
        self._bad_field_tester(self.original_class, Invalid, secondary_investigator="error")
        self._bad_field_tester(self.original_class, Invalid, primary_investigator="100")
        self._bad_field_tester(self.original_class, Invalid, secondary_investigator="100")
        self._bad_field_tester(self.original_class, Invalid, primary_qa="error")
        self._bad_field_tester(self.original_class, Invalid, secondary_qa="error")
        self._bad_field_tester(self.original_class, Invalid, primary_qa="100")
        self._bad_field_tester(self.original_class, Invalid, secondary_qa="100")


class EditTaskFormTestCase(FormTestCaseBase):
    future_date = datetime.now() + timedelta(days=30)
    original_class = EditTaskForm

    def make_input(self, **overrides):
        d = {'task_name': "Case Foo",
             'task_type': "1",
             'background': "Some background",
             'location': "London",
             'deadline': self.future_date.strftime("%d/%m/%Y")}
        d.update(overrides)
        return d

    def test_success(self):

        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['task_name'], 'Case Foo')
        self.assertEqual(result['task_type'], self.getObjectMocks['GetTaskTypes'].return_value)
        self.assertEqual(result['background'], 'Some background')
        self.assertEqual(result['location'], 'London')
        self.assertEqual(result['deadline'], self.future_date.date())
        self.assertTrue(result['deadline'] > datetime.now().date())

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, task_name=None)
        self._bad_field_tester(self.original_class, Invalid, task_type=None)
        self._bad_field_tester(self.original_class, Invalid, background=None)


class EditCaseFormTestCase(FormTestCaseBase):
    future_date = datetime.now() + timedelta(days=30)
    original_class = EditCaseForm

    def make_input(self, **overrides):
        d = {'case_name': "Case Foo",
             'reference': "1234567",
             'private': None,
             'background': "Some background",
             'location': "London",
             'classification': "2",
             'case_type': "2",
             'justification': "Some justification",
             'priority': "1",
             'authoriser': "40",
             'deadline': self.future_date.strftime("%d/%m/%Y")}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()

        result = self.original_class().to_python(input)

        self.assertEqual(result['case_name'], 'Case Foo')
        self.assertEqual(result['reference'], '1234567')
        self.assertEqual(result['background'], 'Some background')
        self.assertEqual(result['location'], 'London')
        self.assertEqual(result['justification'], 'Some justification')
        self.assertEqual(result['private'], False)
        self.assertEqual(result['deadline'], self.future_date.date())
        self.assertTrue(result['deadline'] > datetime.now().date())
        self.assertIs(result['authoriser'], self.getObjectMocks['GetAuthoriser'].return_value)
        self.assertIs(result['case_type'], self.getObjectMocks['GetCaseType'].return_value)
        self.assertIs(result['priority'], self.getObjectMocks['GetPriority'].return_value)
        self.assertIs(result['classification'], self.getObjectMocks['GetCaseClassification'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, authoriser="error")
        self._bad_field_tester(self.original_class, Invalid, case_type="error")
        self._bad_field_tester(self.original_class, Invalid, classification="error")
        self._bad_field_tester(self.original_class, Invalid, priority="error")
        self._bad_field_tester(self.original_class, Invalid, authoriser="100")
        self._bad_field_tester(self.original_class, Invalid, case_type="100")
        self._bad_field_tester(self.original_class, Invalid, classification="100")
        self._bad_field_tester(self.original_class, Invalid, priority="100")
        self._bad_field_tester(self.original_class, Invalid, authoriser=None)
        self._bad_field_tester(self.original_class, Invalid, case_type=None)
        self._bad_field_tester(self.original_class, Invalid, classification=None)
        self._bad_field_tester(self.original_class, Invalid, case_name=None)
        self._bad_field_tester(self.original_class, Invalid, background=None)
        self._bad_field_tester(self.original_class, Invalid, justification=None)
        self._bad_field_tester(self.original_class, Invalid, priority=None)


class AddCaseLinkFormTestCase(FormTestCaseBase):
    original_class = AddCaseLinkForm

    def make_input(self, **overrides):
        d = {'reason_add': "foo",
             'case_links_add': "1"}
        d.update(overrides)
        return d

    def test_success(self):

        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['reason_add'], 'foo')
        self.assertEqual(result['case_links_add'], self.getObjectMocks['GetCase'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, reason_add=None)
        self._bad_field_tester(self.original_class, Invalid, case_links_add=None)
        self._bad_field_tester(self.original_class, Invalid, case_links_add="foo")
        self._bad_field_tester(self.original_class, Invalid, case_links_add="100")
        self._bad_field_tester(self.original_class, Invalid, case_links_add="-1")


class RemoveCaseLinkFormTestCase(FormTestCaseBase):
    original_class = RemoveCaseLinkForm

    def make_input(self, **overrides):
        d = {'reason': "foo",
             'case_links': "1"}
        d.update(overrides)
        return d

    def test_success(self):

        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['reason'], 'foo')
        self.assertEqual(result['case_links'], self.getObjectMocks['GetCase'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, reason=None)
        self._bad_field_tester(self.original_class, Invalid, case_links=None)
        self._bad_field_tester(self.original_class, Invalid, case_links="foo")
        self._bad_field_tester(self.original_class, Invalid, case_links="100")
        self._bad_field_tester(self.original_class, Invalid, case_links="-1")


class EditCaseManagersFormTestCase(FormTestCaseBase):
    original_class = EditCaseManagersForm

    def make_input(self, **overrides):
        d = {'primary_case_manager': "17",
             'secondary_case_manager': "18"}
        d.update(overrides)
        return d

    def test_success(self):
        primary_case_manager_mock = MagicMock()
        secondary_case_manager_mock = MagicMock()
        def mock_case_manager_getobject(id):
            if id == '17':
                return primary_case_manager_mock
            if id == '18':
                return secondary_case_manager_mock
            return None

        self.getObjectMocks['GetCaseManager'].side_effect = mock_case_manager_getobject

        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['primary_case_manager'], primary_case_manager_mock)
        self.assertEqual(result['secondary_case_manager'], secondary_case_manager_mock)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, primary_case_manager=None)
        self._bad_field_tester(self.original_class, Invalid, primary_case_manager="foo")
        self._bad_field_tester(self.original_class, Invalid, primary_case_manager="100")
        self._bad_field_tester(self.original_class, Invalid, primary_case_manager="-1")
        self._bad_field_tester(self.original_class, Invalid, secondary_case_manager=None)
        self._bad_field_tester(self.original_class, Invalid, secondary_case_manager="foo")
        self._bad_field_tester(self.original_class, Invalid, secondary_case_manager="100")
        self._bad_field_tester(self.original_class, Invalid, secondary_case_manager="-1")


class ReAssignTasksFormTestCase(FormTestCaseBase):
    original_class = ReAssignTasksForm

    def make_input(self, **overrides):
        d = {'task_reassign': "1",
             'case_reassign': "1"}
        d.update(overrides)
        return d

    def test_success(self):

        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['task_reassign'], self.getObjectMocks['GetTask'].return_value)
        self.assertEqual(result['case_reassign'], self.getObjectMocks['GetCase'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, task_reassign=None)
        self._bad_field_tester(self.original_class, Invalid, task_reassign="foo")
        self._bad_field_tester(self.original_class, Invalid, task_reassign="100")
        self._bad_field_tester(self.original_class, Invalid, task_reassign="-1")
        self._bad_field_tester(self.original_class, Invalid, case_reassign=None)
        self._bad_field_tester(self.original_class, Invalid, case_reassign="foo")
        self._bad_field_tester(self.original_class, Invalid, case_reassign="100")
        self._bad_field_tester(self.original_class, Invalid, case_reassign="-1")


class EditUserFormTestCase(FormTestCaseBase):
    original_class = EditUserForm

    def make_input(self, **overrides):
        d = {'forename': "foo",
             'surname': "foo1",
             'middlename': "foo2",
             'username': "user",
             'email': "email",
             'telephone': "phone",
             'alt_telephone': "phone2",
             'fax': "fax",
             'job_title': "job",
             'team': "1",
             'photo': None,
             'manager': "1",
             'user': "2"}
        d.update(overrides)
        return d

    def test_success(self):
        user_mock = MagicMock()
        manager_mock = MagicMock()

        def mock_user_getobject(id):
            if id == '2':
                return user_mock
            if id == '1':
                return manager_mock
            return None

        self.getObjectMocks['GetUser'].side_effect = mock_user_getobject

        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['forename'], 'foo')
        self.assertEqual(result['surname'], 'foo1')
        self.assertEqual(result['middlename'], 'foo2')
        self.assertEqual(result['username'], 'user')
        self.assertEqual(result['email'], 'email')
        self.assertEqual(result['telephone'], 'phone')
        self.assertEqual(result['alt_telephone'], 'phone2')
        self.assertEqual(result['fax'], 'fax')
        self.assertEqual(result['job_title'], 'job')
        self.assertEqual(result['user'], user_mock)
        self.assertEqual(result['manager'], manager_mock)
        self.assertEqual(result['team'], self.getObjectMocks['GetTeam'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, user=None)
        self._bad_field_tester(self.original_class, Invalid, user="foo")
        self._bad_field_tester(self.original_class, Invalid, user="100")
        self._bad_field_tester(self.original_class, Invalid, user="-1")
        self._bad_field_tester(self.original_class, Invalid, manager=None)
        self._bad_field_tester(self.original_class, Invalid, manager="foo")
        self._bad_field_tester(self.original_class, Invalid, manager="100")
        self._bad_field_tester(self.original_class, Invalid, manager="-1")
        self._bad_field_tester(self.original_class, Invalid, team=None)
        self._bad_field_tester(self.original_class, Invalid, team="foo")
        self._bad_field_tester(self.original_class, Invalid, team="100")
        self._bad_field_tester(self.original_class, Invalid, team="-1")
        self._bad_field_tester(self.original_class, Invalid, forename=None)
        self._bad_field_tester(self.original_class, Invalid, surname=None)
        self._bad_field_tester(self.original_class, Invalid, username=None)
        self._bad_field_tester(self.original_class, Invalid, email=None)
        self._bad_field_tester(self.original_class, Invalid, job_title=None)


class AddUserFormTestCase(FormTestCaseBase):
    original_class = AddUserForm

    def make_input(self, **overrides):
        d = {'forename': "foo",
             'surname': "foo1",
             'middlename': "foo2",
             'username': "user",
             'email': "email",
             'telephone': "phone",
             'alt_telephone': "phone2",
             'fax': "fax",
             'job_title': "job",
             'team': "1",
             'manager': "1",
             'administrator': "yes",
             'casemanager': "yes",
             'requester': "yes",
             'authoriser': "yes",
             'investigator': "yes",
             'qa': "yes"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['forename'], 'foo')
        self.assertEqual(result['surname'], 'foo1')
        self.assertEqual(result['middlename'], 'foo2')
        self.assertEqual(result['username'], 'user')
        self.assertEqual(result['email'], 'email')
        self.assertEqual(result['telephone'], 'phone')
        self.assertEqual(result['alt_telephone'], 'phone2')
        self.assertEqual(result['fax'], 'fax')
        self.assertEqual(result['job_title'], 'job')
        self.assertEqual(result['manager'], self.getObjectMocks['GetUser'].return_value)
        self.assertEqual(result['team'], self.getObjectMocks['GetTeam'].return_value)
        self.assertEqual(result['administrator'], True)
        self.assertEqual(result['casemanager'], True)
        self.assertEqual(result['requester'], True)
        self.assertEqual(result['authoriser'], True)
        self.assertEqual(result['investigator'], True)
        self.assertEqual(result['qa'], True)

    def test_alternatives(self):
        input = self.make_input(administrator="no", casemanager="no", requester="no", authoriser="no",
                                investigator="no", qa="no")
        result = self.original_class().to_python(input)
        self.assertEqual(result['administrator'], False)
        self.assertEqual(result['casemanager'], False)
        self.assertEqual(result['requester'], False)
        self.assertEqual(result['authoriser'], False)
        self.assertEqual(result['investigator'], False)
        self.assertEqual(result['qa'], False)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, manager="foo")
        self._bad_field_tester(self.original_class, Invalid, manager="100")
        self._bad_field_tester(self.original_class, Invalid, manager="-1")
        self._bad_field_tester(self.original_class, Invalid, team=None)
        self._bad_field_tester(self.original_class, Invalid, team="foo")
        self._bad_field_tester(self.original_class, Invalid, team="100")
        self._bad_field_tester(self.original_class, Invalid, team="-1")
        self._bad_field_tester(self.original_class, Invalid, forename=None)
        self._bad_field_tester(self.original_class, Invalid, surname=None)
        self._bad_field_tester(self.original_class, Invalid, username=None)
        self._bad_field_tester(self.original_class, Invalid, email=None)
        self._bad_field_tester(self.original_class, Invalid, job_title=None)
        self._bad_field_tester(self.original_class, Invalid, administrator=None)
        self._bad_field_tester(self.original_class, Invalid, casemanager=None)
        self._bad_field_tester(self.original_class, Invalid, requester=None)
        self._bad_field_tester(self.original_class, Invalid, authoriser=None)
        self._bad_field_tester(self.original_class, Invalid, investigator=None)
        self._bad_field_tester(self.original_class, Invalid, qa=None)
        self._bad_field_tester(self.original_class, Invalid, administrator="foo")
        self._bad_field_tester(self.original_class, Invalid, casemanager="foo")
        self._bad_field_tester(self.original_class, Invalid, requester="foo")
        self._bad_field_tester(self.original_class, Invalid, authoriser="foo")
        self._bad_field_tester(self.original_class, Invalid, investigator="foo")
        self._bad_field_tester(self.original_class, Invalid, qa="foo")


class EditRolesFormTestCase(FormTestCaseBase):
    original_class = EditRolesForm

    def make_input(self, **overrides):
        d = {'administrator': "yes",
             'casemanager': "yes",
             'requester': "yes",
             'authoriser': "yes",
             'investigator': "yes",
             'qa': "yes",
            }
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['administrator'], True)
        self.assertEqual(result['casemanager'], True)
        self.assertEqual(result['requester'], True)
        self.assertEqual(result['authoriser'], True)
        self.assertEqual(result['investigator'], True)
        self.assertEqual(result['qa'], True)

    def test_alternatives(self):
        input = self.make_input(administrator="no", casemanager="no", requester="no", authoriser="no",
                                investigator="no", qa="no")
        result = self.original_class().to_python(input)
        self.assertEqual(result['administrator'], False)
        self.assertEqual(result['casemanager'], False)
        self.assertEqual(result['requester'], False)
        self.assertEqual(result['authoriser'], False)
        self.assertEqual(result['investigator'], False)
        self.assertEqual(result['qa'], False)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, administrator=None)
        self._bad_field_tester(self.original_class, Invalid, casemanager=None)
        self._bad_field_tester(self.original_class, Invalid, requester=None)
        self._bad_field_tester(self.original_class, Invalid, authoriser=None)
        self._bad_field_tester(self.original_class, Invalid, investigator=None)
        self._bad_field_tester(self.original_class, Invalid, qa=None)
        self._bad_field_tester(self.original_class, Invalid, administrator="foo")
        self._bad_field_tester(self.original_class, Invalid, casemanager="foo")
        self._bad_field_tester(self.original_class, Invalid, requester="foo")
        self._bad_field_tester(self.original_class, Invalid, authoriser="foo")
        self._bad_field_tester(self.original_class, Invalid, investigator="foo")
        self._bad_field_tester(self.original_class, Invalid, qa="foo")


class OptionsFormTestCase(FormTestCaseBase):
   original_class = OptionsForm

   def make_input(self, **overrides):
       d = {'company': "Foo",
            'department': "dep",
            'folder': "folder",
            'datedisplay': "%B %Y",
            'case_names': "NumericIncrement",
            'task_names': "NumericIncrement",
            'upload_case_names': None,
            'upload_task_names': None}
       d.update(overrides)
       return d

   def test_success(self):
       input = self.make_input()
       result = self.original_class().to_python(input)
       self.assertEqual(result['company'], "Foo")
       self.assertEqual(result['department'], "dep")
       self.assertEqual(result['folder'], "folder")
       self.assertEqual(result['datedisplay'], "%B %Y")
       self.assertEqual(result['case_names'], "NumericIncrement")
       self.assertEqual(result['task_names'], "NumericIncrement")
       self.assertEqual(result['upload_case_names'], None)
       self.assertEqual(result['upload_task_names'], None)

   def test_alternatives(self):
       self.mock_case = self.mock_storage('test.txt', 'seek', 'mimetype', 'content_type', 'save', mimetype="text/plain")
       self.mock_task = self.mock_storage('test.txt', 'seek', 'mimetype', 'content_type', 'save', mimetype="text/plain")

       input = self.make_input(upload_case_names=self.mock_case)
       result = self.original_class().to_python(input)
       self.assertIs(result['upload_case_names'], self.mock_case.filename)

       input = self.make_input(upload_task_names=self.mock_task)
       result = self.original_class().to_python(input)
       self.assertIs(result['upload_task_names'], self.mock_task.filename)

   def test_bad_fields(self):
       self._bad_field_tester(self.original_class, Invalid, datedisplay="foo")
       self._bad_field_tester(self.original_class, Invalid, case_names="foo")
       self._bad_field_tester(self.original_class, Invalid, task_names="foo")
       self._bad_field_tester(self.original_class, Invalid,
                              upload_task_names=self.mock_storage('test.png', 'seek', 'mimetype', 'save',
                                                                  'content_type', mimetype="image/png"))
       self._bad_field_tester(self.original_class, Invalid,
                              upload_case_names=self.mock_storage('test.png', 'seek', 'mimetype', 'save',
                                                                  'content_type', mimetype="image/png"))


class UploadTaskFileTestCase(FormTestCaseBase):
    original_class = UploadTaskFile

    def make_input(self, **overrides):
        self.mock = self.mock_storage('test.png', 'seek', 'content_type')
        d = {'file_title': "Foo",
             'comments': "Foo1",
             'file': self.mock}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['file_title'], 'Foo')
        self.assertEqual(result['comments'], 'Foo1')
        self.assertEqual(result['file'], self.mock)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, file_title=None)
        self._bad_field_tester(self.original_class, Invalid, comments=None)
        self._bad_field_tester(self.original_class, Invalid, file=None)


class AuthOptionsFormTestCase(FormTestCaseBase):
    original_class = AuthOptionsForm

    def make_input(self, **overrides):
        d = {'see_tasks': "yes",
             'see_evidence': "yes"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['see_tasks'], True)
        self.assertEqual(result['see_evidence'], True)

    def test_alternatives(self):
        input = self.make_input(see_evidence="no", see_tasks="no")
        result = self.original_class().to_python(input)
        self.assertEqual(result['see_tasks'], False)
        self.assertEqual(result['see_evidence'], False)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, see_tasks=None)
        self._bad_field_tester(self.original_class, Invalid, see_evidence=None)
        self._bad_field_tester(self.original_class, Invalid, see_tasks="foo")
        self._bad_field_tester(self.original_class, Invalid, see_evidence="foo")


class AddTeamFormTestCase(FormTestCaseBase):
    original_class = AddTeamForm

    def make_input(self, **overrides):
        d = {'t_department_name': "1",
             'new_team_name': "Foo"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['t_department_name'], self.getObjectMocks['GetDepartment'].return_value)
        self.assertEqual(result['new_team_name'], "Foo")

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, t_department_name="100")
        self._bad_field_tester(self.original_class, Invalid, t_department_name="-1")
        self._bad_field_tester(self.original_class, Invalid, t_department_name="foo")
        self._bad_field_tester(self.original_class, Invalid, t_department_name=None)


class RenameTeamFormTestCase(FormTestCaseBase):
    original_class = RenameTeamForm

    def make_input(self, **overrides):
        d = {'old_team_name': "1",
             'rename_team': "Foo"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['old_team_name'], self.getObjectMocks['GetTeam'].return_value)
        self.assertEqual(result['rename_team'], "Foo")

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, old_team_name="100")
        self._bad_field_tester(self.original_class, Invalid, old_team_name="-1")
        self._bad_field_tester(self.original_class, Invalid, old_team_name="foo")
        self._bad_field_tester(self.original_class, Invalid, old_team_name=None)


class RemoveTeamFormTestCase(FormTestCaseBase):
    original_class = RemoveTeamForm

    def make_input(self, **overrides):
        d = {'team_name': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['team_name'], self.getObjectMocks['GetTeam'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, team_name="100")
        self._bad_field_tester(self.original_class, Invalid, team_name="-1")
        self._bad_field_tester(self.original_class, Invalid, team_name="foo")
        self._bad_field_tester(self.original_class, Invalid, team_name=None)


class AddDepartmentFormTestCase(FormTestCaseBase):
    original_class = AddDepartmentForm

    def make_input(self, **overrides):
        d = {'department_name': "words"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['department_name'], "words")

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, department_name=None)


class RenameDepartmentFormTestCase(FormTestCaseBase):
    original_class = RenameDepartmentForm

    def make_input(self, **overrides):
        d = {'old_department_name': "1",
             'new_dep_name': "Foo"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['old_department_name'], self.getObjectMocks['GetDepartment'].return_value)
        self.assertEquals(result['new_dep_name'], "Foo")

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, old_department_name="100")
        self._bad_field_tester(self.original_class, Invalid, old_department_name="-1")
        self._bad_field_tester(self.original_class, Invalid, old_department_name=None)
        self._bad_field_tester(self.original_class, Invalid, new_dep_name=None)


class RemoveDepartmentFormTestCase(FormTestCaseBase):
    original_class = RemoveDepartmentForm

    def make_input(self, **overrides):
        d = {'remove_department_name': "1"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['remove_department_name'], self.getObjectMocks['GetDepartment'].return_value)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, remove_department_name="100")
        self._bad_field_tester(self.original_class, Invalid, remove_department_name="-1")
        self._bad_field_tester(self.original_class, Invalid, remove_department_name="foo")
        self._bad_field_tester(self.original_class, Invalid, remove_department_name=None)


class TimeSheetCellTestCase(FormTestCaseBase):
    original_class = TimeSheetCell

    def make_input(self, **overrides):
        d = {'value': "10",
             'datetime': "01012000"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['value'], 10)
        self.assertEqual(result['datetime'], datetime(2000, 1, 1).date())

    def _bad_field_tester(self, **bad_field):
        input = self.make_input(**bad_field)
        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(input)
        invalid = cm.exception
        self.assertIn(bad_field.keys()[0], invalid.error_dict)
        self.assertEqual(len(invalid.error_dict), 1)

    def test_bad_fields(self):
        self._bad_field_tester(value=25)
        self._bad_field_tester(value=-1)
        self._bad_field_tester(datetime="notadate")
        self._bad_field_tester(datetime="99131234")


class CaseHoursTestCase(FormTestCaseBase):
    original_class = CaseHours

    def make_input(self, **overrides):
        d = {'case': "1",
             'timesheet': [{'datetime': "15082016", 'value': "1"},
                           {'datetime': "16082016", 'value': "2"},
                           {'datetime': "17082016", 'value': "3"},
                           {'datetime': "18082016", 'value': "4"},
                           {'datetime': "19082016", 'value': "5"},
                           {'datetime': "20082016", 'value': "6"},
                           {'datetime': "21082016", 'value': "7"}]}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['case'], self.getObjectMocks['GetCase'].return_value)
        self.assertEqual(result['timesheet'][0]['datetime'], date(2016, 8, 15))
        self.assertEqual(result['timesheet'][0]['value'], 1)

    def test_bad_fields(self):
        d = {'case': None,
             'timesheet': [{'datetime': "15082016", 'value': "-1"},
                          {'datetime': "16082016", 'value': "25"},
                          {'datetime': "17082016", 'value': "foo"},
                          {'datetime': "foo", 'value': "4"},
                          {'datetime': "40082016", 'value': "5"},
                          {'datetime': "20082016", 'value': "6"},
                          {'datetime': "21082016", 'value': "7"}]}
        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(d)
        invalid = cm.exception
        self.assertEqual(len(invalid.error_dict), 2)
        self.assertIn('case', invalid.error_dict)
        self.assertIn('timesheet', invalid.error_dict)

class TaskHoursTestCase(FormTestCaseBase):
    original_class = TaskHours

    def make_input(self, **overrides):
        d = {'task': "1",
             'timesheet': [{'datetime': "15082016", 'value': "1"},
                           {'datetime': "16082016", 'value': "2"},
                           {'datetime': "17082016", 'value': "3"},
                           {'datetime': "18082016", 'value': "4"},
                           {'datetime': "19082016", 'value': "5"},
                           {'datetime': "20082016", 'value': "6"},
                           {'datetime': "21082016", 'value': "7"}]}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['task'], self.getObjectMocks['GetTask'].return_value)
        self.assertEqual(result['timesheet'][0]['datetime'], date(2016, 8, 15))
        self.assertEqual(result['timesheet'][0]['value'], 1)

    def test_bad_fields(self):
        d = {'task': "100",
             'timesheet': [{'datetime': "15082016", 'value': "-1"},
                          {'datetime': "16082016", 'value': "25"},
                          {'datetime': "17082016", 'value': "foo"},
                          {'datetime': "foo", 'value': "4"},
                          {'datetime': "40082016", 'value': "5"},
                          {'datetime': "20082016", 'value': "6"},
                          {'datetime': "21082016", 'value': "7"}]}
        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(d)
        invalid = cm.exception
        self.assertEqual(len(invalid.error_dict), 2)
        self.assertIn('task', invalid.error_dict)
        self.assertIn('timesheet', invalid.error_dict)


class CaseTimeSheetFormTestCase(FormTestCaseBase):
    original_class = CaseTimeSheetForm

    def make_input(self, **overrides):
        d = {'cases': [{'case': "1",
                        'timesheet': [{'datetime': "15082016", 'value': "1"},
                                      {'datetime': "16082016", 'value': "2"},
                                      {'datetime': "17082016", 'value': "3"},
                                      {'datetime': "18082016", 'value': "4"},
                                      {'datetime': "19082016", 'value': "5"},
                                      {'datetime': "20082016", 'value': "6"},
                                      {'datetime': "21082016", 'value': "7"}]}]}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['cases'][0]['case'], self.getObjectMocks['GetCase'].return_value)
        self.assertEqual(result['cases'][0]['timesheet'][0]['datetime'], date(2016, 8, 15))
        self.assertEqual(result['cases'][0]['timesheet'][0]['value'], 1)

    def test_bad_fields(self):
        d = {'cases': [{'case': "foo",
                        'timesheet': [{'datetime': "15082016", 'value': "-1"},
                                      {'datetime': "16082016", 'value': "25"},
                                      {'datetime': "17082016", 'value': "foo"},
                                      {'datetime': "foo", 'value': "4"},
                                      {'datetime': "40082016", 'value': "5"},
                                      {'datetime': "20082016", 'value': "6"},
                                      {'datetime': "21082016", 'value': "7"}]}]}
        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(d)
        invalid = cm.exception
        self.assertEqual(len(invalid.error_dict), 1)


class TaskTimeSheetFormTestCase(FormTestCaseBase):
    original_class = TaskTimeSheetForm

    def make_input(self, **overrides):
        d = {'tasks': [{'task': "1",
                        'timesheet': [ {'datetime': "15082016", 'value': "1"},
                                       {'datetime': "16082016", 'value': "2"},
                                       {'datetime': "17082016", 'value': "3"},
                                       {'datetime': "18082016", 'value': "4"},
                                       {'datetime': "19082016", 'value': "5"},
                                       {'datetime': "20082016", 'value': "6"},
                                       {'datetime': "21082016", 'value': "7"}]}]}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertIs(result['tasks'][0]['task'], self.getObjectMocks['GetTask'].return_value)
        self.assertEqual(result['tasks'][0]['timesheet'][0]['datetime'], date(2016, 8, 15))
        self.assertEqual(result['tasks'][0]['timesheet'][0]['value'], 1)

    def test_bad_fields(self):
        d = {'tasks': [{'task': "foo",
                        'timesheet': [{'datetime': "15082016", 'value': "-1"},
                                      {'datetime': "16082016", 'value': "25"},
                                      {'datetime': "17082016", 'value': "foo"},
                                      {'datetime': "foo", 'value': "4"},
                                      {'datetime': "40082016", 'value': "5"},
                                      {'datetime': "20082016", 'value': "6"},
                                      {'datetime': "21082016", 'value': "7"}]}]}
        with self.assertRaises(Invalid) as cm:
            result = self.original_class().to_python(d)
        invalid = cm.exception
        self.assertEqual(len(invalid.error_dict), 1)


class ManagersInheritFormTestCase(FormTestCaseBase):
    original_class = ManagersInheritForm

    def make_input(self, **overrides):
        d = {'manager_inherit': "true"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['manager_inherit'], True)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, manager_inherit=None)
        self._bad_field_tester(self.original_class, Invalid, manager_inherit="notboolean")


class CloseCaseFormTestCase(FormTestCaseBase):
    original_class = CloseCaseForm

    def make_input(self, **overrides):
        d = {'closure': "words"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['closure'], "words")

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, closure=None)


class ChangeCaseStatusFormTestCase(FormTestCaseBase):
    original_class = ChangeCaseStatusForm

    def make_input(self, **overrides):
        d = {'change': "words"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['change'], "words")

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, change=None)


class EvidenceRetentionFormTestCase(FormTestCaseBase):
    original_class = EvidenceRetentionForm

    def make_input(self, **overrides):
        d = {'evi_ret': "True",
             'evi_ret_months': "1",
             'remove_evi_ret': "0"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = self.original_class().to_python(input)
        self.assertEqual(result['evi_ret'], True)
        self.assertEqual(result['evi_ret_months'], 1)
        self.assertEqual(result['remove_evi_ret'], True)

    def test_bad_fields(self):
        self._bad_field_tester(self.original_class, Invalid, evi_ret="foo")
        self._bad_field_tester(self.original_class, Invalid, evi_ret=None)
        self._bad_field_tester(self.original_class, Invalid, evi_ret_months="foo")
        self._bad_field_tester(self.original_class, Invalid, evi_ret_months=None)
        self._bad_field_tester(self.original_class, Invalid, evi_ret_months="-1")
