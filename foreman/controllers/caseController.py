# library imports
from werkzeug import Response, redirect
# local imports
from baseController import BaseController
from taskController import TaskController
from ..model import Case, User, CaseStatus, UserCaseRoles, Task, UserTaskRoles, LinkedCase, UserRoles, \
    CaseHistory, TaskHistory, TaskStatus, ForemanOptions, CaseClassification, CaseType
from ..utils.utils import multidict_to_dict, session
from ..forms.forms import AddCaseForm, AddTaskForm, EditCaseForm, AddCaseLinkForm, RemoveCaseLinkForm, EditCaseManagersForm, \
    ReAssignTasksForm


class CaseController(BaseController):
    def view_all(self):
        view = multidict_to_dict(self.request.args)
        allowed = CaseStatus.all_statuses
        allowed.append("All")
        allowed.append("Queued")
        if 'view' in view:
            if self.request.args['view'] in CaseStatus.all_statuses:
                all_cases = Case.get_cases(view['view'].title(), self.current_user,
                                           current_user_perms=self.check_view_permissions("Case", "admin"),
                                           case_perm_checker=self.check_permissions)
            elif self.request.args['view'] == "All":
                all_cases = Case.get_cases("All",  self.current_user,
                                           current_user_perms=self.check_view_permissions("Case", "admin"),
                                           case_perm_checker=self.check_permissions)
            else:
                all_cases = Case.get_cases('Open',  self.current_user,
                                           current_user_perms=self.check_view_permissions("Case", "admin"),
                                           case_perm_checker=self.check_permissions)
        else:
            all_cases = Case.get_cases('Open',  self.current_user,
                                       current_user_perms=self.check_view_permissions("Case", "admin"),
                                       case_perm_checker=self.check_permissions)
            view['view'] = "Open"
        return self.return_response('pages', 'view_cases.html', cases=all_cases, case_status=view['view'].title(),
                                    current_user=TaskController.current_user)

    def view(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'view')
            if case.tasks:
                # if all the tasks are in created status, then this adds link to set all the tasks to allocated /
                # queued in one go
                all_tasks_created = len(set([task.status for task in case.tasks])) == 1 \
                                    and case.tasks[0].status == TaskStatus.CREATED
            else:
                all_tasks_created = False
            return self.return_response('pages', 'view_case.html', case=case, all_tasks_created=all_tasks_created)
        else:
            return self.return_404(reason="The case you are trying to view does not exist.")

    def change_status(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'edit')
            args = multidict_to_dict(self.request.args)
            change = False
            if "status" in args and args["status"] in CaseStatus.all_statuses:
                status = args["status"]
                if status == CaseStatus.OPEN:
                    verb = ['open', 'opened']
                elif status == CaseStatus.CLOSED:
                    verb = ['close', 'closed']
                else:
                    verb = ['archive', 'archived']
                if 'confirm' in args and args['confirm'] == "true":
                    case.set_status(status, self.current_user)
                    change = True
                return self.return_response('pages', 'confirm_case_status_change.html', case=case, change=change,
                                            status=status, verb=verb)
            else:
                return self.return_404(reason="The case or status change you are trying to make does not exist.")
        else:
            return self.return_404(reason="The case or status change you are trying to make does not exist.")

    def add(self):
        self.check_permissions(self.current_user, "Case", 'add')
        case_loc = ForemanOptions.get_default_location()
        managers = [(user.id, user.fullname) for user in UserRoles.get_managers()]
        classifications = [(cl.replace(" ", "").lower(), cl) for cl in CaseClassification.get_classifications()]
        case_types = [(ct.replace(" ", "").lower(), ct) for ct in CaseType.get_case_types()]

        if self.validate_form(AddCaseForm()):
            new_case = Case(self.form_result['case_name'], self.current_user, self.form_result['background'],
                            self.form_result['reference'], self.form_result['private'], self.form_result['location'],
                            self.form_result['classification'], self.form_result['case_type'])
            session.add(new_case)
            session.flush()
            new_case.add_change(self.current_user)
            session.flush()

            if self.form_result['primary_case_manager']:
                self._create_new_user_role(UserCaseRoles.PRINCIPLE_CASE_MANAGER, new_case,
                                           self.form_result['primary_case_manager'])
            if self.form_result['secondary_case_manager']:
                self._create_new_user_role(UserCaseRoles.SECONDARY_CASE_MANAGER, new_case,
                                           self.form_result['secondary_case_manager'])
            return self.return_response('pages', 'view_case.html', case=new_case, classifications=classifications,
                                        case_types=case_types)
        else:
            return self.return_response('pages', 'add_case.html', case_loc=case_loc,
                                    managers=managers, errors=self.form_error, classifications=classifications,
                                    case_types=case_types)

    def _return_edit_response(self, case, active_tab, errors=None):
        managers = [(user.id, user.fullname) for user in UserRoles.get_managers()]
        reassign_cases = [(r_case.id, r_case.case_name) for r_case in Case.get_all() if r_case.id != case.id]
        status_options = [(status, status) for status in CaseStatus.all_statuses]
        case_history = self._get_case_history_changes(case)
        tasks_history = self._get_tasks_history_changes(case)
        case_manager_history = self._get_case_manager_history_changes(case)
        reassign_tasks = [(task.id, task.task_name) for task in case.tasks]
        linked_cases = LinkedCase.get_links(case)
        linked_case_ids = [linked_case.id for linked_case in linked_cases]
        case_link_options = [(case_link.id, case_link.case_name) for case_link in Case.get_all()
                             if case_link.id not in [case.id] + linked_case_ids]
        case_link_remove_options = [(case_link.id, case_link.case_name) for case_link in linked_cases]
        principle_man = case.principle_case_manager.fullname if case.principle_case_manager else "Please Select"
        secondary_man = case.secondary_case_manager.fullname if case.secondary_case_manager else "Please Select"
        classifications = [(cl.replace(" ", "").lower(), cl) for cl in CaseClassification.get_classifications()]
        case_types = [(ct.replace(" ", "").lower(), ct) for ct in CaseType.get_case_types()]

        return self.return_response('pages', 'edit_case.html', case=case, active_tab=active_tab,
                                    status_options=status_options, case_link_options=case_link_options,
                                    case_link_remove_options=case_link_remove_options, managers=managers,
                                    principle_man=principle_man, secondary_man=secondary_man,
                                    reassign_tasks=reassign_tasks, reassign_cases=reassign_cases,
                                    case_history=case_history, case_manager_history=case_manager_history,
                                    tasks_history=tasks_history, errors=errors, classifications=classifications,
                                    case_types=case_types)

    def edit(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'edit')

            form_type = multidict_to_dict(self.request.args)
            if 'form' in form_type and form_type['form'] == "edit_case":
                if self.validate_form(EditCaseForm()):
                    case.case_name = self.form_result['case_name']
                    if self.form_result['reference'] != "None":
                        case.reference = self.form_result['reference']
                    case.private = self.form_result['private']
                    case.background = self.form_result['background']
                    case.location = self.form_result['location']
                    case.classification = self.form_result['classification']
                    case.case_type = self.form_result['case_type']
                    case.add_change(self.current_user)
                    return self._return_edit_response(case, 0)
                else:
                    return self._return_edit_response(case, 0, self.form_error)
            elif 'form' in form_type and form_type['form'] == "add_link":
                if self.validate_form(AddCaseLinkForm()):
                    new_link = LinkedCase(case, self.form_result['case_links_add'], self.form_result['reason_add'],
                                          self.current_user)
                    session.add(new_link)
                    session.flush()
                    return self._return_edit_response(case, 1)
                else:
                    return self._return_edit_response(case, 1, self.form_error)
            elif 'form' in form_type and form_type['form'] == "remove_link":
                if self.validate_form(RemoveCaseLinkForm()):
                    new_link = LinkedCase(case, self.form_result['case_links'], self.form_result['reason'],
                                          self.current_user, removed=True)
                    session.add(new_link)
                    session.flush()
                    return self._return_edit_response(case, 1)
                else:
                    return self._return_edit_response(case, 1, self.form_error)
            elif 'form' in form_type and form_type['form'] == "edit_case_managers":
                if self.validate_form(EditCaseManagersForm()):
                    if case.principle_case_manager != self.form_result['primary_case_manager']:
                        self._create_new_user_role(UserCaseRoles.PRINCIPLE_CASE_MANAGER, case,
                                                   self.form_result['primary_case_manager'])
                    if case.secondary_case_manager != self.form_result['secondary_case_manager']:
                        self._create_new_user_role(UserCaseRoles.SECONDARY_CASE_MANAGER, case,
                                                   self.form_result['secondary_case_manager'])
                    return self._return_edit_response(case, 2)
                else:
                    return self._return_edit_response(case, 2, self.form_error)
            elif 'form' in form_type and form_type['form'] == "reassign_tasks":
                if self.validate_form(ReAssignTasksForm()):
                    task_to_reassign = self.form_result['task_reassign']
                    case_to_reassign = self.form_result['case_reassign']
                    ## ressign task to case
                    return self._return_edit_response(case, 3)
                else:
                    return self._return_edit_response(case, 3, self.form_error)
            else:
                return self._return_edit_response(case, 0)

        else:
            return self.return_404(
                reason="The case you are trying to edit does not exist and therefore not editable.")

    def close(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'close')

            closed = False
            confirm_close = multidict_to_dict(self.request.args)

            if 'confirm' in confirm_close and confirm_close['confirm'] == "true":
                case.close_case()
                closed = True

            return self.return_response('pages', 'confirm_close_case.html', case=case, closed=closed)
        else:
            return self.return_404(reason="You have tried to close an invalid case.")

    @staticmethod
    def _get_case_history_changes(case):
        history = CaseHistory.get_changes(case)
        statuses = CaseStatus.get_changes(case)
        results = history + statuses
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
    def _get_tasks_history_changes(case):
        history = []
        for task in case.tasks:
            history += TaskHistory.get_changes(task)
            history += TaskStatus.get_changes(task)
        history.sort(key=lambda d: d['date_time'])
        return history

    def _create_new_user_role(self, role, case, form_result):
        try:
            user_role = UserCaseRoles.get_filter_by(role=role, case=case)[0]
            user_role.add_change(self.current_user, form_result)
            session.flush()
        except IndexError:
            if form_result is not True:
                new_role = UserCaseRoles(form_result, case, role)
                session.add(new_role)
                session.flush()
                new_role.add_change(self.current_user)