# library imports
from werkzeug import Response, redirect
from datetime import datetime
from os import path
# local imports
from baseController import BaseController
from taskController import TaskController
from ..model import Case, CaseStatus, UserCaseRoles, Task, UserTaskRoles, LinkedCase, UserRoles
from ..model import CaseHistory, TaskHistory, TaskStatus, ForemanOptions, CaseClassification, CaseType, TaskType
from ..model import CasePriority, EvidenceStatus, CaseUpload
from ..utils.utils import multidict_to_dict, session, config, upload_file
from ..utils.mail import email
from ..forms.forms import AddCaseForm, EditCaseForm, AddCaseLinkForm, RemoveCaseLinkForm, RequesterAddTaskForm
from ..forms.forms import EditCaseManagersForm, ReAssignTasksForm, RequesterAddCaseForm, AddTaskForm, AuthoriseCaseForm
from ..forms.forms import CloseCaseForm, ChangeCaseStatusForm, UploadCaseFile


class CaseController(BaseController):
    def _create_breadcrumbs(self):
        BaseController._create_breadcrumbs(self)
        self.breadcrumbs.append({'title': 'Cases', 'path': self.urls.build('case.view_all')})

    def view_upload(self, case_id, upload_id):
        upload = self._validate_case_upload(case_id, upload_id)
        if upload is not None:
            self.check_permissions(self.current_user, upload.case, 'view')
            self.breadcrumbs.append({'title': upload.file_title,
                                     'path': self.urls.build('case.view_upload',
                                                             dict(case_id=upload.case.id, upload_id=upload.id))})
            return self.return_response('pages', 'view_case_upload.html', upload=upload)
        else:
            return self.return_404()

    def delete_upload(self, case_id, upload_id):
        upload = self._validate_case_upload(case_id, upload_id)
        if upload is not None:
            self.check_permissions(self.current_user, upload.case, 'delete_file')
            self.breadcrumbs.append({'title': upload.file_title,
                                     'path': self.urls.build('case.view_upload', dict(case_id=upload.case.id,
                                                                                      upload_id=upload.id))})
            self.breadcrumbs.append({'title': "Delete",
                                     'path': self.urls.build('case.delete_upload', dict(case_id=upload.case.id,
                                                                                        upload_id=upload.id))})
            closed = False
            confirm_close = multidict_to_dict(self.request.args)
            if 'confirm' in confirm_close and confirm_close['confirm'] == "true":
                upload.delete(self.current_user)
                closed = True

            return self.return_response('pages', 'delete_case_upload.html', upload=upload, closed=closed)
        else:
            return self.return_404()

    def view_all(self):
        self.check_permissions(self.current_user, 'Case', 'view-all')

        view = multidict_to_dict(self.request.args)

        if 'view' in view:
            if self.request.args['view'].title() in CaseStatus.all_statuses:
                all_cases = Case.get_cases(view['view'].title(), self.current_user,
                                           case_perm_checker=self.check_permissions)
            elif self.request.args['view'].title() == "Pending":
                all_cases = Case.get_cases(CaseStatus.PENDING, self.current_user,
                                           case_perm_checker=self.check_permissions)
            elif self.request.args['view'].title() == "All":
                all_cases = Case.get_cases("All", self.current_user, case_perm_checker=self.check_permissions)
            elif self.request.args['view'].title() == "Authorised":
                all_cases = Case.get_cases_authorised(self.current_user, self.check_permissions, self.current_user,
                                                      CaseStatus.approved_statuses)
            elif self.request.args['view'].title() == "Unassigned":
                all_cases = Case.get_cases("Created", self.current_user, case_perm_checker=self.check_permissions,
                                           case_man=True)
            elif self.request.args['view'].title() == "My":
                if self.current_user.is_case_manager:
                    all_cases = Case.get_current_cases(self.current_user, self.check_permissions, self.current_user)
                else:
                    all_cases = []
            else:
                all_cases = Case.get_cases('Open', self.current_user, case_perm_checker=self.check_permissions)
        else:
            if self.current_user.is_authoriser():
                all_cases = Case.get_cases(CaseStatus.PENDING, self.current_user,
                                           case_perm_checker=self.check_permissions)
                view['view'] = "Pending"
            else:
                all_cases = Case.get_cases('Open', self.current_user, case_perm_checker=self.check_permissions)
                view['view'] = "Open"
        return self.return_response('pages', 'view_cases.html', cases=all_cases, case_status=view['view'].title(),
                                    current_user=TaskController.current_user)

    def view(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'view')
            if case.tasks:
                # if all the tasks are in created status, then this adds link to set all the tasks to queued in one go
                all_tasks_created = len(set([task.status for task in case.tasks])) == 1 \
                                    and case.tasks[0].status == TaskStatus.CREATED
            else:
                all_tasks_created = False
            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            return self.return_response('pages', 'view_case.html', case=case, all_tasks_created=all_tasks_created)
        else:
            return self.return_404(reason="The case you are trying to view does not exist.")

    def change_status(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'edit')

            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            self.breadcrumbs.append({'title': "Change Status",
                                     'path': self.urls.build('case.change_status', dict(case_id=case.id))})

            args = multidict_to_dict(self.request.args)
            change = False
            special_note = None
            email_alert_flag = False
            options = ForemanOptions.get_options()

            if "status" in args and args["status"] in CaseStatus.all_statuses:
                status = args["status"]
                if status == CaseStatus.OPEN:
                    verb = ['open', 'opened']
                    if options.email_alert_req_case_opened and case.requester is not None:
                        email_alert_flag = True
                elif status == CaseStatus.CLOSED:
                    verb = ['close', 'closed']
                    if options.email_alert_req_case_closed and case.requester is not None:
                        email_alert_flag = True
                else:
                    verb = ['archive', 'archived']
                    if options.email_alert_req_case_archived and case.requester is not None:
                        email_alert_flag = True
                    special_note = """Please note that by archiving the case, you are also automatically archiving any
                    associated evidence & tasks. You will <b>not</b> be able to make any further changes to the case, tasks
                     or the evidence, apart from changing evidence statuses to <i>destroyed</i>."""
                if 'confirm' in args and args['confirm'] == "true":
                    if self.validate_form(ChangeCaseStatusForm()):
                        reason = self.form_result['change']
                        case.set_status(status, self.current_user)
                        case.get_status().reason = reason
                        change = True

                        if email_alert_flag:
                            url = config.get('admin', 'website_domain') + self.urls.build('case.view',
                                                                                          dict(case_id=case.id))
                            self.send_email_alert([case.requester], "Case status has changed",
                                                  """Your case {} is now {}.

The case can be viewed here: {}""".format(case.case_name, verb[1], url))

                        if status == CaseStatus.ARCHIVED:
                            for evidence in case.evidence:
                                evidence.set_status(EvidenceStatus.ARCHIVED, self.current_user,
                                                    "Automatic archiving of evidence as the case has been archived.")

                        special_note = None
                return self.return_response('pages', 'confirm_case_status_change.html', case=case, change=change,
                                            status=status, verb=verb, errors=self.form_error, special_note=special_note,
                                            email_alert_flag=email_alert_flag)
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
        authorisers = [(user.id, user.fullname) for user in UserRoles.get_authorisers(self.current_user.department)]
        classifications = [(cl.id, cl.classification) for cl in CaseClassification.get_all() if cl != "Undefined"]
        case_types = [(ct.id, ct.case_type) for ct in CaseType.get_all() if ct.case_type != "Undefined"]
        priorities = [(priority.id, priority.case_priority) for priority in CasePriority.get_all()]
        args = multidict_to_dict(self.request.args)
        email_alert_flag = False

        options = ForemanOptions.get_options()
        if options.email_alert_all_caseman_new_case:
            email_alert_flag = True

        if 'type' in args and args['type'] == "requester" and is_requester:
            if self.validate_form(RequesterAddCaseForm()):
                case_name = ForemanOptions.get_next_case_name()

                new_case = Case(case_name, self.current_user, self.form_result['background'],
                                self.form_result['reference'], self.form_result['private'], None,
                                self.form_result['classification'].classification,
                                self.form_result['case_type'].case_type,
                                self.form_result['justification'], self.form_result['priority'],
                                self.form_result['deadline'],
                                authorisor=self.form_result['authoriser'])
                session.add(new_case)
                session.flush()
                new_case.add_change(self.current_user)
                session.flush()
                self._create_new_user_role(UserCaseRoles.REQUESTER, new_case, self.current_user)
                self._create_new_user_role(UserCaseRoles.AUTHORISER, new_case, self.form_result['authoriser'])
                self._send_authorise_email(new_case)
                url = config.get('admin', 'website_domain') + self.urls.build('case.view', dict(case_id=new_case.id))
                self.send_email_alert(UserRoles.get_managers(), "A new case has been created",
                                      """A new case has been created and is pending authorisation.

Case details:
Case requester: {}
Case type: {}
Case priority: {}

The case can be viewed here: {}""".format(new_case.requester.fullname, new_case.case_type, new_case.case_priority, url))

                return self.return_response('pages', 'case_added.html', case=new_case)
            else:
                return self.return_response('pages', 'add_case.html', case_loc=case_loc, is_requester=is_requester,
                                            managers=managers, errors=self.form_error, classifications=classifications,
                                            case_types=case_types, priorities=priorities, authorisers=authorisers,
                                            email_alert_flag=email_alert_flag)
        elif self.validate_form(AddCaseForm()):
            new_case = Case(self.form_result['case_name'], self.current_user, self.form_result['background'],
                            self.form_result['reference'], self.form_result['private'], self.form_result['location'],
                            self.form_result['classification'].classification, self.form_result['case_type'].case_type,
                            self.form_result['justification'], self.form_result['priority'],
                            authorisor=self.form_result['authoriser'])
            session.add(new_case)
            session.flush()
            new_case.add_change(self.current_user)
            session.flush()

            self._create_new_user_role(UserCaseRoles.AUTHORISER, new_case, self.form_result['authoriser'])
            self._send_authorise_email(new_case)

            if self.form_result['primary_case_manager']:
                self._create_new_user_role(UserCaseRoles.PRINCIPLE_CASE_MANAGER, new_case,
                                           self.form_result['primary_case_manager'])
            if self.form_result['secondary_case_manager']:
                self._create_new_user_role(UserCaseRoles.SECONDARY_CASE_MANAGER, new_case,
                                           self.form_result['secondary_case_manager'])
            return self.return_response('pages', 'view_case.html', case=new_case, classifications=classifications,
                                        case_types=case_types, priorities=priorities)
        else:
            if not is_requester:
                next_case_name = ForemanOptions.get_next_case_name()
            else:
                next_case_name = None
            return self.return_response('pages', 'add_case.html', case_loc=case_loc, is_requester=is_requester,
                                        managers=managers, errors=self.form_error, classifications=classifications,
                                        case_types=case_types, next_case_name=next_case_name, priorities=priorities,
                                        authorisers=authorisers, email_alert_flag=email_alert_flag)

    def add_task(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'add-task')
            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            self.breadcrumbs.append({'title': "Add new task", 'path': self.urls.build('case.add_task',
                                                                                      dict(case_id=case.id))})

            is_requester = self.current_user.is_requester()
            task_type_options = [(tt.id, tt.task_type) for tt in TaskType.get_all() if tt.task_type != "Undefined"]

            args = multidict_to_dict(self.request.args)
            if 'type' in args and args['type'] == "requester" and is_requester:
                if self.validate_form(RequesterAddTaskForm()):
                    task_name = ForemanOptions.get_next_task_name(case, self.form_result['task_type'].task_type)
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
                new_task = Task(case, self.form_result['task_type'], self.form_result['task_name'],
                                self.current_user, self.form_result['background'], self.form_result['location'],
                                deadline=self.form_result['deadline'] if self.form_result != "" else None)
                session.add(new_task)
                session.flush()
                new_task.add_change(self.current_user)
                session.flush()

                if self.form_result['primary_investigator']:
                    self._create_new_user_role(UserTaskRoles.PRINCIPLE_INVESTIGATOR, new_task,
                                               self.form_result['primary_investigator'], role_obj="task")
                if self.form_result['secondary_investigator']:
                    self._create_new_user_role(UserTaskRoles.SECONDARY_INVESTIGATOR, new_task,
                                               self.form_result['secondary_investigator'], role_obj="task")
                if self.form_result['primary_qa']:
                    self._create_new_user_role(UserTaskRoles.PRINCIPLE_QA, new_task, self.form_result['primary_qa'],
                                               role_obj="task")
                if self.form_result['secondary_qa']:
                    self._create_new_user_role(UserTaskRoles.SECONDARY_QA, new_task, self.form_result['secondary_qa'],
                                               role_obj="task")

                session.commit()
                return redirect(
                    self.urls.build('case.view', {"case_id": case.id}))
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
            self.check_permissions(self.current_user, case, 'can-assign')
            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            self.breadcrumbs.append({'title': "Change Task Statuses",
                                     'path': self.urls.build('case.change_task_statuses',
                                                             dict(case_id=case.id))})
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

    def _return_edit_response(self, case, active_tab, errors=None, **pass_through_args):
        email_alert_flag = False
        options = ForemanOptions.get_options()
        if options.email_alert_req_case_caseman_assigned and case.requester is not None:
            email_alert_flag = True
        managers = [(user.id, user.fullname) for user in UserRoles.get_managers()]
        reassign_cases = []
        for r_case in Case.get_cases('Workable', self.current_user, case_perm_checker=self.check_permissions):
            if r_case.id != case.id:
                reassign_cases.append((r_case.id, r_case.case_name))
        status_options = [(status, status) for status in CaseStatus.all_statuses]
        case_history = self._get_case_history_changes(case)
        tasks_history = self._get_tasks_history_changes(case)
        case_manager_history = self._get_case_manager_history_changes(case)
        reassign_tasks = [(task.id, task.task_name) for task in case.tasks]
        linked_cases = LinkedCase.get_links(case)
        linked_case_ids = [linked_case.id for linked_case in linked_cases]
        case_link_options = []
        for case_link in Case.get_cases('All', self.current_user, case_perm_checker=self.check_permissions):
            if case_link.id not in [case.id] + linked_case_ids:
                case_link_options.append((case_link.id, case_link.case_name))
        case_link_remove_options = [(case_link.id, case_link.case_name) for case_link in linked_cases]
        principle_man = case.principle_case_manager.fullname if case.principle_case_manager else "Please Select"
        secondary_man = case.secondary_case_manager.fullname if case.secondary_case_manager else "Please Select"
        classifications = [(cl.id, cl.classification) for cl in CaseClassification.get_all() if cl != "Undefined"]
        case_types = [(ct.id, ct.case_type) for ct in CaseType.get_all() if ct.case_type != "Undefined"]
        priorities = [(priority.id, priority.case_priority) for priority in CasePriority.get_all()]
        authorisers = [(user.id, user.fullname) for user in UserRoles.get_authorisers(self.current_user.department)]
        return self.return_response('pages', 'edit_case.html', case=case, active_tab=active_tab,
                                    status_options=status_options, case_link_options=case_link_options,
                                    case_link_remove_options=case_link_remove_options, managers=managers,
                                    principle_man=principle_man, secondary_man=secondary_man,
                                    reassign_tasks=reassign_tasks, reassign_cases=reassign_cases,
                                    case_history=case_history, case_manager_history=case_manager_history,
                                    tasks_history=tasks_history, errors=errors, classifications=classifications,
                                    case_types=case_types, priorities=priorities, authorisers=authorisers,
                                    email_alert_flag=email_alert_flag, **pass_through_args)

    def edit(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'edit')
            form_type = multidict_to_dict(self.request.args)

            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            self.breadcrumbs.append({'title': "Edit",
                                     'path': self.urls.build('case.edit', dict(case_id=case.id))})

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
                    if self.form_result['reference'] != "":
                        case.reference = self.form_result['reference']
                    case.private = self.form_result['private']
                    case.background = self.form_result['background']
                    case.location = self.form_result['location']
                    case.classification = self.form_result['classification'].classification
                    case.case_type = self.form_result['case_type'].case_type
                    case.justification = self.form_result['justification']
                    if self.form_result['deadline'] is not None:
                        case.deadline = datetime.combine(self.form_result['deadline'], datetime.min.time())
                    case.case_priority = self.form_result['priority'].case_priority
                    case.case_priority_colour = self.form_result['priority'].colour
                    case.add_change(self.current_user)

                    if case.deadline is not None:
                        for task in case.tasks:
                            if task.deadline is None or task.deadline > case.deadline:
                                task.deadline = datetime.combine(case.deadline, datetime.min.time())

                    if (case.requester is not None and self.current_user.id == case.requester.id \
                            and case.authorised.case_authorised == "NOAUTH") or (case.requester is None and \
                            self.current_user.id == case.principle_case_manager.id and \
                            case.authorised.case_authorised == "NOAUTH"):
                        case.authorise(self.form_result['authoriser'], "Case has been Edited", "PENDING")
                        case.set_status(CaseStatus.PENDING, self.current_user)
                        self._send_authorise_email(case, edit=True)
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
            elif 'form' in form_type and form_type['form'] == "upload_file":
                if self.validate_form(UploadCaseFile()):
                    f = self.form_result['file']
                    new_directory = path.join(CaseUpload.ROOT, CaseUpload.DEFAULT_FOLDER, str(case.id))
                    file_name = upload_file(f, new_directory)

                    upload = CaseUpload(self.current_user.id, case.id, file_name, self.form_result['comments'],
                                        self.form_result['file_title'])
                    session.add(upload)
                    session.commit()
                    return self._return_edit_response(case, -1, success_upload=True, upload_id=upload.id)
                else:
                    return self._return_edit_response(case, -1, self.form_error)
            elif 'form' in form_type and form_type['form'] == "edit_case_managers":
                if self.validate_form(EditCaseManagersForm()):
                    options = ForemanOptions.get_options()
                    url = config.get('admin', 'website_domain') + self.urls.build('case.view', dict(case_id=case.id))

                    if case.principle_case_manager != self.form_result['primary_case_manager']:
                        self._create_new_user_role(UserCaseRoles.PRINCIPLE_CASE_MANAGER, case,
                                                   self.form_result['primary_case_manager'])
                        if options.email_alert_req_case_caseman_assigned and case.requester is not None and self.form_result['primary_case_manager'] is not None:
                            self.send_email_alert([case.requester], "Case has been picked up by a case manager",
                                                  """{} been assigned to case {} as the primary case manager.

The case can be viewed here: {}""".format(self.form_result['primary_case_manager'].fullname, case.case_name, url))
                    if case.secondary_case_manager != self.form_result['secondary_case_manager']:
                        self._create_new_user_role(UserCaseRoles.SECONDARY_CASE_MANAGER, case,
                                                   self.form_result['secondary_case_manager'])
                        if options.email_alert_req_case_caseman_assigned and case.requester is not None and self.form_result['secondary_case_manager'] is not None:
                            self.send_email_alert([case.requester], "Case has been picked up by a case manager",
                                              """{} been assigned to case {} as the secondary case manager.

The case can be viewed here: {}""".format(self.form_result['secondary_case_manager'].fullname, case.case_name, url))
                    return self._return_edit_response(case, 2)
                else:
                    return self._return_edit_response(case, 2, self.form_error)
            elif 'form' in form_type and form_type['form'] == "reassign_tasks":
                if self.validate_form(ReAssignTasksForm()):
                    task_to_reassign = self.form_result['task_reassign']
                    case_to_reassign = self.form_result['case_reassign']
                    task_to_reassign.case = case_to_reassign
                    task_to_reassign.add_change(self.current_user)
                    return self._return_edit_response(case, 3)
                else:
                    return self._return_edit_response(case, 3, self.form_error)
            else:
                return self._return_edit_response(case, active_tab)

        else:
            return self.return_404(
                reason="The case you are trying to edit does not exist and therefore not editable.")

    def authorise(self, case_id):
        case = self._validate_case(case_id)
        auth_choices = [("Authorised", "Authorised"), ("Rejected", "Rejected")]
        complete = False
        email_alert_flag = False
        options = ForemanOptions.get_options()
        if options.email_alert_all_caseman_case_auth:
            email_alert_flag = True

        if case is not None:
            case_history = self._get_case_history_changes(case)
            self.check_permissions(self.current_user, case, 'authorise')

            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            self.breadcrumbs.append({'title': "Authorise",
                                     'path': self.urls.build('case.authorise', dict(case_id=case.id))})

            if self.validate_form(AuthoriseCaseForm()):
                reason = self.form_result['reason']
                auth = self.form_result['auth']
                if auth is True:
                    authorisation = "AUTH"
                    if options.email_alert_all_caseman_case_auth:
                        url = config.get('admin', 'website_domain') + self.urls.build('case.view',
                                                                                      dict(case_id=case.id))
                        if case.requester is None:
                            requester = case.principle_case_manager
                        else:
                            requester = case.requester
                        self.send_email_alert(UserRoles.get_managers(), "A case has been authorised",
                                              """A new case has been created and authorised.

Case details:
Case name: {}
Case requester: {}
Case type: {}
Case priority: {}

The case can be viewed here: {}""".format(case.case_name, requester.fullname, case.case_type, case.case_priority,
                                          url))
                else:
                    authorisation = "NOAUTH"
                case.authorise(self.current_user, reason, authorisation)
                complete = True
                self._send_authorised_email(case)
            return self.return_response('pages', 'authorise_case.html', case=case, case_history=case_history,
                                        complete=complete, auth_choices=auth_choices,
                                        email_alert_flag=email_alert_flag)
        else:
            return self.return_404(reason="You have tried to authorise an invalid case.")

    def close(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            email_alert_flag = False
            options = ForemanOptions.get_options()
            if options.email_alert_req_case_closed and case.requester is not None:
                email_alert_flag = True

            self.check_permissions(self.current_user, case, 'close')

            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            self.breadcrumbs.append({'title': "Close",
                                     'path': self.urls.build('case.close', dict(case_id=case.id))})
            closed = False
            confirm_close = multidict_to_dict(self.request.args)

            if 'confirm' in confirm_close and confirm_close['confirm'] == "true":
                if self.validate_form(CloseCaseForm()):
                    reason = self.form_result['closure']
                    case.close_case(reason, self.current_user)
                    closed = True
                    if email_alert_flag and case.requester is not None:
                        url = config.get('admin', 'website_domain') + self.urls.build('case.view',
                                                                                      dict(case_id=case.id))
                        self.send_email_alert([case.requester], "Case status has changed", """Your case {} is now closed.

The case can be viewed here: {}""".format(case.case_name, url))

            return self.return_response('pages', 'confirm_close_case.html', case=case, closed=closed,
                                        errors=self.form_error, email_alert_flag=email_alert_flag)
        else:
            return self.return_404(reason="You have tried to close an invalid case.")

    def _send_authorise_email(self, new_case, edit=False):
        # automatic email from requester to authoriser to authorise
        authoriser = new_case.authoriser
        if new_case.requester is None:
            requester = self.current_user # situation where case manager created their own case
        else:
            requester = new_case.requester

        if edit is False:
            verb = "created a new"
        else:
            verb = "edited a"

        email([authoriser.email], "Please authorise case {}".format(new_case.case_name), """
Hello {},

{} has {} case on Foreman and has requested your authorisation. Details:
Case name: {}
Case Reference: {}
Link to authorise or reject: {}{}

Thanks,
Foreman
{}""".format(authoriser.forename, requester.fullname, verb, new_case.case_name,
             new_case.reference,
             config.get('admin', 'website_domain'),
             self.urls.build('case.authorise', dict(case_id=new_case.id)),
             config.get('admin', 'website_domain')), config.get('email', 'from_address'), cc=[requester.email])

    def _send_authorised_email(self, case):
        # automatic email from authoriser to requester that it has been rejected/authorised
        authoriser = case.authoriser
        if case.requester is not None:
            requester = case.requester
        else:
            requester = case.principle_case_manager # on situation where case manager created their own case

        ccs = [authoriser.email]
        if case.authorised.case_authorised == "AUTH":
            decision = "authorised"
        else:
            decision = "rejected"

        subject = "Case {} has been {}".format(case.case_name, decision)

        email([requester.email], subject, """
Hello {},

{} has {} case {} with the reason:
{}

Link to the case: {}{}

Thanks,
Foreman
{}""".format(requester.forename, authoriser.fullname, decision, case.case_name, case.authorised.reason,
             config.get('admin', 'website_domain'),
             self.urls.build('case.view', dict(case_id=case.id)),
             config.get('admin', 'website_domain')), config.get('email', 'from_address'), cc=ccs)
