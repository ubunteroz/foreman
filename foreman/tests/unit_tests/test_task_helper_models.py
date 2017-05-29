from datetime import datetime
from os import path
from shutil import copyfile
# local imports
import base_tester
from foreman.model import User, TaskStatus, Task, TaskType, TaskCategory, Case, TaskUpload, TaskNotes, TaskHistory
from foreman.utils.utils import session, ROOT_DIR


class ModelTestTaskBase(base_tester.UnitTestCase):
    pass


class TaskStatusTestCase(ModelTestTaskBase):
    def setUp(self):
        self.current_user = User.get(1)
        self.case = Case.get(1)
        self.task_type = TaskType.get(1)

        self.task1 = Task(self.case, self.task_type, "task name", self.current_user)
        session.add(self.task1)
        session.commit()

    def tearDown(self):
        session.delete(self.task1)
        session.delete(self.new_status)
        session.delete(self.new_status_1)
        session.commit()

    def test_new_status_test_case(self):
        self.new_status = TaskStatus(self.task1.id, TaskStatus.CREATED, self.current_user)
        session.add(self.new_status)
        session.commit()

        self.assertEqual(self.task1.get_status(), self.new_status)
        self.assertEqual(self.new_status.user_id, self.current_user.id)
        self.assertEqual(self.new_status.case_id, self.task1.case.id)
        self.assertEqual(self.new_status.task_id, self.task1.id)
        self.assertEqual(self.new_status.status, TaskStatus.CREATED)

        self.new_status_1 = TaskStatus(self.task1.id, TaskStatus.ALLOCATED, self.current_user)
        session.add(self.new_status_1)
        session.commit()

        self.assertEqual(self.task1.get_status(), self.new_status_1)

        result = self.new_status_1.previous
        self.assertEqual(result, self.new_status)

        result = self.new_status.previous  # the 1st status is automatically added on a new task, go back one more
        self.assertFalse(result.previous)


class TaskUploadTestCase(ModelTestTaskBase):
    def setUp(self):
        self.upload_location = path.join('tests', 'test_images')
        copyfile(path.join(ROOT_DIR, self.upload_location, "original.png"),
                 path.join(ROOT_DIR, self.upload_location, "test_task_upload.png"))

        self.current_user = User.get(1)
        self.delete_user = User.get(2)
        self.task = Task.get(1)
        self.new_task_upload = TaskUpload(self.current_user.id, self.task.id, self.task.case.id, "test_task_upload.png",
                                          "notes", "title", self.upload_location)
        session.add(self.new_task_upload)
        session.commit()

    def tearDown(self):
        session.delete(self.new_task_upload)
        session.commit()

    def test_new_upload_test_case(self):
        now = datetime.now()
        self.assertEqual(self.new_task_upload.file_note, "notes")
        self.assertEqual(self.new_task_upload.uploader, self.current_user)
        self.assertEqual(self.new_task_upload.task, self.task)
        self.assertEqual(self.new_task_upload.file_name, "test_task_upload.png")
        self.assertEqual(self.new_task_upload.file_title, "title")
        self.assertEqual(self.new_task_upload.deleted, False)
        self.assertEqual(self.new_task_upload.date_deleted, None)
        self.assertEqual(self.new_task_upload.deleter, None)
        self.assertGreaterEqual(now, self.new_task_upload.date_time)

    def test_file_deletion_test_case(self):
        self.new_task_upload.delete(self.delete_user)
        self.assertEqual(self.new_task_upload.deleted, True)
        now = datetime.now()
        self.assertGreaterEqual(now, self.new_task_upload.date_deleted)
        self.assertEqual(self.new_task_upload.deleter, self.delete_user)

    def test_changes_test_case(self):
        upload_1 = TaskUpload(self.current_user.id, self.task.id, self.task.case.id, "test_task_upload.png", "notes",
                              "title1", self.upload_location)
        upload_2 = TaskUpload(self.current_user.id, self.task.id, self.task.case.id, "test_task_upload.png", "notes",
                              "title2", self.upload_location)
        session.add(upload_1)
        session.add(upload_2)
        session.commit()
        upload_1.delete(self.current_user)
        session.commit()

        self.assertEqual(4, len(TaskUpload.get_changes_for_user(self.current_user)))
        self.assertEqual(4, len(TaskUpload.get_changes(self.task)))
        self.assertEqual(0, len(TaskUpload.get_changes_for_user(self.delete_user)))

        session.delete(upload_1)
        session.delete(upload_2)

    def test_hashing_test_case(self):
        hash_upload = TaskUpload(self.current_user.id, self.task.id, self.task.case.id, "test_task_upload.png", "notes",
                                 "title3", self.upload_location)
        session.add(hash_upload)
        session.commit()

        hashed = "7d3d80572d847fd029309585f3ec57a20ccdc820358bac6a8f8a9246968a3c66"
        self.assertEqual(hash_upload.file_hash, hashed)
        session.delete(hash_upload)


