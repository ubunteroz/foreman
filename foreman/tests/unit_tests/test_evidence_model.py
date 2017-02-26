from datetime import datetime, timedelta
# local imports
import base_tester
from foreman.model import User, ForemanOptions
from foreman.utils.utils import session


class ModelTestEvidenceBase(base_tester.UnitTestCase):
    current_user = None
    now = datetime.now()


class EvidenceWriteTestCase(ModelTestEvidenceBase):
    pass


class EvidenceReadTestCase(ModelTestEvidenceBase):
    pass
