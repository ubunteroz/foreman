from os import path

# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController
from ..model import User, UserRoles, Case, CaseHistory, TaskHistory, TaskStatus, CaseStatus, EvidenceHistory
from ..model import UserHistory, UserRolesHistory, UserTaskRolesHistory, UserCaseRolesHistory, Task, TaskUpload
from ..model import EvidencePhotoUpload, Team, Evidence, LinkedCase, TaskNotes, ChainOfCustody
from ..forms.forms import PasswordChangeForm, EditUserForm, EditRolesForm, AddUserForm, AdminPasswordChangeForm
from ..utils.utils import multidict_to_dict, session, config, upload_file
from ..utils.mail import email


class UserController(BaseController):
    def _create_breadcrumbs(self):
        BaseController._create_breadcrumbs(self)
        if self.current_user.is_admin():
            self.breadcrumbs.append({'title': 'Users', 'path': self.urls.build('user.view_all')})

    def view_all(self):
        self.check_permissions(self.current_user, "User", 'view-all')
        all_users = User.get_all().all()
        return self.return_response('pages', 'view_users.html', users=all_users)

    def view(self, user_id):
        user = self._validate_user(user_id)
        if user is not None:
            # no permissions check, all logged in users can view a user profile
            self.breadcrumbs.append({'title': user.fullname,
                                     'path': self.urls.build('user.view', dict(user_id=user.id))})
            role_groups = UserRoles.roles
            user_roles = UserRoles.get_role_names(user_id)
            cases_working_on = Case.cases_with_user_involved(user_id, active=True)
            user_changes_history = get_user_changes(user)
            get_evidence_case = Evidence.get
            return self.return_response('pages', 'view_user.html', user=user, role_groups=role_groups,
                                        user_roles=user_roles, cases_working_on=cases_working_on,
                                        user_changes_history=user_changes_history, get_evidence_case=get_evidence_case)
        else:
            return self.return_404()

    def view_department(self, department_id):
        dep = self._validate_department(department_id)
        if dep is not None:
            # no permissions check, all logged in users can view a user department
            self.breadcrumbs.append({'title': dep.department, 'path': self.urls.build('user.view_department',
                                                                                      dict(department_id=dep.id))})
            return self.return_response('pages', 'view_department.html', department=dep)
        else:
            return self.return_404()

    def view_team(self, department_id, team_id):
        team = self._validate_team(team_id)
        if team is not None:
            # no permissions check, all logged in users can view a user team
            self.breadcrumbs.append({'title': team.department.department,
                                     'path': self.urls.build('user.view_department',
                                                             dict(department_id=team.department.id))})
            self.breadcrumbs.append({'title': team.team,
                                     'path': self.urls.build('user.view_team', dict(team_id=team.id,
                                                                                    department_id=team.department.id))})
            return self.return_response('pages', 'view_team.html', team=team)
        else:
            return self.return_404()

    def add(self):
        self.check_permissions(self.current_user, "User", 'add')
        self.breadcrumbs.append({'title': "Add User", 'path': self.urls.build('user.add')})

        if self.validate_form(AddUserForm):
            new_user_password = User.make_random_password()
            if self.form_result['middlename'] == "":
                self.form_result['middlename'] = None
            new_user = User(self.form_result['username'], new_user_password, self.form_result['forename'],
                            self.form_result['surname'], self.form_result['email'], validated=True,
                            middle=self.form_result['middlename'])
            session.add(new_user)
            session.flush()
            new_user.job_title = self.form_result['job_title']
            new_user.team = self.form_result['team']

            if self.form_result['telephone'] == "":
                self.form_result['telephone'] = None
            new_user.telephone = self.form_result['telephone']
            if self.form_result['alt_telephone'] == "":
                self.form_result['alt_telephone'] = None
            new_user.alt_telephone = self.form_result['alt_telephone']
            if self.form_result['fax'] == "":
                self.form_result['fax'] = None
            new_user.fax = self.form_result['fax']

            new_user.add_change(self.current_user)
            session.flush()

            for role in UserRoles.roles:
                if self.form_result[role.lower().replace(" ", "")] is True:
                    new_role = UserRoles(new_user, role, False)
                else:
                    new_role = UserRoles(new_user, role, True)
                session.add(new_role)
                session.flush()
                new_role.add_change(self.current_user)

            email([new_user.email], "You had been added as a user to Foreman",
                  """
Hello {},

The administrator for Foreman has added an account for you:
Username: {}
Password: {}

Please change this randomly generated password when you first log in.

Thanks,
Foreman
{}
            """.format(new_user.forename, new_user.username, new_user_password, config.get('admin', 'website_domain')),
                  config.get('email', 'from_address'))
            return self.view(new_user.id)
        else:
            role_types = []
            for role in UserRoles.roles:
                role_types.append((role, role.lower().replace(" ", ""), [("yes", "Yes"), ("no", "No")]))
            teams = sorted([(team.id, team.department.department + ": " + team.team) for team in Team.get_all()],
                           key=lambda t: t[1])
            return self.return_response('pages', 'add_user.html', role_types=role_types, errors=self.form_error,
                                        teams=teams)

    def edit(self, user_id):
        user = self._validate_user(user_id)

        if user is not None:
            form_type = multidict_to_dict(self.request.args)
            if 'tab' in form_type and form_type['tab'] == "edit_roles":
                self.check_permissions(self.current_user, user, 'edit-roles')
                active_tab = 1
            else:
                active_tab = 0

            self.breadcrumbs.append(
                {'title': user.fullname, 'path': self.urls.build('user.view', dict(user_id=user.id))})
            self.breadcrumbs.append({'title': "Edit", 'path': self.urls.build('user.edit', dict(user_id=user.id))})

            if 'form' in form_type and form_type['form'] == "edit_roles":
                self.check_permissions(self.current_user, user, 'edit-roles')

                active_tab = 1
                if self.validate_form(EditRolesForm()):
                    for role in UserRoles.roles:
                        # admin - user id 1 -  cannot remove administrator
                        active_role = UserRoles.check_user_has_active_role(user, role)
                        if active_role != self.form_result[role.lower().replace(" ", "")]:
                            if not (user.id == 1 and role == "Administrator" and self.form_result[
                                'administrator'] is False):
                                UserRoles.edit_user_role(user, role, self.current_user)
                            else:
                                self.form_error['administrator'] = "Cannot remove the admin role."
                                self.form_result['administrator'] = True

            elif 'form' in form_type and form_type['form'] == "edit_user":
                self.check_permissions(self.current_user, user, 'edit')

                active_tab = 0
                if self.validate_form(EditUserForm()):
                    user.username = self.form_result['username']
                    user.forename = self.form_result['forename']
                    user.surname = self.form_result['surname']
                    user.email = self.form_result['email']
                    if self.form_result['middlename'] == "":
                        user.middle = None
                    else:
                        user.middle = self.form_result['middlename']
                    user.job_title = self.form_result['job_title']
                    user.team = self.form_result['team']
                    if self.form_result['photo'] is not None:
                        user.photo = upload_file(self.form_result['photo'], User.PROFILE_PHOTO_FOLDER)
                    if self.form_result['telephone'] == "":
                        self.form_result['telephone'] = None
                    user.telephone = self.form_result['telephone']
                    if self.form_result['alt_telephone'] == "":
                        self.form_result['alt_telephone'] = None
                    user.alt_telephone = self.form_result['alt_telephone']
                    if self.form_result['fax'] == "":
                        self.form_result['fax'] = None
                    user.fax = self.form_result['fax']

                    user.add_change(self.current_user)

            self.check_permissions(self.current_user, user, 'edit')
            role_types = []
            for role in UserRoles.roles:
                role_types.append((role, role.lower().replace(" ", ""), [("yes", "Yes"), ("no", "No")]))
            user_history = get_user_history_changes(user)
            user_role_history = get_user_role_history_changes(user)
            teams = sorted([(team.id, team.department.department + ": " + team.team) for team in Team.get_all()],
                           key=lambda t: t[1])
            return self.return_response('pages', 'edit_user.html', user=user, active_tab=active_tab,
                                        role_types=role_types, user_history=user_history, teams=teams,
                                        user_role_history=user_role_history, errors=self.form_error)
        else:
            return self.return_404()

    def edit_password(self, user_id):
        user = self._validate_user(user_id)
        if user is not None:
            self.check_permissions(self.current_user, user, 'edit-password')
            self.breadcrumbs.append({'title': user.fullname,
                                     'path': self.urls.build('user.view', dict(user_id=user.id))})
            self.breadcrumbs.append({'title': "Edit Password",
                                     'path': self.urls.build('user.edit_password', dict(user_id=user.id))})

            if user.username == self.current_user.username:
                if self.validate_form(PasswordChangeForm()):
                    if user.check_password(user.username, self.form_result['password']):
                        # successful password change
                        user.set_password(self.form_result['new_password'])

                        email([user.email], "Your Foreman password has changed",
                              """
Hello {},

Just to let you know your password has been changed. If this is not the case, please inform your administrator immediately.

Thanks,
Foreman
{}
                        """.format(user.forename, config.get('admin', 'website_domain')),
                              config.get('email', 'from_address'))
                        return self.return_response('pages', 'edit_password.html', user=user, success=True)
                    else:
                        self.form_error['password'] = "Current password is not correct"
                        return self.return_response('pages', 'edit_password.html', user=user, errors=self.form_error)
                else:
                    return self.return_response('pages', 'edit_password.html', user=user, errors=self.form_error)
            elif self.validate_form(AdminPasswordChangeForm()):
                user.set_password(self.form_result['new_password'])
                email([user.email], "Your Foreman password has changed",
                      """
Hello {},

Just to let you know the administrator has changed your password:
Username: {}
Password: {}

Please change this password when you next log in.

Thanks,
Foreman
{}
                    """.format(user.forename, user.username, self.form_result['new_password'],
                               config.get('admin', 'website_domain')),
                      config.get('email', 'from_address'))
                return self.return_response('pages', 'edit_password.html', user=user, success=True, admin=True)
            else:
                return self.return_response('pages', 'edit_password.html', user=user, errors=self.form_error)
        else:
            return self.return_404()

    def case_history(self, user_id):
        user = self._validate_user(user_id)
        if user is not None:
            self.check_permissions(self.current_user, user, "view-history")
            self.breadcrumbs.append({'title': user.fullname,
                                     'path': self.urls.build('user.view', dict(user_id=user.id))})
            self.breadcrumbs.append({'title': "Case History",
                                     'path': self.urls.build('user.case_history', dict(user_id=user.id))})

            if user.is_investigator() or user.is_QA():
                current_tasks_qaed = Task.get_current_qas(user, self.check_permissions, self.current_user)
                old_tasks_qaed = Task.get_completed_qas(user, self.check_permissions, self.current_user)
                current_tasks_investigated = Task.get_current_investigations(user, self.check_permissions,
                                                                             self.current_user)
                old_tasks_investigated = Task.get_completed_investigations(user, self.check_permissions,
                                                                           self.current_user)
            else:
                current_tasks_investigated = None
                old_tasks_investigated = None
                current_tasks_qaed = None
                old_tasks_qaed = None

            if user.is_case_manager():
                old_cases_managed = Case.get_completed_cases(user, self.check_permissions, self.current_user)
                current_cases_managed = Case.get_current_cases(user, self.check_permissions, self.current_user)
            else:
                old_cases_managed = None
                current_cases_managed = None

            if user.is_requester():
                old_cases_requested = Case.get_cases_requested(user, self.check_permissions,
                                                               self.current_user, [CaseStatus.CLOSED,
                                                                                   CaseStatus.ARCHIVED])
                current_cases_requested = Case.get_cases_requested(user, self.check_permissions, self.current_user,
                                                                   [CaseStatus.CREATED, CaseStatus.OPEN,
                                                                    CaseStatus.PENDING])
            else:
                old_cases_requested = None
                current_cases_requested = None

            return self.return_response('pages', 'user_case_history.html', current_tasks_qaed=current_tasks_qaed,
                                        current_tasks_investigated=current_tasks_investigated, user=user,
                                        old_cases_managed=old_cases_managed,
                                        current_cases_managed=current_cases_managed,
                                        old_tasks_investigated=old_tasks_investigated, old_tasks_qaed=old_tasks_qaed,
                                        old_cases_requested=old_cases_requested,
                                        current_cases_requested=current_cases_requested)
        else:
            return self.return_404()