class TaskNotesTestCase(ModelTestTaskBase):
    def setUp(self):
        self.task = Task.get(1)
        self.user = User.get(1)

        self.note = TaskNotes("note", self.user.id, self.task.id)
        session.add(self.note)
        session.commit()

    def tearDown(self):
        session.delete(self.note)
        session.commit()

    def test_task_notes_test_case(self):
        now = datetime.now()
        self.assertEqual(self.note.note, "note")
        self.assertEqual(self.note.author, self.user)
        self.assertEqual(self.note.task, self.task)
        self.assertGreaterEqual(now, self.note.date_time)

        notehash = "edb465624291e4053c6c5ea4b7eb320dec773e10a57d26b95dcf0564f8e310f8"
        self.assertEqual(notehash, self.note.hash)
        self.assertTrue(self.note.check_hash())

    def test_changes_test_case(self):
        notes_1 = TaskNotes("Note 1", self.user.id, self.task.id)
        notes_2 = TaskNotes("Note 2", self.user.id, self.task.id)
        session.add(notes_1)
        session.add(notes_2)
        session.commit()

        self.assertEqual(3, len(TaskNotes.get_changes_for_user(self.user)))
        self.assertEqual(3, len(TaskNotes.get_changes(self.task)))

        session.delete(notes_1)
        session.delete(notes_2)


class TaskHistoryTestCase(ModelTestTaskBase):
    def setUp(self):
        self.current_user = User.get(1)
        self.case = Case.get(1)
        self.task_type = TaskType.get(1)

        self.task = Task(self.case, self.task_type, "name", self.current_user)
        self.task.add_change(self.current_user)
        session.add(self.task)
        session.commit()

    def tearDown(self):
        session.delete(self.task)
        session.commit()

    def test_history_test_case(self):
        new_name = "New task name"
        self.task.task_name = new_name
        self.task.add_change(self.current_user)

        task_hist = TaskHistory.get_filter_by(task_id=self.task.id).all()
        self.assertEqual(len(task_hist), 2)

        # check histories
        result = task_hist[1].previous
        self.assertEqual(result, task_hist[0])

        result = task_hist[0].previous
        self.assertIsNone(result)

        # check changes stored
        self.assertEqual(task_hist[1].task_name, new_name)
        self.assertEqual(task_hist[0].task_name, "name")
        self.assertNotEqual(task_hist[0].date_time, task_hist[1].date_time)

        # but nothing else changed
        self.assertEqual(task_hist[0].user_id, task_hist[1].user_id)
        self.assertEqual(task_hist[0].task_type_id, task_hist[1].task_type_id)
        self.assertEqual(task_hist[0].background, task_hist[1].background)
        self.assertEqual(task_hist[0].location, task_hist[1].location)
        self.assertEqual(task_hist[0].deadline, task_hist[1].deadline)


