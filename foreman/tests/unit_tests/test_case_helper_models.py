from datetime import datetime
from os import path
from shutil import copyfile
from werkzeug.exceptions import InternalServerError
# local imports
import base_tester
from foreman.model import CaseAuthorisation, Case, User, ForemanOptions, LinkedCase, CaseStatus, CaseHistory, \
    CaseClassification, CaseType, CasePriority, CaseUpload
from foreman.utils.utils import session, ROOT_DIR


class ModelTestCaseBase(base_tester.UnitTestCase):
    current_user = None
    defaults = ForemanOptions.get_options()
    now = datetime.now()


class CaseClassificationTestCase(ModelTestCaseBase):
    def tearDown(self):
        cc = CaseClassification.get_filter_by(classification="Private").first()
        if cc is not None:
            session.delete(cc)
            session.commit()

    def test_case_classification_test_case(self):
        # test defaults
        default_list = ['Public', 'Secret', 'Confidential', 'Internal', 'Undefined']
        defaults = CaseClassification.get_all()
        default_output = [d.classification for d in defaults]
        self.assertEqual(len(default_output), 5)
        for d in default_list:
            self.assertIn(d, default_output)

        # test adding classification
        classification = "Private"
        cc = CaseClassification(classification)
        session.add(cc)
        session.commit()

        new_list = CaseClassification.get_all()
        list_output = [d.classification for d in new_list]
        self.assertEqual(len(list_output), 6)
        self.assertIn(classification, list_output)

        # test get classifications
        classifications = CaseClassification.get_classifications()
        self.assertEqual(len(classifications), 5)
        default_list.append(classification)
        default_list.remove("Undefined")
        for d in default_list:
            self.assertIn(d, classifications)


class CaseTypeTestCase(ModelTestCaseBase):
    def tearDown(self):
        cc = CaseType.get_filter_by(case_type="Policy Violation").first()
        if cc is not None:
            session.delete(cc)
            session.commit()

    def test_case_type_test_case(self):
        # test defaults
        default_list = ['eDiscovery', 'Internal Investigation', 'Fraud Investigation', 'Incident Response',
                        'Security & Malware Investigation', 'Other', 'Undefined']
        defaults = CaseType.get_all()
        default_output = [d.case_type for d in defaults]
        self.assertEqual(len(default_output), 7)
        for d in default_list:
            self.assertIn(d, default_output)

        # test adding case types
        case_type = "Policy Violation"
        cc = CaseType(case_type)
        session.add(cc)
        session.commit()

        new_list = CaseType.get_all()
        list_output = [d.case_type for d in new_list]
        self.assertEqual(len(list_output), 8)
        self.assertIn(case_type, list_output)

        # test get case types
        casetypes = CaseType.get_case_types()
        self.assertEqual(len(casetypes), 7)
        default_list.append(case_type)
        default_list.remove("Undefined")
        for d in default_list:
            self.assertIn(d, casetypes)


class CasePriorityTestCase(ModelTestCaseBase):
    def tearDown(self):
        cc = CasePriority.get_filter_by(case_priority="Informational").first()
        if cc is not None:
            session.delete(cc)
        cc = CasePriority.get_filter_by(case_priority="Major").first()
        if cc is not None:
            session.delete(cc)
        session.commit()

    def test_case_priority_test_case(self):
        # test defaults
        default_list = [("Low", "#00CCFF", False),
                        ("Normal", "#009900", True),
                        ("High", "#FF9933", False),
                        ("Critical", "#CC0000", False)]
        defaults = CasePriority.get_all()
        default_output = [(default.case_priority, default.colour, default.default) for default in defaults]
        self.assertEqual(len(default_output), 4)
        for d in default_list:
            self.assertIn(d, default_output)

        self.assertEqual("Normal", CasePriority.default_value().case_priority)

        # test adding priority
        case_priority = "Informational"
        cc = CasePriority(case_priority, "#FFFFFF", False)
        session.add(cc)
        session.commit()

        new_list = CasePriority.get_all()
        list_output = [default.case_priority for default in new_list]
        self.assertEqual(len(list_output), 5)
        self.assertIn(case_priority, list_output)

        # test adding a new default priority
        case_priority = "Major"
        cc = CasePriority(case_priority, "#000000", True)
        session.add(cc)
        session.commit()

        self.assertEqual("Major", CasePriority.default_value().case_priority)
        self.assertFalse(CasePriority.get_filter_by(case_priority="Normal").first().default)


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

        result = self.new_status.previous  # the 1st status is automatically added on a new case, go back one more
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


class CaseUploadTestCase(ModelTestCaseBase):
    def setUp(self):
        self.upload_location = path.join('tests', 'test_images')
        copyfile(path.join(ROOT_DIR, self.upload_location, "original.png"),
                 path.join(ROOT_DIR, self.upload_location, "test_case_upload.png"))

        self.current_user = User.get(1)
        self.delete_user = User.get(2)
        self.case = Case.get(1)
        self.new_case_upload = CaseUpload(self.current_user.id, self.case.id, "test_case_upload.png", "notes", "title4",
                                          self.upload_location)
        session.add(self.new_case_upload)
        session.commit()

    def tearDown(self):
        session.delete(self.new_case_upload)
        session.commit()

    def test_new_upload(self):
        self.assertEqual(self.new_case_upload.file_note, "notes")
        self.assertEqual(self.new_case_upload.uploader, self.current_user)
        self.assertEqual(self.new_case_upload.case, self.case)
        self.assertEqual(self.new_case_upload.file_name, "test_case_upload.png")
        self.assertEqual(self.new_case_upload.file_title, "title4")
        self.assertEqual(self.new_case_upload.deleted, False)
        self.assertEqual(self.new_case_upload.date_deleted, None)
        self.assertEqual(self.new_case_upload.deleter, None)
        self.assertGreaterEqual(self.new_case_upload.date_time, self.now)

    def test_file_deletion(self):
        self.new_case_upload.delete(self.delete_user)
        self.assertEqual(self.new_case_upload.deleted, True)
        self.now = datetime.now()
        self.assertGreaterEqual(self.now, self.new_case_upload.date_deleted)
        self.assertEqual(self.new_case_upload.deleter, self.delete_user)

    def test_changes(self):
        upload_1 = CaseUpload(self.current_user.id, self.case.id, "test_case_upload.png", "notes", "title1",
                              self.upload_location)
        upload_2 = CaseUpload(self.current_user.id, self.case.id, "test_case_upload.png", "notes", "title2",
                              self.upload_location)
        session.add(upload_1)
        session.add(upload_2)
        session.commit()
        upload_1.delete(self.current_user)
        session.commit()

        self.assertEqual(4, len(CaseUpload.get_changes_for_user(self.current_user)))
        self.assertEqual(4, len(CaseUpload.get_changes(self.case)))
        self.assertEqual(0, len(CaseUpload.get_changes_for_user(self.delete_user)))

        session.delete(upload_1)
        session.delete(upload_2)

    def test_hashing(self):
        hash_upload = CaseUpload(self.current_user.id, self.case.id, "test_case_upload.png", "notes", "title3",
                                 self.upload_location)
        session.add(hash_upload)
        session.commit()

        hashed = "8d88d048b3930f1c9d2989221b7dde62393d42ed8e746ddae5cf706c4c392f60"
        self.assertEqual(hash_upload.file_hash, hashed)
        session.delete(hash_upload)

