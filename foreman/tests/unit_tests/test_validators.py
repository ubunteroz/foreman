# python imports
from os import path
import datetime
from formencode import Invalid
from mock import patch, Mock

# local imports
import base_tester
from foreman.forms.validators import Match, GetInvestigator, GetQA, GetCaseManager, GetAuthoriser, GetUser, GetUsers, \
    NotEmptyUpload, PositiveNumberAboveZero, TimeSheetDateTime, ValidDate, TestDateFormat, ValidTime, QADecision, \
    IsPrincipleInvestigator, AddIcon, GetForemanCaseNameOptions, GetForemanTaskNameOptions, GetCaseClassification, \
    GetPriority, GetCaseType, GetTeam, GetDepartment, GetCase, GetTask, GetTaskTypes, GetTaskCategory, GetEvidenceType,\
    GetEvidenceStatus, GetBooleanYesNo, GetBooleanAuthReject, CheckHex, Upload, UploadCustodyAttachment, \
    UploadTaskFiles, UploadEvidencePhoto, UploadNames, UploadProfilePhoto, PasswordCheck, ManagerCheck, \
    RequiredFieldEvidence, IsPrincipleQA, CheckUniqueUsername, CheckUniqueEmail, CheckUniqueDepartment, CheckUniqueTeam, \
    CheckUniqueTask, CheckUniqueCase, CheckUniqueReference, CheckUniqueCaseEdit, CheckUniqueReferenceEdit, \
    CheckUniqueEmailEdit, CheckUniqueUsernameEdit, CheckUniqueDepartmentEdit, CheckUniqueTeamEdit, CheckUniqueTaskEdit, \
    UploadCaseFiles
from foreman.model import UserRoles
from foreman.utils.utils import ROOT_DIR


class ValidatorTestCaseBase(base_tester.UnitTestCase):

    def mock_user(self, role_names=None):
        if role_names is not None:
            roles = [Mock(role=name) for name in role_names]
        else:
            roles = None

        mock_user = Mock(roles=roles)
        return mock_user

    def user_roles_tester(self, validator, role_names):
        with patch('foreman.forms.validators.User') as mockUser:
            mockUser.get.return_value = self.mock_user(role_names=role_names)
            with self.assertRaises(Invalid):
                validator.to_python('100')

    def nulls_news_testers(self, validator, new=False, null=True, return_null=None):
        if null is True:
            self.assertEqual(validator().to_python('null'), return_null)
            with self.assertRaises(Invalid):
                validator(allow_null=False).to_python('null')
        else:
            with self.assertRaises(Invalid):
                validator().to_python('null')
            self.assertEqual(validator(allow_null=True).to_python('null'), return_null)

        if new is True:
            self.assertEqual(validator().to_python('new'), "new")
            with self.assertRaises(Invalid):
                validator(allow_new=False).to_python('new')
        else:
            with self.assertRaises(Invalid):
                validator().to_python('new')
            self.assertEqual(validator(allow_new=True).to_python('new'), "new")


class CheckUniqueBase(ValidatorTestCaseBase):
    def success_tester(self, validator):
        with patch.object(validator, 'object_class') as mockObj:
            mockObj.get_filter_by.return_value.first.return_value = None
            result = validator().to_python('uniquevalue')
            self.assertIs(result, "uniquevalue")

            called_with = {validator.attribute_to_compare: "uniquevalue"}
            mockObj.get_filter_by.assert_called_once_with(**called_with)

    def failure_tester(self, validator):
        with patch.object(validator, 'object_class') as mockObj:
            mockObj.get_filter_by.return_value.first.return_value = Mock()
            with self.assertRaises(Invalid):
                validator().to_python('duplicatevalue')
            called_with = {validator.attribute_to_compare: "duplicatevalue"}
            mockObj.get_filter_by.assert_called_once_with(**called_with)


class CheckUniqueCaseTestCase(CheckUniqueBase):
    def test_success(self):
        self.success_tester(CheckUniqueCase)

    def test_failure(self):
        self.failure_tester(CheckUniqueCase)


class CheckUniqueTaskTestCase(CheckUniqueBase):
    def test_success(self):
        self.success_tester(CheckUniqueTask)

    def test_failure(self):
        self.failure_tester(CheckUniqueTask)


