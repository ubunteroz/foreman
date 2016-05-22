# foreman imports
from foreman.model import User, ForemanOptions, UserRoles, Case, UserCaseRoles, CaseType, EvidenceStatus, CaseStatus
from foreman.model import TaskType, Task, TaskStatus, UserTaskRoles, EvidenceType, Evidence, EvidencePhotoUpload
from utils import session, config, ROOT_DIR
from random import randint
from os import path, mkdir, stat
import shutil
from datetime import datetime
import population

now = datetime.now()


def create_test_cases(case_managers, requestors, investigators, authorisers):
    backgrounds = [
        """Employee {} has been accused of harassment and bullying. Please conduct an investigation into the
         matter. """,
        """It is believed that employee {} has been surfing inappropriate websites during their lunch break.
        Please provide a report on their internet activities and anything else that may be required.""",
        """We believe that employee {} has a virus on their workstation RFHSHFS35eee.
        The IDS system has picked up on unusually high volumes of encrypted internet traffic. Please quarantine this
        machine and investigate the malware. """,
        """All emails between the employee {} and the external company 'Avaba' to be searched, as well as all documents on
        the employee home drives and network drives searched for any connections with this company.""",
        """An employee {} is leaving the firm next week and has sent out a large number of emails with attachments.
        We suspect this might be business related data; but they have encrypted the attachments so we cannot tell.
        Please conduct an investigation into all emails sent outwith the firm as well as any printing activity and
        removable media activity. """,
        """Employee {} is suspected to be involved with fraudulent activity. Please investigate their machine to find
        any user-made documents.""",
        """Employee {} is on gardening leave, however a colleague suspects they have logged in remotely from home.
        Please investigate all user access logs to ascertain if this is true. """,
        """Employee {} has complained to the help-desk that a virus has encrypted all her files. Please investigate is
        this is Cryptolocker or similar and if we can recover the files.""",
        """Employee {} has sent an encrypted file to her personal email address and the email was labeled "confidential".
        Please retrieve this email and password crack the contents.""",
        """Unusual activity - file edits, name changes, deletions, has occurred on the drive //share01/network/001. Please investigate this
        activity. """]
    justifications = [
        "This case is required by the Legal department as part of a civil case where disclosure of information is required.",
        "This case is required as policy dictates any gross misconduct must be investigated by the internal forensics team.",
        "This project is justified as it has been approved by the CEO."]
    random_users = ['Madalene Kuta','Margarite Singley','Rodger Ruzicka','Kamilah Moriarity',
                    'Eleni Brwon','Kayce Linquist', 'Sanora Kocher','Eldridge Alaniz','Ivan Guard',
                    'Trevor Parramore','Thea Wiles','Gayla Bomgardner','Arvilla Cun', 'Tara Marse',
                    'Leona Dhillon','Lidia Joo','Shaunte Frieden','Margareta Beauchamp',
                    'Kai Carnley','Kelsey Proffit','Pauline Strout','Krystin Viola','Tammie Funchess',
                    'Callie Doris', 'Zenobia Fralick', 'Max Kittle','Calvin Mcfalls', 'Ted Duwe',
                    'Melanie Pittsley','Galen Howton', 'Beulah Colgan', 'Faith Goin', 'Adelia Horiuchi',
                    'Karma Mader', 'Johnathan Mcnulty','Brandon Zuniga', 'Freddie Clune', 'Shani Santee',
                    'Ann Ackerman','Rodrigo Vanscyoc','Garrett Trudel','Stephenie Hurla','Travis Yokum',
                    'Clara Borkholder','Olin Kyles', 'Heriberto Slye','Ashley Tweed','Shanell Sikora',
                    'Karissa Pompei','Gema Shears']
    print "Adding 10 cases:"
    for i in xrange(0, 10):
        case_manager = case_managers[i]
        requestor = requestors[i]
        justification = justifications[i%3]
        background = backgrounds[i]
        rand_user = random_users[i]
        background = background.replace("{}", rand_user)
        classification = "Confidential"
        case_type = CaseType.get_case_types()[i%6]
        private = i%2
        if private == 0:
            is_private = True
        else:
            is_private = False
        new_case = Case(ForemanOptions.get_next_case_name(), requestor, background=background, reference=None,
                        private=is_private, location=None, classification=classification, case_type=case_type,
                        justification=justification)
        session.add(new_case)
        session.flush()
        new_case.add_change(requestor)
        session.commit()
        auth = authorisers[randint(0, len(authorisers) - 1)]

        UserCaseRoles(auth, new_case, UserCaseRoles.AUTHORISER)
        new_case.authorise(auth, "Case Creation", "PENDING")

        n = UserCaseRoles(requestor, new_case, UserCaseRoles.REQUESTER)
        n.add_change(requestor)
        n1 = UserCaseRoles(case_manager, new_case, UserCaseRoles.PRINCIPLE_CASE_MANAGER)
        n1.add_change(requestor)

        if i%2 == 0:
            case_manager_2 = case_managers[(i+1)%10]
            n1 = UserCaseRoles(case_manager_2, new_case, UserCaseRoles.SECONDARY_CASE_MANAGER)
            n1.add_change(case_manager)
        session.flush()

        new_case.authorise(auth, "Looks acceptable. Please go ahead.", "AUTH")

        if i%4 == 1 and i != 9:
            new_case.set_status(CaseStatus.OPEN, new_case.principle_case_manager)
        if i%4 == 2:
            new_case.set_status(CaseStatus.CLOSED, new_case.principle_case_manager)
        if i%4 == 3:
            new_case.set_status(CaseStatus.ARCHIVED, new_case.principle_case_manager)
        print "Case added to Foreman."

        if i < 9:
            inv = create_test_tasks(new_case, investigators, rand_user, i if i > 4 else 4)
        else:
            create_test_tasks(new_case, investigators, rand_user, 1, progress=False)
        create_evidence(new_case, inv, rand_user, i)
    session.commit()


