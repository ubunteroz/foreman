from datetime import datetime
from werkzeug.exceptions import InternalServerError
# local imports
import base_tester
from foreman.model import User, ForemanOptions, Department, Team, UserMessage, UserHistory, TaskTimeSheets, CaseTimeSheets
from foreman.utils.utils import session


class ModelTestUserBase(base_tester.UnitTestCase):
    pass


class DepartmentTestCase(ModelTestUserBase):
    pass


class TeamTestCase(ModelTestUserBase):
    pass


class UserMessageTestCase(ModelTestUserBase):
    pass


class UserHistoryTestCase(ModelTestUserBase):
    pass


class TaskTimeSheetsTestCase(ModelTestUserBase):
    pass


class CaseTimeSheetsTestCase(ModelTestUserBase):
    pass