class CheckUniqueTeamTestCase(CheckUniqueBase):
    def test_success(self):
        self.success_tester(CheckUniqueTeam)

    def test_failure(self):
        self.failure_tester(CheckUniqueTeam)


class CheckUniqueDepartmentTestCase(CheckUniqueBase):
    def test_success(self):
        self.success_tester(CheckUniqueDepartment)

    def test_failure(self):
        self.failure_tester(CheckUniqueDepartment)


class CheckUniqueUsernameTestCase(CheckUniqueBase):
    def test_success(self):
        self.success_tester(CheckUniqueUsername)

    def test_failure(self):
        self.failure_tester(CheckUniqueUsername)


class CheckUniqueEmailTestCase(CheckUniqueBase):
    def test_success(self):
        self.success_tester(CheckUniqueEmail)

    def test_failure(self):
        self.failure_tester(CheckUniqueEmail)


class CheckUniqueReferenceTestCase(CheckUniqueBase):
    def test_success(self):
        self.success_tester(CheckUniqueReference)

    def test_failure(self):
        self.failure_tester(CheckUniqueReference)


class CheckUniqueBaseEdit(ValidatorTestCaseBase):
    state = None

    def success_tester(self, validator, input):
        with patch.object(validator, 'object_class') as mockObj:
            mockObj.get_filter_by.return_value.first.return_value = None
            result = validator.to_python(input, self.state)
            self.assertEqual(result, input)

        # ok if the returned value is the object we are editing
        with patch.object(validator, 'object_class') as mockObj:
            result_mock = Mock()
            result_mock.id = 1
            mockObj.get_filter_by.return_value.first.return_value = result_mock
            result = validator.to_python(input, self.state)

            self.assertEqual(result, input)
            called_with = {validator.attribute_to_compare: "foo"}
            mockObj.get_filter_by.assert_called_once_with(**called_with)

    def failure_tester(self, validator, input):
        with patch.object(validator, 'object_class') as mockObj:
            result_mock = Mock()
            result_mock.id = 2
            mockObj.get_filter_by.return_value.first.return_value = result_mock
            with self.assertRaises(Invalid):
                result = validator.to_python(input, self.state)
            called_with = {validator.attribute_to_compare: "foo"}
            mockObj.get_filter_by.assert_called_once_with(**called_with)


class CheckUniqueCaseTestCaseEdit(CheckUniqueBaseEdit):
    input = {
        'case_name': "foo",
        'edit_obj': "1"
    }

    def test_success(self):
        self.success_tester(CheckUniqueCaseEdit('case_name', 'edit_obj'), self.input)

    def test_failure(self):
        self.failure_tester(CheckUniqueCaseEdit('case_name', 'edit_obj'), self.input)


class CheckUniqueTaskTestCaseEdit(CheckUniqueBaseEdit):
    input = {
        'task_name': "foo",
        'edit_obj': "1"
    }

    def test_success(self):
        self.success_tester(CheckUniqueTaskEdit('task_name', 'edit_obj'), self.input)

    def test_failure(self):
        self.failure_tester(CheckUniqueTaskEdit('task_name', 'edit_obj'), self.input)


class CheckUniqueTeamTestCaseEdit(CheckUniqueBaseEdit):
    input = {
        'team': "foo",
        'edit_obj': "1"
    }

    def test_success(self):
        self.success_tester(CheckUniqueTeamEdit('team', 'edit_obj'), self.input)

    def test_failure(self):
        self.failure_tester(CheckUniqueTeamEdit('team', 'edit_obj'), self.input)


class CheckUniqueDepartmentTestCaseEdit(CheckUniqueBaseEdit):
    input = {
        'department': "foo",
        'edit_obj': "1"
    }

    def test_success(self):
        self.success_tester(CheckUniqueDepartmentEdit('department', 'edit_obj'), self.input)

    def test_failure(self):
        self.failure_tester(CheckUniqueDepartmentEdit('department', 'edit_obj'), self.input)


class CheckUniqueUsernameTestCaseEdit(CheckUniqueBaseEdit):
    input = {
        'username': "foo",
        'edit_obj': "1"
    }

    def test_success(self):
        self.success_tester(CheckUniqueUsernameEdit('username', 'edit_obj'), self.input)

    def test_failure(self):
        self.failure_tester(CheckUniqueUsernameEdit('username', 'edit_obj'), self.input)