def generate_task_background(task_type, rand_user):
    keywords = ['Accountant', 'Acid test ratio', 'Autocratic management', 'Production', 'Value Chain', 'Optimal',
                'fraudulent', 'misjudged', 'fraud*', 'innocent', 'guilty', 'hate OR hatred', 'boss', 'manager sucks',
                'waste of time', '(bored OR boredom) AND leave', 'court OR law OR lawyer', 'oppotunity', 'golden',
                'fired OR redundant OR loss OR quit', 'revenge', 'attack AND management']
    keyword = keywords[randint(0, len(keywords)/2):randint(len(keywords)/2, len(keywords) - 1)]
    if "search" in task_type.lower():
        return "Please conduct one {} for employee {}. The search terms are: {}".format(task_type.lower(), rand_user,
                                                                                        "<br/>".join(keyword))
    elif "analysis" in task_type.lower():
        out =  "Please conduct {}. ".format(task_type.lower())
        if "machine" in task_type.lower() or "mobile" in task_type.lower() or "tablet" in task_type.lower():
            out += "The evidence will be delivered to your lab in the next few working days. "
        return out
    elif "image" in task_type.lower() or "capture" in task_type.lower():
        return "Please create a {} for further analysis.".format(task_type.lower())
    elif "logs" in task_type.lower():
        return "Please analyse the {} to determine any suspicious activity.".format(task_type.lower())
    else:
        return "Please conduct a {} analysis.".format(task_type.lower())


