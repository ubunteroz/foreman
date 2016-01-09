from userModel import UserRoles
from caseModel import CaseStatus, TaskStatus, ForemanOptions

class BaseChecker(object):
    def check(self, user, obj):
        raise NotImplemented("Must be overridden")


class UserIsCurrentUserChecker(BaseChecker):
    def check(self, user, obj):
        return user.id == obj.id


class AdminChecker(BaseChecker):
    def check(self, user, obj):
        return UserRoles.check_user_has_active_role(user, UserRoles.ADMIN)


class CaseManagerForCaseChecker(BaseChecker):
    def check(self, user, case):
        case_managers = case.case_managers
        both_none = True
        for case_manager in case_managers:
            if case_manager is not None:
                both_none = False
            if case_manager and user.id == case_manager.id:
                return True
        if both_none is True:
            return CaseManagerChecker().check(user, case)
        return False


class CaseManagerForTaskChecker(BaseChecker):
    def check(self, user, task):
        case_managers = task.case.case_managers
        for case_manager in case_managers:
            if case_manager and user.id == case_manager.id:
                return True
        return False


class CaseManagerForEvidenceChecker(BaseChecker):
    def check(self, user, evidence):
        if evidence.case_id is not None:
            case_managers = evidence.case.case_managers
            for case_manager in case_managers:
                if case_manager and user.id == case_manager.id:
                    return True
            return False
        else:
            return CaseManagerChecker().check(user, "None")


class CaseManagerChecker(BaseChecker):
    def check(self, user, obj):
        return UserRoles.check_user_has_active_role(user, UserRoles.CASE_MAN)


class InvestigatorForTaskChecker(BaseChecker):
    def check(self, user, task):
        if user.id in [inv.id for inv in task.investigators]:
            return True
        return False


class StartInvestigationForTaskChecker(BaseChecker):
    def check(self, user, task):
        if task.status in TaskStatus.notStarted and UserRoles.check_user_has_active_role(user, UserRoles.INV):
            return True
        return False


class CompleteInvestigationForTaskChecker(BaseChecker):
    def check(self, user, task):
        if user.id in [inv.id for inv in task.investigators] and task.status in TaskStatus.invRoles:
            return True
        return False


class InvestigatorForCaseChecker(BaseChecker):
    def check(self, user, obj):
        try:
            tasks = obj.tasks
        except AttributeError:
            try:
                tasks = obj.case.tasks
            except Exception:
                return False

        for task in tasks:
            if user.id in [inv.id for inv in task.investigators]:
                return True
        return False


class InvestigatorForEvidenceChecker(BaseChecker):
    def check(self, user, evidence):
        if evidence.case_id is not None:
            tasks = evidence.case.tasks
            for task in tasks:
                if user.id in [inv.id for inv in task.investigators]:
                    return True
            return False
        else:
            return InvestigatorChecker().check(user, "None")


class InvestigatorChecker(BaseChecker):
    def check(self, user, obj):
        return UserRoles.check_user_has_active_role(user, UserRoles.INV)


class QAForTaskChecker(BaseChecker):
    def check(self, user, task):
        if user.id in [inv.id for inv in task.QAs]:
            return True
        return False


class CompleteQAForTaskChecker(BaseChecker):
    def check(self, user, task):
        if user.id in [inv.id for inv in task.QAs] and task.status in TaskStatus.qaRoles:
            return True
        return False


class AddNotesForTaskChecker(BaseChecker):
    def check(self, user, task):
        if InvestigatorForTaskChecker().check(user, task) or QAForTaskChecker().check(user, task):
            if task.status in TaskStatus.notesAllowed:
                return True
        return False


class QAForEvidenceChecker(BaseChecker):
    def check(self, user, evidence):
        if evidence.case_id is not None:
            tasks = evidence.case.tasks
            for task in tasks:
                if user.id in [inv.id for inv in task.QAs]:
                    return True
            return False
        else:
            return QAChecker().check(user, "None")


class QAForCaseChecker(BaseChecker):
    def check(self, user, obj):
        try:
            tasks = obj.tasks
        except AttributeError:
            try:
                tasks = obj.case.tasks
            except Exception:
                return False
        for task in tasks:
            if user.id in [inv.id for inv in task.QAs]:
                return True
        return False


