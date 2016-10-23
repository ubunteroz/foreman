from datetime import datetime, timedelta
# local imports
import base_tester
from foreman.controllers.baseController import BaseController
from foreman.model import Base, Task, User, ForemanOptions, TaskStatus, UserTaskRoles, TaskCategory, TaskType, Case
from foreman.model import CaseStatus, TaskHistory, UserTaskRolesHistory, TaskNotes
from foreman.utils.utils import session

class ModelTestCaseBase(base_tester.UnitTestCase):
    current_user = None
    now = datetime.now()


class TaskWriteTestCase(ModelTestCaseBase):
    def setUp(self):
        self.current_user = User.get(1)
        self.case = Case.get(1)
        self.task_type = TaskType.get(1)
        self.new_task = Task(self.case, self.task_type, "taskname", self.current_user)
        session.add(self.new_task)

    def tearDown(self):
        session.delete(self.new_task)

        tasks = TaskHistory.get_all()
        for t in tasks:
            if t.task_id is None:
                session.delete(t)

        statuses = TaskStatus.get_all()
        for s in statuses:
            if s.task_id is None:
                session.delete(s)

        notes = TaskNotes.get_all()
        for n in notes:
            if n.task_id is None:
                session.delete(n)

        user_roles = UserTaskRolesHistory.get_all()
        for u in user_roles:
            if u.task is None:
                session.delete(u)

        session.commit()

    def test_new_task_test_case(self):
        self.assertEqual(self.new_task.task_name, "taskname")
        self.assertEqual(self.new_task.task_type, self.task_type)
        self.assertGreaterEqual(self.new_task.creation_date, self.now)

        self.assertIsNone(self.new_task.deadline)

        deadline_date = datetime.combine(self.now + timedelta(days=20), datetime.min.time())
        self.case.deadline = deadline_date
        new_task_deadline_case = Task(self.case, self.task_type, "taskname3", self.current_user)
        session.add(new_task_deadline_case)
        self.assertEqual(new_task_deadline_case.deadline, deadline_date)
        session.delete(new_task_deadline_case)

        self.assertEqual(self.new_task.status, TaskStatus.CREATED)

    def test_status_changes_test_case(self):
        self.new_task.request_QA(self.current_user)
        self.assertEqual(self.new_task.status, TaskStatus.QA)

        self.new_task.set_status(TaskStatus.DELIVERY, self.current_user)
        self.assertEqual(self.new_task.status, TaskStatus.DELIVERY)

        self.new_task.deliver_task(self.current_user)
        self.assertEqual(self.new_task.status, TaskStatus.COMPLETE)

        self.new_task.close_task(self.current_user)
        self.assertEqual(self.new_task.status, TaskStatus.CLOSED)

        statuses = self.new_task.statuses
        self.assertEqual(len(statuses), 5)
        self.assertEqual(statuses[-1].status, TaskStatus.CLOSED)
        self.assertEqual(statuses[-2].status, TaskStatus.COMPLETE)
        self.assertEqual(statuses[-3].status, TaskStatus.DELIVERY)
        self.assertEqual(statuses[-4].status, TaskStatus.QA)

    def test_changes_test_case(self):
        self.new_task.task_name = "changed"
        self.new_task.add_change(self.current_user)
        self.new_task.case_name = "changed again"
        self.new_task.add_change(self.current_user)

        num_changes = self.new_task.history
        self.assertEqual(len(num_changes), 2)

        history = TaskHistory.get_changes(self.new_task)
        self.assertEqual(len(history), 1)

        user_changes = self.current_user.task_history_changes
        self.assertEqual(len(user_changes), 2)

    def test_doing_case_work_test_case(self):
        note = "notes"
        self.new_task.add_note(note, self.current_user)
        self.assertEqual(self.new_task.notes[-1].note, note)

        self.new_task.start_work(self.current_user)
        self.assertEqual(self.new_task.status, TaskStatus.PROGRESS)
        self.assertEqual(self.new_task.get_status().note,
                         "{} has started work on this task".format(self.current_user.fullname))

    def test_passing_QA_test_case(self):
        user = User.get(2)
        task1 = Task(self.case, self.task_type, "pass_QA", self.current_user)
        session.add(task1)
        self.assertEqual(task1.status, TaskStatus.CREATED)

        # one QAer
        role = UserTaskRoles(user, task1, UserTaskRoles.PRINCIPLE_QA)
        session.add(role)
        session.commit()

        task1.pass_QA("note3", user)
        self.assertEqual(task1.notes[-1].note, "note3")
        self.assertEqual(task1.status, TaskStatus.DELIVERY)

        # two QAers - test cases, only 1 passes it, no change. when second passes it, change.
        user2 = User.get(3)
        task2 = Task(self.case, self.task_type, "pass_QA1", self.current_user)
        session.add(task2)
        role = UserTaskRoles(user, task2, UserTaskRoles.PRINCIPLE_QA)
        role2 = UserTaskRoles(user2, task2, UserTaskRoles.SECONDARY_QA)
        session.add(role)
        session.add(role2)
        session.commit()

        task2.pass_QA("note4", user)
        self.assertEqual(task2.notes[-1].note, "note4")
        self.assertEqual(task2.status, TaskStatus.CREATED)
        task2.pass_QA("note5", user2)
        self.assertEqual(task2.notes[-1].note, "note5")
        self.assertEqual(task2.status, TaskStatus.DELIVERY)

        # 1 QAer, but not assigned to this case
        user = User.get(10)
        task1.set_status(TaskStatus.QA, self.current_user)
        task1.princQA = task1.seconQA = False
        task1.pass_QA("note6", user)
        self.assertEqual(task1.status, TaskStatus.QA) # no change
        self.assertNotEqual(task1.notes[-1].note, "note6") # no change

        session.delete(task1)
        session.delete(task2)

        ### issue, what is waiting on 2nd QA and they are removed from case? state of limbo?

    def test_failing_QA_test_case(self):
        user = User.get(2)
        task1 = Task(self.case, self.task_type, "fail_QA", self.current_user)
        session.add(task1)
        self.assertEqual(task1.status, TaskStatus.CREATED)

        # one QAer
        role = UserTaskRoles(user, task1, UserTaskRoles.PRINCIPLE_QA)
        session.add(role)
        session.commit()

        task1.fail_QA("note7", user)
        self.assertEqual(task1.notes[-1].note, "note7")
        self.assertEqual(task1.status, TaskStatus.PROGRESS)

        # two QAers
        user2 = User.get(3)
        task2 = Task(self.case, self.task_type, "fail_QA1", self.current_user)
        session.add(task2)
        role = UserTaskRoles(user, task2, UserTaskRoles.PRINCIPLE_QA)
        role2 = UserTaskRoles(user2, task2, UserTaskRoles.SECONDARY_QA)
        session.add(role)
        session.add(role2)
        session.commit()

        task2.fail_QA("note8", user2)
        self.assertEqual(task2.notes[-1].note, "note8")
        self.assertEqual(task2.status, TaskStatus.PROGRESS)

        # 1 QAer, but not assigned to this case
        user = User.get(10)
        task1.set_status(TaskStatus.QA, self.current_user)
        task1.princQA = task1.seconQA = False
        task1.fail_QA("note9", user)
        self.assertEqual(task1.status, TaskStatus.QA)  # no change
        self.assertNotEqual(task1.notes[-1].note, "note9") # no change

        session.delete(task1)
        session.delete(task2)

    def test_assign_task_test_case(self):
        user = User.get(5)
        user1 = User.get(6)
        user2 = User.get(6)
        user3 = User.get(22)
        task = Task(self.case, self.task_type, "assign_inv", self.current_user)
        session.add(task)
        session.commit()

        task.set_status(TaskStatus.CREATED, self.current_user)
        task.assign_task(user)
        self.assertEqual(task.status, TaskStatus.ALLOCATED)
        self.assertEqual(task.principle_investigator, user)

        task.set_status(TaskStatus.CREATED, self.current_user)
        task.assign_task(user1, principle=False)
        self.assertEqual(task.status, TaskStatus.CREATED)
        self.assertEqual(task.secondary_investigator, user1)

        task.set_status(TaskStatus.CREATED, self.current_user)
        task.assign_task(user2, True, manager=user3)
        self.assertEqual(task.status, TaskStatus.ALLOCATED)
        self.assertEqual(task.principle_investigator, user2)

        task.assign_task(user3) # not got an investigator role
        self.assertNotEqual(task.principle_investigator, user3)

        session.delete(task)

    def test_assign_qa_test_case(self):
        user = User.get(5)
        user1 = User.get(6)
        user2 = User.get(23)

        task = Task(self.case, self.task_type, "assign_qa", self.current_user)
        session.add(task)
        session.commit()

        task.assign_qa(user)
        self.assertEqual(task.principle_QA, user)

        task.assign_qa(user1, principle=False)
        self.assertEqual(task.secondary_QA, user1)

        task.assign_qa(user2)  # not got a QA role
        self.assertNotEqual(task.principle_QA, user2)

        session.delete(task)

    def test_inv_assigns_qa_test_case(self):
        task = Task(self.case, self.task_type, "inv_assign_qa", self.current_user)
        session.add(task)
        session.commit()

        prin = User.get(2)
        sec = User.get(3)
        assignee = User.get(6)

        task.investigator_assign_qa(prin, None, assignee, True) # assign just principle QA to prin
        self.assertEqual(task.principle_QA, prin)

        task.investigator_assign_qa(None, sec, assignee, True) # assign just secondary QA to sec
        self.assertEqual(task.secondary_QA, sec)

        task.investigator_assign_qa(sec, prin, assignee) # assign principle and secondary QA
        self.assertEqual(task.principle_QA, sec)
        self.assertEqual(task.secondary_QA, prin)

        prin = User.get(25)
        task.investigator_assign_qa(prin, None, assignee, True) # prin is not a QA
        self.assertEqual(task.principle_QA, sec) # hasn't changed

        session.delete(task)


