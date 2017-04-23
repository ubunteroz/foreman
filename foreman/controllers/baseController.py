# python imports
from os import path
import simplejson as json
# library imports
from werkzeug import Response
from werkzeug.exceptions import Forbidden
from mako.lookup import TemplateLookup
from formencode import Invalid
from formencode.variabledecode import variable_decode
# local imports
from ..utils.utils import session, ROOT_DIR, multidict_to_dict, config
from ..utils.mail import email
from ..model import User, CaseStatus, Case, Task, TaskStatus, Evidence, has_permissions, ForemanOptions, UserCaseRoles
from ..model import TaskUpload, EvidencePhotoUpload, Team, Department, CaseHistory, UserTaskRoles, TaskHistory
from ..model import EvidenceHistory, EvidenceStatus, SpecialText, CaseUpload, UserRoles

lookup = TemplateLookup(directories=[path.join(ROOT_DIR, 'templates')], output_encoding='utf-8', input_encoding='utf-8')


def jsonify(func):
    """ Wrap a function so as to jsonify the return value and wrap it in
    a Werkzeug response object. """

    def _wrapper(*args, **kwds):
        r = func(*args, **kwds)
        if isinstance(r, Response):
            return r
        else:
            return Response(json.dumps(r), mimetype='application/json')

    return _wrapper


