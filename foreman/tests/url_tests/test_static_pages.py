"""
Tests to check that all pages work as expected with a 200 status code and not 404 or 500 for example.
"""

# local imports
from base_tester import URLTestCase


class IndexTestCase(URLTestCase):

    def test_url(self):
        self._check_url('/', None, 401)  # not logged in
        self._check_url('/', 1)  # login as admin
        self._check_url('/', 19)  # login as a case manager
        self._check_url('/', 11)  # login as an investigator
        self._check_url('/', 7)  # login as a QA
        self._check_url('/', 33)  # login as a requester


class LoginTestCase(URLTestCase):

    def test_url(self):
        self._check_url('/login/', None, 401)


class RegisterTestCase(URLTestCase):

    def test_url(self):
        self._check_url('/register/', None)


class LogoutTestCase(URLTestCase):

    def test_url(self):
        self._check_url('/logout/', None, 401)  # not logged in
        self._check_url('/logout/', 1)  # login as admin
        self._check_url('/logout/', 19)  # login as a case manager
        self._check_url('/logout/', 11)  # login as an investigator
        self._check_url('/logout/', 7)  # login as a QA
        self._check_url('/logout/', 33)  # login as a requester


class AdminTestCase(URLTestCase):

    def test_url(self):
        self._check_url('/admin/', None, 401)  # not logged in
        self._check_url('/admin/', 1)  # login as admin
        self._check_url('/admin/', 19, 403)  # login as a case manager
        self._check_url('/admin/', 11, 403)  # login as an investigator
        self._check_url('/admin/', 7, 403)  # login as a QA
        self._check_url('/admin/', 33, 403)  # login as a requester
