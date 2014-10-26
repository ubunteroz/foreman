"""
Tests to check that all pages work as expected with a 200 status code and not 404 or 500 for example.
"""

# local imports
from base_tester import URLTestCase


class CasesTestCase(URLTestCase):

    def test_view_all_cases(self):
        self._check_url('/cases/', None, 401)  # not logged in
        self._check_url('/cases/', 1)  # login as admin
        self._check_url('/cases/', 19)  # login as a case manager
        self._check_url('/cases/', 1)  # login as an investigator
        self._check_url('/cases/', 7)  # login as a QA
        self._check_url('/cases/', 33, 403)  # login as a requester

    def test_view_case(self):
        self._check_url('/cases/test_doesnt_exist/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/fish/', None, 401)  # not logged in
        self._check_url('/cases/fish/', 1)  # login as admin
        self._check_url('/cases/fish/', 19)  # login as a case manager
        self._check_url('/cases/fish/', 11)  # login as an investigator
        self._check_url('/cases/fish/', 7)  # login as a QA
        self._check_url('/cases/fish/', 33, 403)  # login as a requester
        self._check_url('/cases/fish/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/fish/', 5)  # login as a primary investigator for this case
        self._check_url('/cases/fish/', 3)  # login as a secondary investigator for this case
        self._check_url('/cases/fish/', 4)  # login as a primary QA for this case
        self._check_url('/cases/fish/', 2)  # login as a secondary QA for this case
        self._check_url('/cases/fish/', 28)  # login as a requester for this case

    def test_view_private_case(self):
        self._check_url('/cases/cat/', None, 401)  # not logged in
        self._check_url('/cases/cat/', 1)  # login as admin
        self._check_url('/cases/cat/', 19, 403)  # login as a case manager
        self._check_url('/cases/cat/', 11, 403)  # login as an investigator
        self._check_url('/cases/cat/', 7, 403)  # login as a QA
        self._check_url('/cases/cat/', 28, 403)  # login as a requester
        self._check_url('/cases/cat/', 17)  # login as a primary case manager for this case
        self._check_url('/cases/cat/', 18)  # login as a secondary case manager for this case
        self._check_url('/cases/cat/', 3)  # login as a primary investigator for this case
        self._check_url('/cases/cat/', 4)  # login as a primary QA for this case
        self._check_url('/cases/cat/', 2)  # login as a secondary QA for this case
        self._check_url('/cases/cat/', 27)  # login as a requester for this case

    def test_add_case(self):
        self._check_url('/cases/add/', None, 401)  # not logged in
        self._check_url('/cases/add/', 1)  # login as admin
        self._check_url('/cases/add/', 19)  # login as a case manager
        self._check_url('/cases/add/', 11, 403)  # login as an investigator
        self._check_url('/cases/add/', 7, 403)  # login as a QA
        self._check_url('/cases/add/', 33)  # login as a requester

    def test_edit_case(self):
        self._check_url('/cases/edit/test_doesnt_exist/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/edit/fish/', None, 401)  # not logged in
        self._check_url('/cases/edit/fish/', 1)  # login as admin
        self._check_url('/cases/edit/fish/', 19, 403)  # login as a case manager
        self._check_url('/cases/edit/fish/', 11, 403)  # login as an investigator
        self._check_url('/cases/edit/fish/', 7, 403)  # login as a QA
        self._check_url('/cases/edit/fish/', 33, 403)  # login as a requester
        self._check_url('/cases/edit/fish/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/edit/fish/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/edit/fish/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/edit/fish/', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/edit/fish/', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/edit/fish/', 28, 403)  # login as a requester for this case

    def test_close_case(self):
        self._check_url('/cases/close/test_doesnt_exist/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/close/fish/', None, 401)  # not logged in
        self._check_url('/cases/close/fish/', 1)  # login as admin
        self._check_url('/cases/close/fish/', 19, 403)  # login as a case manager
        self._check_url('/cases/close/fish/', 11, 403)  # login as an investigator
        self._check_url('/cases/close/fish/', 7, 403)  # login as a QA
        self._check_url('/cases/close/fish/', 33, 403)  # login as a requester
        self._check_url('/cases/close/fish/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/close/fish/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/close/fish/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/close/fish/', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/close/fish/', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/close/fish/', 28, 403)  # login as a requester for this case

    def test_change_status_case(self):
        self._check_url('/cases/change_status/test_doesnt_exist/?status=Closed', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/change_status/fish/', 1, 404)  # login as admin, but no actual status change
        self._check_url('/cases/change_status/fish/?status=Testing', 1, 404)  # login as admin, but wrong type of status
        self._check_url('/cases/change_status/fish/?status=Closed', None, 401)  # not logged in
        self._check_url('/cases/change_status/fish/?status=Closed', 1)  # login as admin
        self._check_url('/cases/change_status/fish/?status=Closed', 19, 403)  # login as a case manager
        self._check_url('/cases/change_status/fish/?status=Closed', 11, 403)  # login as an investigator
        self._check_url('/cases/change_status/fish/?status=Closed', 7, 403)  # login as a QA
        self._check_url('/cases/change_status/fish/?status=Closed', 33, 403)  # login as a requester
        self._check_url('/cases/change_status/fish/?status=Closed', 18)  # login as a primary case manager for this case
        self._check_url('/cases/change_status/fish/?status=Closed', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/change_status/fish/?status=Closed', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/change_status/fish/?status=Closed', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/change_status/fish/?status=Closed', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/change_status/fish/?status=Closed', 28, 403)  # login as a requester for this case