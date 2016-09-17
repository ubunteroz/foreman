from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import Local, LocalManager
# local imports
import base_tester
from foreman.controllers.baseController import BaseController
from foreman.model import Base, Case, User, CasePriority, ForemanOptions, CaseStatus, UserCaseRoles, CaseHistory


class ModelTestCaseBase(base_tester.UnitTestCase):
    current_user = None
    defaults = ForemanOptions.get_options()
    now = datetime.now()
    session = None
    db = None

    def setup_memory_database(self):
        local = Local()
        local_manager = LocalManager([local])
        sessionMaker = sessionmaker(autocommit=True)
        self.session = scoped_session(sessionMaker, local_manager.get_ident)
        self.db = create_engine('sqlite://')
        sessionMaker.configure(bind=self.db, autocommit=True, autoflush=True)
        Base.metadata.create_all(self.db)

    def drop_memory_database(self):
        Base.metadata.reflect(self.db)
        Base.metadata.drop_all(self.db)


class CaseWriteTestCase(ModelTestCaseBase):

    def setUp(self):
        self.setup_memory_database()

        self.current_user = User("username1", "pass", "forename", "surname", "email", True)

        self.new_case = Case("name", self.current_user)
        self.case_authed = Case("auth", self.current_user)
        self.case_rejected = Case("rejected", self.current_user)
        self.case_changes = Case("changes", self.current_user)
        self.case_changes.add_change(self.current_user)

    def tearDown(self):
        self.drop_memory_database()

    def test_creation_test_case(self):
        self.assertEqual("name", self.new_case.case_name)
        status = self.new_case.get_status()
        self.assertEqual(self.current_user, status.user)
        self.assertEqual(status.status, self.new_case.currentStatus)
        self.assertIsNone(self.new_case.reference)
        self.assertIsNone(self.new_case.background)
        self.assertFalse(self.new_case.private)
        self.assertIsNone(self.new_case.classification)
        self.assertIsNone(self.new_case.case_type)
        self.assertIsNone(self.new_case.justification)
        self.assertEqual(self.new_case.case_priority, CasePriority.default_value().case_priority)
        self.assertEqual(self.new_case.case_priority_colour, CasePriority.default_value().colour)
        self.assertEqual(self.new_case.location, self.defaults.default_location)
        self.assertGreaterEqual(self.new_case.creation_date, self.now)
        self.assertIsNone(self.new_case.deadline)

    def test_authorisation(self):
        auth = User("username2", "pass", "forename", "surname", "email", True)
        reason = "reason"

        auth_code = "AUTH"
        self.case_authed.authorise(auth, reason, auth_code)
        self.assertEqual(self.case_authed.get_status().status, CaseStatus.CREATED)

        auth_code = "NOAUTH"
        self.case_rejected.authorise(auth, reason, auth_code)
        self.assertEqual(self.case_rejected.get_status().status, CaseStatus.REJECTED)

    def test_setting_status(self):
        status = CaseStatus.OPEN
        user = User.get(1)

        self.new_case.set_status(status, user)
        self.assertEqual(self.new_case.get_status().status, CaseStatus.OPEN)
        self.assertNotEqual(self.new_case.get_status().status, CaseStatus.CREATED)

        status = "nonsense"
        self.new_case.set_status(status, user)
        self.assertEqual(self.new_case.get_status().status, CaseStatus.OPEN)
        self.assertNotEqual(self.new_case.get_status().status, status)

    def test_closing_case(self):
        reason = "reason"
        user = self.current_user

        self.new_case.close_case(reason, user)
        current_status = self.new_case.get_status()
        self.assertEqual(current_status.status, CaseStatus.CLOSED)
        self.assertEqual(current_status.reason, reason)

    def test_add_change(self):
        self.case_changes.case_name = "changed"
        self.case_changes.add_change(self.current_user)
        self.case_changes.case_name = "changed again"
        self.case_changes.add_change(self.current_user)

        user_changes = self.current_user.case_history_changes
        self.assertEqual(len(user_changes), 3)

        case_changes = self.case_changes.history
        self.assertEqual(len(case_changes), 2)

        history = CaseHistory.get_changes(self.case_changes)
        self.assertEqual(len(history), 1)


