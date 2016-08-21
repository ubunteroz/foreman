# library imports
from formencode import Schema, Invalid, validators as v
from formencode.foreach import ForEach
from formencode.compound import All, Pipe
from formencode.variabledecode import NestedVariables
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
    classification = GetCaseClassification(not_empty=True)
    case_type = GetCaseType(not_empty=True)
    justification = v.UnicodeString(not_empty=True)
    priority = GetPriority(not_empty=True)
    authoriser = GetAuthoriser(not_empty=True)
    deadline = Pipe(v.DateConverter(month_style='dd/mm/yyyy'), v.DateValidator(today_or_after=True))


class RequesterAddCaseForm(Schema):
    reference = v.UnicodeString()
    private = v.Bool()
    background = v.UnicodeString(not_empty=True)
    classification = GetCaseClassification(not_empty=True)
    case_type = GetCaseType(not_empty=True)
    justification = v.UnicodeString(not_empty=True)
    priority = GetPriority(not_empty=True)
    authoriser = GetAuthoriser(not_empty=True)
    deadline = Pipe(v.DateConverter(month_style='dd/mm/yyyy'), v.DateValidator(today_or_after=True))


class AuthoriseCaseForm(Schema):
    reason = v.UnicodeString(not_empty=True)
    auth = GetBooleanAuthReject(not_empty=True)


class AddPriorityForm(Schema):
    priority = v.UnicodeString(not_empty=True)
    default = GetBooleanYesNo(not_empty=True)
    colour = CheckHex(not_empty=True)


class RemovePriorityForm(Schema):
    priority_remove = GetPriority(not_empty=True)


class RemoveClassificationForm(Schema):
    classification = GetCaseClassification(not_empty=True)


class RemoveCaseTypeForm(Schema):
    case_type = GetCaseType(not_empty=True)


class AddClassificationForm(Schema):
    new_classification = v.UnicodeString(not_empty=True)


class AddCaseTypeForm(Schema):
    new_case_type = v.UnicodeString(not_empty=True)


class AddTaskForm(Schema):
    task_name = v.UnicodeString(not_empty=True)
    task_type = GetTaskTypes(not_empty=True)
    background = v.UnicodeString(not_empty=True)
    location = v.UnicodeString()
    primary_investigator = GetInvestigator()
    secondary_investigator = GetInvestigator()
    primary_qa = GetQA()
    secondary_qa = GetQA()
    deadline = Pipe(v.DateConverter(month_style='dd/mm/yyyy'), v.DateValidator(today_or_after=True))


class RequesterAddTaskForm(Schema):
    task_type = GetTaskTypes(not_empty=True)
    background = v.UnicodeString(not_empty=True)


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
    password = v.UnicodeString(not_empty=True)
    password_2 = v.UnicodeString(not_empty=True)
    email = v.UnicodeString(not_empty=True)
    team = GetTeam(not_empty=True)

    chained_validators = [
        Match('password', 'password_2'),
    ]


class QACheckerForm(Schema):
    notes = v.UnicodeString(not_empty=True)
    qa_decision = QADecision(not_empty=True)


class AddTaskNotesForm(Schema):
    notes = v.UnicodeString(not_empty=True)


class DeactivateUser(Schema):
    deactivate_user = GetUser(not_empty=True)


class ReactivateUser(Schema):
    reactivate_user = GetUser(not_empty=True)


class AssignInvestigatorForm(Schema):
    role = IsPrincipleInvestigator()
    investigator = GetInvestigator()


class AssignQAForm(Schema):
    investigator = GetQA(allow_null=False, not_empty=True)
    investigator2 = GetQA(allow_null=True)


class AssignQAFormSingle(Schema):
    investigator = GetQA(allow_null=False, not_empty=True)


class AskForQAForm(Schema):
    qa_partners = GetUsers(allow_null=False)
    subject = v.UnicodeString(not_empty=True)
    body = v.UnicodeString(not_empty=True)


class ChainOfCustodyForm(Schema):
    date = ValidDate(not_empty=True)
    time = ValidTime(not_empty=True)
    user = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    attach = UploadCustodyAttachment()
    label = v.UnicodeString(if_missing=None)

    chained_validators = [v.RequireIfMissing('label', present='attach')]


class EditEvidenceForm(Schema):
    reference = v.UnicodeString(not_empty=True)
    status = GetEvidenceStatus(not_empty=True)
    bag_num = v.UnicodeString()
    type = GetEvidenceType(not_empty=True)
    originator = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    location = v.UnicodeString(not_empty=True)


class EditEvidenceQRCodesForm(Schema):
    qr_code_text = v.UnicodeString(not_empty=True)
    qr_code = v.Bool()


class AddEvidenceTypeForm(Schema):
    evi_type_new = v.UnicodeString(not_empty=True)
    icon_input = AddIcon(not_empty=True)


class RemoveEvidenceTypeForm(Schema):
    evi_type = GetEvidenceType(not_empty=True)


class MoveTaskTypeForm(Schema):
    task_type = GetTaskTypes(not_empty=True)
    task_category = GetTaskCategory(not_empty=True)


class AddTaskTypeForm(Schema):
    new_task_type = v.UnicodeString(not_empty=True)
    change_task_category = GetTaskCategory(not_empty=True)