class BaseController():
    def __init__(self, request, urls):
        self.request = request
        self.urls = urls
        self.form_error = {}
        self.form_result = {}
        self.user_posted = {}
        self._create_breadcrumbs()

    def _create_breadcrumbs(self):
        self.breadcrumbs = [{'title': 'Home', 'path': self.urls.build('general.index')}]

    def return_404(self, **variables):
        variables.update(**self._get_base_variables())
        template = lookup.get_template(path.join('base', '404.html'))
        html = template.render(urls=self.urls, **variables)
        return Response(html, mimetype='text/html', status=404)

    def return_500(self):
        template = lookup.get_template(path.join('base', '500.html'))
        html = template.render(urls=self.urls, **self._get_base_variables())
        return Response(html, mimetype='text/html', status=500)

    def return_403(self):
        template = lookup.get_template(path.join('base', '403.html'))
        html = template.render(urls=self.urls, **self._get_base_variables())
        return Response(html, mimetype='text/html', status=403)

    def return_response(self, *location, **variables):
        """ Return the rendered template with variables """
        variables.update(**self._get_base_variables())
        template = lookup.get_template(path.join(*location))
        html = template.render(urls=self.urls, breadcrumbs=self.breadcrumbs, **variables)
        return Response(html, mimetype='text/html', status=variables.get('_status', 200))

    def validate_form(self, schema):
        """ Validates a form post against schema. If no form was posted, return False.
        If form was posted and it is invalid, return False and set self.form_error.
        If form validated correctly, return True and set self.form_result """
        if self.request.method != 'POST':
            return False
        try:
            # Convert fields with more than one value into lists
            form_vars = multidict_to_dict(self.request.form)
            self.user_posted = form_vars
            form_vars.update(multidict_to_dict(self.request.files))
            self.form_result = schema.to_python(variable_decode(form_vars))
            return True
        except Invalid, e:
            self.form_error = e.unpack_errors(encode_variables=True)
            return False

    def _get_current_user(self):
        """ Load the current user from the database. If no user is logged in, return None."""
        if 'userid' in self.request.session:
            return User.get(self.request.session['userid'])
        else:
            return None

    current_user = property(_get_current_user)

    def _get_base_variables(self):
        """ Variables needed on every template page. Automatically added """
        base_vars = dict()
        base_vars['current_user'] = self.current_user
        base_vars['check_perms'] = self.check_view_permissions
        base_vars['check_perms_user'] = self.check_permissions
        base_vars['error_message_website_wide'] = []
        base_vars['help_message_website_wide'] = []
        base_vars['admin_help_message_website_wide'] = []
        base_vars['form_result'] = self.user_posted
        base_vars['case_special_text'] = SpecialText.get_text('case').text if SpecialText.get_text(
            'case') is not None else ""
        base_vars['task_special_text'] = SpecialText.get_text('task').text if SpecialText.get_text(
            'task') is not None else ""
        base_vars['evidence_special_text'] = SpecialText.get_text('evidence').text if SpecialText.get_text(
            'evidence') is not None else ""

        if self.current_user:
            base_vars['user_qa_cases'] = Case.get_cases(CaseStatus.OPEN, self.current_user, worker=True, QA=True)
            base_vars['user_cases'] = Case.get_cases(CaseStatus.OPEN, self.current_user, worker=True)
            base_vars['open_cases'] = len(
                Case.get_cases(CaseStatus.OPEN, self.current_user, case_perm_checker=self.check_permissions))
            base_vars['created_cases'] = len(
                Case.get_cases(CaseStatus.CREATED, self.current_user, case_perm_checker=self.check_permissions))
            base_vars['created_cases_no_manager'] = len(
                Case.get_cases(CaseStatus.CREATED, self.current_user, case_perm_checker=self.check_permissions,
                               case_man=True))
            if self.current_user.is_case_manager:
                base_vars['my_cases'] = len(Case.get_current_cases(self.current_user, self.check_permissions,
                                                                   self.current_user))
            else:
                base_vars['my_cases'] = 0


            if self.current_user.is_admin():
                overload = ForemanOptions.run_out_of_names()
                if overload[0]:
                    base_vars['error_message_website_wide'].append(
                        {'title': "Task name issue",
                         'text': """Foreman has run out of names from your uploaded task names list.
                         Please ask your administrator to add more.
                         More details can be found in the admin control panel."""
                         }
                    )
                if overload[1]:
                    base_vars['error_message_website_wide'].append(
                        {'title': "Case name issue",
                         'text': """Foreman has run out of names from your uploaded case names list.
                         Please ask your administrator to add more.
                         More details can be found in the admin control panel."""
                         }
                    )

                if User.get_amount() == 1:
                    base_vars['admin_help_message_website_wide'].append(
                        {'title': "Add more users",
                         'text': "You are currently the only user of Foreman.<a href='" +
                                 self.urls.build('user.add') + "'>Add more users here.</a>"
                         }
                    )

                if self.current_user.id == 1 and User.check_password(self.current_user.username, "changeme"):
                    base_vars['error_message_website_wide'].append(
                        {'title': "Change your default password",
                         'text': """You are currently using the default admin password which is published publicly.
                         You are advised to change this immediately. """
                         }
                    )

                num_invalid = User.get_number_unvalidated()
                if num_invalid >= 1:
                    plural = "s" if num_invalid > 1 else ""
                    base_vars['help_message_website_wide'].append(
                        {'title': "Validate Users",
                         'text': "You currently have {} user{} waiting to be validated. "
                                 "<a href='{}'>Validate them here</a>".format(num_invalid, plural,
                                                                              self.urls.build("general.admin",
                                                                                              dict(active_tab=5)))
                         }
                    )

        if self.current_user and self.current_user.is_requester():
            auths = len(UserRoles.get_authorisers(self.current_user.department))
            if auths == 0:
                base_vars['help_message_website_wide'].append(
                    {'title': "You have no authorisers",
                     'text': """You are currently a requester with no authorisers for your department.
                     You will not be able to add any new cases unless authorisers are added."""})

        base_vars['invRoles'] = TaskStatus.invRoles
        base_vars['qaRoles'] = TaskStatus.qaRoles

        base_vars['unassigned_tasks'] = len(Task.get_queued_tasks())
        base_vars['task_statuses'] = {'created': TaskStatus.CREATED, 'start': TaskStatus.ALLOCATED,
                                      'progress': TaskStatus.PROGRESS, 'deliver': TaskStatus.DELIVERY,
                                      'queued': TaskStatus.QUEUED, 'complete': TaskStatus.COMPLETE, 'qa': TaskStatus.QA,
                                      'closed': TaskStatus.CLOSED}
        base_vars['case_statuses'] = {'created': CaseStatus.CREATED, 'archived': CaseStatus.ARCHIVED,
                                      'closed': CaseStatus.CLOSED, 'open': CaseStatus.OPEN,
                                      'rejected': CaseStatus.REJECTED, 'pending': CaseStatus.PENDING}
        if self.current_user and self.current_user.is_requester():
            base_vars['requester_created_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                            self.current_user, [CaseStatus.CREATED])
            base_vars['requester_opened_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                           self.current_user, [CaseStatus.OPEN])
            base_vars['requester_closed_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                           self.current_user, [CaseStatus.CLOSED])
            base_vars['requester_archived_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                             self.current_user, [CaseStatus.ARCHIVED])
            base_vars['requester_rejected_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                             self.current_user, [CaseStatus.REJECTED])
            base_vars['requester_pending_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                            self.current_user, [CaseStatus.PENDING])
        if self.current_user and self.current_user.is_case_manager():
            base_vars['caseman_rejected_cases'] = Case.get_cases_requested_case_manager(self.current_user,
                                                                                        self.check_permissions,
                                                                                        self.current_user,
                                                                                        [CaseStatus.REJECTED])
            base_vars['caseman_pending_cases'] = Case.get_cases_requested_case_manager(self.current_user,
                                                                                       self.check_permissions,
                                                                                       self.current_user,
                                                                                       [CaseStatus.PENDING])
        if self.current_user and self.current_user.is_authoriser():
            base_vars['authoriser_to_authorise'] = Case.get_cases_authorised(self.current_user, self.check_permissions,
                                                                             self.current_user, [CaseStatus.PENDING])
            base_vars['authoriser_rejected'] = Case.get_cases_authorised(self.current_user, self.check_permissions,
                                                                         self.current_user, [CaseStatus.REJECTED])
            base_vars['authoriser_authorised'] = Case.get_cases_authorised(self.current_user, self.check_permissions,
                                                                           self.current_user,
                                                                           CaseStatus.approved_statuses)

        return base_vars

    @staticmethod
    def send_email_alert(to_users, title, message):
        email_addr = [user.email for user in to_users if user is not None]
        subject = "auto notification: {}".format(title)
        email(email_addr, subject, """
Hello,

{}

Thanks,
Foreman
{}""".format(message, config.get('admin', 'website_domain')), config.get('email', 'from_address'))

    @staticmethod
    def _validate_task(case_id, task_id):
        try:
            int(case_id)
        except ValueError:
            return None
        case = Case.get(case_id)
        if case is not None:
            try:
                int(task_id)
            except ValueError:
                return None
            task = Task.get(task_id)
            if task.case.id == case.id:
                return task
            else:
                return None
        else:
            return None

    @staticmethod
    def _validate_task_upload(case_id, task_id, upload_id):
        task = BaseController._validate_task(case_id, task_id)
        if task is not None:
            try:
                int(upload_id)
            except ValueError:
                return None
            upload = TaskUpload.get_filter_by(task_id=task.id, id=upload_id).first()
            if upload is not None and upload.deleted is False:
                return upload
            else:
                return None
        else:
            return None

    @staticmethod
    def _validate_case_upload(case_id, upload_id):
        case = BaseController._validate_case(case_id)
        if case is not None:
            try:
                int(upload_id)
            except ValueError:
                return None
            upload = CaseUpload.get_filter_by(case_id=case.id, id=upload_id).first()
            if upload is not None and upload.deleted is False:
                return upload
            else:
                return None
        else:
            return None

    @staticmethod
    def _validate_evidence_photo(evidence_id, upload_id):
        evidence = BaseController._validate_evidence(evidence_id)
        if evidence is not None:
            try:
                int(upload_id)
            except ValueError:
                return None
            upload = EvidencePhotoUpload.get_filter_by(evidence_id=evidence.id, id=upload_id).first()
            if upload is not None and upload.deleted is False:
                return upload
            else:
                return None
        else:
            return None

    @staticmethod
    def _validate_case(case_id):
        try:
            int(case_id)
        except ValueError:
            return None
        case = Case.get(case_id)
        return case

    @staticmethod
    def _validate_user(user_id):
        try:
            int(user_id)
        except ValueError:
            return None
        user = User.get_filter_by(id=user_id).first()
        return user

    @staticmethod
    def _validate_evidence(evidence_id, case_id=None):
        try:
            int(evidence_id)
        except ValueError:
            return None

        if case_id:
            case = Case.get(case_id)
            if case is not None:
                evidence = Evidence.get_filter_by(case_id=case.id, id=evidence_id).first()
                return evidence
            else:
                return None
        else:
            evidence = Evidence.get_filter_by(id=evidence_id).first()
            return evidence

    @staticmethod
    def _validate_team(team_id):
        try:
            int(team_id)
        except ValueError:
            return None
        team = Team.get_filter_by(id=team_id).first()
        return team

    @staticmethod
    def _validate_department(dep_id):
        try:
            int(dep_id)
        except ValueError:
            return None
        team = Department.get_filter_by(id=dep_id).first()
        return team

    @staticmethod
    def check_permissions(user, obj, action):
        allowed = has_permissions(user, obj, action)
        if not allowed:
            raise Forbidden

    def check_view_permissions(self, obj, action):
        return has_permissions(self.current_user, obj, action)

    @staticmethod
    def _get_case_history_changes(case):
        history = CaseHistory.get_changes(case)
        statuses = CaseStatus.get_changes(case)
        uploads = CaseUpload.get_changes(case)
        results = history + statuses + uploads
        results.sort(key=lambda d: d['date_time'])
        return results

    @staticmethod
    def _get_case_manager_history_changes(case):
        primary = UserCaseRoles.get_history(case, UserCaseRoles.PRINCIPLE_CASE_MANAGER)
        secondary = UserCaseRoles.get_history(case, UserCaseRoles.SECONDARY_CASE_MANAGER)
        results = primary + secondary
        results.sort(key=lambda d: d['date_time'])
        return results

    @staticmethod
    def _get_all_user_history_changes(case):
        case_managers = BaseController._get_case_manager_history_changes(case)
        requester = UserCaseRoles.get_history(case, UserCaseRoles.REQUESTER)
        authoriser = UserCaseRoles.get_history(case, UserCaseRoles.AUTHORISER)
        requester = [] if requester is None else requester
        authoriser = [] if authoriser is None else authoriser
        results = case_managers + requester + authoriser
        results.sort(key=lambda d: d['date_time'])
        return results

    @staticmethod
    def _get_all_task_user_history_changes(task):
        primary = UserTaskRoles.get_history(task, UserTaskRoles.PRINCIPLE_INVESTIGATOR)
        secondary = UserTaskRoles.get_history(task, UserTaskRoles.SECONDARY_INVESTIGATOR)
        primary_qa = UserTaskRoles.get_history(task, UserTaskRoles.PRINCIPLE_QA)
        secondary_qa = UserTaskRoles.get_history(task, UserTaskRoles.SECONDARY_QA)
        results = primary + secondary + primary_qa + secondary_qa
        results.sort(key=lambda d: d['date_time'])
        return results

    @staticmethod
    def _get_tasks_history_changes(case):
        history = []
        for task in case.tasks:
            history += BaseController._get_task_history_changes(task)
        history.sort(key=lambda d: d['date_time'])
        return history

    @staticmethod
    def _get_task_history_changes(task):
        history = []
        history += TaskHistory.get_changes(task)
        history += TaskStatus.get_changes(task)
        history.sort(key=lambda d: d['date_time'])
        return history

    @staticmethod
    def _get_evidence_history_changes(evidence):
        history = []
        history += EvidenceHistory.get_changes(evidence)
        history += EvidenceStatus.get_changes(evidence)
        history.sort(key=lambda d: d['date_time'])
        return history

    def _create_new_user_role(self, role, obj, form_result, role_obj="case"):
        if role_obj == "case":
            role_class = UserCaseRoles
            user_role = role_class.get_filter_by(role=role, case=obj).first()
        else:
            role_class = UserTaskRoles
            user_role = role_class.get_filter_by(role=role, task=obj).first()

        if form_result is None:
            if user_role is None:
                # no change, empty role stays empty
                pass
            else:
                # person being removed
                user_role.add_change(self.current_user, True)
                session.flush()
        else:
            if user_role is None:
                # empty role getting a person added
                new_role = role_class(form_result, obj, role)
                session.add(new_role)
                session.flush()
                new_role.add_change(self.current_user)
            else:
                # person being replaced
                user_role.add_change(self.current_user, form_result)
                session.flush()