class AuthoriserForCaseChecker(BaseChecker):
    def check(self, user, case):
        authoriser = case.authoriser
        if authoriser and user.id == authoriser.id:
                return True
        return False


class AuthoriserForTaskChecker(BaseChecker):
    def check(self, user, task):
        authoriser = task.case.authoriser
        options = ForemanOptions.get_options()
        if options.auth_view_tasks and authoriser and user.id == authoriser.id:
                return True
        return False


class AuthoriserChecker(BaseChecker):
    def check(self, user, obj):
        return UserRoles.check_user_has_active_role(user, UserRoles.AUTH)


class QAChecker(BaseChecker):
    def check(self, user, obj):
        return UserRoles.check_user_has_active_role(user, UserRoles.QA)


class RequesterChecker(BaseChecker):
    def check(self, user, obj):
        return UserRoles.check_user_has_active_role(user, UserRoles.REQUESTER)


class RequesterForCaseChecker(BaseChecker):
    def check(self, user, case):
        requester_role = UserRoles.check_user_has_active_role(user, UserRoles.REQUESTER)
        requester_user = case.requester
        if requester_user is None:
            return False
        return requester_user.id == user.id and requester_role


class RequesterForTaskChecker(BaseChecker):
    def check(self, user, task):
        requester_role = UserRoles.check_user_has_active_role(user, UserRoles.REQUESTER)
        requester_user = task.case.requester
        if requester_user is None:
            return False
        else:
            return requester_user.id == user.id and requester_role


class RequesterForEvidenceChecker(BaseChecker):
    def check(self, user, evidence):
        if evidence.case_id is not None:
            requester_role = UserRoles.check_user_has_active_role(user, UserRoles.REQUESTER)
            requester_user = evidence.case.requester
            return requester_user.id == user.id and requester_role
        else:
            return False


class AuthoriserForEvidenceChecker(BaseChecker):
    def check(self, user, evidence):
        if evidence.case_id is not None:
            authoriser = evidence.case.authoriser
            options = ForemanOptions.get_options()
            if options.auth_view_evidence and authoriser and user.id == authoriser.id:
                return True
            return False
        return False


class PrivateEvidenceChecker(BaseChecker):
    def check(self, user, evidence):
        if evidence.case_id is not None:
            return evidence.case.private
        else:
            return False


class PrivateCaseChecker(BaseChecker):
    def check(self, user, case):
        return case.private


class PrivateTaskChecker(BaseChecker):
    def check(self, user, task):
        return task.case.private


class ArchivedTaskChecker(BaseChecker):
    def check(self, user, task):
        return task.case.status == CaseStatus.ARCHIVED


class ArchivedCaseChecker(BaseChecker):
    def check(self, user, case):
        if case:
            return case.status == CaseStatus.ARCHIVED
        else:
            return False


class ClosedCaseChecker(BaseChecker):
    def check(self, user, case):
        if case:
            return case.status == CaseStatus.CLOSED
        else:
            return False


class RejectedCaseChecker(BaseChecker):
    def check(self, user, case):
        if case:
            return case.status == CaseStatus.REJECTED
        else:
            return False


class NotApprovedCaseChecker(BaseChecker):
    def check(self, user, case):
        if case:
            return case.status == CaseStatus.PENDING
        else:
            return False


class CaseEditableChecker(BaseChecker):
    def check(self, user, case):
        return ArchivedCaseChecker().check(user, case) or RejectedCaseChecker().check(user, case) or \
               NotApprovedCaseChecker().check(user, case)


class TaskEditableChecker(BaseChecker):
    def check(self, user, task):
        return ArchivedCaseChecker().check(user, task.case) or RejectedCaseChecker().check(user, task.case) or \
               NotApprovedCaseChecker().check(user, task.case)


class EvidenceEditableChecker(BaseChecker):
    def check(self, user, evidence):
        return ArchivedCaseChecker().check(user, evidence.case) or RejectedCaseChecker().check(user, evidence.case) or \
               NotApprovedCaseChecker().check(user, evidence.case)


class CaseApprovedChecker(BaseChecker):
    def check(self, user, case):
        if case.status in CaseStatus.approved_statuses:
            return True
        return False


class UserIsManager(BaseChecker):
    def check(self, manager, obj):
        return manager.is_a_manager()


class UserIsManagerOf(BaseChecker):
    def check(self, manager, user):
        return manager.is_manager_of(user)


