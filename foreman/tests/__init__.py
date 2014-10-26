"""
This is where all the unit and functional tests are kept.
"""

import unittest
from ..utils.utils import setup

test_units = [
    'unit_tests.test_validators',
    'unit_tests.test_forms',
]

test_functions = [
    'functional_tests.test_baseController',
    'functional_tests.test_caseController',
    'functional_tests.test_generalController',
    'functional_tests.test_evidenceController',
    'functional_tests.test_forensicsController',
    'functional_tests.test_reportController',
    'functional_tests.test_taskController',
    'functional_tests.test_userController',
]

test_urls = [
    'url_tests.test_static_pages',
    'url_tests.test_case_pages',
    'url_tests.test_task_pages',
    'url_tests.test_user_pages',
    'url_tests.test_forensics_pages',
]


def get_suite_from_module(name):
    return unittest.defaultTestLoader.loadTestsFromName('%s.%s' % (__name__, name))


def build_app_suite(list_name):
    suite = unittest.TestSuite()
    for name in list_name:
        suite.addTest(get_suite_from_module(name))
    return suite


# This is for launch.py to run
def run_tests(config_file, unit_tests=True, functional_tests=True, url_tests=True):
    setup(config_file)

    if unit_tests:
        print "\n\n~~ Running Unit Tests ~~\n\n"
        pass
        #suite_unit_tests = build_app_suite(test_units)
        #unittest.TextTestRunner(verbosity=2).run(suite_unit_tests)

    if functional_tests:
        print "\n\n~~ Running Functional Tests ~~\n\n"
        pass
        #suite_functional_tests = build_app_suite(test_functions)
        #unittest.TextTestRunner(verbosity=2).run(suite_functional_tests)

    if url_tests:
        print "\n\n~~ Running URL Tests ~~\n\n"
        suite_url_tests = build_app_suite(test_urls)
        unittest.TextTestRunner(verbosity=2).run(suite_url_tests)
