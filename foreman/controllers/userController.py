# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController
from ..model import User, UserRoles, Case, CaseHistory, TaskHistory, TaskStatus, CaseStatus, EvidenceHistory
from ..model import UserHistory, UserRolesHistory, UserTaskRolesHistory, UserCaseRolesHistory
from ..forms.forms import PasswordChangeForm, EditUserForm, EditRolesForm, AddUserForm, AdminPasswordChangeForm
from ..utils.utils import multidict_to_dict, session, config
from ..utils.mail import email

class UserController(BaseController):
    def view_all(self):
        all_users = User.get_all()
        return self.return_response('pages', 'view_users.html', users=all_users)

    def view(self, user_id):
        user = self._validate_user(user_id)
        if user is not None:
            role_groups = UserRoles.roles
            user_roles = UserRoles.get_role_names(user_id)
            cases_worked_on = Case.cases_with_user_involved(user_id)
            user_changes_history = get_user_changes(user)
            return self.return_response('pages', 'view_user.html', user=user, role_groups=role_groups,
                                        user_roles=user_roles, cases_worked_on=cases_worked_on,
                                        user_changes_history=user_changes_history)
        else:
            return self.return_404()

    def add(self):
        if self.validate_form(AddUserForm):
            new_user_password = User.make_random_password()
            print new_user_password, "*"*99
            if self.form_result['middlename'] == "":
                self.form_result['middlename'] = None
            new_user = User(self.form_result['username'], new_user_password, self.form_result['forename'],
                            self.form_result['surname'], self.form_result['email'], validated=True,
                            middle=self.form_result['middlename'])
            session.add(new_user)
            session.flush()
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
            """.format(new_user.forename, new_user.username, new_user_password), config.get('email', 'from_address'))
            return self.view(new_user.id)
        else:
            role_types = []
            for role in UserRoles.roles:
                role_types.append((role, role.lower().replace(" ", ""), [("yes", "Yes"), ("no", "No")]))
            return self.return_response('pages','add_user.html', role_types=role_types)

    def edit(self, user_id):
        user = self._validate_user(user_id)
        if user is not None:

            form_type = multidict_to_dict(self.request.args)
            if 'tab' in form_type and form_type['tab'] == "edit_roles":
                self.check_permissions(self.current_user, user, 'edit-roles')
                active_tab = 1
            else:
                active_tab = 0

            if 'form' in form_type and form_type['form'] == "edit_roles":
                self.check_permissions(self.current_user, user, 'edit-roles')

                active_tab = 1
                if self.validate_form(EditRolesForm()):
                    for role in UserRoles.roles:
                        active_role = UserRoles.check_user_has_active_role(user, role)
                        if active_role != self.form_result[role.lower().replace(" ", "")]:
                            UserRoles.edit_user_role(user, role, self.current_user)

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
                    user.add_change(self.current_user)

            self.check_permissions(self.current_user, user, 'edit')
            role_types = []
            for role in UserRoles.roles:
                role_types.append((role, role.lower().replace(" ", ""), [("yes", "Yes"), ("no", "No")]))
            user_history = get_user_history_changes(user)
            user_role_history = get_user_role_history_changes(user)
            return self.return_response('pages', 'edit_user.html', user=user, active_tab=active_tab,
                                        role_types=role_types, user_history=user_history,
                                        user_role_history=user_role_history, errors=self.form_error)
        else:
            return self.return_404()

    def edit_password(self, user_id):
        user = self._validate_user(user_id)
        if user is not None:
            self.check_permissions(self.current_user, user, 'edit-password')

            if self.validate_form(PasswordChangeForm()):
                if user.check_password(user.username, self.form_result['password']):
                    # successful password change
                    user.set_password(self.form_result['new_password'])

                    email([user.email], "Your Foreman password has changed",
                    """
                        Hello {},

                        Just to let you know your password has been changed. If this is not the case, please inform
                        your administrator immediately.

                        Thanks,
                        Foreman
                    """.format(user.forename), config.get('email', 'from_address'))
                    return self.return_response('pages', 'edit_password.html', user=user, success=True)
                else:
                    self.form_error['password'] = "Current password is not correct"
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
                    """.format(user.forename, user.username, self.form_result['new_password']),
                    config.get('email', 'from_address'))
                return self.return_response('pages', 'edit_password.html', user=user, success=True, admin=True)
            else:
                return self.return_response('pages', 'edit_password.html', user=user, errors=self.form_error)
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
    results.sort(key=lambda d: d['date_time'])
    return results