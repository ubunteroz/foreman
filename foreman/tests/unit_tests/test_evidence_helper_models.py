from datetime import datetime
from os import path
from hashlib import sha256
from shutil import copyfile
# local imports
import base_tester
from foreman.model import User, Evidence, Case, ChainOfCustody, EvidenceStatus, EvidenceHistory, EvidencePhotoUpload, \
    EvidenceType
from foreman.utils.utils import session, ROOT_DIR


class ModelTestEvidenceBase(base_tester.UnitTestCase):
    @staticmethod
    def hash_files(upload_location):
        blocksize = 65536
        hasher = sha256()
        with open(path.join(ROOT_DIR, upload_location), "rb") as f:
            buf = f.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(blocksize)
        return hasher.hexdigest()


class ChainOfCustodyTestCase(ModelTestEvidenceBase):
    def setUp(self):
        self.now = datetime.now()
        self.current_user = User.get(4)
        self.case = Case.get(1)
        self.evidence_type = EvidenceType.get(1)
        self.evidence = Evidence(self.case, "ref", self.evidence_type.evidence_type, "comment", "origin", "location",
                             self.current_user)
        session.add(self.evidence)

        self.chain = ChainOfCustody(self.evidence, self.current_user, "cust", datetime(2017, 1, 1), True, "comment")
        session.add(self.chain)
        session.commit()

    def tearDown(self):
        session.delete(self.evidence)
        session.delete(self.chain)
        session.commit()

    def test_chain_of_custody_test_case(self):
        self.assertEqual(self.chain.evidence.id, self.evidence.id)
        self.assertEqual(self.chain.user_id, self.current_user.id)
        self.assertEqual(self.chain.check_in, True)
        self.assertEqual(self.chain.comment, "comment")
        self.assertEqual(self.chain.custodian, "cust")

        directory = path.join(ROOT_DIR, 'tests', 'test_images')
        #receipt = open(path.join(directory, "original.png"), "rb")
        #self.chain.upload_custody_receipt(receipt, "label", directory)
        #self.assertEqual(self.chain.custody_receipt, "original.png")
        #self.assertEqual(self.chain.custody_receipt_label, "label")

    def test_chain_history_test_case(self):
        chain_1 = ChainOfCustody(self.evidence, self.current_user, "custodian", datetime(2017, 1, 2), False, "comment1")
        chain_2 = ChainOfCustody(self.evidence, self.current_user, "custodian2", datetime(2017, 1, 3), True, "comment2")
        session.add(chain_1)
        session.add(chain_2)
        session.commit()

        self.assertEqual(3, len(ChainOfCustody.get_changes_for_user(self.current_user)))
        self.assertEqual(3, len(ChainOfCustody.get_changes(self.evidence)))

        session.delete(chain_1)
        session.delete(chain_2)


class EvidenceStatusTestCase(ModelTestEvidenceBase):
    def setUp(self):
        self.current_user = User.get(1)
        self.case = Case.get(1)
        self.evidence_type = EvidenceType.get(1)
        self.evi1 = Evidence(self.case, "ref", self.evidence_type.evidence_type, "comment", "origin", "location", self.current_user)
        session.add(self.evi1)
        session.commit()

    def tearDown(self):
        session.delete(self.evi1)
        session.delete(self.new_status)
        session.delete(self.new_status_1)
        session.commit()

    def test_new_status_test_case(self):
        self.new_status = EvidenceStatus(self.evi1.id, EvidenceStatus.ACTIVE, self.current_user)
        session.add(self.new_status)
        session.commit()

        self.assertEqual(self.evi1.status, self.new_status.status)
        self.assertEqual(self.new_status.user_id, self.current_user.id)
        self.assertEqual(self.new_status.case_id, self.evi1.case.id)
        self.assertEqual(self.new_status.evidence_id, self.evi1.id)
        self.assertEqual(self.new_status.status, EvidenceStatus.ACTIVE)

        self.new_status_1 = EvidenceStatus(self.evi1.id, EvidenceStatus.ARCHIVED, self.current_user)
        session.add(self.new_status_1)
        session.commit()

        self.assertEqual(self.evi1.status, self.new_status_1.status)

        result = self.new_status_1.previous
        self.assertEqual(result, self.new_status)
        result = self.new_status.previous
        self.assertFalse(result.previous)