class CheckUniqueEmailTestCaseEdit(CheckUniqueBaseEdit):
    input = {
        'email': "foo",
        'edit_obj': "1"
    }

    def test_success(self):
        self.success_tester(CheckUniqueEmailEdit('email', 'edit_obj'), self.input)

    def test_failure(self):
        self.failure_tester(CheckUniqueEmailEdit('email', 'edit_obj'), self.input)


class CheckUniqueReferenceTestCasEdit(CheckUniqueBaseEdit):
    input = {
        'reference': "foo",
        'edit_obj': "1"
    }

    def test_success(self):
        self.success_tester(CheckUniqueReferenceEdit('reference', 'edit_obj'), self.input)

    def test_failure(self):
        self.failure_tester(CheckUniqueReferenceEdit('reference', 'edit_obj'), self.input)


class RequiredFieldEvidenceTestCase(ValidatorTestCaseBase):
    state = None

    def make_input(self, **overrides):
        d = {'evi_ret': "True",
             'evi_ret_months': "2"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = RequiredFieldEvidence('evi_ret','evi_ret_months').to_python(input, self.state)
        self.assertEqual(result, input)

    def test_alternatives(self):
        input = self.make_input(evi_ret="False", evi_ret_months="")
        result = RequiredFieldEvidence('evi_ret','evi_ret_months').to_python(input, self.state)
        self.assertEqual(result, input)

    def test_failure(self):
        input = self.make_input(evi_ret_months="")
        with self.assertRaises(Invalid) as cm:
            result = RequiredFieldEvidence('evi_ret','evi_ret_months').to_python(input, self.state)
        invalid = cm.exception
        self.assertIn('evi_ret_months', invalid.error_dict)


class MatchTestCase(ValidatorTestCaseBase):
    state = None

    def make_input(self, **overrides):
        d = {'password': "pass",
             'password2': "pass"}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = Match('password','password2').to_python(input, self.state)
        self.assertEqual(result, input)

        input = self.make_input(extra="foo")
        result = Match('password', 'password2').to_python(input, self.state)
        self.assertEqual(result, input)

    def test_failure(self):
        input = self.make_input(password2="foo")
        with self.assertRaises(Invalid) as cm:
            result = Match('password','password2').to_python(input, self.state)
        invalid = cm.exception
        self.assertIn('password', invalid.error_dict)
        self.assertIn('password2', invalid.error_dict)


class NotEmptyUploadTestCase(ValidatorTestCaseBase):
    state = None

    def make_input(self, **overrides):
        mock = self.mock_storage('test.png', 'seek', 'mimetype', 'content_type', mimetype="image/text")
        d = {'case_names': "FromList",
             'case_upload': mock}
        d.update(overrides)
        return d

    def test_success(self):
        input = self.make_input()
        result = NotEmptyUpload('case_names','case_upload').to_python(input, self.state)
        self.assertEqual(result, input)

    def test_alternatives(self):
        input = self.make_input(case_names="NumericIncrement", case_upload=None)
        result = NotEmptyUpload('case_names','case_upload').to_python(input, self.state)
        self.assertEqual(result, input)

    def test_failure(self):
        input = self.make_input(case_upload="")
        with self.assertRaises(Invalid) as cm:
            result = NotEmptyUpload('case_names','case_upload').to_python(input, self.state)
        invalid = cm.exception
        self.assertIn('case_names', invalid.error_dict)
        self.assertIn('case_upload', invalid.error_dict)


class PositiveNumberAboveZeroTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = PositiveNumberAboveZero.to_python('1')
        self.assertIs(result, 1)

    def test_failure(self):
        with self.assertRaises(Invalid):
            PositiveNumberAboveZero.to_python('-1')
        with self.assertRaises(Invalid):
            PositiveNumberAboveZero.to_python('0')
        with self.assertRaises(Invalid):
            PositiveNumberAboveZero.to_python('foo')


class TimeSheetDateTimeTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = TimeSheetDateTime.to_python('01012001')
        self.assertEqual(result, datetime.date(2001, 1, 1))

    def test_failure(self):
        with self.assertRaises(Invalid):
            TimeSheetDateTime.to_python('foo')
        with self.assertRaises(Invalid):
            TimeSheetDateTime.to_python('40012001')
        with self.assertRaises(Invalid):
            TimeSheetDateTime.to_python('010101')


class ValidDateTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = ValidDate.to_python('01/01/2001')
        self.assertEqual(result, datetime.date(2001, 1, 1))

    def test_failure(self):
        with self.assertRaises(Invalid):
            ValidDate.to_python('foo')
        with self.assertRaises(Invalid):
            ValidDate.to_python('40/01/2001')
        with self.assertRaises(Invalid):
            ValidDate.to_python('01012001')


class ValidTimeTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = ValidTime.to_python('12:00')
        self.assertEqual(result, datetime.time(12, 00))

    def test_failure(self):
        with self.assertRaises(Invalid):
            ValidTime.to_python('25:00')
        with self.assertRaises(Invalid):
            ValidTime.to_python('foo')


class TestDateFormatTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = TestDateFormat.to_python('%d%m%Y %H:%M')
        self.assertEqual(result, '%d%m%Y %H:%M')

    def test_failure(self):
        with self.assertRaises(Invalid):
            TestDateFormat.to_python('test')


class QADecisionTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = QADecision.to_python('qa_pass')
        self.assertEqual(result, True)

        result = QADecision.to_python('qa_fail')
        self.assertEqual(result, False)

    def test_failure(self):
        with self.assertRaises(Invalid):
            QADecision.to_python('foo')


class IsPrincipleInvestigatorTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = IsPrincipleInvestigator.to_python('Principle Investigator')
        self.assertEqual(result, True)

        result = IsPrincipleInvestigator.to_python('Secondary Investigator')
        self.assertEqual(result, False)

    def test_failure(self):
        with self.assertRaises(Invalid):
            IsPrincipleInvestigator.to_python('foo')


class IsPrincipleQATestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = IsPrincipleQA.to_python('Principle QA')
        self.assertEqual(result, True)

        result = IsPrincipleQA.to_python('Secondary QA')
        self.assertEqual(result, False)

    def test_failure(self):
        with self.assertRaises(Invalid):
            IsPrincipleQA.to_python('foo')


class AddIconTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = AddIcon.to_python('Tag.png')
        self.assertEqual(result, path.join(ROOT_DIR, 'static', 'images', 'siteimages', 'evidence_icons_unique',
                                           "Tag.png"))

    def test_failure(self):
        with self.assertRaises(Invalid):
            AddIcon.to_python('foo')


class GetForemanCaseNameOptionsTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = GetForemanCaseNameOptions.to_python('DateNumericIncrement')
        self.assertEqual(result, 'DateNumericIncrement')

    def test_failure(self):
        with self.assertRaises(Invalid):
            GetForemanCaseNameOptions.to_python('foo')

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetUsers, new=False, null=False, return_null=None)


class GetForemanTaskNameOptionsTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = GetForemanTaskNameOptions.to_python('FromList')
        self.assertEqual(result, 'FromList')

    def test_failure(self):
        with self.assertRaises(Invalid):
            GetForemanTaskNameOptions.to_python('foo')

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetUsers, new=False, null=False, return_null=None)


class GetUsersTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetUsers()
            mockUser.get.return_value = self.mock_user()
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)
            mockUser.get.assert_called_once_with(100)

        validator = GetUsers()
        mockUser.get.return_value = "both"
        result = validator.to_python('both')
        self.assertIs(result, mockUser.get.return_value)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetUsers, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetUsers()
            mockUser.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetUserTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetUser()
            mockUser.get.return_value = self.mock_user()
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)
            mockUser.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetUser, new=False, null=True, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetUser()
            mockUser.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetInvestigatorTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetInvestigator()
            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.INV])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)
            mockUser.get.assert_called_once_with(100)

            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.QA, UserRoles.INV, UserRoles.CASE_MAN])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)

    def test_failure_wrong_roles(self):
        validator = GetInvestigator()
        self.user_roles_tester(validator, [UserRoles.QA])
        self.user_roles_tester(validator, [UserRoles.QA, UserRoles.ADMIN])
        self.user_roles_tester(validator, None)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetInvestigator, new=False, null=True, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetInvestigator()
            mockUser.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetQATestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetQA()
            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.QA])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)
            mockUser.get.assert_called_once_with(100)

            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.QA, UserRoles.INV, UserRoles.CASE_MAN])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)

    def test_failure_wrong_roles(self):
        validator = GetQA()
        self.user_roles_tester(validator, [UserRoles.INV])
        self.user_roles_tester(validator, [UserRoles.CASE_MAN, UserRoles.ADMIN])
        self.user_roles_tester(validator, None)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetQA, new=False, null=True, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetQA()
            mockUser.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetCaseManagerTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetCaseManager()
            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.CASE_MAN])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)
            mockUser.get.assert_called_once_with(100)

            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.QA, UserRoles.INV, UserRoles.CASE_MAN])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)

    def test_failure_wrong_roles(self):
        validator = GetCaseManager()
        self.user_roles_tester(validator, [UserRoles.INV])
        self.user_roles_tester(validator, [UserRoles.QA, UserRoles.ADMIN])
        self.user_roles_tester(validator, None)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetCaseManager, new=False, null=True, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetCaseManager()
            mockUser.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetAuthoriserTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetAuthoriser()
            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.AUTH])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)
            mockUser.get.assert_called_once_with(100)

            mockUser.get.return_value = self.mock_user(role_names=[UserRoles.QA, UserRoles.AUTH, UserRoles.CASE_MAN])
            result = validator.to_python('100')
            self.assertIs(result, mockUser.get.return_value)

    def test_failure_wrong_roles(self):
        validator = GetAuthoriser()
        self.user_roles_tester(validator, [UserRoles.INV])
        self.user_roles_tester(validator, [UserRoles.QA, UserRoles.ADMIN])
        self.user_roles_tester(validator, None)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetAuthoriser, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockUser:
            validator = GetAuthoriser()
            mockUser.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetCaseClassificationTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.CaseClassification') as mockCaseClassification:
            validator = GetCaseClassification()
            mockCaseClassification.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockCaseClassification.get.return_value)
            mockCaseClassification.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetCaseClassification, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockCaseClassification:
            validator = GetCaseClassification()
            mockCaseClassification.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetPriorityTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.CasePriority') as mockCasePriority:
            validator = GetPriority()
            mockCasePriority.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockCasePriority.get.return_value)
            mockCasePriority.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetPriority, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.User') as mockCasePriority:
            validator = GetPriority()
            mockCasePriority.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetCaseTypeTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.CaseType') as mockGetCaseType:
            validator = GetCaseType()
            mockGetCaseType.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockGetCaseType.get.return_value)
            mockGetCaseType.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetCaseType, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.CaseType') as mockGetCaseType:
            validator = GetCaseType()
            mockGetCaseType.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetTaskTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.Task') as mockTask:
            validator = GetTask()
            mockTask.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockTask.get.return_value)
            mockTask.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetTask, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.Task') as mockTask:
            validator = GetTask()
            mockTask.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetCaseTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.Case') as mockCase:
            validator = GetCase()
            mockCase.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockCase.get.return_value)
            mockCase.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetCase, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.Case') as mockCase:
            validator = GetCase()
            mockCase.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetDepartmentTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.Department') as mockDepartment:
            validator = GetDepartment()
            mockDepartment.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockDepartment.get.return_value)
            mockDepartment.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetDepartment, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.Department') as mockDepartment:
            validator = GetDepartment()
            mockDepartment.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetTeamTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.Team') as mockTeam:
            validator = GetTeam()
            mockTeam.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockTeam.get.return_value)
            mockTeam.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetTeam, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.Team') as mockTeam:
            validator = GetTeam()
            mockTeam.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetTaskTypesTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.TaskType') as mockTaskType:
            validator = GetTaskTypes()
            mockTaskType.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockTaskType.get.return_value)
            mockTaskType.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetTaskTypes, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.TaskType') as mockTaskType:
            validator = GetTaskTypes()
            mockTaskType.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetTaskCategoryTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.TaskCategory') as mockTaskCategory:
            validator = GetTaskCategory()
            mockTaskCategory.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockTaskCategory.get.return_value)
            mockTaskCategory.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetTaskCategory, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.TaskCategory') as mockTaskCategory:
            validator = GetTaskCategory()
            mockTaskCategory.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetEvidenceTypeTestCase(ValidatorTestCaseBase):
    def test_success(self):
        with patch('foreman.forms.validators.EvidenceType') as mockEvidenceType:
            validator = GetEvidenceType()
            mockEvidenceType.get.return_value = Mock()
            result = validator.to_python('100')
            self.assertIs(result, mockEvidenceType.get.return_value)
            mockEvidenceType.get.assert_called_once_with(100)

    def test_nulls_and_news(self):
        self.nulls_news_testers(GetEvidenceType, new=False, null=False, return_null=None)

    def test_failure_user_does_not_exist(self):
        with patch('foreman.forms.validators.EvidenceType') as mockEvidenceType:
            validator = GetEvidenceType()
            mockEvidenceType.get.return_value = None
            with self.assertRaises(Invalid):
                validator.to_python('100')


class GetEvidenceStatusTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = GetEvidenceStatus.to_python('Destroyed')
        self.assertEqual(result, 'Destroyed')

    def test_failure(self):
        with self.assertRaises(Invalid):
            GetEvidenceStatus.to_python('foo')


class GetBooleanYesNoTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = GetBooleanYesNo.to_python('yes')
        self.assertEqual(result, True)

        result = GetBooleanYesNo.to_python('no')
        self.assertEqual(result, False)

    def test_failure(self):
        with self.assertRaises(Invalid):
            GetBooleanYesNo.to_python('foo')


class GetBooleanAuthRejectTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = GetBooleanAuthReject.to_python('Authorised')
        self.assertEqual(result, True)

        result = GetBooleanAuthReject.to_python('Rejected')
        self.assertEqual(result, False)

    def test_failure(self):
        with self.assertRaises(Invalid):
            GetBooleanAuthReject.to_python('foo')


class CheckHexTestCase(ValidatorTestCaseBase):
    def test_success(self):
        result = CheckHex.to_python('#F0F0F0')
        self.assertEqual(result, "#F0F0F0")

    def test_failure(self):
        with self.assertRaises(Invalid):
            CheckHex.to_python('FFFFFF')
        with self.assertRaises(Invalid):
            CheckHex.to_python('#not')