def get_user_role_history_changes(user):
    """
    Gets the history of the user's roles
    @param user:
    @return: A list of the user's role history
    """
    results = []
    for role in UserRoles.roles:
        results += UserRolesHistory.get_changes(user, role)
    results.sort(key=lambda d: d['date_time'])
    return results


def get_user_history_changes(user):
    """
    Gets the history of the user's changes, e.g. name change
    @param user:
    @return: A list of the user's history
    """
    results = UserHistory.get_changes(user)
    results.sort(key=lambda d: d['date_time'])
    return results


def get_user_changes(user):
    """
    Gets the history of all the changes the user has made on Foreman objects
    @param user:
    @return: A list of the user's change history
    """
    results = CaseHistory.get_changes_for_user(user)
    results += TaskHistory.get_changes_for_user(user)
    results += TaskStatus.get_changes_for_user(user)
    results += CaseStatus.get_changes_for_user(user)
    results += UserHistory.get_changes_for_user(user)
    results += EvidenceHistory.get_changes_for_user(user)
    results += UserTaskRolesHistory.get_changes_for_user(user)
    results += UserCaseRolesHistory.get_changes_for_user(user)
    results += UserRolesHistory.get_changes_for_user(user)
    results += TaskUpload.get_changes_for_user(user)
    results += EvidencePhotoUpload.get_changes_for_user(user)
    results += LinkedCase.get_changes_for_user(user)
    results += TaskNotes.get_changes_for_user(user)
    results += ChainOfCustody.get_changes_for_user(user)
    results.sort(key=lambda d: d['date_time'])
    return results