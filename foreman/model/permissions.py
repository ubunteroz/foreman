from userModel import UserRoles
from caseModel import CaseStatus, TaskStatus


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


class ArchivedEvidenceChecker(BaseChecker):
    def check(self, user, evidence):
        if evidence.case_id is not None:
            return evidence.case.status == CaseStatus.ARCHIVED
        else:
            return False


class ArchivedCaseChecker(BaseChecker):
    def check(self, user, case):
        return case.status == CaseStatus.ARCHIVED


class ClosedCaseChecker(BaseChecker):
    def check(self, user, case):
        return case.status == CaseStatus.CLOSED


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
    ('Case', 'request'): Or(AdminChecker(), RequesterChecker()),
    ('Case', 'view-all'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker()),
    ('Case', 'examiner'): Or(AdminChecker(), InvestigatorChecker(), QAChecker()),
    ('Case', 'edit'): And(Or(AdminChecker(), CaseManagerForCaseChecker()), Not(ArchivedCaseChecker())),
    ('Case', 'manage'): Or(AdminChecker(), CaseManagerChecker()),
    ('Case', 'close'): And(
                        Or(AdminChecker(),
                            CaseManagerForCaseChecker()),
                        And(
                            Or(Not(ArchivedCaseChecker()),
                                Not(ClosedCaseChecker())))),
    ('Case', 'view'): Or(
                        AdminChecker(),
                        And(
                            Or(CaseManagerChecker(),
                                InvestigatorChecker(),
                                QAChecker(),
                                RequesterForCaseChecker()),
                            Not(PrivateCaseChecker())),
                        And(
                            Or(InvestigatorForCaseChecker(),
                                QAForCaseChecker(),
                                RequesterForCaseChecker(),
                                CaseManagerForCaseChecker()),
                            PrivateCaseChecker())),
    ('Case', 'add'): Or(AdminChecker(), CaseManagerChecker(), RequesterChecker()),
    ('Task', 'edit'): And(Or(AdminChecker(), CaseManagerForTaskChecker()), Not(ArchivedTaskChecker())),
    ('Task', 'close'): And(Or(AdminChecker(), CaseManagerForTaskChecker()), Not(ArchivedTaskChecker())),
    ('Task', 'view-all'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker()),
    ('Task', 'view-qas'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker()),
    ('Task', 'view'): Or(
                        RequesterForTaskChecker(),
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
    ('Case', 'add-task'): Or(AdminChecker(), CaseManagerForCaseChecker(), RequesterForCaseChecker()),
    ('Task', 'work'): And(Or(AdminChecker(), CompleteInvestigationForTaskChecker()), Not(ArchivedTaskChecker())),
    ('Task', 'assign-self'): And(Or(AdminChecker(), StartInvestigationForTaskChecker()), Not(ArchivedTaskChecker())),
    ('Task', 'assign-other'): And(Or(AdminChecker(), CaseManagerForTaskChecker()), Not(ArchivedTaskChecker())),
    ('Task', 'qa'): And(Or(AdminChecker(), CompleteQAForTaskChecker()), Not(ArchivedTaskChecker())),
    ('Evidence', 'view-all'): Or(AdminChecker(), InvestigatorChecker(), QAChecker(), CaseManagerChecker()),
    ('Evidence', 'view'): Or(
                        AdminChecker(),
                        RequesterForEvidenceChecker(),
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
    ('Evidence', 'dis-associate'): And(Or(AdminChecker(), CaseManagerForEvidenceChecker()), Not(ArchivedEvidenceChecker())),
    ('Evidence', 'remove'): And(Or(AdminChecker(), CaseManagerForEvidenceChecker()), Not(ArchivedEvidenceChecker())),
    ('Evidence', 'edit'): And(
                            Or(AdminChecker(),
                                CaseManagerForEvidenceChecker(),
                                InvestigatorForEvidenceChecker(),
                                QAForEvidenceChecker()),
                            Not(ArchivedEvidenceChecker())),
    ('Evidence', 'check-in-out'): And(
                            Or(AdminChecker(),
                                CaseManagerForEvidenceChecker(),
                                InvestigatorForEvidenceChecker(),
                                QAForEvidenceChecker()),
                            Not(ArchivedEvidenceChecker())),
    ('Case', 'add-evidence'): Or(AdminChecker(), CaseManagerForCaseChecker(), InvestigatorForCaseChecker()),
    ('User', 'edit-password'): Or(AdminChecker(), UserIsCurrentUserChecker()),
    ('User', 'edit'): Or(AdminChecker(), UserIsCurrentUserChecker()),
    ('User', 'edit-roles'): AdminChecker(),
    ('User', 'add'): AdminChecker(),
    ('User', 'view-active-roles'): Or(AdminChecker()),
    ('User', 'view-changes'): Or(AdminChecker()),
    ('User', 'view-all'): AdminChecker(),
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
