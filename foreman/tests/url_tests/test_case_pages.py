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
        self._check_url('/cases/', 33)  # login as a requester
        self._check_url('/cases/', 37)  # login as an authoriser

    def test_view_case(self):
        self._check_url('/cases/test_doesnt_exist/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/', None, 401)  # not logged in
        self._check_url('/cases/2/', 1)  # login as admin
        self._check_url('/cases/2/', 19)  # login as a case manager
        self._check_url('/cases/2/', 11)  # login as an investigator
        self._check_url('/cases/2/', 7)  # login as a QA
        self._check_url('/cases/2/', 33, 403)  # login as a requester
        self._check_url('/cases/2/', 39, 403)  # login as an authoriser
        self._check_url('/cases/2/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/', 5)  # login as a primary investigator for this case
        self._check_url('/cases/2/', 3)  # login as a secondary investigator for this case
        self._check_url('/cases/2/', 4)  # login as a primary QA for this case
        self._check_url('/cases/2/', 2)  # login as a secondary QA for this case
        self._check_url('/cases/2/', 28)  # login as a requester for this case
        self._check_url('/cases/2/', 38)  # login as a authoriser for this case

    def test_view_private_case(self):
        self._check_url('/cases/1/', None, 401)  # not logged in
        self._check_url('/cases/1/', 1)  # login as admin
        self._check_url('/cases/1/', 19, 403)  # login as a case manager
        self._check_url('/cases/1/', 11, 403)  # login as an investigator
        self._check_url('/cases/1/', 7, 403)  # login as a QA
        self._check_url('/cases/1/', 28, 403)  # login as a requester
        self._check_url('/cases/1/', 38, 403)  # login as an authoriser
        self._check_url('/cases/1/', 17)  # login as a primary case manager for this case
        self._check_url('/cases/1/', 18)  # login as a secondary case manager for this case
        self._check_url('/cases/1/', 3)  # login as a primary investigator for this case
        self._check_url('/cases/1/', 4)  # login as a primary QA for this case
        self._check_url('/cases/1/', 2)  # login as a secondary QA for this case
        self._check_url('/cases/1/', 27)  # login as a requester for this case
        self._check_url('/cases/1/', 37)  # login as an authoriser for this case

    def test_add_case(self):
        self._check_url('/cases/add/', None, 401)  # not logged in
        self._check_url('/cases/add/', 1)  # login as admin
        self._check_url('/cases/add/', 19)  # login as a case manager
        self._check_url('/cases/add/', 11, 403)  # login as an investigator
        self._check_url('/cases/add/', 7, 403)  # login as a QA
        self._check_url('/cases/add/', 33)  # login as a requester
        self._check_url('/cases/add/', 39, 403)  # login as an authoriser

    def test_edit_case(self):
        self._check_url('/cases/edit/test_doesnt_exist/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/edit/2/', None, 401)  # not logged in
        self._check_url('/cases/edit/2/', 1)  # login as admin
        self._check_url('/cases/edit/2/', 19, 403)  # login as a case manager
        self._check_url('/cases/edit/2/', 11, 403)  # login as an investigator
        self._check_url('/cases/edit/2/', 7, 403)  # login as a QA
        self._check_url('/cases/edit/2/', 33, 403)  # login as a requester
        self._check_url('/cases/edit/2/', 39, 403)  # login as an authoriser
        self._check_url('/cases/edit/2/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/edit/2/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/edit/2/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/edit/2/', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/edit/2/', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/edit/2/', 28)  # login as a requester for this case
        self._check_url('/cases/edit/2/', 38, 403)  # login as an authoriser for this case

    def test_close_case(self):
        self._check_url('/cases/close/test_doesnt_exist/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/close/2/', None, 401)  # not logged in
        self._check_url('/cases/close/2/', 1)  # login as admin
        self._check_url('/cases/close/2/', 19, 403)  # login as a case manager
        self._check_url('/cases/close/2/', 11, 403)  # login as an investigator
        self._check_url('/cases/close/2/', 7, 403)  # login as a QA
        self._check_url('/cases/close/2/', 33, 403)  # login as a requester
        self._check_url('/cases/close/2/', 39, 403)  # login as an authoriser
        self._check_url('/cases/close/2/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/close/2/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/close/2/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/close/2/', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/close/2/', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/close/2/', 28, 403)  # login as a requester for this case
        self._check_url('/cases/close/2/', 38, 403)  # login as an authoriser for this case

    def test_change_status_case(self):
        self._check_url('/cases/change_status/test_doesnt_exist/?status=Closed', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/change_status/2/', 1, 404)  # login as admin, but no actual status change
        self._check_url('/cases/change_status/2/?status=Testing', 1, 404)  # login as admin, but wrong type of status
        self._check_url('/cases/change_status/2/?status=Closed', None, 401)  # not logged in
        self._check_url('/cases/change_status/2/?status=Closed', 1)  # login as admin
        self._check_url('/cases/change_status/2/?status=Closed', 19, 403)  # login as a case manager
        self._check_url('/cases/change_status/2/?status=Closed', 11, 403)  # login as an investigator
        self._check_url('/cases/change_status/2/?status=Closed', 7, 403)  # login as a QA
        self._check_url('/cases/change_status/2/?status=Closed', 33, 403)  # login as a requester
        self._check_url('/cases/change_status/2/?status=Closed', 39, 403)  # login as an authoriser
        self._check_url('/cases/change_status/2/?status=Closed', 18)  # login as a primary case manager for this case
        self._check_url('/cases/change_status/2/?status=Closed', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/change_status/2/?status=Closed', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/change_status/2/?status=Closed', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/change_status/2/?status=Closed', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/change_status/2/?status=Closed', 28)  # login as a requester for this case
        self._check_url('/cases/change_status/2/?status=Closed', 38, 403)  # login as an authoriser for this case

    def test_view_upload_file(self):
        # all those who can view cases can view case file uploads
        self._check_url('/cases/3/uploads/1/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/test/uploads/1/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/uploads/4/', 1, 404)  # login as admin, but wrong upload
        self._check_url('/cases/2/uploads/test/', 1, 404)  # login as admin, but wrong upload
        self._check_url('/cases/2/uploads/1/', None, 401)  # not logged in
        self._check_url('/cases/2/uploads/1/', 1)  # login as admin
        self._check_url('/cases/2/uploads/1/', 19)  # login as a case manager
        self._check_url('/cases/2/uploads/1/', 11)  # login as an investigator
        self._check_url('/cases/2/uploads/1/', 7)  # login as a QA
        self._check_url('/cases/2/uploads/1/', 33, 403)  # login as a requester
        self._check_url('/cases/2/uploads/1/', 39, 403)  # login as an authoriser
        self._check_url('/cases/2/uploads/1/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/uploads/1/', 5)  # login as a primary investigator for this case
        self._check_url('/cases/2/uploads/1/', 3)  # login as a secondary investigator for this case
        self._check_url('/cases/2/uploads/1/', 4)  # login as a primary QA for this case
        self._check_url('/cases/2/uploads/1/', 2)  # login as a secondary QA for this case
        self._check_url('/cases/2/uploads/1/', 28)  # login as a requester for this case
        self._check_url('/cases/2/uploads/1/', 38)  # login as an authoriser for this case

    def test_delete_upload_file(self):
        # only admins, the requester and case manager of the case can delete files
        self._check_url('/cases/3/uploads/1/delete/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/test/uploads/1/delete/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/uploads/4/delete/', 1, 404)  # login as admin, but wrong upload
        self._check_url('/cases/2/uploads/test/delete/', 1, 404)  # login as admin, but wrong upload
        self._check_url('/cases/2/uploads/1/delete/', None, 401)  # not logged in
        self._check_url('/cases/2/uploads/1/delete/', 1)  # login as admin
        self._check_url('/cases/2/uploads/1/delete/', 19, 403)  # login as a case manager
        self._check_url('/cases/2/uploads/1/delete/', 11, 403)  # login as an investigator
        self._check_url('/cases/2/uploads/1/delete/', 7, 403)  # login as a QA
        self._check_url('/cases/2/uploads/1/delete/', 33, 403)  # login as a requester
        self._check_url('/cases/2/uploads/1/delete/', 39, 403)  # login as an authoriser
        self._check_url('/cases/2/uploads/1/delete/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/uploads/1/delete/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/2/uploads/1/delete/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/2/uploads/1/delete/', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/2/uploads/1/delete/', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/2/uploads/1/delete/', 28)  # login as a requester for this case
        self._check_url('/cases/2/uploads/1/delete/', 38, 403)  # login as an authoriser for this case

    def test_authorise_case(self):
        self._check_url('/cases/authorise/test_doesnt_exist/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/authorise/12/', None, 401)  # not logged in
        self._check_url('/cases/authorise/12/', 1, 403)  # login as admin
        self._check_url('/cases/authorise/12/', 19, 403)  # login as a case manager
        self._check_url('/cases/authorise/12/', 11, 403)  # login as an investigator
        self._check_url('/cases/authorise/12/', 7, 403)  # login as a QA
        self._check_url('/cases/authorise/12/', 33, 403)  # login as a requester
        self._check_url('/cases/authorise/12/', 37, 403)  # login as an authoriser
        self._check_url('/cases/authorise/12/', 18, 403)  # login as a primary case manager for this case
        self._check_url('/cases/authorise/12/', 39)  # login as an authoriser for this case

        # case not pending, aka already auth/denied
        self._check_url('/cases/authorise/6/', 39, 403)  # login as an authoriser for this case