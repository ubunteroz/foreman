#!/usr/bin/env python
import sys
from os import path

sys.path.append(path.dirname(__file__))

def make_app():
    from foreman.utils.utils import setUp
    setUp()

    from foreman.application import make_app
    return make_app()

application = make_app()
