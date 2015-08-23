"""
Tests to check that all pages work as expected with a 200 status code and not 404 or 500 for example.
"""

# local imports
from base_tester import URLTestCase


class ForensicsTestCase(URLTestCase):

    def test_work_on_task(self):
        self._check_url('/cases/2/test_doesnt_exist/notes/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/6/23/notes/', None, 401)  # not logged in
        self._check_url('/cases/6/23/notes/', 1)  # login as admin
        self._check_url('/cases/6/23/notes/', 19, 403)  # login as a case manager
        self._check_url('/cases/6/23/notes/', 11, 403)  # login as an investigator
        self._check_url('/cases/6/23/notes/', 7, 403)  # login as a QA
        self._check_url('/cases/6/23/notes/', 33, 403)  # login as a requester
        self._check_url('/cases/6/23/notes/', 22, 403)  # login as a primary case manager for this case
        self._check_url('/cases/6/23/notes/', 4)  # login as a primary investigator for this case
        self._check_url('/cases/6/23/notes/', 5, 403)  # login as a primary QA for this case
        self._check_url('/cases/6/23/notes/', 32, 403)  # login as a requester for this case
        self._check_url('/cases/6/24/notes/', 4, 403)  # login as a primary investigator for this case

    def test_qa_work(self):
        self._check_url('/cases/2/test_doesnt_exist/qa/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/8/qa/', None, 401)  # not logged in
        self._check_url('/cases/2/8/qa/', 1)  # login as admin
        self._check_url('/cases/2/8/qa/', 19, 403)  # login as a case manager
        self._check_url('/cases/2/8/qa/', 11, 403)  # login as an investigator
        self._check_url('/cases/2/8/qa/', 7, 403)  # login as a QA
        self._check_url('/cases/2/8/qa/', 33, 403)  # login as a requester
        self._check_url('/cases/2/8/qa/', 18, 403)  # login as a primary case manager for this case
        self._check_url('/cases/2/8/qa/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/2/8/qa/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/2/8/qa/', 2)  # login as a primary QA for this case
        self._check_url('/cases/2/8/qa/', 28, 403)  # login as a requester for this case