class RemoveTaskTypeForm(Schema):
    remove_task_type = GetTaskTypes(not_empty=True)


class AddTaskCategoryForm(Schema):
    new_task_category = v.UnicodeString(not_empty=True)


class RemoveCategoryForm(Schema):
    remove_task_category = GetTaskCategory(not_empty=True)


class AddEvidenceForm(Schema):
    reference = v.UnicodeString(not_empty=True)
    status = GetEvidenceStatus(not_empty=True)
    bag_num = v.UnicodeString()
    type = GetEvidenceType(not_empty=True)
    originator = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    location = v.UnicodeString(not_empty=True)
    qr = v.Bool()


class AddEvidencePhotoForm(Schema):
    file_title = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    file = UploadEvidencePhoto(not_empty=True)


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
    deadline = Pipe(v.DateConverter(month_style='dd/mm/yyyy'), v.DateValidator(today_or_after=True))


class EditCaseForm(Schema):
    case_name = v.UnicodeString(not_empty=True)
    reference = v.UnicodeString()
    private = v.Bool()
    background = v.UnicodeString(not_empty=True)
    location = v.UnicodeString()
    justification = v.UnicodeString(not_empty=True)
    classification = GetCaseClassification(not_empty=True)
    case_type = GetCaseType(not_empty=True)
    priority = GetPriority(not_empty=True)
    authoriser = GetAuthoriser(not_empty=True)
    deadline = Pipe(v.DateConverter(month_style='dd/mm/yyyy'), v.DateValidator(today_or_after=True))


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
    telephone = v.UnicodeString()
    alt_telephone = v.UnicodeString()
    fax = v.UnicodeString()
    job_title = v.UnicodeString(not_empty=True)
    team = GetTeam(not_empty=True)
    photo = UploadProfilePhoto()
    manager = GetUser()
    user = GetUser(not_empty=True)

    chained_validators = [
        ManagerCheck('user', 'manager')
    ]


class AddUserForm(Schema):
    forename = v.UnicodeString(not_empty=True)
    surname = v.UnicodeString(not_empty=True)
    middlename = v.UnicodeString()
    username = v.UnicodeString(not_empty=True)
    email = v.UnicodeString(not_empty=True)
    telephone = v.UnicodeString()
    alt_telephone = v.UnicodeString()
    fax = v.UnicodeString()
    job_title = v.UnicodeString(not_empty=True)
    team = GetTeam(not_empty=True)
    administrator = GetBooleanYesNo(not_empty=True)
    casemanager = GetBooleanYesNo(not_empty=True)
    requester = GetBooleanYesNo(not_empty=True)
    authoriser = GetBooleanYesNo(not_empty=True)
    investigator = GetBooleanYesNo(not_empty=True)
    qa = GetBooleanYesNo(not_empty=True)
    manager = GetUser()


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
    datedisplay = TestDateFormat(not_empty=True)
    case_names = GetForemanCaseNameOptions(not_empty=True)
    task_names = GetForemanTaskNameOptions(not_empty=True)
    upload_case_names = UploadNames()
    upload_task_names = UploadNames()


class UploadTaskFile(Schema):
    file_title = v.UnicodeString(not_empty=True)
    comments = v.UnicodeString(not_empty=True)
    file = UploadTaskFiles(not_empty=True)


class AuthOptionsForm(Schema):
    see_tasks = GetBooleanYesNo(not_empty=True)
    see_evidence = GetBooleanYesNo(not_empty=True)


class AddTeamForm(Schema):
    t_department_name = GetDepartment(not_empty=True)
    new_team_name = v.UnicodeString(not_empty=True)


class RenameTeamForm(Schema):
    old_team_name = GetTeam(not_empty=True)
    rename_team = v.UnicodeString(not_empty=True)


class RemoveTeamForm(Schema):
    team_name = GetTeam(not_empty=True)


class AddDepartmentForm(Schema):
    department_name = v.UnicodeString(not_empty=True)


class RenameDepartmentForm(Schema):
    old_department_name = GetDepartment(not_empty=True)
    new_dep_name = v.UnicodeString(not_empty=True)


class RemoveDepartmentForm(Schema):
    remove_department_name = GetDepartment(not_empty=True)


class TimeSheetCell(Schema):
    value = v.Number(max=24, min=0)
    datetime = TimeSheetDateTime()


class CaseHours(Schema):
    case = GetCase(not_empty=True)
    timesheet = ForEach(TimeSheetCell())


class TaskHours(Schema):
    task = GetTask(not_empty=True)
    timesheet = ForEach(TimeSheetCell())


class CaseTimeSheetForm(Schema):
    cases = ForEach(CaseHours())


class TaskTimeSheetForm(Schema):
    tasks = ForEach(TaskHours())


class ManagersInheritForm(Schema):
    manager_inherit = v.StringBool(not_empty=True)


class CloseCaseForm(Schema):
    closure = v.UnicodeString(not_empty=True)


class ChangeCaseStatusForm(Schema):
    change = v.UnicodeString(not_empty=True)


class EvidenceRetentionForm(Schema):
    evi_ret = v.StringBool(not_empty=True)
    evi_ret_months = PositiveNumberAboveZero(not_empty=True)
    remove_evi_ret = v.Bool()