
# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController
from ..model.caseModel import Task, User, ForemanOptions
from ..model.generalModel import TaskType, TaskCategory, EvidenceType
from ..forms.forms import LoginForm, OptionsForm, AddEvidenceTypeForm, RegisterForm
from ..utils.utils import multidict_to_dict, session


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

        form_type = multidict_to_dict(self.request.args)
        if 'form' in form_type and form_type['form'] == "options" and self.validate_form(OptionsForm()):
            ForemanOptions.set_options(self.form_result['company'], self.form_result['department'],
                                       self.form_result['folder'], self.form_result['datedisplay'])
        elif 'form' in form_type and form_type['form'] == "evidence_types" and self.validate_form(AddEvidenceTypeForm()):
            new_evidence_type = EvidenceType(self.form_result['evi_type'], None)
            session.add(new_evidence_type)
            session.flush()
        elif 'validate_user' in form_type:
            user = self._validate_user(form_type['validate_user'])
            if user:
                user.validated = True
                session.flush()
                user.add_change(self.current_user)

        users = User.get_filter_by(validated=False).all()
        options = ForemanOptions.get_options()

        if 'active_tab' in form_type:
            try:
                active_tab = int(form_type['active_tab'])
            except ValueError:
                active_tab = 0
        else:
            active_tab = 0
        task_types = {}
        task_categories = TaskCategory.get_all()
        evidence_types = EvidenceType.get_evidence_types()
        for cat in task_categories:
            task_types[cat.category] = [t.task_type for t in TaskType.get_filter_by(category_id=cat.id).all()]
        return self.return_response('pages', 'admin.html', options=options, active_tab=active_tab,
                                    task_types=task_types, evidence_types=evidence_types, users=users)