class PasswordCheckTestCase(ValidatorTestCaseBase):
    state = None
    user = None

    def make_input(self, **overrides):
        d = {'username': "user",
             'password': "pass"}
        d.update(overrides)
        return d

    def mock_user(self, username):
        if username is not None:
            self.user = Mock()
            return self.user
        else:
            return None

    def mock_password_check(self, username, password):
        return username == "user" and password == "pass"

    def test_success(self):
        input = self.make_input()
        with patch('foreman.forms.validators.User') as mockUser:
            mockUser.get_filter_by.first.return_value = self.mock_user("user")
            mockUser.check_password.return_value = self.mock_password_check(**input)
            result = PasswordCheck('username','password').to_python(input, self.state)
            self.assertEqual(result, input)
            mockUser.get_filter_by.assert_called_once_with(username="user")
            mockUser.check_password.assert_called_once_with("user", "pass")

            input = self.make_input(extra="foo")
            result = PasswordCheck('username', 'password').to_python(input, self.state)
            self.assertEqual(result, input)

    def failure_tester(self, **input_changes):
        input = self.make_input(**input_changes)
        with patch('foreman.forms.validators.User') as mockUser:
            mockUser.get_filter_by.first.return_value = self.mock_user("user")
            mockUser.check_password.return_value = self.mock_password_check(**input)

            with self.assertRaises(Invalid) as cm:
                result = PasswordCheck('username', 'password').to_python(input, self.state)
            invalid = cm.exception
            self.assertIn('username', invalid.error_dict)
            self.assertIn('password', invalid.error_dict)

    def test_failure(self):
        self.failure_tester(password="wrong")
        self.failure_tester(password="")
        self.failure_tester(username="")
        self.failure_tester(username="nonexistant")


class ManagerCheckTestCase(ValidatorTestCaseBase):
    state = None

    def setUp(self):
        self.mock_report = Mock(id=42)

    def mock_user(self, id, report_chain=None):
        if report_chain is None:
            report_chain = []

        mock = Mock(id=id)
        mock._manager_loop_checker.return_value = report_chain
        return mock

    def make_input(self, user, manager=None, **others):
        d = {'user': user,
             'manager': manager}
        d.update(others)
        return d

    def test_success(self):
        user = self.mock_user(1)
        input = self.make_input(user)
        result = ManagerCheck('user','manager').to_python(input, self.state)
        self.assertEqual(result, input)

        user = self.mock_user(1)
        input = self.make_input(user, manager=self.mock_user(2))
        result = ManagerCheck('user','manager').to_python(input, self.state)
        self.assertEqual(result, input)

        user = self.mock_user(1, report_chain=[self.mock_report])
        input = self.make_input(user, manager=self.mock_user(2))
        result = ManagerCheck('user','manager').to_python(input, self.state)
        self.assertEqual(result, input)

    def test_failure(self):
        user = self.mock_user(42, report_chain=[self.mock_report])
        input = self.make_input(user, manager=self.mock_user(42))
        with self.assertRaises(Invalid) as cm:
            result = ManagerCheck('user', 'manager').to_python(input, self.state)
        invalid = cm.exception
        self.assertIn('manager', invalid.error_dict)


