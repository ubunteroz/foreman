# python imports
from formencode import Invalid
from mock import patch

# local imports
import base_tester
from foreman.forms.forms import RegisterForm


class RegisterFormTestCase(base_tester.UnitTestCase):

    def make_input(self, **overrides):
        d = {'forename': "Foo",
             'middlename': None,
             'surname': "Bar",
             'username': "FooBar",
             'password': "pass",
             'password_2': "pass",
             'email': "foo@bar.com",
             'team' : "1"}
        d.update(overrides)
        return d

    def test_success(self):
        with patch('foreman.forms.validators.Team') as MockTeam:
            input = self.make_input()
            result = RegisterForm().to_python(input)
            self.assertEqual(result['forename'], 'Foo')
            self.assertEqual(result['middlename'], '')
            self.assertIs(result['team'], MockTeam.get.return_value)

    def test_password_mismatch(self):
        with patch('foreman.forms.validators.Team') as MockTeam:
            input = self.make_input(password_2="foo")

            with self.assertRaises(Invalid) as cm:
                result = RegisterForm().to_python(input)

            invalid = cm.exception
            self.assertIn('password', invalid.error_dict)
            self.assertIn('password_2', invalid.error_dict)
            self.assertEqual(len(invalid.error_dict), 2)

    def test_required_field(self):
        with patch('foreman.forms.validators.Team') as MockTeam:
            input = self.make_input(forename=None)

            with self.assertRaises(Invalid) as cm:
                result = RegisterForm().to_python(input)

            invalid = cm.exception
            self.assertIn('forename', invalid.error_dict)
            self.assertEqual(len(invalid.error_dict), 1)

    def test_bad_team(self):
        with patch('foreman.forms.validators.Team') as MockTeam:
            input = self.make_input(team="foo")

            with self.assertRaises(Invalid) as cm:
                result = RegisterForm().to_python(input)

            invalid = cm.exception
            self.assertIn('team', invalid.error_dict)
            self.assertEqual(len(invalid.error_dict), 1)

    def test_team_doesnt_exist(self):
        with patch('foreman.forms.validators.Team') as MockTeam:
            MockTeam.get.return_value = None
            input = self.make_input(team="2")

            with self.assertRaises(Invalid) as cm:
                result = RegisterForm().to_python(input)

            invalid = cm.exception
            self.assertIn('team', invalid.error_dict)
            self.assertEqual(len(invalid.error_dict), 1)