class EvidenceHistoryTestCase(ModelTestEvidenceBase):
    def setUp(self):
        self.current_user = User.get(1)
        self.case = Case.get(1)
        self.evidence_type = EvidenceType.get(1)
        self.evidence = Evidence(self.case, "ref", self.evidence_type.evidence_type, "comment", "origin", "location",
                             self.current_user)
        self.evidence.add_change(self.current_user)
        session.add(self.evidence)
        session.commit()

    def tearDown(self):
        session.delete(self.evidence)
        session.commit()

    def test_history_test_case(self):
        new_name = "New evidence name"
        self.evidence.reference = new_name
        self.evidence.add_change(self.current_user)

        evi_hist = EvidenceHistory.get_filter_by(evidence_id=self.evidence.id).all()
        self.assertEqual(len(evi_hist), 2)

        # check histories
        result = evi_hist[1].previous
        self.assertEqual(result, evi_hist[0])

        result = evi_hist[0].previous
        self.assertIsNone(result)

        # check changes stored
        self.assertEqual(evi_hist[1].reference, new_name)
        self.assertEqual(evi_hist[0].reference, "ref")
        self.assertNotEqual(evi_hist[0].date_time, evi_hist[1].date_time)

        # but nothing else changed
        self.assertEqual(evi_hist[0].user_id, evi_hist[1].user_id)
        self.assertEqual(evi_hist[0].type, evi_hist[1].type)
        self.assertEqual(evi_hist[0].comment, evi_hist[1].comment)
        self.assertEqual(evi_hist[0].originator, evi_hist[1].originator)


class EvidencePhotoUploadTestCase(ModelTestEvidenceBase):
    def setUp(self):
        self.upload_location = path.join('tests', 'test_images')
        copyfile(path.join(ROOT_DIR, self.upload_location, "original.png"),
                 path.join(ROOT_DIR, self.upload_location, "test_evidence_upload.png"))

        self.current_user = User.get(1)
        self.delete_user = User.get(2)
        self.evidence = Evidence.get(1)
        self.new_evidence_upload = EvidencePhotoUpload(self.current_user.id, self.evidence.id, "test_evidence_upload.png",
                                                       "notes", "title", self.upload_location)
        session.add(self.new_evidence_upload)
        session.commit()

    def tearDown(self):
        session.delete(self.new_evidence_upload)
        session.commit()

    def test_new_upload_test_case(self):
        now = datetime.now()
        self.assertEqual(self.new_evidence_upload.file_note, "notes")
        self.assertEqual(self.new_evidence_upload.uploader, self.current_user)
        self.assertEqual(self.new_evidence_upload.evidence, self.evidence)
        self.assertEqual(self.new_evidence_upload.file_name, "test_evidence_upload.png")
        self.assertEqual(self.new_evidence_upload.file_title, "title")
        self.assertEqual(self.new_evidence_upload.deleted, False)
        self.assertEqual(self.new_evidence_upload.date_deleted, None)
        self.assertEqual(self.new_evidence_upload.deleter, None)
        self.assertGreaterEqual(now, self.new_evidence_upload.date_time)

    def test_file_deletion_test_case(self):
        self.new_evidence_upload.delete(self.delete_user)
        self.assertEqual(self.new_evidence_upload.deleted, True)
        now = datetime.now()
        self.assertGreaterEqual(now, self.new_evidence_upload.date_deleted)
        self.assertEqual(self.new_evidence_upload.deleter, self.delete_user)

    def test_changes_test_case(self):
        upload_1 = EvidencePhotoUpload(self.current_user.id, self.evidence.id, "test_evidence_upload.png", "notes",
                              "title1", self.upload_location)
        upload_2 = EvidencePhotoUpload(self.current_user.id, self.evidence.id, "test_evidence_upload.png", "notes",
                              "title2", self.upload_location)
        session.add(upload_1)
        session.add(upload_2)
        session.commit()
        upload_1.delete(self.current_user)
        session.commit()
        self.assertEqual(4, len(EvidencePhotoUpload.get_changes_for_user(self.current_user)))
        self.assertEqual(5, len(EvidencePhotoUpload.get_changes(self.evidence)))
        self.assertEqual(0, len(EvidencePhotoUpload.get_changes_for_user(self.delete_user)))

        session.delete(upload_1)
        session.delete(upload_2)

    def test_hashing_test_case(self):
        hash_upload = EvidencePhotoUpload(self.current_user.id, self.evidence.id, "test_evidence_upload.png", "notes",
                                 "title3", self.upload_location)
        session.add(hash_upload)
        session.commit()

        hashed = "7d3d80572d847fd029309585f3ec57a20ccdc820358bac6a8f8a9246968a3c66"
        self.assertEqual(hash_upload.file_hash, hashed)
        session.delete(hash_upload)


