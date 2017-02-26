from datetime import datetime
from werkzeug.exceptions import InternalServerError
# local imports
import base_tester
from foreman.model import User, ForemanOptions, UserRoles, UserRolesHistory, UserCaseRoles, UserCaseRolesHistory,\
    UserTaskRoles, UserTaskRolesHistory
from foreman.utils.utils import session


class ModelTestRoleBase(base_tester.UnitTestCase):
    pass


class UserRolesTestCase(ModelTestRoleBase):
    pass


class UserRolesHistoryTestCase(ModelTestRoleBase):
    pass


class UserCaseRolesTestCase(ModelTestRoleBase):
    pass


class UserCaseRolesHistoryTestCase(ModelTestRoleBase):
    pass


class UserTaskRolesTestCase(ModelTestRoleBase):
    pass


class UserTaskRolesHistoryTestCase(ModelTestRoleBase):
    pass
