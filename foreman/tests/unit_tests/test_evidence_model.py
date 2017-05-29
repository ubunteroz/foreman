from datetime import datetime, timedelta
from monthdelta import MonthDelta
from os import path, remove
# local imports
import base_tester
from foreman.controllers.baseController import BaseController
from foreman.model import User, Evidence, Case, EvidenceStatus, EvidenceType, ForemanOptions, ChainOfCustody
from foreman.utils.utils import session, ROOT_DIR


class ModelTestEvidenceBase(base_tester.UnitTestCase):
    current_user = None
    now = datetime.now()


class EvidenceReadTestCase(ModelTestEvidenceBase):
    def setUp(self):
        self.current_user = User.get(1)
        self.case = Case.get(1)
        self.evidence = Evidence.get(1)

    def test_evidence_attributes_test_case(self):
        self.assertEqual(self.evidence.type, "DVD")
        self.assertEqual(self.evidence.case_id, 2)
        self.assertEqual(self.evidence.user_id, 18)
        self.assertEqual(self.evidence.qr_code, True)
        code_text = "Case: {} | Ref: {} | Date Added: {} | Added by: {}".format(self.evidence.case.case_name,
                                                                                self.evidence.reference,
                                                                               self.evidence.date_added,
                                                                                self.evidence.user.fullname)
        self.assertEqual(self.evidence.qr_code_text, code_text)
        self.assertEqual(self.evidence.originator, "Cristiano Slim Ronaldo")
        self.assertEqual(self.evidence.location, "Main Evidence Cabinet")
        self.assertEqual(self.evidence.current_status, EvidenceStatus.INACTIVE)
        self.assertEqual(self.evidence.status, EvidenceStatus.INACTIVE)
        self.assertEqual(self.evidence.chain_of_custody_status.check_in, True)
        self.assertEqual(self.evidence.icon, "dvd")

    def test_get_evidence_test_case(self):
        perms = BaseController.check_permissions
        users = [User.get(28), User.get(39), User.get(19), User.get(22), User.get(4)]
        perms = [Evidence.get_all_evidence(user, perms) for user in users]

        self.assertEqual(len(perms[0]), 1)
        self.assertEqual(len(perms[1]), 8)
        self.assertEqual(len(perms[2]), 9)
        self.assertEqual(len(perms[3]), 7)
        self.assertEqual(len(perms[4]), 11)

        caseless = Evidence.get_caseless()
        self.assertEqual(len(caseless), 1)
        self.assertEqual(caseless[0].id, 4)


class EvidenceWriteTestCase(ModelTestEvidenceBase):
    def setUp(self):
        self.current_user = User.get(1)
        self.case = Case.get(1)
        self.evidence_type = EvidenceType.get(1)

        self.now = datetime.now()

        self.evidence = Evidence(self.case, "ref", self.evidence_type.evidence_type, "comment", "origin", "location",
                                 self.current_user, "BAG1", False)
        session.add(self.evidence)

        self.evidence1 = Evidence(self.case, "ref", self.evidence_type.evidence_type, "comment", "origin", "location",
                                 self.current_user, "BAG1", False)
        session.add(self.evidence1)
        session.commit()

    def tearDown(self):
        session.delete(self.evidence)
        session.delete(self.evidence1)
        session.commit()

    def test_creation_test_case(self):
        self.evidence.set_status(EvidenceStatus.ACTIVE, self.current_user, "note")
        self.assertEqual(self.evidence.current_status, EvidenceStatus.ACTIVE)

        self.assertIsNone(self.evidence.retention_start_date)
        self.evidence.set_status(EvidenceStatus.ARCHIVED, self.current_user, "note")
        self.assertEqual(self.evidence.current_status, EvidenceStatus.ARCHIVED)
        self.assertGreaterEqual(self.evidence.retention_start_date, self.now)

        self.evidence.disassociate()
        self.assertIsNone(self.evidence.case)

        self.evidence.associate(Case.get(2))
        self.assertEqual(self.evidence.case_id, 2)

    def test_retention_period_test_case(self):
        options = ForemanOptions.get_options()
        options.evidence_retention = True
        options.evidence_retention_period = 12  # months
        self.evidence1.set_status(EvidenceStatus.ARCHIVED, self.current_user, "note")
        self.assertEqual(self.evidence1.current_status, EvidenceStatus.ARCHIVED)
        self.assertGreaterEqual(self.evidence1.retention_start_date, self.now)
        self.assertEqual(self.evidence1.retention_date, self.evidence1.retention_start_date + MonthDelta(12))
        self.assertFalse(self.evidence1.reminder_due())

        self.evidence1.retention_date = self.now - timedelta(1)  # change to yesterday
        self.assertTrue(self.evidence1.reminder_due())

    def test_checkins_test_case(self):
        self.evidence.check_in("cust", self.current_user, datetime(2017,1,1), "comment")
        self.assertEqual(1, len(ChainOfCustody.get_changes(self.evidence)))

        self.evidence.check_out("cust", self.current_user, datetime(2017, 1, 2), "comment")
        self.assertEqual(2, len(ChainOfCustody.get_changes(self.evidence)))

    def test_make_qr_code_test_case(self):
        location = path.join(ROOT_DIR, 'tests', 'test_images', "{}.png".format(self.evidence.id))
        if path.exists(location):
            remove(location)
        self.evidence.create_qr_code(location)
        self.assertTrue(path.exists(location))

