#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import warnings
from sqlalchemy import exc as sa_exc

from werkzeug.serving import run_simple


def make_app(config_file):
    import foreman.utils.utils
    foreman.utils.utils.setup(config_file)
    from foreman.application import make_app
    return make_app()


def runserver(args):
    """Start Foreman running under a simple development server."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        app = make_app(args.config_file)
        run_simple(args.host, args.port, app, args.reloader, False)


def setup(args):
    """ Initialise database """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)

        from foreman.utils.utils import init_database, drop_database, load_initial_values, setup, create_admin_user
        setup(args.config_file)
        drop_database()
        init_database()
        load_initial_values()
        create_admin_user()


def example(args):
    """ Initialise database and set up an example system """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        from foreman.utils.utils import init_database, drop_database, populate_database, setup
        setup(args.config_file)
        drop_database()
        init_database()
        populate_database()


def run_tests(args):
    """ Initialise database, set up example test system and run tests """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        from foreman.utils.utils import init_database, drop_database, populate_test_database, setup

        urls = False if args.test_urls == "False" else True
        unit = False if args.test_unit == "False" else True
        functional = False if args.test_func == "False" else True

        if urls is False and unit is False and functional is False:
            urls = unit = functional = True

        print "\n\n~~ Setting up Test Database ~~\n\n"

        setup(args.config_file)
        drop_database()
        init_database()
        populate_test_database()

        import foreman.tests
        foreman.tests.run_tests(args.config_file, unit, functional, urls)


def scheduler(args):
    """ run scheduled tasks e.g. the evidence retention period checker """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)

        import foreman.utils.utils
        foreman.utils.utils.setup(args.config_file)

        from foreman.utils.scheduled_tasks import scheduled
        for entry in scheduled:
            getattr(foreman.utils.scheduled_tasks, entry)()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()

    runserver_parser = subparsers.add_parser('runserver', help='Start Foreman using a simple development server')
    runserver_parser.add_argument('--host', default='localhost')
    runserver_parser.add_argument('--port', type=int, default=5000)
    runserver_parser.add_argument('--reloader', action='store_true')
    runserver_parser.add_argument('config_file')
    runserver_parser.set_defaults(func=runserver)

    setup_parser = subparsers.add_parser('setup', help='Initialise database')
    setup_parser.add_argument('config_file')
    setup_parser.set_defaults(func=setup)

    setup_ex_parser = subparsers.add_parser('setup_example', help='Initialise and populate database with sample data')
    setup_ex_parser.add_argument('config_file')
    setup_ex_parser.set_defaults(func=example)

    scheduled_tasks = subparsers.add_parser('scheduled_tasks', help='Run this in a CRON job / task scheduler')
    scheduled_tasks.add_argument('config_file')
    scheduled_tasks.set_defaults(func=scheduler)

    test_parser = subparsers.add_parser('run_tests', help='Run functional & unit tests',
                                        description='If all the optional test arguments are False, they will all be run.')
    test_parser.add_argument('--test_urls', default='False', help='Test the foreman URLs. Default: False. Set TEST_URLS to True')
    test_parser.add_argument('--test_unit', default='False', help='Run Unit Tests. Default: False. Set TEST_UNIT to True')
    test_parser.add_argument('--test_func', default='False', help='Run Functional. Default: False. Set TEST_FUNC to True')
    test_parser.add_argument('config_file')
    test_parser.set_defaults(func=run_tests)

    args = parser.parse_args()
    args.func(args)
