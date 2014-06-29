# library imports
from formencode import Schema, Invalid, validators as v
from formencode.foreach import ForEach
from formencode.compound import All
#local imports
from validators import *


class AddCaseForm(Schema):
    case_name = v.UnicodeString(not_empty=True)
    reference = v.UnicodeString()
    private = v.Bool()
    background = v.UnicodeString(not_empty=True)
    location = v.UnicodeString()
    primary_case_manager = GetCaseManager(not_empty=True)
    secondary_case_manager = GetCaseManager(not_empty=True)
    classification = GetCaseClassification(not_emtpy=True)
    case_type = GetCaseType(not_empty=True)
    justification = v.UnicodeString(not_empty=True)


class RemoveClassificationForm(Schema):
    classification = GetCaseClassification(not_emtpy=True)


class RemoveCaseTypeForm(Schema):
    case_type = GetCaseType(not_empty=True)


class AddClassificationForm(Schema):
    classification = v.UnicodeString(not_emtpy=True)


class AddCaseTypeForm(Schema):
    case_type = v.UnicodeString(not_empty=True)


class AddTaskForm(Schema):
    task_name = v.UnicodeString(not_empty=True)
    task_type = GetTaskTypes(not_empty=True)
    background = v.UnicodeString(not_empty=True)
    location = v.UnicodeString()
    primary_investigator = GetInvestigator()
    secondary_investigator = GetInvestigator()
    primary_qa = GetQA()
    secondary_qa = GetQA()


class LoginForm(Schema):
    username = v.UnicodeString(not_empty=True)
    password = v.UnicodeString(not_empty=True)

    chained_validators = [
        PasswordCheck('username', 'password')
    ]


class PasswordChangeForm(Schema):
    password = v.UnicodeString(not_empty=True)
    new_password = v.UnicodeString(not_empty=True)
    new_password_2 = v.UnicodeString(not_empty=True)

    chained_validators = [
        Match('new_password', 'new_password_2'),
    ]


class AdminPasswordChangeForm(Schema):
    new_password = v.UnicodeString(not_empty=True)
    new_password_2 = v.UnicodeString(not_empty=True)

    chained_validators = [
        Match('new_password', 'new_password_2'),
    ]

class RegisterForm(Schema):
    forename = v.UnicodeString(not_empty=True)
    surname = v.UnicodeString(not_empty=True)
    middlename = v.UnicodeString()
    username = v.UnicodeString(not_empty=True)
    username = v.UnicodeString(not_empty=True)
    password = v.UnicodeString(not_empty=True)
    password_2 = v.UnicodeString(not_empty=True)
    email = v.UnicodeString(not_empty=True)

    chained_validators = [
        Match('password', 'password_2'),
    ]

class QACheckerForm(Schema):
    notes = v.UnicodeString(not_empty=True)
    qa_decision = QADecision(not_empty=True)


class AddTaskNotesForm(Schema):
    notes = v.UnicodeString(not_empty=True)


class AssignInvestigatorForm(Schema):
    role = IsPrincipleInvestigator()
    investigator = GetUser()


class AssignQAForm(Schema):
    investigator = GetUser(allow_null=False)
    investigator2 = GetUser(allow_null=True)


class AssignQAFormSingle(Schema):
    investigator = GetUser(allow_null=False)


class AskForQAForm(Schema):
    qa_partners = GetUsers(allow_null=False)
    subject = v.UnicodeString(not_empty=True)
    body = v.UnicodeString(not_empty=True)


class ChainOfCustodyForm(Schema):
    date = ValidDate(not_empty=True)
    time = ValidTime(not_empty=True)
    user = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    #attach = UploadCustodyAttachment()
    label = v.UnicodeString()


class EditEvidenceForm(Schema):
    reference = v.UnicodeString(not_empty=True)
    bag_num = v.UnicodeString(not_empty=True)
    type = GetEvidenceType(not_empty=True)
    originator = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    location = v.UnicodeString(not_empty=True)


class EditEvidenceQRCodesForm(Schema):
    qr_code_text = v.UnicodeString(not_empty=True)
    qr_code = v.Bool()


class EditEvidencePhotosForm(Schema):
    photo_1 = UploadEvidencePhoto()
    photo_2 = UploadEvidencePhoto()
    photo_3 = UploadEvidencePhoto()


