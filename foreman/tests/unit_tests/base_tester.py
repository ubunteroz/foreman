# python imports
import unittest
from mock import MagicMock


class UnitTestCase(unittest.TestCase):
    original_class = None

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def mock_storage(self, filename, *args, **kwargs):
        spec = ['__iter__', 'filename'] + [arg for arg in args]
        return MagicMock(spec=spec, filename=filename, **kwargs)