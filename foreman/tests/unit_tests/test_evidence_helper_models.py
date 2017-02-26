from datetime import datetime
from werkzeug.exceptions import InternalServerError
# local imports
import base_tester
from foreman.model import User, ForemanOptions, ChainOfCustody, EvidenceStatus, EvidenceHistory, EvidencePhotoUpload, EvidenceType
from foreman.utils.utils import session


class ModelTestEvidenceBase(base_tester.UnitTestCase):
    pass


class ChainOfCustodyTestCase(ModelTestEvidenceBase):
    pass


class EvidenceStatusTestCase(ModelTestEvidenceBase):
    pass


class EvidenceHistoryTestCase(ModelTestEvidenceBase):
    pass


class EvidencePhotoUploadTestCase(ModelTestEvidenceBase):
    pass


class EvidenceTypeTestCase(ModelTestEvidenceBase):
    pass