class TaskReadTestCase(ModelTestCaseBase):

    def setUp(self):
        self.current_user = User.get(1)

    def test_properties_test_case(self):
        task = Task.get(1)
        self.assertEqual(task.name, task.task_name)

        status = TaskStatus.QUEUED
        self.assertEqual(status, task.status)

        inv_1 = User.get(2)
        inv_2 = User.get(4)
        inv_3 = User.get(6)
        qa_1 = User.get(3)
        qa_2 = User.get(5)
        task = Task.get(9)

        self.assertEqual(inv_1, task.principle_investigator)
        self.assertEqual(inv_2, task.secondary_investigator)
        self.assertEqual(qa_1, task.principle_QA)
        self.assertEqual(qa_2, task.secondary_QA)

        self.assertIn(inv_1, task.investigators)
        self.assertIn(inv_2, task.investigators)
        self.assertIn(qa_1, task.QAs)
        self.assertIn(qa_2, task.QAs)

        self.assertIn(inv_1, task.workers)
        self.assertNotIn(inv_3, task.workers)

        task = Task.get(6)
        self.assertIsNone(task.secondary_QA)
        self.assertIsNone(task.secondary_investigator)

        task = Task.get(17)
        self.assertFalse(task.investigators)
        self.assertFalse(task.QAs)

        task = Task.get(7)
        start, end = task.date_range
        self.assertEqual(start, task.creation_date)
        self.assertGreaterEqual(end, self.now)

        task = Task.get(25)
        start, end = task.date_range
        self.assertEqual(start, task.creation_date)
        self.assertEqual(end, task.case.get_status().date_time)

    def test_task_roles_and_perms_test_case(self):
        perms = BaseController.check_permissions

        inv = User.get(8)
        tasks_inv = [Task.get(34), Task.get(35), Task.get(41), Task.get(42)] # two private, two normal
        result_tasks = Task._check_perms(inv, tasks_inv, perms)
        self.assertEqual(tasks_inv, result_tasks)

        # now have some tasks that are private
        tasks_inv = [Task.get(9), Task.get(10), Task.get(11), Task.get(12)]
        result_tasks = Task._check_perms(inv, tasks_inv, perms)
        self.assertFalse(result_tasks)

        inv = User.get(10)
        task = Task.get(13)

        result = task.get_user_roles(inv.id)
        self.assertFalse(result)

        inv = User.get(3)
        result = task.get_user_roles(inv.id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].role, UserTaskRoles.PRINCIPLE_QA)

    def test_task_lists_for_users_test_case(self):
        perms = BaseController.check_permissions

        inv = User.get(2)
        qaed_tasks = [Task.get(12), Task.get(16), Task.get(22), Task.get(28), Task.get(35), Task.get(43)]
        tasks = Task.get_completed_qas(inv, perms, self.current_user)
        self.assertEqual(len(tasks), 6)
        for qa in qaed_tasks:
            self.assertIn(qa, tasks)

        inv = User.get(6)
        tasks = Task.get_current_qas(inv, perms, self.current_user)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], Task.get(21))

        inv = User.get(8)
        inv_tasks = [Task.get(35), Task.get(42)]
        tasks = Task.get_completed_investigations(inv, perms, self.current_user)
        self.assertEqual(len(tasks), 2)
        for invt in inv_tasks:
            self.assertIn(invt, tasks)

        inv = User.get(8)
        tasks = Task.get_current_investigations(inv, perms, self.current_user)
        self.assertFalse(tasks)

        inv = User.get(3)
        inv_tasks = [Task.get(6), Task.get(8), Task.get(19)]
        tasks = Task.get_current_investigations(inv, perms, self.current_user)
        self.assertEqual(len(tasks), 3)
        for invt in inv_tasks:
            self.assertIn(invt, tasks)

    def test_num_of_tasks_for_users_test_case(self):
        inv = User.get(1)
        cat = TaskCategory.get(1).category
        date_req = self.now
        num_tasks = Task.get_num_created_tasks_for_given_month_user_is_investigator_for(inv, cat, date_req)
        self.assertEqual(num_tasks, 0)

        inv = User.get(2)
        num_tasks = Task.get_num_created_tasks_for_given_month_user_is_investigator_for(inv, cat, date_req)
        self.assertEqual(num_tasks, 6)

        cat = TaskCategory.get(2).category
        num_tasks = Task.get_num_created_tasks_for_given_month_user_is_investigator_for(inv, cat, date_req)
        self.assertEqual(num_tasks, 0)

        inv = User.get(9)
        cat = None
        num_tasks = Task.get_num_created_tasks_for_given_month_user_is_investigator_for(inv, cat, date_req)
        self.assertEqual(num_tasks, 1)

        cat = TaskCategory.get(1).category
        num_tasks = Task.get_num_created_tasks_for_given_month_user_is_investigator_for(inv, cat, date_req)
        self.assertEqual(num_tasks, 0)

        cat = None
        date_req = self.now - timedelta(days=60)
        num_tasks = Task.get_num_created_tasks_for_given_month_user_is_investigator_for(inv, cat, date_req)
        self.assertEqual(num_tasks, 0)

        start = self.now - timedelta(days=2)
        end = self.now + timedelta(days=2)
        inv = User.get(2)
        cat = TaskCategory.get(1).category
        status = "Performing QA"
        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, status)
        self.assertEqual(num_tasks, 7)

        cat = None
        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, status)
        self.assertEqual(num_tasks, 8)

        inv = User.get(3)
        cat = TaskCategory.get(1).category
        status = "Waiting for QA"
        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, status)
        self.assertEqual(num_tasks, 9)

        status = "Nonsense"
        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, status)
        self.assertEqual(num_tasks, 0)

        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, TaskStatus.ALLOCATED)
        self.assertEqual(num_tasks, 13)

        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, TaskStatus.CLOSED)
        self.assertEqual(num_tasks, 7)

        start = self.now - timedelta(days=30)
        end = self.now - timedelta(days=20)
        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, status)
        self.assertEqual(num_tasks, 0)

        inv = User.get(1)
        num_tasks = Task.get_num_tasks_by_user_for_date_range(inv, cat, start, end, status)
        self.assertEqual(num_tasks, 0)

        date_req = self.now
        inv = User.get(4)
        num_tasks = Task.get_num_completed_qas_for_given_month(inv, date_req)
        self.assertEqual(num_tasks, 5)

        inv = User.get(11)
        num_tasks = Task.get_num_completed_qas_for_given_month(inv, date_req)
        self.assertEqual(num_tasks, 0)

        date_req = self.now - timedelta(days=60)
        inv = User.get(4)
        num_tasks = Task.get_num_completed_qas_for_given_month(inv, date_req)
        self.assertEqual(num_tasks, 0)

    def test_task_lists_test_case(self):
        tasks = [Task.get(5), Task.get(18)]
        result_tasks = Task.get_queued_tasks()
        self.assertEqual(len(result_tasks), 2)
        for task in tasks:
            self.assertIn(task, result_tasks)

        task_type = TaskType.get(1)
        tasks = Task.get_tasks_with_type(task_type)
        self.assertEqual(len(tasks), 13)

    def test_get_user_tasks_test_case(self):
        perms = BaseController.check_permissions

        user = User.get(2)
        active_qas = Task.get_active_QAs(user)  # get all active QAs for that user
        self.assertEqual(len(active_qas), 1)
        self.assertEqual(active_qas[0], Task.get(8))

        active_qas = Task.get_active_QAs(user, perms)  # get all active QAs that user has permission to see
        self.assertEqual(len(active_qas), 2)
        self.assertIn(Task.get(8), active_qas)
        self.assertIn(Task.get(21), active_qas)

        user = User.get(3)
        active_tasks = Task.get_active_tasks(user)  # get all active tasks for that user
        self.assertEqual(len(active_tasks), 3)
        self.assertIn(Task.get(6), active_tasks)
        self.assertIn(Task.get(8), active_tasks)
        self.assertIn(Task.get(19), active_tasks)

        active_tasks = Task.get_active_tasks(user, perms)  # get all active tasks that user has permission to see
        self.assertEqual(len(active_tasks), 9)

        user = User.get(6)
        prim, sec = Task.get_tasks_requiring_QA_by_user(user) # get all active QAs for that user
        self.assertFalse(sec)
        self.assertEqual(len(prim), 1)
        self.assertEqual(prim[0], Task.get(21))

        # get all completed QAs for that user in active cases
        prim, sec = Task.get_tasks_requiring_QA_by_user(user, task_statuses=TaskStatus.qaComplete)
        self.assertFalse(sec)
        self.assertFalse(prim)

        # get all QAs for that user for all case statuses, in tasks where QA can make notes
        user = User.get(5)
        prim, sec = Task.get_tasks_requiring_QA_by_user(user, case_statuses=CaseStatus.all_statuses,
                                                        task_statuses=TaskStatus.notesAllowed)
        self.assertFalse(sec)
        self.assertEqual(len(prim), 4)
        self.assertIn(Task.get(3), prim)
        self.assertIn(Task.get(7), prim)
        self.assertIn(Task.get(20), prim)
        self.assertIn(Task.get(38), prim)

        # get all tasks assigned to user for active tasks in open cases
        user = User.get(5)
        prim, sec = Task.get_tasks_assigned_to_user(user)
        self.assertEqual(len(prim), 2)
        self.assertFalse(sec)
        self.assertIn(Task.get(8), prim)
        self.assertIn(Task.get(21), prim)

        # get all tasks for that user for all case statuses, in tasks where inv can make notes
        prim, sec = Task.get_tasks_assigned_to_user(user, case_statuses=CaseStatus.all_statuses,
                                                    task_statuses=TaskStatus.notesAllowed)
        self.assertEqual(len(prim), 4)
        self.assertFalse(sec)
