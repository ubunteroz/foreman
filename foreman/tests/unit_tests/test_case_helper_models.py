from datetime import datetime
from werkzeug.exceptions import InternalServerError
# local imports
import base_tester
from foreman.model import CaseAuthorisation, Case, User, ForemanOptions, LinkedCase, CaseStatus, CaseHistory
from foreman.utils.utils import session


class ModelTestCaseBase(base_tester.UnitTestCase):
    current_user = None
    defaults = ForemanOptions.get_options()
    now = datetime.now()


class CaseAuthorisationTestCase(ModelTestCaseBase):
    def setUp(self):
        self.current_user = User.get(1)

        self.case = Case("name", self.current_user)
        session.add(self.case)
        session.commit()

        self.case_auths = []

    def tearDown(self):
        session.delete(self.case)
        for ca in self.case_auths:
            session.delete(ca)
        session.commit()

    def test_creation_test_case(self):
        authorised = "PENDING"
        case_auth = CaseAuthorisation(self.current_user, self.case, authorised, "reason1")
        self.case_auths.append(case_auth)
        session.add(case_auth)

        self.assertEqual(case_auth.case, self.case)
        self.assertEqual(case_auth.authoriser, self.current_user)
        self.assertGreaterEqual(case_auth.date_time, self.now)

        authorised = "NOAUTH"
        case_auth = CaseAuthorisation(self.current_user, self.case, authorised, "reason2")
        self.case_auths.append(case_auth)
        session.add(case_auth)

        authorised = "AUTH"
        case_auth = CaseAuthorisation(self.current_user, self.case, authorised, "reason3")
        self.case_auths.append(case_auth)
        session.add(case_auth)

        session.commit()

        changes = CaseAuthorisation.get_changes(self.case)

        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0]['change_log']['Case'], ('NOAUTH', "reason2"))
        self.assertEqual(changes[1]['change_log']['Case'], ('AUTH', "reason3"))

    def test_wrong_auth_code_test_case(self):
        with self.assertRaises(InternalServerError):
            CaseAuthorisation(self.current_user, self.case, "wrong code", "reason4")


class LinkedCaseTestCase(ModelTestCaseBase):
    def setUp(self):
        self.current_user = User.get(1)

        self.case1 = Case("name 1", self.current_user)
        self.case2 = Case("name 2", self.current_user)
        session.add(self.case1)
        session.add(self.case2)

        self.link = LinkedCase(self.case1, self.case2, "reason", self.current_user)
        session.add(self.link)
        session.commit()

    def tearDown(self):
        session.delete(self.case1)
        session.delete(self.case2)
        session.delete(self.link)
        session.commit()

    def test_new_links_test_case(self):
        self.assertEqual(self.link.case_linker_id, self.case1.id)
        self.assertEqual(self.link.case_linkee_id, self.case2.id)
        self.assertGreaterEqual(self.link.date_time, self.now)
        self.assertFalse(self.link.removed)
        self.assertEqual(self.link.user, self.current_user)

    def test_bidirectional_test_case(self):
        result = self.link.bidirectional(self.case1, "linker")
        self.assertFalse(result)

        self.link_reversed = LinkedCase(self.case2, self.case1, "reason #2", self.current_user)
        session.add(self.link_reversed)
        session.commit()

        result = self.link.bidirectional(self.case1, "linker")
        self.assertTrue(result)

        self.link_reversed_removed = LinkedCase(self.case2, self.case1, "reason #2", self.current_user, True)
        session.add(self.link_reversed_removed)
        session.commit()

        result = self.link.bidirectional(self.case1, "linker")
        self.assertFalse(result)

        results = self.link_reversed_removed.link_removed(self.case1.id)
        self.assertTrue(results)

        results = self.link.link_removed(self.case2.id)
        self.assertFalse(results)

        result = self.link_reversed_removed.previous
        self.assertEqual(self.link_reversed, result)

    def test_links_test_case(self):
        # links to..
        results = LinkedCase.get_links(self.case1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.case2)

        results = LinkedCase.get_links(self.case2)
        self.assertEqual(len(results), 0)

        # linked from..
        results = LinkedCase.get_from_links(self.case2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.case1)

        results = LinkedCase.get_from_links(self.case1)
        self.assertEqual(len(results), 0)


class CaseStatusTestCase(ModelTestCaseBase):
    def setUp(self):
        self.current_user = User.get(1)

        self.case1 = Case("name 1", self.current_user)
        session.add(self.case1)
        session.commit()

    def tearDown(self):
        session.delete(self.case1)
        session.delete(self.new_status)
        session.delete(self.new_status_1)
        session.commit()

    def test_new_status_test_case(self):
        self.new_status = CaseStatus(self.case1.id, CaseStatus.CREATED, self.current_user)
        session.add(self.new_status)
        session.commit()

        self.assertEqual(self.case1.get_status(), self.new_status)
        self.assertEqual(self.new_status.user_id, self.current_user.id)
        self.assertEqual(self.new_status.case_id, self.case1.id)

        self.new_status_1 = CaseStatus(self.case1.id, CaseStatus.OPEN, self.current_user)
        session.add(self.new_status_1)
        session.commit()

        self.assertEqual(self.case1.get_status(), self.new_status_1)

        result = self.new_status_1.previous
        self.assertEqual(result, self.new_status)

        result = self.new_status.previous # the 1st status is automatically added on a new case, go back one more
        self.assertFalse(result.previous)


class CaseHistoryTestCase(ModelTestCaseBase):
    def setUp(self):
        self.current_user = User.get(1)

        self.case1 = Case("name 1", self.current_user)
        self.case1.add_change(self.current_user)
        session.add(self.case1)
        session.commit()

    def tearDown(self):
        session.delete(self.case1)
        session.commit()

    def test_history_test_case(self):
        new_name = "New case name"
        self.case1.case_name = new_name
        self.case1.add_change(self.current_user)

        case_hist = CaseHistory.get_filter_by(case_id=self.case1.id).all()
        self.assertEqual(len(case_hist), 2)

        # check histories
        result = case_hist[1].previous
        self.assertEqual(result, case_hist[0])

        result = case_hist[0].previous
        self.assertIsNone(result)

        # check changes stored
        self.assertEqual(case_hist[1].case_name, new_name)
        self.assertEqual(case_hist[0].case_name, "name 1")
        self.assertNotEqual(case_hist[0].date_time, case_hist[1].date_time)

        # but nothing else changed
        self.assertEqual(case_hist[0].private, case_hist[1].private)
        self.assertEqual(case_hist[0].case_type, case_hist[1].case_type)
        self.assertEqual(case_hist[0].classification, case_hist[1].classification)
        self.assertEqual(case_hist[0].reference, case_hist[1].reference)
        self.assertEqual(case_hist[0].deadline, case_hist[1].deadline)
