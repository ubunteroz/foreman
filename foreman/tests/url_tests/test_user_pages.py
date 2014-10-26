"""
Tests to check that all pages work as expected with a 200 status code and not 404 or 500 for example.
"""

# local imports
from base_tester import URLTestCase


class TaskTestCase(URLTestCase):

    def test_view_all_users(self):
        self._check_url('/users/', None, 401)  # not logged in
        self._check_url('/users/', 1)  # login as admin
        self._check_url('/users/', 19, 403)  # login as a case manager
        self._check_url('/users/', 11, 403)  # login as an investigator
        self._check_url('/users/', 7, 403)  # login as a QA
        self._check_url('/users/', 33, 403)  # login as a requester

    def test_view_user(self):
        self._check_url('/users/test/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/6568/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/2/', None, 401)  # not logged in
        self._check_url('/users/2/', 1)  # login as admin
        self._check_url('/users/2/', 19)  # login as another user
        self._check_url('/users/2/', 2)  # login as user

    def test_add_user(self):
        self._check_url('/users/add/', None, 401)  # not logged in
        self._check_url('/users/add/', 1)  # login as admin
        self._check_url('/users/add/', 19, 403)  # login as a non admin

    def test_edit_user(self):
        self._check_url('/users/edit/test/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/edit/6568/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/edit/2/', None, 401)  # not logged in
        self._check_url('/users/edit/2/', 1)  # login as admin
        self._check_url('/users/edit/2/', 19, 403)  # login as another user
        self._check_url('/users/edit/2/', 2)  # login as user

    def test_edit_user_password(self):
        self._check_url('/users/edit_password/test/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/edit_password/6568/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/edit_password/2/', None, 401)  # not logged in
        self._check_url('/users/edit_password/2/', 1)  # login as admin
        self._check_url('/users/edit_password/2/', 19, 403)  # login as another user
        self._check_url('/users/edit_password/2/', 2)  # login as user

    def test_view_user_case_history(self):
        self._check_url('/users/test/case_history/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/6568/case_history/', 1, 404)  # login as admin, but non-existent user
        self._check_url('/users/2/case_history/', None, 401)  # not logged in
        self._check_url('/users/2/case_history/', 1)  # login as admin
        self._check_url('/users/2/case_history/', 19)  # login as another user
        self._check_url('/users/2/case_history/', 33, 403)  # login as a requester
        self._check_url('/users/33/case_history/', 33)  # login as a requester viewing their own