def create_test_tasks(case, investigators, rand_user, i, progress=True):
    task_types = TaskType.get_all().all()
    numTasks = i
    inv = case.principle_case_manager
    for x in range(0, numTasks):
        task_type = task_types[x]
        task_name = ForemanOptions.get_next_task_name(case)
        task_background = generate_task_background(task_type.task_type, rand_user)
        new_task = Task(case, task_type, task_name, case.principle_case_manager, background=task_background)
        session.add(new_task)
        print "\tTask added to Case."
        session.flush()
        new_task.add_change(case.principle_case_manager)

        if progress is True:
            new_task.set_status(TaskStatus.QUEUED, case.principle_case_manager)
        if progress is True and (x >= 1 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED):
            new_task.set_status(TaskStatus.ALLOCATED, case.principle_case_manager)
            inv = investigators[x]
            qa = investigators[(x+1) % i]
            u = UserTaskRoles(inv, new_task, UserTaskRoles.PRINCIPLE_INVESTIGATOR)
            u1 = UserTaskRoles(qa, new_task, UserTaskRoles.PRINCIPLE_QA)
            session.add(u)
            session.add(u1)
            session.flush()
            u.add_change(case.principle_case_manager)
            u1.add_change(case.principle_case_manager)
            session.commit()

            if x % 3 == 0:
                inv2 = investigators[(x+2) % i]
                u2 = UserTaskRoles(inv2, new_task, UserTaskRoles.SECONDARY_INVESTIGATOR)
                session.add(u2)
                session.flush()
                u2.add_change(case.principle_case_manager)
                session.commit()
            else:
                inv2 = None

            if x % 3 == 1:
                qa2 = investigators[(x+3) % i]
                u3 = UserTaskRoles(qa2, new_task, UserTaskRoles.SECONDARY_QA)
                session.add(u3)
                session.flush()
                u3.add_change(case.principle_case_manager)
                session.commit()

            if x >= 2 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                new_task.set_status(TaskStatus.PROGRESS, new_task.principle_investigator)
            if x >= 3 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                new_task.set_status(TaskStatus.QA, new_task.principle_investigator)
            if x >= 4 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                new_task.pass_QA("Well done, case work looks fine.", new_task.principle_QA)
                if new_task.secondary_QA:
                    new_task.pass_QA("I agree, all looks good. QA pass.", new_task.secondary_QA)
            if x >= 5 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                new_task.set_status(TaskStatus.COMPLETE, new_task.principle_investigator)
                if case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                    new_task.set_status(TaskStatus.CLOSED, case.principle_case_manager)
    return inv


def create_evidence(case, inv, rand_user, num):
    numEvidence = num % 3
    ref = 1
    for i in range(0, numEvidence):
        evi = EvidenceType.get_evidence_types()[num]
        e = Evidence(case, case.case_name + "-SCH-20140228-HDD_00" + str(ref), evi,
                     "Hard drive from {}'s main machine".format(rand_user),
                     case.requester.fullname, "Main Evidence Cabinet",
                     case.principle_case_manager, "B0000"+str(i), True)
        ref += 1
        session.add(e)
        print "\tEvidence added to case."
        e.add_change(case.principle_case_manager)
        session.flush()
        e.create_qr_code()
        e.check_in(inv.fullname, inv, now, "Initial check in to the storage cabinet")

        photo_location = path.abspath(path.join(ROOT_DIR, "files", "evidence_photos", str(e.id)))
        shutil.copy(path.join(ROOT_DIR, "static", "example_images", "evidence_example (1).jpg"), photo_location)
        upload = EvidencePhotoUpload(inv.id, e.id, "evidence_example (1).jpg", "A comment", "Image")
        session.add(upload)
        session.commit()

        if case.status == CaseStatus.ARCHIVED:
            e.set_status(EvidenceStatus.ARCHIVED, inv)
            session.flush()
        session.commit()

def disassociate_evidence(inv):
    evidence = Evidence.get(4)
    evidence.case_id = None
    session.flush()

    evidence = Evidence.get(5)
    evidence.check_out(inv.fullname, inv, now, "out")

def create_test_data():
    population.load_initial_values_test()
    admin = population.create_admin_user()
    investigators = population.create_test_investigators(admin)
    case_managers = population.create_test_case_managers(admin)
    requestors = population.create_test_requestors(admin)
    authorisers = population.create_test_authorisers(admin)
    create_test_cases(case_managers, requestors, investigators, authorisers)
    disassociate_evidence(investigators[1])