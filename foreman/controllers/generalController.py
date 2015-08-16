from os import listdir
from os.path import isfile, join
from datetime import datetime
from monthdelta import MonthDelta

# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController, jsonify
from ..model.caseModel import Task, User, ForemanOptions, Case, Evidence, CaseStatus
from ..model.generalModel import TaskType, TaskCategory, EvidenceType, CaseClassification, CaseType, CasePriority
from ..model.userModel import UserRoles, Department, Team
from ..forms.forms import LoginForm, OptionsForm, AddEvidenceTypeForm, RegisterForm, AddClassificationForm
from ..forms.forms import AddCaseTypeForm, RemoveCaseTypeForm, RemoveClassificationForm, RemoveEvidenceTypeForm
from ..forms.forms import MoveTaskTypeForm, AddTaskTypeForm, RemoveTaskTypeForm, AddTaskCategoryForm, RemoveCategoryForm
from ..forms.forms import AddTeamForm, RenameTeamForm, RemoveTeamForm, AddDepartmentForm, RenameDepartmentForm
from ..forms.forms import RemoveDepartmentForm
from ..forms.forms import AddPriorityForm, RemovePriorityForm, AuthOptionsForm
from ..utils.utils import multidict_to_dict, session, ROOT_DIR, config
from ..utils.mail import email


