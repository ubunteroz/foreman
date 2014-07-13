from os import listdir
from os.path import isfile, join
from datetime import datetime
from monthdelta import monthdelta

# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController, jsonify
from ..model.caseModel import Task, User, ForemanOptions, Case, Evidence, CaseStatus
from ..model.generalModel import TaskType, TaskCategory, EvidenceType, CaseClassification, CaseType
from ..model.userModel import UserRoles
from ..forms.forms import LoginForm, OptionsForm, AddEvidenceTypeForm, RegisterForm, AddClassificationForm
from ..forms.forms import AddCaseTypeForm, RemoveCaseTypeForm, RemoveClassificationForm, RemoveEvidenceTypeForm
from ..forms.forms import MoveTaskTypeForm, AddTaskTypeForm, RemoveTaskTypeForm, AddTaskCategoryForm, RemoveCategoryForm
from ..utils.utils import multidict_to_dict, session, ROOT_DIR


class GeneralController(BaseController):
    
    def index(self, **vars):
        tasks = len(Task.get_active_tasks(user=self.current_user))
        qas = len(Task.get_active_QAs(user=self.current_user))
        return self.return_response('pages', 'index.html', number_of_qas=qas, number_of_tasks=tasks)

    def login(self):
        if self.validate_form(LoginForm()):
            user = User.get_user_with_username(self.form_result['username'].lower())
            if user is not None:
                if user.validated is False:
                    return self.return_response('pages', 'login.html', validated=False)
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
            return self.return_response('pages', 'login.html', errors=self.form_error)

    def logout(self):
        if 'userid' in self.request.session:
            del self.request.session['userid']

        return self.return_response('pages', 'login.html', errors=self.form_error)

    def register(self):
        success = False
        if self.validate_form(RegisterForm()):
            if self.form_result['middlename'] == "":
                self.form_result['middlename'] = None
            new_user = User(self.form_result['username'].lower(), self.form_result['password'], self.form_result['forename'],
                            self.form_result['surname'], self.form_result['email'],
                            middle=self.form_result['middlename'])
            session.add(new_user)
            session.flush()
            success = True
        return self.return_response('pages', 'register.html', errors=self.form_error, success=success)

    def admin(self):
        self.check_permissions(self.current_user, "Case", 'admin')
        icon_path = join(ROOT_DIR, 'static', 'images', 'siteimages', 'evidence_icons_unique')

        form_type = multidict_to_dict(self.request.args)
        if 'form' in form_type and form_type['form'] == "options" and self.validate_form(OptionsForm()):
            ForemanOptions.set_options(self.form_result['company'], self.form_result['department'],
                                       self.form_result['folder'], self.form_result['datedisplay'])
        elif 'form' in form_type and form_type['form'] == "add_evidence_types" and self.validate_form(AddEvidenceTypeForm()):
            new_evidence_type = EvidenceType(self.form_result['evi_type'], self.form_result['icon_input'])
            session.add(new_evidence_type)
            session.flush()
        elif 'form' in form_type and form_type['form'] == "remove_evidence_types" and self.validate_form(RemoveEvidenceTypeForm()):
            evidence_type = EvidenceType.get_filter_by(evidence_type=self.form_result['evi_type']).first()
            if evidence_type:
                session.delete(evidence_type)
                session.commit()
                # find all evidence that have this type and assign it to 'Undefined'
                evidences = Evidence.get_filter_by(type=evidence_type.evidence_type).all()
                for evidence in evidences:
                    evidence.type = EvidenceType.undefined()
        elif 'validate_user' in form_type:
            user = self._validate_user(form_type['validate_user'])
            if user:
                user.validated = True
                session.flush()
                user.add_change(self.current_user)
        elif 'form' in form_type and form_type['form'] == 'remove_classification' and self.validate_form(RemoveClassificationForm):
            classification = CaseClassification.get_filter_by(classification=self.form_result['classification']).first()
            if classification:
                session.delete(classification)
                session.commit()
                # find all cases that have this classification and assign it to 'Undefined'
                cases = Case.get_filter_by(classification=classification.classification).all()
                for case in cases:
                    case.classification = CaseClassification.undefined()
        elif 'form' in form_type and form_type['form'] == 'add_classification' and self.validate_form(AddClassificationForm):
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
            new_tt = TaskType(self.form_result['task_type'], self.form_result['task_category'])
            session.add(new_tt)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'remove_task_type' and self.validate_form(RemoveTaskTypeForm):
            task_type = self.form_result['task_type']
            # find all task that have this type and assign it to 'Undefined'
            tasks = Task.get_tasks_with_type(task_type)
            for task in tasks:
                task.task_type = TaskType.get_filter_by(task_type=TaskType.undefined()).first()
                session.flush()
                pass
            session.delete(task_type)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'add_task_category' and self.validate_form(AddTaskCategoryForm):
            new_tc = TaskCategory(self.form_result['task_category'])
            session.add(new_tc)
            session.commit()
        elif 'form' in form_type and form_type['form'] == 'remove_task_category' and self.validate_form(RemoveCategoryForm):
            category = self.form_result['task_category']
            session.delete(category)
            session.commit()

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
        icons = [f for f in listdir(icon_path) if isfile(join(icon_path,f)) and f != "Thumbs.db"]
        empty_categories = [(ct.replace(" ", "").lower(), ct) for ct in TaskCategory.get_empty_categories()]
        return self.return_response('pages', 'admin.html', options=options, active_tab=active_tab, icons=icons,
                                    task_types=task_types, evidence_types=evidence_types, users=users,
                                    classifications=classifications, case_types=case_types, evi_types=evi_types,
                                    empty_categories=empty_categories, task_categories=task_categories,
                                    errors=self.form_error)

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
                                   Case.get_num_cases_opened_on_date(start_date, CaseStatus.ARCHIVED, case_type=category,
                                                                 by_month=True)])
        for category in TaskCategory.get_categories():
            for investigator in UserRoles.get_investigators():
                cases_assigned_inv.append([investigator.fullname, category, Task.get_num_tasks_by_user(investigator,
                                                                                                       category,
                                                                                                       start_date)])

        max_months = 11
        while start_date.month != today_date.month and max_months != 0:
            start_date = start_date + monthdelta(1)
            months.append(start_date.strftime("%B %Y"))
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

        return URL.getTop(num=amount, highlight_funcs=highlight_funcs, remove_funcs=remove_funcs)