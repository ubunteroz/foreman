"""
Tests to check that all pages work as expected with a 200 status code and not 404 or 500 for example.
"""

# local imports
from base_tester import URLTestCase


class ReportingTestCase(URLTestCase):

    def test_report_url(self):
        self._check_url('/reporting/', None, 401)  # not logged in
        self._check_url('/reporting/', 1)  # login as admin
        self._check_url('/reporting/', 19)  # login as a case manager
        self._check_url('/reporting/', 11, 403)  # login as an investigator
        self._check_url('/reporting/', 7, 403)  # login as a QA
        self._check_url('/reporting/', 33, 403)  # login as a requester

    def test_json_tasks_assigned_to_inv_url(self):
        self._check_url('/json/jason_tasks_assigned_to_inv/?start_date=October 2014', None, 401)  # not logged in
        self._check_url('/json/jason_tasks_assigned_to_inv/?start_date=October 2014', 1)  # login as admin
        self._check_url('/json/jason_tasks_assigned_to_inv/?start_date=October 2014', 19)  # login as a case manager
        self._check_url('/json/jason_tasks_assigned_to_inv/?start_date=October 2014', 11, 403)  # login as an investigator
        self._check_url('/json/jason_tasks_assigned_to_inv/?start_date=October 2014', 7, 403)  # login as a QA
        self._check_url('/json/jason_tasks_assigned_to_inv/?start_date=October 2014', 33, 403)  # login as a requester

    def test_json_tasks_qaed_url(self):
        self._check_url('/json/jason_tasks_qaed/?start_date=October 2014', None, 401)  # not logged in
        self._check_url('/json/jason_tasks_qaed/?start_date=October 2014', 1)  # login as admin
        self._check_url('/json/jason_tasks_qaed/?start_date=October 2014', 19)  # login as a case manager
        self._check_url('/json/jason_tasks_qaed/?start_date=October 2014', 11, 403)  # login as an investigator
        self._check_url('/json/jason_tasks_qaed/?start_date=October 2014', 7, 403)  # login as a QA
        self._check_url('/json/jason_tasks_qaed/?start_date=October 2014', 33, 403)  # login as a requester
