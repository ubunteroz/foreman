"""
Tests to check that all pages work as expected with a 200 status code and not 404 or 500 for example.
"""

# local imports
from base_tester import URLTestCase


class TaskTestCase(URLTestCase):

    def test_view_all_tasks(self):
        self._check_url('/tasks/', None, 401)  # not logged in
        self._check_url('/tasks/', 1)  # login as admin
        self._check_url('/tasks/', 19)  # login as a case manager
        self._check_url('/tasks/', 1)  # login as an investigator
        self._check_url('/tasks/', 7)  # login as a QA
        self._check_url('/tasks/', 33, 403)  # login as a requester

    def test_view_qas(self):
        self._check_url('/tasks/qa/', None, 401)  # not logged in
        self._check_url('/tasks/qa/', 1)  # login as admin
        self._check_url('/tasks/qa/', 19)  # login as a case manager
        self._check_url('/tasks/qa/', 1)  # login as an investigator
        self._check_url('/tasks/qa/', 7)  # login as a QA
        self._check_url('/tasks/qa/', 33, 403)  # login as a requester

    def test_assign_myself_to_task(self):
        self._check_url('/cases/2/test/assign_me/?assign=primary', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/5/assign_me/', 1, 404)  # login as admin, but no assignment
        self._check_url('/cases/2/5/assign_me/?assign=testing', 1, 404)  # login as admin, but no wrong assignment
        self._check_url('/cases/2/8/assign_me/?assign=primary', 1, 404)  # login as admin, but no assignment left
        self._check_url('/cases/2/8/assign_me/?assign=secondary', 1, 404)  # login as admin, but no assignment left
        self._check_url('/cases/2/5/assign_me/?assign=primary', None, 401)  # not logged in
        self._check_url('/cases/2/5/assign_me/?assign=primary', 1)  # login as admin
        self._check_url('/cases/2/5/assign_me/?assign=primary', 19, 403)  # login as a case manager
        self._check_url('/cases/2/5/assign_me/?assign=primary', 11)  # login as an investigator
        self._check_url('/cases/2/5/assign_me/?assign=primary', 7)  # login as a QA
        self._check_url('/cases/2/5/assign_me/?assign=primary', 33, 403)  # login as a requester
        self._check_url('/cases/2/5/assign_me/?assign=primary', 18, 403)  # login as a primary case manager for this case
        self._check_url('/cases/2/5/assign_me/?assign=primary', 28, 403)  # login as a requester for this case

    def test_assign_other_to_tasks(self):
        self._check_url('/cases/2/test/assign/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/8/assign/', 1, 404)  # login as admin, but no assignment left
        self._check_url('/cases/2/5/assign/', None, 401)  # not logged in
        self._check_url('/cases/2/5/assign/', 1)  # login as admin
        self._check_url('/cases/2/5/assign/', 19, 403)  # login as a case manager
        self._check_url('/cases/2/5/assign/', 11, 403)  # login as an investigator
        self._check_url('/cases/2/5/assign/', 7, 403)  # login as a QA
        self._check_url('/cases/2/5/assign/', 33, 403)  # login as a requester
        self._check_url('/cases/2/5/assign/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/5/assign/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/2/5/assign/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/2/5/assign/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/2/5/assign/', 28, 403)  # login as a requester for this case

    def test_view_task(self):
        self._check_url('/cases/2/test/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/8/', None, 401)  # not logged in
        self._check_url('/cases/2/8/', 1)  # login as admin
        self._check_url('/cases/2/8/', 19)  # login as a case manager
        self._check_url('/cases/2/8/', 11)  # login as an investigator
        self._check_url('/cases/2/8/', 7)  # login as a QA
        self._check_url('/cases/2/8/', 33, 403)  # login as a requester
        self._check_url('/cases/2/8/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/8/', 5)  # login as a primary investigator for this case
        self._check_url('/cases/2/8/', 3)  # login as a secondary investigator for this case
        self._check_url('/cases/2/8/', 2)  # login as a primary QA for this case
        self._check_url('/cases/2/8/', 28)  # login as a requester for this case

    def test_view_private_task(self):
        self._check_url('/cases/1/4/', None, 401)  # not logged in
        self._check_url('/cases/1/4/', 1)  # login as admin
        self._check_url('/cases/1/4/', 19, 403)  # login as a case manager
        self._check_url('/cases/1/4/', 11, 403)  # login as an investigator
        self._check_url('/cases/1/4/', 7, 403)  # login as a QA
        self._check_url('/cases/1/4/', 28, 403)  # login as a requester
        self._check_url('/cases/1/4/', 17)  # login as a primary case manager for this case
        self._check_url('/cases/1/4/', 18)  # login as a secondary case manager for this case
        self._check_url('/cases/1/4/', 3)  # login as a primary investigator for this case
        self._check_url('/cases/1/4/', 4)  # login as a primary QA for this case
        self._check_url('/cases/1/4/', 2)  # login as a secondary QA for this case
        self._check_url('/cases/1/4/', 27)  # login as a requester for this case

    def test_add_task(self):
        self._check_url('/cases/2/tasks/add/', None, 401)  # not logged in
        self._check_url('/cases/2/tasks/add/', 1)  # login as admin
        self._check_url('/cases/2/tasks/add/', 19, 403)  # login as a case manager
        self._check_url('/cases/2/tasks/add/', 11, 403)  # login as an investigator
        self._check_url('/cases/2/tasks/add/', 7, 403)  # login as a QA
        self._check_url('/cases/2/tasks/add/', 33, 403)  # login as a requester
        self._check_url('/cases/2/tasks/add/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/tasks/add/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/2/tasks/add/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/2/tasks/add/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/2/tasks/add/', 28)  # login as a requester for this case

    def test_edit_task(self):
        self._check_url('/cases/2/test/edit/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/8/edit/', None, 401)  # not logged in
        self._check_url('/cases/2/8/edit/', 1)  # login as admin
        self._check_url('/cases/2/8/edit/', 19, 403)  # login as a case manager
        self._check_url('/cases/2/8/edit/', 11, 403)  # login as an investigator
        self._check_url('/cases/2/8/edit/', 7, 403)  # login as a QA
        self._check_url('/cases/2/8/edit/', 33, 403)  # login as a requester
        self._check_url('/cases/2/8/edit/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/8/edit/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/2/8/edit/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/2/8/edit/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/2/8/edit/', 28, 403)  # login as a requester for this case

    def test_close_task(self):
        self._check_url('/cases/2/test_doesnt_exist/close/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/8/close/', None, 401)  # not logged in
        self._check_url('/cases/2/8/close/', 1)  # login as admin
        self._check_url('/cases/2/8/close/', 19, 403)  # login as a case manager
        self._check_url('/cases/2/8/close/', 11, 403)  # login as an investigator
        self._check_url('/cases/2/8/close/', 7, 403)  # login as a QA
        self._check_url('/cases/2/8/close/', 33, 403)  # login as a requester
        self._check_url('/cases/2/8/close/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/8/close/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/2/8/close/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/2/8/close/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/2/8/close/', 28, 403)  # login as a requester for this case

    def test_change_status_task(self):
        self._check_url('/cases/2/test_doesnt_exist/change_status/?status=Closed', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/2/8/change_status/', 1, 404)  # login as admin, but no actual status change
        self._check_url('/cases/2/8/change_status/?status=Testing', 1, 404)  # login as admin, but wrong type of status
        self._check_url('/cases/2/8/change_status/?status=Closed', None, 401)  # not logged in
        self._check_url('/cases/2/8/change_status/?status=Closed', 1)  # login as admin
        self._check_url('/cases/2/8/change_status/?status=Closed', 19, 403)  # login as a case manager
        self._check_url('/cases/2/8/change_status/?status=Closed', 11, 403)  # login as an investigator
        self._check_url('/cases/2/8/change_status/?status=Closed', 7, 403)  # login as a QA
        self._check_url('/cases/2/8/change_status/?status=Closed', 33, 403)  # login as a requester
        self._check_url('/cases/2/8/change_status/?status=Closed', 18)  # login as a primary case manager for this case
        self._check_url('/cases/2/8/change_status/?status=Closed', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/2/8/change_status/?status=Closed', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/2/8/change_status/?status=Closed', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/2/8/change_status/?status=Closed', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/2/8/change_status/?status=Closed', 28, 403)  # login as a requester for this case

    def test_change_all_statuses_task(self):
        self._check_url('/cases/testing/change_statuses/?status=Queued', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/6/change_statuses/', 1, 404)  # login as admin, but no actual status change
        self._check_url('/cases/13/change_statuses/?status=Testing', 1, 404)  # login as admin, but wrong type of status
        self._check_url('/cases/2/change_statuses/?status=Queued', 1, 404)  # login as admin, but cannot work for this case
        self._check_url('/cases/6/change_statuses/?status=Queued', None, 401)  # not logged in
        self._check_url('/cases/6/change_statuses/?status=Queued', 1, 404)  # login as admin, but this cases tasks cannot be queued
        self._check_url('/cases/13/change_statuses/?status=Queued', 1)  # login as admin
        self._check_url('/cases/13/change_statuses/?status=Queued', 23, 403)  # login as a case manager
        self._check_url('/cases/13/change_statuses/?status=Queued', 11, 403)  # login as an investigator
        self._check_url('/cases/13/change_statuses/?status=Queued', 7, 403)  # login as a QA
        self._check_url('/cases/13/change_statuses/?status=Queued', 33, 403)  # login as a requester
        self._check_url('/cases/13/change_statuses/?status=Queued', 19)  # login as a primary case manager for this case
        self._check_url('/cases/13/change_statuses/?status=Queued', 29, 403)  # login as a requester for this case
