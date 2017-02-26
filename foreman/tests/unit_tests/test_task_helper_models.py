from datetime import datetime
from werkzeug.exceptions import InternalServerError
# local imports
import base_tester
from foreman.model import User, ForemanOptions, TaskStatus, TaskUpload, TaskNotes, TaskHistory, TaskType, TaskCategory
from foreman.utils.utils import session


class ModelTestTaskBase(base_tester.UnitTestCase):
    pass


class TaskStatusTestCase(ModelTestTaskBase):
    pass


class TaskUploadTestCase(ModelTestTaskBase):
    pass


class TaskNotesTestCase(ModelTestTaskBase):
    pass


class TaskHistoryTestCase(ModelTestTaskBase):
    pass


class TaskTypeTestCase(ModelTestTaskBase):
    pass


class TaskCategoryTestCase(ModelTestTaskBase):
    pass

