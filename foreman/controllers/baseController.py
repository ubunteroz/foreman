# python imports
from os import path
import simplejson as json
# library imports
from werkzeug import Response, redirect
from werkzeug.exceptions import Forbidden
from mako.lookup import TemplateLookup
from formencode import Invalid
from formencode.variabledecode import variable_decode
# local imports
from ..utils.utils import session, ROOT_DIR, multidict_to_dict
from ..model import User, CaseStatus, Case, Task, TaskStatus, Evidence, has_permissions

lookup = TemplateLookup(directories=[path.join(ROOT_DIR, 'templates')], output_encoding='utf-8')


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

    def return_404(self, **vars):
        vars.update(**self._get_base_variables())
        template = lookup.get_template(path.join('base', '404.html'))
        html = template.render(urls=self.urls, **vars)
        return Response(html, mimetype='text/html', status=404)

    def return_500(self):
        template = lookup.get_template(path.join('base', '500.html'))
        html = template.render(urls=self.urls, **self._get_base_variables())
        return Response(html, mimetype='text/html', status=500)

    def return_403(self):
        template = lookup.get_template(path.join('base', '403.html'))
        html = template.render(urls=self.urls, **self._get_base_variables())
        return Response(html, mimetype='text/html', status=403)

    def return_response(self, *location, **vars):
        """ Return the rendered template with variables """
        vars.update(**self._get_base_variables())
        template = lookup.get_template(path.join(*location))
        html = template.render(urls=self.urls, **vars)
        return Response(html, mimetype='text/html', status=vars.get('_status', 200))

    def validate_form(self, schema):
        """ Validates a form post against schema. If no form was posted, return False. 
        If form was posted and it is invalid, return False and set self.form_error.
        If form validated correctly, return True and set self.form_result """
        if self.request.method != 'POST':
            return False
        try:
            # Convert fields with more than one value into lists
            form_vars = multidict_to_dict(self.request.form)
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
        if self.current_user:
            base_vars['user_qa_cases'] = Case.get_cases(CaseStatus.OPEN, self.current_user, user=True, QA=True,
                                                        current_user_perms=self.check_view_permissions("Case", "admin"))
            base_vars['user_cases'] = Case.get_cases(CaseStatus.OPEN, self.current_user, user=True,
                                                     current_user_perms=self.check_view_permissions("Case", "admin"))
            base_vars['open_cases'] = len(Case.get_cases(CaseStatus.OPEN, self.current_user,
                                                         current_user_perms=self.check_view_permissions("Case",
                                                                                                        "admin"),
                                                         case_perm_checker=self.check_permissions))
            base_vars['created_cases'] = len(Case.get_cases(CaseStatus.CREATED, self.current_user,
                                                            current_user_perms=self.check_view_permissions("Case",
                                                                                                           "admin"),
                                                            case_perm_checker=self.check_permissions))
        base_vars['invRoles'] = TaskStatus.invRoles
        base_vars['qaRoles'] = TaskStatus.qaRoles
        base_vars['unassigned_tasks'] = len(Task.get_queued_tasks())
        base_vars['task_statuses'] = {'created': TaskStatus.CREATED, 'start': TaskStatus.ALLOCATED,
                                      'progress': TaskStatus.PROGRESS, 'deliver': TaskStatus.DELIVERY,
                                      'queued': TaskStatus.QUEUED, 'complete': TaskStatus.COMPLETE, 'qa': TaskStatus.QA,
                                      'closed': TaskStatus.CLOSED}
        base_vars['case_statuses'] = {'created': CaseStatus.CREATED, 'archived': CaseStatus.ARCHIVED,
                                      'closed': CaseStatus.CLOSED, 'open': CaseStatus.OPEN}
        if self.current_user.is_requester():
            base_vars['requester_created_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                            self.current_user, [CaseStatus.CREATED])
            base_vars['requester_opened_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                           self.current_user, [CaseStatus.OPEN])
            base_vars['requester_closed_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                           self.current_user, [CaseStatus.CLOSED])
            base_vars['requester_archived_cases'] = Case.get_cases_requested(self.current_user, self.check_permissions,
                                                                             self.current_user, [CaseStatus.ARCHIVED])
        return base_vars

    @staticmethod
    def _validate_task(case_id, task_id):
        case = Case.get_filter_by(case_name=case_id).first()
        if case is not None:
            task = Task.get_filter_by(task_name=task_id, case_id=case.id).first()
            return task
        else:
            return None

    @staticmethod
    def _validate_case(case_id):
        case = Case.get_filter_by(case_name=case_id).first()
        return case

    @staticmethod
    def _validate_user(user_id):
        user = User.get_filter_by(id=user_id).first()
        return user

    @staticmethod
    def _validate_evidence(evidence_id, case_id=None):
        if case_id:
            case = Case.get_filter_by(case_name=case_id).first()
            if case is not None:
                evidence = Evidence.get_filter_by(case_id=case.id, reference=evidence_id).first()
                return evidence
            else:
                return None
        else:
            evidence = Evidence.get_filter_by(reference=evidence_id).first()
            return evidence

    @staticmethod
    def check_permissions(user, obj, action):
        allowed = has_permissions(user, obj, action)
        if not allowed:
            raise Forbidden

    def check_view_permissions(self, obj, action):
        return has_permissions(self.current_user, obj, action)