class TaskTypeTestCase(ModelTestTaskBase):
    def tearDown(self):
        cc = TaskType.get_filter_by(task_type="Piece of Paper").first()
        if cc is not None:
            session.delete(cc)
            session.commit()

    def test_task_type_test_case(self):
        # test defaults
        default_list = [('Email Search', 'Communications Retrieval'),
                      ('Email Archive Search', 'Communications Retrieval'),
                      ('Instant Messenger Search', 'Communications Retrieval'),
                      ('Chat Room Search', 'Communications Retrieval'),
                      ('Fax Search', 'Communications Retrieval'),
                      ('Text Message Search', 'Communications Retrieval'),
                      ('PST File Recovery', 'Communications Retrieval'),
                      ('User Browser History', 'Internet Logs'),
                      ('Proxy Logs', 'Internet Logs'),
                      ('Firewall / DHCP logs', 'Internet Logs'),
                      ('Machine Image', 'Computer Forensics'),
                      ('Machine Remote Image', 'Computer Forensics'),
                      ('Machine Analysis', 'Computer Forensics'),
                      ('Mobile Image', 'Mobile & Tablet Forensics'),
                      ('Tablet Image', 'Mobile & Tablet Forensics'),
                      ('Mobile Analysis', 'Mobile & Tablet Forensics'),
                      ('Tablet Analysis', 'Mobile & Tablet Forensics'),
                      ('User Personal Drive Search', 'Networked Data'),
                      ('User Personal Drive Capture', 'Networked Data'),
                      ('Networked Drive Search', 'Networked Data'),
                      ('Networked Drive Capture', 'Networked Data'),
                      ('Windows Event Log Analysis', 'Log file Analysis'),
                      ('Printer Log Analysis', 'Log file Analysis'),
                      ('SIEM Log Analysis', 'Log file Analysis'),
                      ('Malware Analysis', 'Specialist Tasks'),
                      ('Undefined', 'Other')]
        defaults = TaskType.get_all()
        default_output = [d.task_type for d in defaults]
        self.assertEqual(len(default_output), 26)
        for d in default_list:
            self.assertIn(d[0], default_output)

        # test adding task types
        task_type = "Piece of Paper"
        cat = TaskType.get_category('Other')
        cc = TaskType(task_type, cat)
        session.add(cc)
        session.commit()

        new_list = TaskType.get_all()
        list_output = [d.task_type for d in new_list]
        self.assertEqual(len(list_output), 27)
        self.assertIn(task_type, list_output)


class TaskCategoryTestCase(ModelTestTaskBase):
    def tearDown(self):
        cc = TaskCategory.get_filter_by(category="Paper").first()
        if cc is not None:
            session.delete(cc)
            session.commit()
        cc = TaskType.get_filter_by(task_type="Piece of Paper").first()
        if cc is not None:
            session.delete(cc)
            session.commit()

    def test_task_category_test_case(self):
        # test defaults
        default_list = ['Communications Retrieval', 'Internet Logs', 'Computer Forensics', 'Mobile & Tablet Forensics',
                        'Networked Data', 'Log file Analysis', 'Specialist Tasks', 'Other']
        defaults = TaskCategory.get_all()
        default_output = [d.category for d in defaults]
        self.assertEqual(len(default_output), 8)
        for d in default_list:
            self.assertIn(d, default_output)

        # test adding task category
        category = "Paper"
        cc = TaskCategory(category)
        session.add(cc)
        session.commit()

        new_list = TaskCategory.get_all()
        list_output = [d.category for d in new_list]
        self.assertEqual(len(list_output), 9)
        self.assertIn(category, list_output)

        # test get task category
        categories = TaskCategory.get_categories()
        self.assertEqual(len(categories), 9)
        default_list.append(category)
        default_list.remove("Other")
        for d in default_list:
            self.assertIn(d, categories)

        # get empty categories
        empties = TaskCategory.get_empty_categories().all()
        self.assertEqual(len(empties), 1)
        self.assertEqual(empties[0].category, category)

        task_type = "Piece of Paper"
        cat = TaskType.get_category('Paper')
        cc = TaskType(task_type, cat)
        session.add(cc)
        session.commit()

        empties = TaskCategory.get_empty_categories().all()
        self.assertEqual(len(empties), 0)