class Not(BaseChecker):
    checker = None

    def __init__(self, checker):
        self.checker = checker

    def check(self, user, obj):
        return not self.checker.check(user, obj)


class Or(BaseChecker):
    checkers = None

    def __init__(self, *checkers):
        self.checkers = checkers

    def check(self, user, obj):
        for checker in self.checkers:
            if checker.check(user, obj):
                return True
        return False


class And(BaseChecker):
    checkers = None

    def __init__(self, *checkers):
        self.checkers = checkers

    def check(self, user, obj):
        for checker in self.checkers:
            if not checker.check(user, obj):
                return False
        return True

permissions = {
    ('Case', 'admin'): AdminChecker(),
    ('Case', 'report'): Or(AdminChecker(), InvestigatorForCaseChecker(), CaseManagerForCaseChecker(),
                           QAForCaseChecker()),
    ('Case', 'view-all'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker(),
                             RequesterChecker(), AuthoriserChecker()),
    ('Case', 'edit'): And(Or(AdminChecker(),
                             And(CaseManagerForCaseChecker(), CaseApprovedChecker()),
                             And(RequesterForCaseChecker())),
                          Not(ArchivedCaseChecker()), Not(RejectedCaseChecker())),
    ('Case', 'close'): And(
                        Or(AdminChecker(),
                            CaseManagerForCaseChecker()),
                        And(
                            Or(Not(ArchivedCaseChecker()),
                                Not(ClosedCaseChecker())))),
    ('Case', 'view'): Or(
                        AdminChecker(),
                        AuthoriserForCaseChecker(),
                        And(
                            CaseApprovedChecker(),
                            Or(CaseManagerChecker(),
                                InvestigatorChecker(),
                                QAChecker(),
                                RequesterForCaseChecker()),
                            Not(PrivateCaseChecker())),
                        And(
                            CaseApprovedChecker(),
                            Or(InvestigatorForCaseChecker(),
                                QAForCaseChecker(),
                                RequesterForCaseChecker(),
                                CaseManagerForCaseChecker()),
                            PrivateCaseChecker()),
                        And(
                            Not(CaseApprovedChecker()), RequesterForCaseChecker())),
    ('Case', 'add'): Or(AdminChecker(), CaseManagerChecker(), RequesterChecker()),
    ('Case', 'authorise'): AuthoriserForCaseChecker(),
    ('Task', 'edit'): And(Or(AdminChecker(), CaseManagerForTaskChecker()), Not(TaskEditableChecker())),
    ('Task', 'close'): And(Or(AdminChecker(), CaseManagerForTaskChecker()), Not(ArchivedTaskChecker())),
    ('Task', 'view-all'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker()),
    ('Task', 'view-qas'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker()),
    ('Task', 'view'): Or(
                        RequesterForTaskChecker(),
                        AuthoriserForTaskChecker(),
                        AdminChecker(),
                        And(
                            Or(CaseManagerChecker(),
                                InvestigatorChecker(),
                                QAChecker()),
                            Not(PrivateTaskChecker())),
                        And(
                            Or(InvestigatorForCaseChecker(),
                                QAForCaseChecker(),
                                CaseManagerForTaskChecker()),
                            PrivateTaskChecker())),
    ('Case', 'add-task'): And(Or(AdminChecker(), CaseManagerForCaseChecker(), RequesterForCaseChecker()),
                              Not(CaseEditableChecker())),
    ('Task', 'work'): And(Or(AdminChecker(), CompleteInvestigationForTaskChecker()), Not(TaskEditableChecker())),
    ('Task', 'add_notes'): And(Or(AdminChecker(), AddNotesForTaskChecker()), Not(TaskEditableChecker())),
    ('Task', 'add_file'): And(Or(AdminChecker(), CompleteInvestigationForTaskChecker(),
                                    CaseManagerForTaskChecker()), Not(TaskEditableChecker())),
    ('Task', 'delete_file'): And(Or(AdminChecker(), CompleteInvestigationForTaskChecker(),
                                    CaseManagerForTaskChecker()), Not(TaskEditableChecker())),
    ('Task', 'assign-self'): And(Or(AdminChecker(), StartInvestigationForTaskChecker()), Not(TaskEditableChecker())),
    ('Task', 'assign-other'): And(Or(AdminChecker(), CaseManagerForTaskChecker()), Not(TaskEditableChecker())),
    ('Case', 'can-assign'): And(Or(AdminChecker(), CaseManagerForCaseChecker()), Not(CaseEditableChecker())),
    ('Task', 'qa'): And(Or(AdminChecker(), CompleteQAForTaskChecker()), Not(TaskEditableChecker())),
    ('Evidence', 'view-all'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker()),
    ('Evidence', 'view'): Or(
                        AdminChecker(),
                        RequesterForEvidenceChecker(),
                        AuthoriserForEvidenceChecker(),
                        And(
                            Or(CaseManagerChecker(),
                                InvestigatorChecker(),
                                QAChecker()),
                            Not(PrivateEvidenceChecker())),
                        And(
                            Or(InvestigatorForEvidenceChecker(),
                                QAForEvidenceChecker(),
                                CaseManagerForEvidenceChecker()),
                            PrivateTaskChecker())),
    ('Evidence', 'add_file'): And(Or(AdminChecker(), InvestigatorForEvidenceChecker(), QAForEvidenceChecker(),
                                    CaseManagerForEvidenceChecker()), Not(EvidenceEditableChecker())),
    ('Evidence', 'delete_file'): And(Or(AdminChecker(), InvestigatorForEvidenceChecker(), QAForEvidenceChecker(),
                                    CaseManagerForTaskChecker()), Not(EvidenceEditableChecker())),
    ('Evidence', 'associate'): And(Or(AdminChecker(), CaseManagerChecker(), InvestigatorChecker()),
                                   Not(EvidenceEditableChecker())),
    ('Evidence', 'dis-associate'): And(Or(AdminChecker(), CaseManagerForEvidenceChecker(),
                                          InvestigatorForEvidenceChecker()), Not(EvidenceEditableChecker())),
    ('Evidence', 'remove'): And(Or(AdminChecker(), CaseManagerChecker()), Not(EvidenceEditableChecker())),
    ('Evidence', 'add'): And(Or(AdminChecker(), InvestigatorChecker(), CaseManagerChecker())),
    ('Evidence', 'edit'): And(
                            Or(AdminChecker(),
                            And(
                                Or(CaseManagerChecker(),
                                    InvestigatorChecker(),
                                    QAChecker()),
                                Not(PrivateEvidenceChecker())),
                            And(
                                Or(InvestigatorForEvidenceChecker(),
                                    QAForEvidenceChecker(),
                                    CaseManagerForEvidenceChecker()),
                                PrivateTaskChecker())),
                            Not(EvidenceEditableChecker())),
    ('Evidence', 'check-in-out'): And(
                            Or(AdminChecker(),
                                CaseManagerForEvidenceChecker(),
                                InvestigatorForEvidenceChecker(),
                                QAForEvidenceChecker()),
                            Not(EvidenceEditableChecker())),
    ('Case', 'add-evidence'): And(Or(AdminChecker(), CaseManagerForCaseChecker(), InvestigatorForCaseChecker()),
                                 Not(CaseEditableChecker())),
    ('User', 'edit-password'): Or(AdminChecker(), UserIsCurrentUserChecker()),
    ('User', 'edit'): Or(AdminChecker(), UserIsCurrentUserChecker()),
    ('User', 'edit-roles'): AdminChecker(),
    ('User', 'add'): AdminChecker(),
    ('User', 'view-active-roles'): Or(AdminChecker(), UserIsManagerOf()),
    ('User', 'view-changes'): Or(AdminChecker()),
    ('User', 'view-all'): AdminChecker(),
    ('User', 'view_directs_timesheets'): Or(AdminChecker(), UserIsManager()),
    ('User', 'view_timesheet'): Or(AdminChecker(), UserIsCurrentUserChecker(), UserIsManagerOf()),
    ('User', 'edit_timesheet'): Or(AdminChecker(), UserIsCurrentUserChecker()),
    ('User', 'view-history'): Or(AdminChecker(), CaseManagerChecker(), InvestigatorChecker(), QAChecker(),
                                 UserIsCurrentUserChecker()),
    ('Report', 'view'): Or(AdminChecker(), CaseManagerChecker())
}


def has_permissions(user, obj, action):

    if isinstance(obj, basestring):
        obj_class_name = obj
    else:
        obj_class_name = obj.__class__.__name__  # Get class name of the object

    checker = permissions[(obj_class_name, action)]
    return checker.check(user, obj)