class GeneralController(BaseController):
    def index(self, **vars):
        tasks = len(Task.get_active_tasks(user=self.current_user))
        qas = len(Task.get_active_QAs(user=self.current_user))
        opts = ForemanOptions.get_options()
        return self.return_response('pages', 'index.html', number_of_qas=qas, number_of_tasks=tasks,
                                    company=opts.company, department=opts.department)

    def login(self):

        opts = ForemanOptions.get_options()
        if self.validate_form(LoginForm()):
            user = User.get_user_with_username(self.form_result['username'].lower())
            if user is not None:
                if user.validated is False:
                    self.breadcrumbs.append({'title': 'Login', 'path': self.urls.build('general.login')})
                    return self.return_response('pages', 'login.html', validated=False, company=opts.company,
                                                department=opts.department)
                else:
                    # successful login
                    self.request.session['userid'] = self.request.session.get('userid', user.id)

                    if 'redirect' in self.request.args:
                        return redirect(self.request.args['redirect'])
                    else:
                        return self.index()
            else:
                # should not happen that you get a valid form but invalid user
                return self.return_500()
        else:
            self.breadcrumbs.append({'title': 'Login', 'path': self.urls.build('general.login')})
            return self.return_response('pages', 'login.html', errors=self.form_error, company=opts.company,
                                        department=opts.department)

    def logout(self):

        if 'userid' in self.request.session:
            del self.request.session['userid']

        opts = ForemanOptions.get_options()
        self.breadcrumbs.append({'title': 'Login', 'path': self.urls.build('general.login')})
        return self.return_response('pages', 'login.html', errors=self.form_error, company=opts.company,
                                    department=opts.department)

    def register(self):
        self.breadcrumbs.append({'title': 'Register for Foreman', 'path': self.urls.build('general.register')})
        success = False
        teams = sorted([(team.id, team.department.department + ": " + team.team) for team in Team.get_all()],
                           key=lambda t: t[1])
        opts = ForemanOptions.get_options()
        if self.validate_form(RegisterForm()):
            if self.form_result['middlename'] == "":
                self.form_result['middlename'] = None
            new_user = User(self.form_result['username'].lower(), self.form_result['password'],
                            self.form_result['forename'],
                            self.form_result['surname'], self.form_result['email'],
                            middle=self.form_result['middlename'])
            session.add(new_user)
            session.flush()
            new_user.team = self.form_result['team']

            success = True

            # start with no roles, admin must assign roles
            for role in UserRoles.roles:
                new_role = UserRoles(new_user, role, True)
                session.add(new_role)
                session.flush()
                new_role.add_change(new_user)

            email([new_user.email], "Thanks for registering with Foreman", """
Hello {},

Thanks for registering! The administrator will validate your account and you will get an email when this occurs.

Thanks,
Foreman
{}""".format(new_user.forename, config.get('admin', 'website_domain')), config.get('email', 'from_address'))

            admins = UserRoles.get_admins()
            for admin in admins:
                email([admin.email], "A new user has registered with Foreman", """
Hello {},

A new user has registered with the following details. Please log in and validate their account.

Username: {}
Name: {}
Email address: {}

Thanks,
Foreman
{}""".format(admin.forename, new_user.username, new_user.fullname, new_user.email,
             config.get('admin', 'website_domain')), config.get('email', 'from_address'))

        return self.return_response('pages', 'register.html', errors=self.form_error, success=success,
                                    company=opts.company, department=opts.department, teams=teams)

    def admin(self):
        self.check_permissions(self.current_user, "Case", 'admin')
        self.breadcrumbs.append({'title': 'Administration', 'path': self.urls.build('general.admin')})
        icon_path = join(ROOT_DIR, 'static', 'images', 'siteimages', 'evidence_icons_unique')
        over_load = ForemanOptions.run_out_of_names()
        form_type = multidict_to_dict(self.request.args)
        number_cases = number_tasks = validated = val_user = None

        if 'form' in form_type and form_type['form'] == "options" and self.validate_form(OptionsForm()):
            error_flag = False
            check_cases = check_tasks = False
            if self.form_result['case_names'] == "FromList":
                if self.form_result['upload_case_names'] is not None:
                    number_cases = ForemanOptions.import_names("case", join(ROOT_DIR, 'static', 'case_names',
                                                                            self.form_result['upload_case_names']))
                    if number_cases is None:
                        self.form_error['upload_case_names'] = "Error in uploading case names text file."
                        error_flag = True
                else:
                    check_cases = True

            if self.form_result['task_names'] == "FromList":
                if self.form_result['upload_task_names'] is not None:
                    number_tasks = ForemanOptions.import_names("task", join(ROOT_DIR, 'static', 'case_names',
                                                                            self.form_result['upload_task_names']))
                    if number_tasks is None:
                        self.form_error['upload_task_names'] = "Error in uploading task names text file."
                        error_flag = True
                else:
                    check_tasks = True

            if error_flag is not True:
                ForemanOptions.set_options(self.form_result['company'], self.form_result['department'],
                                           self.form_result['folder'], self.form_result['datedisplay'],
                                           self.form_result['case_names'], self.form_result['task_names'])
            if check_cases:
                ForemanOptions.get_next_case_name(test=True)
            if check_tasks:
                ForemanOptions.get_next_task_name(None, test=True)

        elif 'form' in form_type and form_type['form'] == "add_evidence_types" and self.validate_form(
                AddEvidenceTypeForm()):
            new_evidence_type = EvidenceType(self.form_result['evi_type'], self.form_result['icon_input'])
            session.add(new_evidence_type)
            session.flush()
        elif 'form' in form_type and form_type['form'] == "remove_evidence_types" and self.validate_form(
                RemoveEvidenceTypeForm()):
            evidence_type = EvidenceType.get_filter_by(evidence_type=self.form_result['evi_type']).first()
            if evidence_type:
                session.delete(evidence_type)
                session.commit()
                # find all evidence that have this type and assign it to 'Undefined'
                evidences = Evidence.get_filter_by(type=evidence_type.evidence_type).all()
                for evidence in evidences:
                    evidence.type = EvidenceType.undefined()
        elif 'form' in form_type and form_type['form'] == "remove_priority" and self.validate_form(RemovePriorityForm()):
            number_left = CasePriority.get_amount()
            if number_left > 1:
                priority = self.form_result['priority_remove']
                default = priority.default
                session.delete(priority)
                session.commit()
                if default:
                    new_default = CasePriority.get_all().first()
                    new_default.default = True
        elif 'form' in form_type and form_type['form'] == "add_priority" and self.validate_form(AddPriorityForm()):
            if self.form_result['default'] is True:
                for p in CasePriority.get_all():
                    p.default = False
            new_priority = CasePriority(self.form_result['priority'], self.form_result['colour'],
                                        self.form_result['default'])
            session.add(new_priority)
            session.commit()
        elif 'validate_user' in form_type:
            user = self._validate_user(form_type['validate_user'])
            if user:
                user.validated = True
                session.flush()
                user.add_change(self.current_user)
                validated = True
                val_user = user

                email([user.email], "Welcome to Foreman!", """
Hello {},

The administrator has now validated your account and you can now log into the system. Enjoy!

Thanks,
Foreman
{}""".format(user.forename, config.get('admin', 'website_domain')), config.get('email', 'from_address'))


        elif 'form' in form_type and form_type['form'] == 'remove_classification' and self.validate_form(
                RemoveClassificationForm):
            classification = CaseClassification.get_filter_by(classification=self.form_result['classification']).first()
            if classification:
                session.delete(classification)
                session.commit()
                # find all cases that have this classification and assign it to 'Undefined'
                cases = Case.get_filter_by(classification=classification.classification).all()
                for case in cases:
                    case.classification = CaseClassification.undefined()
        elif 'form' in form_type and form_type['form'] == 'add_classification' and self.validate_form(
                AddClassificationForm):
            new_cls = CaseClassification(self.form_result['classification'])
            session.add(new_cls)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'remove_case_type' and self.validate_form(RemoveCaseTypeForm):
            case_type = CaseType.get_filter_by(case_type=self.form_result['case_type']).first()
            if case_type:
                session.delete(case_type)
                session.commit()
                # find all cases that have this type and assign it to 'Undefined'
                cases = Case.get_filter_by(case_type=case_type.case_type).all()
                for case in cases:
                    case.case_type = CaseType.undefined()
        elif 'form' in form_type and form_type['form'] == 'add_case_type' and self.validate_form(AddCaseTypeForm):
            new_type = CaseType(self.form_result['case_type'])
            session.add(new_type)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'move_task_type' and self.validate_form(MoveTaskTypeForm):
            task_type = self.form_result['task_type']
            task_type.category = self.form_result['task_category']
            session.flush()
        elif 'form' in form_type and form_type['form'] == 'add_task_type' and self.validate_form(AddTaskTypeForm):
            new_tt = TaskType(self.form_result['new_task_type'], self.form_result['change_task_category'])
            session.add(new_tt)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'remove_task_type' and self.validate_form(RemoveTaskTypeForm):
            task_type = self.form_result['remove_task_type']
            # find all task that have this type and assign it to 'Undefined'
            tasks = Task.get_tasks_with_type(task_type)
            for task in tasks:
                task.task_type = TaskType.get_filter_by(task_type=TaskType.undefined()).first()
                session.flush()
                pass
            session.delete(task_type)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'add_task_category' and self.validate_form(
                AddTaskCategoryForm):
            new_tc = TaskCategory(self.form_result['add_task_category'])
            session.add(new_tc)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'remove_task_category' and self.validate_form(
                RemoveCategoryForm):
            category = self.form_result['remove_task_category']
            session.delete(category)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'authoriser_options' and self.validate_form(
                AuthOptionsForm):
            options = ForemanOptions.get_options()
            options.auth_view_tasks = self.form_result['see_tasks']
            options.auth_view_evidence = self.form_result['see_evidence']
        elif 'form' in form_type and form_type['form'] == 'remove_department' and self.validate_form(
                RemoveDepartmentForm):
            session.delete(self.form_result['remove_department_name'])
            session.flush()
        elif 'form' in form_type and form_type['form'] == 'add_department' and self.validate_form(
                AddDepartmentForm):
            dep = Department(self.form_result['department_name'])
            session.add(dep)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'rename_department' and self.validate_form(
                RenameDepartmentForm):
            dep = self.form_result['old_department_name']
            dep.department = self.form_result['new_dep_name']
        elif 'form' in form_type and form_type['form'] == 'add_team' and self.validate_form(
                AddTeamForm):
            new_team = Team(self.form_result['new_team_name'], self.form_result['t_department_name'])
            session.add(new_team)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'rename_team' and self.validate_form(
                RenameTeamForm):
            team = self.form_result['old_team_name']
            team.team = self.form_result['rename_team']
        elif 'form' in form_type and form_type['form'] == 'remove_team' and self.validate_form(
                RemoveTeamForm):
            session.delete(self.form_result['team_name'])
            session.flush()
        all_priorities = CasePriority.get_all()
        priorities = [(priority.case_priority, priority.case_priority) for priority in CasePriority.get_all()]
        users = User.get_filter_by(validated=False).all()
        options = ForemanOptions.get_options()

        if 'active_tab' in form_type:
            try:
                active_tab = int(form_type['active_tab'])
            except ValueError:
                active_tab = 0
        else:
            active_tab = 0
        task_types = [(tt.replace(" ", "").lower(), tt) for tt in TaskType.get_task_types()]
        task_categories = [(tc.replace(" ", "").lower(), tc) for tc in TaskCategory.get_categories()]
        evidence_types = EvidenceType.get_evidence_types()
        classifications = [(cl.replace(" ", "").lower(), cl) for cl in CaseClassification.get_classifications()]
        case_types = [(ct.replace(" ", "").lower(), ct) for ct in CaseType.get_case_types()]
        evi_types = [(et.replace(" ", "").lower(), et) for et in evidence_types]
        icons = [f for f in listdir(icon_path) if isfile(join(icon_path, f)) and f != "Thumbs.db"]
        empty_categories = [(ct.replace(" ", "").lower(), ct) for ct in TaskCategory.get_empty_categories()]
        case_name_options = [(cn, cn) for cn in ForemanOptions.CASE_NAME_OPTIONS]
        task_name_options = [(tn, tn) for tn in ForemanOptions.TASK_NAME_OPTIONS]
        authoriser_options = [("yes", "Yes"), ("no", "No")]
        department_options = [(dep.id, dep.department) for dep in Department.get_all()]
        del_department_options = [(dep.id, dep.department) for dep in Department.get_all() if len(dep.teams) == 0]
        team_options = [(t.id, t.team) for t in Team.get_all()]
        del_team_options = [(t.id, t.team) for t in Team.get_all() if len(t.team_members) == 0]
        return self.return_response('pages', 'admin.html', options=options, active_tab=active_tab, icons=icons,
                                    task_types=task_types, evidence_types=evidence_types, users=users,
                                    classifications=classifications, case_types=case_types, evi_types=evi_types,
                                    empty_categories=empty_categories, task_categories=task_categories,
                                    errors=self.form_error, over_load=over_load, case_name_options=case_name_options,
                                    task_name_options=task_name_options, number_cases=number_cases,
                                    number_tasks=number_tasks, validated=validated, val_user=val_user,
                                    all_priorities=all_priorities, priorities=priorities, team_options=team_options,
                                    authoriser_options=authoriser_options, department_options=department_options,
                                    del_department_options=del_department_options, del_team_options=del_team_options)

    def report(self):
        start_date = ForemanOptions.get_date_created()
        today_date = datetime.now()
        months = [start_date.strftime("%B %Y")]
        categories = CaseType.get_case_types()
        cases_opened = []
        cases_closed = []
        cases_archived = []
        total_cases = []
        cases_assigned_inv = []
        active_tab = 0
        for status in CaseStatus.all_statuses:
            total_cases.append([start_date.strftime("%B %Y"), status,
                                Case.get_num_cases_opened_on_date(start_date, status, case_type=None, by_month=True)])
        for category in categories:
            cases_opened.append([start_date.strftime("%B %Y"), category,
                                 Case.get_num_cases_opened_on_date(start_date, CaseStatus.OPEN, case_type=category,
                                                                   by_month=True)])
            cases_closed.append([start_date.strftime("%B %Y"), category,
                                 Case.get_num_cases_opened_on_date(start_date, CaseStatus.CLOSED, case_type=category,
                                                                   by_month=True)])
            cases_archived.append([start_date.strftime("%B %Y"), category,
                                   Case.get_num_cases_opened_on_date(start_date, CaseStatus.ARCHIVED,
                                                                     case_type=category,
                                                                     by_month=True)])
        for category in TaskCategory.get_categories():
            for investigator in UserRoles.get_investigators():
                cases_assigned_inv.append([investigator.fullname, category, Task.get_num_tasks_by_user(investigator,
                                                                                                       category,
                                                                                                       start_date)])

        max_months = 11
        while start_date.month != today_date.month and max_months != 0:
            start_date = start_date + MonthDelta(1)
            months.append(start_date.strftime("%B %Y"))
            for status in CaseStatus.all_statuses:
                total_cases.append([start_date.strftime("%B %Y"), status,
                                    Case.get_num_cases_opened_on_date(start_date, status, case_type=None,
                                                                      by_month=True)])
            for category in categories:
                cases_opened.append([start_date.strftime("%B %Y"), category,
                                     Case.get_num_cases_opened_on_date(start_date, CaseStatus.OPEN, case_type=category,
                                                                       by_month=True)])
                cases_closed.append([start_date.strftime("%B %Y"), category,
                                     Case.get_num_cases_opened_on_date(start_date, CaseStatus.CLOSED,
                                                                       case_type=category,
                                                                       by_month=True)])
                cases_archived.append([start_date.strftime("%B %Y"), category,
                                       Case.get_num_cases_opened_on_date(start_date, CaseStatus.ARCHIVED,
                                                                         case_type=category, by_month=True)])
            max_months -= 1

        return self.return_response('pages', 'report.html', cases_opened=cases_opened, cases_closed=cases_closed,
                                    months=months, cases_archived=cases_archived, total_cases=total_cases,
                                    active_tab=active_tab, cases_assigned_inv=cases_assigned_inv)

    @jsonify
    def jason_tasks_assigned_to_inv(self):
        start_date = self.request.args.get('start_date', datetime.now().strftime("%B %Y"))
        try:
            datetime.strptime(start_date, "%B %Y")
        except ValueError:
            start_date = datetime.now().strftime("%B %Y")
        tasks_assigned_inv = []
        for category in TaskCategory.get_categories():
            for investigator in UserRoles.get_investigators():
                tasks_assigned_inv.append([investigator.fullname, category, Task.get_num_tasks_by_user(investigator,
                                                                                                       category,
                                                                                                       start_date)])
        return tasks_assigned_inv