class AddEvidenceTypeForm(Schema):
    evi_type = v.UnicodeString(not_empty=True)


class RemoveEvidenceTypeForm(Schema):
    evi_type = GetEvidenceType(not_empty=True)


class MoveTaskTypeForm(Schema):
    task_type = GetTaskTypes(not_empty=True)
    task_category = GetTaskCategory(not_empty=True)


class AddTaskTypeForm(Schema):
    task_type = v.UnicodeString(not_empty=True)
    task_category = GetTaskCategory(not_empty=True)


class RemoveTaskTypeForm(Schema):
    task_type = GetTaskTypes(not_empty=True)


class AddTaskCategoryForm(Schema):
    task_category = v.UnicodeString(not_empty=True)


class RemoveCategoryForm(Schema):
    task_category = GetTaskCategory(not_empty=True)


class AddEvidenceForm(Schema):
    reference = v.UnicodeString(not_empty=True)
    bag_num = v.UnicodeString()
    type = GetEvidenceType(not_empty=True)
    originator = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    location = v.UnicodeString(not_empty=True)
    qr = v.Bool()
    photo = ForEach(UploadEvidencePhoto())


class EvidenceAssociateForm(Schema):
    case_reassign = GetCase(not_empty=True)


class EditTaskUsersForm(Schema):
    primary_investigator = GetInvestigator()
    secondary_investigator = GetInvestigator()
    primary_qa = GetQA()
    secondary_qa = GetQA()


class EditTaskForm(Schema):
    task_name = v.UnicodeString(not_empty=True)
    task_type = GetTaskTypes(not_empty=True)
    background = v.UnicodeString(not_empty=True)
    location = v.UnicodeString()


class EditCaseForm(Schema):
    case_name = v.UnicodeString(not_empty=True)
    reference = v.UnicodeString()
    private = v.Bool()
    background = v.UnicodeString(not_empty=True)
    location = v.UnicodeString()
    justification = v.UnicodeString(not_empty=True)
    classification = GetCaseClassification(not_emtpy=True)
    case_type = GetCaseType(not_empty=True)


class AddCaseLinkForm(Schema):
    case_links_add = GetCase(not_empty=True)
    reason_add = v.UnicodeString(not_empty=True)


class RemoveCaseLinkForm(Schema):
    case_links = GetCase(not_empty=True)
    reason = v.UnicodeString(not_empty=True)


class EditCaseManagersForm(Schema):
    primary_case_manager = GetCaseManager(not_empty=True)
    secondary_case_manager = GetCaseManager(not_empty=True)


class ReAssignTasksForm(Schema):
    task_reassign = GetTask(not_empty=True)
    case_reassign = GetCase(not_empty=True)


class EditUserForm(Schema):
    forename = v.UnicodeString(not_empty=True)
    surname = v.UnicodeString(not_empty=True)
    middlename = v.UnicodeString()
    username = v.UnicodeString(not_empty=True)
    email = v.UnicodeString(not_empty=True)


class AddUserForm(Schema):
    forename = v.UnicodeString(not_empty=True)
    surname = v.UnicodeString(not_empty=True)
    middlename = v.UnicodeString()
    username = v.UnicodeString(not_empty=True)
    email = v.UnicodeString(not_empty=True)
    administrator = GetBooleanYesNo(not_empty=True)
    casemanager = GetBooleanYesNo(not_empty=True)
    requester = GetBooleanYesNo(not_empty=True)
    authoriser = GetBooleanYesNo(not_empty=True)
    investigator = GetBooleanYesNo(not_empty=True)
    qa = GetBooleanYesNo(not_empty=True)


class EditRolesForm(Schema):
    administrator = GetBooleanYesNo(not_empty=True)
    casemanager = GetBooleanYesNo(not_empty=True)
    requester = GetBooleanYesNo(not_empty=True)
    authoriser = GetBooleanYesNo(not_empty=True)
    investigator = GetBooleanYesNo(not_empty=True)
    qa = GetBooleanYesNo(not_empty=True)


class OptionsForm(Schema):
    company = v.UnicodeString(not_empty=True)
    department = v.UnicodeString(not_empty=True)
    folder = v.UnicodeString(not_empty=True)
    datedisplay = v.UnicodeString(not_empty=True)