class UploadTestCase(ValidatorTestCaseBase):
    def test_success(self):
        mockFile = self.mock_storage('test.png', 'seek', 'save', 'mimetype', 'content_type', mimetype="image/text")
        result = Upload.to_python(mockFile)
        self.assertEqual(result, 'test.png')

    def test_failure(self):
        with self.assertRaises(Invalid):
            Upload.to_python('foo')


class UploadCustodyAttachmentTestCase(ValidatorTestCaseBase):
    def test_success(self):
        mockFile = self.mock_storage('test.png', 'seek', 'type', 'mimetype', 'content_type', mimetype="image/png")
        result = UploadCustodyAttachment.to_python(mockFile)
        self.assertEqual(result, mockFile)

    def test_failure(self):
        with self.assertRaises(Invalid):
            UploadCustodyAttachment.to_python('foo')


class UploadTaskFilesTestCase(ValidatorTestCaseBase):
    def test_success(self):
        mockFile = self.mock_storage('test.png', 'seek', 'type', 'mimetype', 'content_type', mimetype="image/png")
        result = UploadTaskFiles.to_python(mockFile)
        self.assertEqual(result, mockFile)

    def test_failure(self):
        with self.assertRaises(Invalid):
            UploadTaskFiles.to_python('foo')


class UploadCaseFilesTestCase(ValidatorTestCaseBase):
    def test_success(self):
        mockFile = self.mock_storage('test.png', 'seek', 'type', 'mimetype', 'content_type', mimetype="image/png")
        result = UploadCaseFiles.to_python(mockFile)
        self.assertEqual(result, mockFile)

    def test_failure(self):
        with self.assertRaises(Invalid):
            UploadCaseFiles.to_python('foo')


class UploadEvidencePhotoTestCase(ValidatorTestCaseBase):
    def test_success(self):
        mockFile = self.mock_storage('test.jpg', 'seek', 'type', 'mimetype', 'content_type', mimetype="image/jpg")
        result = UploadEvidencePhoto.to_python(mockFile)
        self.assertEqual(result, mockFile)

    def test_failure(self):
        with self.assertRaises(Invalid):
            UploadEvidencePhoto.to_python('foo')
        with self.assertRaises(Invalid):
            mockFile = self.mock_storage('test.txt', 'seek', 'type', 'mimetype', 'content_type', mimetype="text/plain")
            UploadEvidencePhoto.to_python(mockFile)


class UploadNamesTestCase(ValidatorTestCaseBase):
    def test_success(self):
        mockFile = self.mock_storage('test.txt', 'seek', 'save', 'mimetype', 'content_type', mimetype="text/plain")
        result = UploadNames.to_python(mockFile)
        self.assertEqual(result, 'test.txt')

    def test_failure(self):
        with self.assertRaises(Invalid):
            UploadNames.to_python('foo')
        with self.assertRaises(Invalid):
            mockFile = self.mock_storage('test.png', 'seek', 'save', 'mimetype', 'content_type', mimetype="image/png")
            UploadNames.to_python(mockFile)


class UploadProfilePhotoTestCase(ValidatorTestCaseBase):
    def test_success(self):
        mockFile = self.mock_storage('test.jpg', 'seek', 'type', 'mimetype', 'content_type', mimetype="image/jpg")
        result = UploadProfilePhoto.to_python(mockFile)
        self.assertEqual(result, mockFile)

    def test_failure(self):
        with self.assertRaises(Invalid):
            UploadProfilePhoto.to_python('foo')
        with self.assertRaises(Invalid):
            mockFile = self.mock_storage('test.txt', 'seek', 'type', 'mimetype', 'content_type', mimetype="text/plain")
            UploadProfilePhoto.to_python(mockFile)
