# python imports
import unittest
from mock import patch, DEFAULT
# local imports
from foreman.forms.forms import *


class UnitTestCase(unittest.TestCase):
    original_class = None

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_schema(self):
        pass

    def _bad_field_tester(self, form, exception, **bad_field):
        input = self.make_input(**bad_field)
        with self.assertRaises(exception) as cm:
            result = form().to_python(input)
        invalid = cm.exception
        self.assertIn(bad_field.keys()[0], invalid.error_dict)
        self.assertEqual(len(invalid.error_dict), 1)