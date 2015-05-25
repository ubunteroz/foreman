# library imports
from werkzeug import Response, redirect
# local imports
from baseController import BaseController
from taskController import TaskController
from ..model import Case, CaseStatus, UserCaseRoles, Task, UserTaskRoles, LinkedCase, UserRoles, \
    CaseHistory, TaskHistory, TaskStatus, ForemanOptions, CaseClassification, CaseType, TaskType, CasePriority
from ..utils.utils import multidict_to_dict, session
from ..forms.forms import AddCaseForm, EditCaseForm, AddCaseLinkForm, RemoveCaseLinkForm, RequesterAddTaskForm
from ..forms.forms import EditCaseManagersForm, ReAssignTasksForm, RequesterAddCaseForm, AddTaskForm


class CaseController(BaseController):
    def _create_breadcrumbs(self):
        BaseController._create_breadcrumbs(self)
        self.breadcrumbs.append({'title': 'Cases', 'path': self.urls.build('case.view_all')})

    def view_all(self):
        self.check_permissions(self.current_user, 'Case', 'view-all')

        view = multidict_to_dict(self.request.args)
        allowed = CaseStatus.all_statuses
        allowed.append("All")
        allowed.append("Queued")
        if 'view' in view:
            if self.request.args['view'].title() in CaseStatus.all_statuses:
                all_cases = Case.get_cases(view['view'].title(), self.current_user,
                                           current_user_perms=self.check_view_permissions("Case", "admin"),
                                           case_perm_checker=self.check_permissions)
            elif self.request.args['view'].title() == "All":
                all_cases = Case.get_cases("All", self.current_user,
                                           current_user_perms=self.check_view_permissions("Case", "admin"),
                                           case_perm_checker=self.check_permissions)
            elif self.request.args['view'].title() == "Unassigned":
                all_cases = Case.get_cases("Created", self.current_user,
                                           current_user_perms=self.check_view_permissions("Case", "admin"),
                                           case_perm_checker=self.check_permissions, case_man=True)
            elif self.request.args['view'].title() == "My":
                if self.current_user.is_case_manager:
                    all_cases = Case.get_current_cases(self.current_user, self.check_permissions, self.current_user)
                else:
                    all_cases = []
            else:
                all_cases = Case.get_cases('Open', self.current_user,
                                           current_user_perms=self.check_view_permissions("Case", "admin"),
                                           case_perm_checker=self.check_permissions)
        else:
            all_cases = Case.get_cases('Open', self.current_user,
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
            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.case_name))})
            return self.return_response('pages', 'view_case.html', case=case, all_tasks_created=all_tasks_created)
        else:
            return self.return_404(reason="The case you are trying to view does not exist.")

    def change_status(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'edit')

            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.case_name))})
            self.breadcrumbs.append({'title': "Change Status",
                                     'path': self.urls.build('case.change_status', dict(case_id=case.case_name))})

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
        self.breadcrumbs.append({'title': "Add new case", 'path': self.urls.build('case.add')})
        is_requester = self.current_user.is_requester()
        case_loc = ForemanOptions.get_default_location()
        managers = [(user.id, user.fullname) for user in UserRoles.get_managers()]
        classifications = [(cl.replace(" ", "").lower(), cl) for cl in CaseClassification.get_classifications()]
        case_types = [(ct.replace(" ", "").lower(), ct) for ct in CaseType.get_case_types()]
        priorities = [(priority.case_priority, priority.case_priority) for priority in CasePriority.get_all()]

        args = multidict_to_dict(self.request.args)
        if 'type' in args and args['type'] == "requester" and is_requester:
            if self.validate_form(RequesterAddCaseForm()):
                case_name = ForemanOptions.get_next_case_name()
                new_case = Case(case_name, self.current_user, self.form_result['background'],
                                self.form_result['reference'], self.form_result['private'], None,
                                self.form_result['classification'], self.form_result['case_type'],
                                self.form_result['justification'], self.form_result['priority'])
                session.add(new_case)
                session.flush()
                new_case.add_change(self.current_user)
                session.flush()
                new_role = UserCaseRoles(self.current_user, new_case, UserCaseRoles.REQUESTER)
                session.add(new_role)
                new_role.add_change(self.current_user)
                return self.return_response('pages', 'case_added.html', case=new_case)
            else:
                return self.return_response('pages', 'add_case.html', case_loc=case_loc, is_requester=is_requester,
                                            managers=managers, errors=self.form_error, classifications=classifications,
                                            case_types=case_types, priorities=priorities)
        elif self.validate_form(AddCaseForm()):
            new_case = Case(self.form_result['case_name'], self.current_user, self.form_result['background'],
                            self.form_result['reference'], self.form_result['private'], self.form_result['location'],
                            self.form_result['classification'], self.form_result['case_type'],
                            self.form_result['justification'], self.form_result['priority'])
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
                                        case_types=case_types, priorities=priorities)
        else:
            next_case_name = ForemanOptions.get_next_case_name()
            return self.return_response('pages', 'add_case.html', case_loc=case_loc, is_requester=is_requester,
                                        managers=managers, errors=self.form_error, classifications=classifications,
                                        case_types=case_types, next_case_name=next_case_name, priorities=priorities)

    def add_task(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'add-task')
            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.case_name))})
            self.breadcrumbs.append({'title': "Add new task", 'path': self.urls.build('case.add_task',
                                                                                      dict(case_id=case.case_name))})

            is_requester = self.current_user.is_requester()
            task_type_options = [(tt.replace(" ", "").lower(), tt) for tt in TaskType.get_task_types()]

            args = multidict_to_dict(self.request.args)
            if 'type' in args and args['type'] == "requester" and is_requester:
                if self.validate_form(RequesterAddTaskForm()):
                    task_name = ForemanOptions.get_next_task_name(case, self.form_result['task_type'])
                    new_task = Task(case, self.form_result['task_type'], task_name,
                                    self.current_user, self.form_result['background'])
                    session.add(new_task)
                    session.flush()
                    new_task.add_change(self.current_user)
                    session.flush()
                    return self.return_response('pages', 'task_added.html', task=new_task)
                else:
                    return self.return_response('pages', 'add_task.html', task_type_options=task_type_options,
                                                case=case, errors=self.form_error, is_requester=is_requester)
            elif self.validate_form(AddTaskForm()):
                new_task = Task(case, self.form_result['task_type'], self.form_result['task_name'], self.current_user,
                                self.form_result['background'], self.form_result['location'])
                session.add(new_task)
                session.flush()
                new_task.add_change(self.current_user)
                session.flush()

                if self.form_result['primary_investigator']:
                    self._create_new_user_role(UserTaskRoles.PRINCIPLE_INVESTIGATOR, new_task,
                                               self.form_result['primary_investigator'])
                if self.form_result['secondary_investigator']:
                    self._create_new_user_role(UserTaskRoles.SECONDARY_INVESTIGATOR, new_task,
                                               self.form_result['secondary_investigator'])
                if self.form_result['primary_qa']:
                    self._create_new_user_role(UserTaskRoles.PRINCIPLE_QA, new_task, self.form_result['primary_qa'])
                if self.form_result['secondary_qa']:
                    self._create_new_user_role(UserTaskRoles.SECONDARY_QA, new_task, self.form_result['secondary_qa'])

                session.commit()
                return redirect(
                    self.urls.build('case.view', {"case_id": case.case_name}))  # CaseController.view(case.case_name)
            else:
                investigators = [(user.id, user.fullname) for user in UserRoles.get_investigators()]
                qas = [(user.id, user.fullname) for user in UserRoles.get_qas()]
                return self.return_response('pages', 'add_task.html', investigators=investigators, qas=qas,
                                            task_type_options=task_type_options, case=case, errors=self.form_error,
                                            is_requester=is_requester)
        else:
            return self.return_404()

    def change_task_statuses(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'edit')
            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.case_name))})
            self.breadcrumbs.append({'title': "Change Task Statuses",
                                     'path': self.urls.build('case.change_task_statuses',
                                                             dict(case_id=case.case_name))})
            args = multidict_to_dict(self.request.args)
            change = False
            if "status" in args and args["status"] in TaskStatus.preInvestigation:
                status = args["status"]
                all_tasks_created = len(set([task.status for task in case.tasks])) == 1 \
                                    and case.tasks[0].status == TaskStatus.CREATED
                if not all_tasks_created:
                    return self.return_404()
                if 'confirm' in args and args['confirm'] == "true":
                    for task in case.tasks:
                        task.set_status(status, self.current_user)
                        change = True
                return self.return_response('pages', 'confirm_task_statuses_change.html', case=case, change=change,
                                            status=status)
            else:
                return self.return_404(reason="The case or status change you are trying to make does not exist.")
        else:
            return self.return_404(reason="The case or status change you are trying to make is incorrect.")

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
        priorities = [(priority.case_priority, priority.case_priority) for priority in CasePriority.get_all()]

        return self.return_response('pages', 'edit_case.html', case=case, active_tab=active_tab,
                                    status_options=status_options, case_link_options=case_link_options,
                                    case_link_remove_options=case_link_remove_options, managers=managers,
                                    principle_man=principle_man, secondary_man=secondary_man,
                                    reassign_tasks=reassign_tasks, reassign_cases=reassign_cases,
                                    case_history=case_history, case_manager_history=case_manager_history,
                                    tasks_history=tasks_history, errors=errors, classifications=classifications,
                                    case_types=case_types, priorities=priorities)

    def edit(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'edit')
            form_type = multidict_to_dict(self.request.args)

            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.case_name))})
            self.breadcrumbs.append({'title': "Edit",
                                     'path': self.urls.build('case.edit', dict(case_id=case.case_name))})

            if 'active_tab' in form_type:
                try:
                    active_tab = int(form_type['active_tab'])
                except ValueError:
                    active_tab = 0
            else:
                active_tab = 0
            if 'form' in form_type and form_type['form'] == "edit_case":
                if self.validate_form(EditCaseForm()):
                    case.case_name = self.form_result['case_name']
                    if self.form_result['reference'] != "None" or self.form_result['reference'] != "":
                        case.reference = self.form_result['reference']
                    case.private = self.form_result['private']
                    case.background = self.form_result['background']
                    case.location = self.form_result['location']
                    case.classification = self.form_result['classification']
                    case.case_type = self.form_result['case_type']
                    case.justification = self.form_result['justification']
                    case.case_priority = self.form_result['priority'].case_priority
                    case.case_priority_colour = self.form_result['priority'].colour
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
                    # # ressign task to case
                    return self._return_edit_response(case, 3)
                else:
                    return self._return_edit_response(case, 3, self.form_error)
            else:
                return self._return_edit_response(case, active_tab)

        else:
            return self.return_404(
                reason="The case you are trying to edit does not exist and therefore not editable.")

    def close(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'close')

            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.case_name))})
            self.breadcrumbs.append({'title': "Close",
                                     'path': self.urls.build('case.close', dict(case_id=case.case_name))})
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