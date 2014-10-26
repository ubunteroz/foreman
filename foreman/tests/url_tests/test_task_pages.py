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
        self._check_url('/cases/fish/test/assign_me/?assign=primary', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/fish/fish_01/assign_me/', 1, 404)  # login as admin, but no assignment
        self._check_url('/cases/fish/fish_01/assign_me/?assign=testing', 1, 404)  # login as admin, but no wrong assignment
        self._check_url('/cases/fish/fish_04/assign_me/?assign=primary', 1, 404)  # login as admin, but no assignment left
        self._check_url('/cases/fish/fish_04/assign_me/?assign=secondary', 1, 404)  # login as admin, but no assignment left
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', None, 401)  # not logged in
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', 1)  # login as admin
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', 19, 403)  # login as a case manager
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', 11)  # login as an investigator
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', 7)  # login as a QA
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', 33, 403)  # login as a requester
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', 18, 403)  # login as a primary case manager for this case
        self._check_url('/cases/fish/fish_01/assign_me/?assign=primary', 28, 403)  # login as a requester for this case

    def test_assign_other_to_tasks(self):
        self._check_url('/cases/fish/test/assign/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/fish/fish_04/assign/', 1, 404)  # login as admin, but no assignment left
        self._check_url('/cases/fish/fish_01/assign/', None, 401)  # not logged in
        self._check_url('/cases/fish/fish_01/assign/', 1)  # login as admin
        self._check_url('/cases/fish/fish_01/assign/', 19, 403)  # login as a case manager
        self._check_url('/cases/fish/fish_01/assign/', 11, 403)  # login as an investigator
        self._check_url('/cases/fish/fish_01/assign/', 7, 403)  # login as a QA
        self._check_url('/cases/fish/fish_01/assign/', 33, 403)  # login as a requester
        self._check_url('/cases/fish/fish_01/assign/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/fish/fish_01/assign/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/fish/fish_01/assign/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/fish/fish_01/assign/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/fish/fish_01/assign/', 28, 403)  # login as a requester for this case

    def test_view_task(self):
        self._check_url('/cases/fish/test/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/fish/fish_04/', None, 401)  # not logged in
        self._check_url('/cases/fish/fish_04/', 1)  # login as admin
        self._check_url('/cases/fish/fish_04/', 19)  # login as a case manager
        self._check_url('/cases/fish/fish_04/', 11)  # login as an investigator
        self._check_url('/cases/fish/fish_04/', 7)  # login as a QA
        self._check_url('/cases/fish/fish_04/', 33, 403)  # login as a requester
        self._check_url('/cases/fish/fish_04/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/fish/fish_04/', 5)  # login as a primary investigator for this case
        self._check_url('/cases/fish/fish_04/', 3)  # login as a secondary investigator for this case
        self._check_url('/cases/fish/fish_04/', 2)  # login as a primary QA for this case
        self._check_url('/cases/fish/fish_04/', 28)  # login as a requester for this case

    def test_view_private_task(self):
        self._check_url('/cases/cat/cat_04/', None, 401)  # not logged in
        self._check_url('/cases/cat/cat_04/', 1)  # login as admin
        self._check_url('/cases/cat/cat_04/', 19, 403)  # login as a case manager
        self._check_url('/cases/cat/cat_04/', 11, 403)  # login as an investigator
        self._check_url('/cases/cat/cat_04/', 7, 403)  # login as a QA
        self._check_url('/cases/cat/cat_04/', 28, 403)  # login as a requester
        self._check_url('/cases/cat/cat_04/', 17)  # login as a primary case manager for this case
        self._check_url('/cases/cat/cat_04/', 18)  # login as a secondary case manager for this case
        self._check_url('/cases/cat/cat_04/', 3)  # login as a primary investigator for this case
        self._check_url('/cases/cat/cat_04/', 4)  # login as a primary QA for this case
        self._check_url('/cases/cat/cat_04/', 2)  # login as a secondary QA for this case
        self._check_url('/cases/cat/cat_04/', 27)  # login as a requester for this case

    def test_add_task(self):
        self._check_url('/cases/fish/tasks/add/', None, 401)  # not logged in
        self._check_url('/cases/fish/tasks/add/', 1)  # login as admin
        self._check_url('/cases/fish/tasks/add/', 19, 403)  # login as a case manager
        self._check_url('/cases/fish/tasks/add/', 11, 403)  # login as an investigator
        self._check_url('/cases/fish/tasks/add/', 7, 403)  # login as a QA
        self._check_url('/cases/fish/tasks/add/', 33, 403)  # login as a requester
        self._check_url('/cases/fish/tasks/add/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/fish/tasks/add/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/fish/tasks/add/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/fish/tasks/add/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/fish/tasks/add/', 28)  # login as a requester for this case

    def test_edit_task(self):
        self._check_url('/cases/fish/test/edit/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/fish/fish_04/edit/', None, 401)  # not logged in
        self._check_url('/cases/fish/fish_04/edit/', 1)  # login as admin
        self._check_url('/cases/fish/fish_04/edit/', 19, 403)  # login as a case manager
        self._check_url('/cases/fish/fish_04/edit/', 11, 403)  # login as an investigator
        self._check_url('/cases/fish/fish_04/edit/', 7, 403)  # login as a QA
        self._check_url('/cases/fish/fish_04/edit/', 33, 403)  # login as a requester
        self._check_url('/cases/fish/fish_04/edit/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/fish/fish_04/edit/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/fish/fish_04/edit/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/fish/fish_04/edit/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/fish/fish_04/edit/', 28, 403)  # login as a requester for this case

    def test_close_task(self):
        self._check_url('/cases/fish/test_doesnt_exist/close/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/fish/fish_04/close/', None, 401)  # not logged in
        self._check_url('/cases/fish/fish_04/close/', 1)  # login as admin
        self._check_url('/cases/fish/fish_04/close/', 19, 403)  # login as a case manager
        self._check_url('/cases/fish/fish_04/close/', 11, 403)  # login as an investigator
        self._check_url('/cases/fish/fish_04/close/', 7, 403)  # login as a QA
        self._check_url('/cases/fish/fish_04/close/', 33, 403)  # login as a requester
        self._check_url('/cases/fish/fish_04/close/', 18)  # login as a primary case manager for this case
        self._check_url('/cases/fish/fish_04/close/', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/fish/fish_04/close/', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/fish/fish_04/close/', 2, 403)  # login as a primary QA for this case
        self._check_url('/cases/fish/fish_04/close/', 28, 403)  # login as a requester for this case

    def test_change_status_task(self):
        self._check_url('/cases/fish/test_doesnt_exist/change_status/?status=Closed', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/fish/fish_04/change_status/', 1, 404)  # login as admin, but no actual status change
        self._check_url('/cases/fish/fish_04/change_status/?status=Testing', 1, 404)  # login as admin, but wrong type of status
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', None, 401)  # not logged in
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 1)  # login as admin
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 19, 403)  # login as a case manager
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 11, 403)  # login as an investigator
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 7, 403)  # login as a QA
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 33, 403)  # login as a requester
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 18)  # login as a primary case manager for this case
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 5, 403)  # login as a primary investigator for this case
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 3, 403)  # login as a secondary investigator for this case
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 4, 403)  # login as a primary QA for this case
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 2, 403)  # login as a secondary QA for this case
        self._check_url('/cases/fish/fish_04/change_status/?status=Closed', 28, 403)  # login as a requester for this case

    def test_change_all_statuses_task(self):
        self._check_url('/cases/testing/change_statuses/?status=Queued', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/mouse/change_statuses/', 1, 404)  # login as admin, but no actual status change
        self._check_url('/cases/mouse/change_statuses/?status=Testing', 1, 404)  # login as admin, but wrong type of status
        self._check_url('/cases/fish/change_statuses/?status=Queued', 1, 404)  # login as admin, but cannot work for this case
        self._check_url('/cases/mouse/change_statuses/?status=Queued', None, 401)  # not logged in
        self._check_url('/cases/mouse/change_statuses/?status=Queued', 1)  # login as admin
        self._check_url('/cases/mouse/change_statuses/?status=Queued', 19, 403)  # login as a case manager
        self._check_url('/cases/mouse/change_statuses/?status=Queued', 11, 403)  # login as an investigator
        self._check_url('/cases/mouse/change_statuses/?status=Queued', 7, 403)  # login as a QA
        self._check_url('/cases/mouse/change_statuses/?status=Queued', 33, 403)  # login as a requester
        self._check_url('/cases/mouse/change_statuses/?status=Queued', 26)  # login as a primary case manager for this case
        self._check_url('/cases/mouse/change_statuses/?status=Queued', 36, 403)  # login as a requester for this case