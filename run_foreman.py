#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys

from werkzeug.serving import run_simple


def make_app(config_file):
    import foreman.utils.utils
    foreman.utils.utils.setup(config_file)
    from foreman.application import make_app
    return make_app()


def runserver(args):
    """Start Foreman running under a simple development server."""
    app = make_app(args.config_file)
    run_simple(args.host, args.port, app, args.reloader, False)


def setup(args):
    """ Initialise database """
    from foreman.utils.utils import init_database, drop_database, load_initial_values, setup, create_admin_user
    setup(args.config_file)
    drop_database()
    init_database()
    load_initial_values()
    create_admin_user()


def example(args):
    """ Initialise database and set up an example system """
    from foreman.utils.utils import init_database, drop_database, populate_database, setup
    setup(args.config_file)
    drop_database()
    init_database()
    populate_database()

    
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

    setup_parser = subparsers.add_parser('setup_example', help='Initialise and populate database with sample data')
    setup_parser.add_argument('config_file')
    setup_parser.set_defaults(func=example)

    args = parser.parse_args()
    args.func(args)