class EvidenceTypeTestCase(ModelTestEvidenceBase):
    def tearDown(self):
        cc = EvidenceType.get_filter_by(evidence_type="iPad").first()
        if cc is not None:
            session.delete(cc)
        cc = EvidenceType.get_filter_by(evidence_type="iPed").first()
        if cc is not None:
            session.delete(cc)
        cc = EvidenceType.get_filter_by(evidence_type="iPod").first()
        if cc is not None:
            session.delete(cc)
        session.commit()

    def test_evidence_type_test_case(self):
        # test defaults
        default_list = ['SATA Hard Drive', 'IDE Hard Drive', 'Other Hard Drive', 'USB Hard drive', 'Floppy Disk', 'CD',
                        'DVD', 'Other Removable Media', 'Zip Drive', 'Mobile Phone', 'Smart Phone', 'Tablet', 'PDA',
                        'USB Media', 'GPS Device', 'Digital Camera', 'Gaming System', 'Laptop', 'Whole Computer Tower',
                        'Inkjet Printer', 'Laser Printer', 'Other Printer', 'Scanner', 'Multi-Functional Printer',
                        'Other', 'Music Player', 'Undefined', 'Server']
        defaults = EvidenceType.get_all()
        default_output = [d.evidence_type for d in defaults]
        self.assertEqual(len(default_output), 28)
        for d in default_list:
            self.assertIn(d, default_output)

        # test adding evidence types
        evidence_type = "iPad"
        cc = EvidenceType(evidence_type)
        session.add(cc)
        session.commit()

        new_list = EvidenceType.get_all()
        list_output = [d.evidence_type for d in new_list]
        self.assertEqual(len(list_output), 29)
        self.assertIn(evidence_type, list_output)

        evidence_type = "iPod"
        cc = EvidenceType(evidence_type, "nonexistant_file_location")
        session.add(cc)
        session.commit()

        evidence_type = "iPed"
        icon_loc = path.abspath(path.join(ROOT_DIR, 'static', 'images', 'siteimages', 'icons', "Burn.png"))
        cc = EvidenceType(evidence_type, icon_loc)
        session.add(cc)
        session.commit()

        new_icon1 = path.abspath(path.join(ROOT_DIR, 'static', 'images', 'siteimages', 'evidence_icons', "ipad.png"))
        new_icon2 = path.abspath(path.join(ROOT_DIR, 'static', 'images', 'siteimages', 'evidence_icons', "ipod.png"))
        new_icon3 = path.abspath(path.join(ROOT_DIR, 'static', 'images', 'siteimages', 'evidence_icons', "iped.png"))
        self.assertTrue(path.exists(new_icon1))
        self.assertTrue(path.exists(new_icon2))
        self.assertEqual(self.hash_files(new_icon1), self.hash_files(new_icon2)) # both should be default icon
        self.assertNotEqual(self.hash_files(new_icon3), self.hash_files(new_icon2))
