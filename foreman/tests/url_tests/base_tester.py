# python imports
import unittest
import random
import string

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from foreman.application import make_app
from foreman.model import User, UserRoles


class MockSession(dict):

    def __init__(self, sid):
        self.sid = sid

    def should_save(self):
        return True


class MockSessionStore(object):

    def __init__(self):
        sid = 'testsid'
        self.session = MockSession(sid)

    def get(self, id):
        return self.session

    def new(self):
        return self.session

    def save(self, session):
        pass


class URLTestCase(unittest.TestCase):

    client = None
    resp = None

    def setUp(self):
        self.session_store = MockSessionStore()
        app = make_app(self.session_store)
        self.client = Client(app, BaseResponse, use_cookies=True)

    def tearDown(self):
        pass

    def _check_url(self, url_to_test, user_id, expected_code=200):

        if user_id is not None:
            self.login_user(user_id)
        self.resp = self.client.get(url_to_test)
        self.assertEqual(self.resp.status_code, expected_code)
        if user_id is not None:
            self.logout_user()

    def login_user(self, user_id):
        self.session_store.session['userid'] = user_id

    def logout_user(self):
        if 'userid' in self.session_store.session:
            del self.session_store.session['userid']





