class CaseReadTestCase(ModelTestCaseBase):

    def setUp(self):
        self.current_user = User.get(1)

    def test_authorisations_test_case(self):
        authed_case = Case.get(1)
        no_authed_case = Case.get(10)
        pending_case = Case.get(5)

        # test .is_authorised
        self.assertTrue(authed_case.is_authorised)
        self.assertFalse(no_authed_case.is_authorised)
        self.assertFalse(pending_case.is_authorised)

        # test .authorised
        self.assertEqual(authed_case.authorised.case_authorised, "AUTH")
        self.assertEqual(no_authed_case.authorised.case_authorised, "NOAUTH")
        self.assertEqual(pending_case.authorised.case_authorised, "PENDING")

        for case in Case.get_all():
            self.assertIsNotNone(case.authorised)

        # test .get_cases_authorised()
        auth = User.get(40) # no cases authorised
        perms = BaseController.check_permissions
        statuses = CaseStatus.all_statuses
        cases = Case.get_cases_authorised(auth, perms, self.current_user, statuses)
        self.assertFalse(cases)

        auth = User.get(38) # 4 cases authorised, one auth pending
        cases = Case.get_cases_authorised(auth, perms, self.current_user, statuses)
        self.assertEqual(len(cases), 4)

        statuses = CaseStatus.PENDING
        cases = Case.get_cases_authorised(auth, perms, self.current_user, [statuses])
        self.assertEqual(len(cases), 1)

        auth = User.get(37) # 4 cases authorised, 1 is rejected
        statuses = CaseStatus.all_statuses
        cases = Case.get_cases_authorised(auth, perms, self.current_user, statuses)
        self.assertEqual(len(cases), 4)

        statuses = CaseStatus.approved_statuses
        cases = Case.get_cases_authorised(auth, perms, self.current_user, statuses)
        self.assertEqual(len(cases), 3)

        auth = User.get(3) # not an authoriser
        cases = Case.get_cases_authorised(auth, perms, self.current_user, statuses)
        self.assertFalse(cases)

        auth = User.get(37) # 4 cases authorised: 2 private, 1 rejected
        user = User.get(7) # user not allowed to see 1 private case
        statuses = CaseStatus.all_statuses
        cases = Case.get_cases_authorised(auth, perms, user, statuses)
        self.assertEqual(len(cases), 2)

    def test_properties_test_case(self):
        case = Case.get(1)
        self.assertIsNone(case.date_deadline)

        case = Case.get(4)
        deadline = case.creation_date + timedelta(days=30)
        self.assertEqual(case.date_deadline, ForemanOptions.get_date(deadline))

        case = Case.get(1)
        pcm = User.get(17)
        self.assertEqual(case.principle_case_manager.id, pcm.id)
        scm = User.get(18)
        self.assertEqual(case.secondary_case_manager.id, scm.id)

        cms = case.case_managers
        self.assertIn(pcm, cms)
        self.assertIn(scm, cms)

        req = User.get(27)
        self.assertEqual(case.requester.id, req.id)

        auth = User.get(37)
        self.assertEqual(case.authoriser.id, auth.id)

        case = Case.get(10)
        self.assertIsNone(case.principle_case_manager)
        self.assertIsNone(case.secondary_case_manager)
        self.assertFalse(case.case_managers[0])
        self.assertFalse(case.case_managers[1])

        case = Case.get(3)
        self.assertIsNone(case.requester)

        for case in Case.get_all():
            self.assertIsNotNone(case.authoriser)

    def test_statuses_test_case(self):
        case = Case.get(2)
        self.assertEqual(case.get_status().status, CaseStatus.OPEN)

        case = Case.get(5)
        self.assertEqual(case.get_status().status, CaseStatus.PENDING)

        case = Case.get(3)
        self.assertEqual(case.get_status().status, CaseStatus.CLOSED)

        case = Case.get(4)
        self.assertEqual(case.get_status().status, CaseStatus.ARCHIVED)

        case = Case.get(1)
        self.assertEqual(case.get_status().status, CaseStatus.CREATED)

        case = Case.get(10)
        self.assertEqual(case.get_status().status, CaseStatus.REJECTED)

    def test_links_test_case(self):
        case = Case.get(6)
        links = case.get_links()
        linkees = case.get_from_links()

        self.assertEqual(len(links), 1)
        self.assertEqual(len(linkees), 0)
        self.assertEqual(links[0].id, 5)

        case = Case.get(5)
        links = case.get_links()
        linkees = case.get_from_links()

        self.assertEqual(len(links), 0)
        self.assertEqual(len(linkees), 1)
        self.assertEqual(linkees[0].id, 6)

        # tests with permissions
        perms = BaseController.check_permissions
        user = User.get(4)
        case = Case.get(6)
        links = case.get_links(perm_checker=perms, user=user)

        self.assertEqual(len(links), 0) # linked case is private

    def test_user_perms_test_case(self):
        # test .get_user_roles()
        case = Case.get(1)
        roles = case.get_user_roles(17)[0]
        self.assertEqual(roles.role, UserCaseRoles.PRINCIPLE_CASE_MANAGER)

        self.assertFalse(case.get_user_roles(1))

        # test _check_perms()
        caseman = User.get(18)
        cases = Case.get_all()

        self.assertEqual(len(Case._check_perms(caseman, cases, BaseController.check_permissions)), 6)

        caseman = User.get(1)
        self.assertEqual(len(Case._check_perms(caseman, cases, BaseController.check_permissions)), 12)

    def test_case_requests_test_case(self):

        # test .get_num_cases_opened_on_date()
        date = Case.get(1).creation_date
        case_type = None
        status = CaseStatus.OPEN
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 4)

        status = CaseStatus.CLOSED
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 2)

        status = CaseStatus.ARCHIVED
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 2)

        status = CaseStatus.PENDING
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 12)

        status = CaseStatus.CREATED
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 8)

        status = CaseStatus.REJECTED
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 2)

        case_type = "Incident Response"
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 1)

        status = CaseStatus.ARCHIVED
        self.assertEqual(Case.get_num_cases_opened_on_date(date, status, case_type), 1)

        # test .cases_with_user_involved()
        user = User.get(3).id # investigator
        self.assertEqual(len(Case.cases_with_user_involved(user)), 8)
        self.assertEqual(len(Case.cases_with_user_involved(user, True)), 2)

        user = User.get(20).id # case manager
        self.assertEqual(len(Case.cases_with_user_involved(user)), 2)
        self.assertEqual(len(Case.cases_with_user_involved(user, True)), 0)

        # test .get_completed_cases()
        user = User.get(20)
        cases = Case.get_completed_cases(user, BaseController.check_permissions, self.current_user)
        self.assertIn(Case.get(3), cases)
        self.assertIn(Case.get(4), cases)
        self.assertNotIn(Case.get(5), cases)

        user = User.get(3) # not a case manager
        cases = Case.get_completed_cases(user, BaseController.check_permissions, self.current_user)
        self.assertFalse(cases)

        # test .get_current_cases()
        user = User.get(18)
        cases = Case.get_current_cases(user, BaseController.check_permissions, self.current_user)
        self.assertIn(Case.get(2), cases)
        self.assertIn(Case.get(1), cases)
        self.assertNotIn(Case.get(5), cases)

        user = User.get(4)  # not a case manager
        cases = Case.get_current_cases(user, BaseController.check_permissions, self.current_user)
        self.assertFalse(cases)

        # test .get_cases_requested()
        user = User.get(33)
        cases = Case.get_cases_requested(user, BaseController.check_permissions, self.current_user,
                                         CaseStatus.all_statuses)
        self.assertIn(Case.get(7), cases)
        self.assertNotIn(Case.get(5), cases)

        user = User.get(4)  # not a requester
        cases = Case.get_cases_requested(user, BaseController.check_permissions, self.current_user,
                                         CaseStatus.all_statuses)
        self.assertFalse(cases)

        # test .get_num_completed_case_by_user()
        user = User.get(18)
        start = Case.get(1).creation_date
        end = start + timedelta(days=1)
        status = CaseStatus.OPEN
        self.assertEqual(Case.get_num_completed_case_by_user(user, None, start, end, status), 1)

        status = CaseStatus.CREATED
        self.assertEqual(Case.get_num_completed_case_by_user(user, None, start, end, status), 2)

        status = CaseStatus.CLOSED
        self.assertEqual(Case.get_num_completed_case_by_user(user, None, start, end, status), 0)

        status = CaseStatus.CREATED
        self.assertEqual(Case.get_num_completed_case_by_user(user, "eDiscovery", start, end, status), 1)

        status = CaseStatus.CREATED
        self.assertEqual(Case.get_num_completed_case_by_user(user, "Other", start, end, status), 0)

        # test ._active_before_start()
        case = Case.get(1)
        user = User.get(17)
        self.assertTrue(case._active_before_start(user, case.creation_date))
        self.assertFalse(case._active_before_start(user, case.creation_date - timedelta(days=1)))

        # test ._active_after_end()
        case = Case.get(3)
        user = User.get(20)
        self.assertTrue(case._active_after_end(user, case.creation_date))
        self.assertFalse(case._active_after_end(user, case.creation_date + timedelta(days=1)))

        # test .active_user()
        case = Case.get(1)
        user = User.get(17)
        self.assertTrue(case.active_user(user, case.creation_date))
        self.assertFalse(case.active_user(user, case.creation_date - timedelta(days=1)))

        case = Case.get(3)
        user = User.get(20)
        self.assertTrue(case.active_user(user, case.creation_date))
        self.assertFalse(case.active_user(user, case.creation_date + timedelta(days=1)))

        # test .get_cases()
        status = "All"
        user = User.get(3)
        worker = True
        QA = False
        case_man = False
        perms = BaseController.check_permissions
        cases = Case.get_cases(status, user, worker, QA, perms, case_man) # all cases for user 3 as investigator
        self.assertEqual(len(cases), 8)

        QA = True
        cases = Case.get_cases(status, user, worker, QA, perms, case_man)  # all cases for user 3 as QA
        self.assertEqual(len(cases), 4)

        status = CaseStatus.CLOSED
        cases = Case.get_cases(status, user, worker, QA, perms, case_man)  # all cases for user 3 as QA
        self.assertEqual(len(cases), 2)

        status = "Workable"
        cases = Case.get_cases(status, user, worker, QA, perms, case_man)  # all cases for user 3 as QA
        self.assertEqual(len(cases), 0)

        worker = False
        QA = False
        status = "Queued"
        cases = Case.get_cases(status, user, worker, QA, perms, case_man) # cases with queued tasks
        self.assertEqual(len(cases), 2)

        status = CaseStatus.CREATED
        case_man = True
        cases = Case.get_cases(status, user, worker, QA, perms, case_man) # created cases with no case manager
        self.assertFalse(cases)

        # test .get_cases_requested_case_manager()
        case = Case.get(12)
        case_man = User.get(18)
        perms = BaseController.check_permissions

        cases = Case.get_cases_requested_case_manager(case_man, perms, self.current_user, [CaseStatus.PENDING])
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].id, case.id)

        case = Case.get(11)
        case_man = User.get(17)
        cases = Case.get_cases_requested_case_manager(case_man, perms, self.current_user, [CaseStatus.REJECTED])
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].id, case.id)

        case_man = User.get(18) # user has a rejected case but is secondary case manager
        cases = Case.get_cases_requested_case_manager(case_man, perms, self.current_user, [CaseStatus.REJECTED])
        self.assertFalse(cases)

        case = Case.get(5)
        case_man = User.get(21) # pending case and is primary case manager, but case has requestor
        perms = BaseController.check_permissions
        cases = Case.get_cases_requested_case_manager(case_man, perms, self.current_user, [CaseStatus.PENDING])
        self.assertFalse(cases)
