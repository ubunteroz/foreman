# foreman imports
from foreman.model import User, ForemanOptions, UserRoles, Case, UserCaseRoles, CaseType, CaseClassification, CaseStatus
from foreman.model import TaskType, Task, TaskStatus, UserTaskRoles, EvidenceType, Evidence, TaskUpload
from foreman.model import EvidencePhotoUpload, Department, Team
from utils import session, config, ROOT_DIR
from random import randint
from os import path, mkdir, stat
import shutil
from datetime import datetime, timedelta


def create_admin_user():
    admin = User("administrator", "changeme", "The", "Administrator", config.get('admin', 'admin_email'),
                 validated=True)
    session.add(admin)
    session.flush()
    admin.team = Team.get(1)
    admin.job_title = "Administrator"

    admin_role = UserRoles(admin, "Administrator", False)
    session.add(admin_role)
    session.flush()

    for role in UserRoles.roles:
        if role != "Administrator":
            new_role = UserRoles(admin, role, True)
            session.add(new_role)
            session.flush()

    admin.add_change(admin)
    session.flush()

    session.commit()
    return admin


def load_initial_values():
    opts = ForemanOptions("%d %b %Y %H:%M:%S %Z", r"C:\Foreman", "DateNumericIncrement", "NumericIncrement", "A Large Company",
                          "Investigations")
    session.add(opts)
    session.flush()
    session.commit()

    dep = Department("Forensics Department")
    session.add(dep)
    session.commit()
    t = Team("Forensics Team", dep)
    session.add(t)
    session.commit()


def load_initial_values_test():
    opts = ForemanOptions("%d %b %Y %H:%M:%S", r"C:\Foreman", "FromList", "NumericIncrement", "Wordwide Forensics Inc",
                          "Investigations & Digital Forensics Department", c_leading_zeros=3,
                          t_leading_zeros=2,
                          c_list_location=path.abspath(path.join(ROOT_DIR, "utils", "test_case_names.txt")))
    session.add(opts)
    session.flush()
    session.commit()

    deps = [('IT Security', ['Investigations & Digital Forensics', 'CERT Team', 'Security Operations Centre']),
            ('Human Resources', ['HR Complaints']), ('Internal Audit', ['Fraud Prevention', 'Investigations']),
            ('Legal', ['Litigation'])]
    for department, teams in deps:
        dep = Department(department)
        session.add(dep)
        session.commit()
        for team in teams:
            t = Team(team, dep)
            session.add(t)
            session.commit()


def create_test_investigators(admin):
    u1 = User("holmess", "password", "Sherlock", "Holmes", "sherlock.holmes@example.org", validated=True)
    u2 = User("barnabyt", "password", "Tom", "Barnaby", "thomas.barnaby@example.org", validated=True)
    u3 = User("wexfordr", "password", "Reginald", "Wexford", "reginald.wexford@example.org", validated=True)
    u4 = User("bergeracj", "password", "Jim", "Bergerac", "jim.bergerac@example.org", validated=True)
    u5 = User("cagneyc", "password", "Christine", "Cagney", "christine.cagney@example.orgk", validated=True)
    u6 = User("columbof", "password", "Frank", "Columbo", "frank.columbo@example.org", validated=True)
    u7 = User("poiroth", "password", "Hercule", "Poirot", "hercule.poirot@example.org", validated=True)
    u8 = User("frostj", "password", "Jack", "Frost", "jack.frost@example.org", validated=True)
    u9 = User("huntg", "password", "Gene", "Hunt", "gene.hunt@example.org", validated=True)
    u10 = User("lunds", "password", "Sarah", "Lund", "sarah.lund@example.org", validated=True)
    u11 = User("mcnultyj", "password", "Jimmy", "McNulty", "james.mcnulty@example.org", validated=True)
    u12 = User("montalbanos", "password", "Salvo", "Montalbano", "salvo.montalbano@example.org", validated=True)
    u13 = User("morsee", "password", "Endeavour", "Morse", "endeavour.morse@example.org", validated=True)
    u14 = User("rebusj", "password", "John", "Rebus", "john.rebus@example.org", validated=True)
    u15 = User("taylorm", "password", "Mac", "Taylor", "mac.taylor@example.org", validated=True)
    session.add(u1)
    session.add(u2)
    session.add(u3)
    session.add(u4)
    session.add(u5)
    session.add(u6)
    session.add(u7)
    session.add(u8)
    session.add(u9)
    session.add(u10)
    session.add(u11)
    session.add(u12)
    session.add(u13)
    session.add(u14)
    session.add(u15)
    session.flush()
    u1.add_change(admin)
    u2.add_change(admin)
    u3.add_change(admin)
    u4.add_change(admin)
    u5.add_change(admin)
    u6.add_change(admin)
    u7.add_change(admin)
    u8.add_change(admin)
    u9.add_change(admin)
    u10.add_change(admin)
    u11.add_change(admin)
    u12.add_change(admin)
    u13.add_change(admin)
    u14.add_change(admin)
    u15.add_change(admin)
    session.flush()
    session.commit()
    investigators = [u1, u2, u3, u4, u5, u6, u7, u8, u9, u10, u11, u12, u13, u14, u15]

    managers=[]
    for u in investigators:
        sen = randint(0,5)
        if sen == 5:
            u.job_title = "Forensic Investigations Manager"
            managers.append(u)
        elif sen == 3 or sen == 4:
            u.job_title = "Senior Forensic Investigator"
        else:
            u.job_title = "Forensic Investigator"
        u.team = Team.get_filter_by(team='Investigations & Digital Forensics').first()
        u.add_change(admin)

        ur1 = UserRoles(u, "Investigator", False)
        ur2 = UserRoles(u, "QA", False)
        ur3 = UserRoles(u, "Case Manager", True)
        ur4 = UserRoles(u, "Requester", True)
        ur5 = UserRoles(u, "Authoriser", True)
        ur6 = UserRoles(u, "Administrator", True)
        session.add(ur1)
        session.add(ur2)
        session.add(ur3)
        session.add(ur4)
        session.add(ur5)
        session.add(ur6)
        session.flush()
        ur1.add_change(admin)
        ur2.add_change(admin)
        ur3.add_change(admin)
        ur4.add_change(admin)
        ur5.add_change(admin)
        ur6.add_change(admin)
        session.flush()
    session.commit()

    for inv in investigators:
        if inv in managers:
            inv.manager = admin
        else:
            inv.manager = managers[randint(0, len(managers)-1)]

    print "15 Investigators added to Foreman."
    return investigators


def create_test_case_managers(admin):
    u1 = User("gatesw", "password", "Bill", "Gates", "william.gates@example.org", validated=True)
    u2 = User("heluc", "password", "Carlos", "Helu", "carlos.slim-helu@example.org", middle="Slim", validated=True)
    u3 = User("geonaa", "password", "Amancio", "Gaona", "amancio.gaona@example.org", validated=True)
    u4 = User("buffettw", "password", "Warren", "Buffett", "warren.buffett@example.org", validated=True)
    u5 = User("desmaraisj", "password", "Jacqueline", "Desmarais", "jacqueline.desmarais@example.orgk", validated=True)
    u6 = User("ellisonl", "password", "Larry", "Ellison", "larry.ellison@example.org", validated=True)
    u7 = User("kochc", "password", "Charles", "Koch", "charles.koch@example.org", validated=True)
    u8 = User("kochd", "password", "David", "Koch", "david.koch@example.org", validated=True)
    u9 = User("adelson", "password", "Sheldon", "Adelson", "sheldon.adelson@example.org", validated=True)
    u10 = User("walton", "password", "Christy", "Walton", "christy.walton@example.org", validated=True)
    session.add(u1)
    session.add(u2)
    session.add(u3)
    session.add(u4)
    session.add(u5)
    session.add(u6)
    session.add(u7)
    session.add(u8)
    session.add(u9)
    session.add(u10)
    session.flush()
    u1.add_change(admin)
    u2.add_change(admin)
    u3.add_change(admin)
    u4.add_change(admin)
    u5.add_change(admin)
    u6.add_change(admin)
    u7.add_change(admin)
    u8.add_change(admin)
    u9.add_change(admin)
    u10.add_change(admin)
    session.flush()
    session.commit()
    case_managers = [u1, u2, u3, u4, u5, u6, u7, u8, u9, u10]

    managers = []
    for u in case_managers:
        sen = randint(0,5)
        if sen == 5:
            u.job_title = "Forensic Case Manager Lead"
            managers.append(u)
        elif sen == 3 or sen == 4:
            u.job_title = "Senior Forensic Case Manager"
        else:
            u.job_title = "Forensic Case Manager"
        u.team = Team.get_filter_by(team='Investigations & Digital Forensics').first()
        u.add_change(admin)

        ur1 = UserRoles(u, "Investigator", True)
        ur2 = UserRoles(u, "QA", True)
        ur3 = UserRoles(u, "Case Manager", False)
        ur4 = UserRoles(u, "Requester", True)
        ur5 = UserRoles(u, "Authoriser", True)
        ur6 = UserRoles(u, "Administrator", True)
        session.add(ur1)
        session.add(ur2)
        session.add(ur3)
        session.add(ur4)
        session.add(ur5)
        session.add(ur6)
        session.flush()
        ur1.add_change(admin)
        ur2.add_change(admin)
        ur3.add_change(admin)
        ur4.add_change(admin)
        ur5.add_change(admin)
        ur6.add_change(admin)
        session.flush()
    session.commit()

    for inv in case_managers:
        if inv in managers:
            inv.manager = admin
        else:
            inv.manager = managers[randint(0, len(managers)-1)]

    print "10 Case Managers added to Foreman."
    return case_managers


def create_test_authorisers(admin):
    u1 = User("presleye", "password", "Elvis", "Presley", "elvis.presley@example.org", validated=True)
    u2 = User("johne", "password", "Elton", "John", "elton.john@example.org", validated=True)
    u3 = User("sinatraf", "password", "Frank", "Sinatra", "frank.sinatra@example.org", validated=True)
    u4 = User("lennoxa", "password", "Annie", "Lennox", "annie.lennox@example.org", validated=True)
    session.add(u1)
    session.add(u2)
    session.add(u3)
    session.add(u4)
    session.flush()
    u1.add_change(admin)
    u2.add_change(admin)
    u3.add_change(admin)
    u4.add_change(admin)
    session.flush()
    session.commit()
    authorisers = [u1, u2, u3, u4]

    job_types = ["Head of Department", "Team Lead"]

    for u in authorisers:
        job = randint(0,1)
        team = randint(0,5)
        u.job_title = job_types[job]
        u.team = Team.get_all().all()[team]

        u.add_change(admin)
        ur1 = UserRoles(u, "Investigator", True)
        ur2 = UserRoles(u, "QA", True)
        ur3 = UserRoles(u, "Case Manager", True)
        ur4 = UserRoles(u, "Requester", True)
        ur5 = UserRoles(u, "Authoriser", False)
        ur6 = UserRoles(u, "Administrator", True)
        session.add(ur1)
        session.add(ur2)
        session.add(ur3)
        session.add(ur4)
        session.add(ur5)
        session.add(ur6)
        session.flush()
        ur1.add_change(admin)
        ur2.add_change(admin)
        ur3.add_change(admin)
        ur4.add_change(admin)
        ur5.add_change(admin)
        ur6.add_change(admin)
        session.flush()
    session.commit()
    print "4 Authorisers added to Foreman."
    return authorisers


def create_test_requestors(admin):
    u1 = User("mayweatherf", "password", "Floyd", "Mayweather", "floyd.mayweather@example.org", validated=True)
    u2 = User("ronaldoc", "password", "Cristiano", "Ronaldo", "cristiano.ronaldo@example.org", middle="Slim",
              validated=True)
    u3 = User("jamesl", "password", "LeBron", "James", "lebron.james@example.org", validated=True)
    u4 = User("messil", "password", "Lionel", "Messi", "lionel.messi@example.org", validated=True)
    u5 = User("bryantk", "password", "Kobe", "Bryant", "kobe.bryant@example.orgk", validated=True)
    u6 = User("woodst", "password", "Tiger", "Woods", "tiger.woods@example.org", validated=True)
    u7 = User("federerr", "password", "Roger", "Federer", "roger.federer@example.org", validated=True)
    u8 = User("mickelsonp", "password", "Phil", "Mickelson", "phil.mickelson@example.org", validated=True)
    u9 = User("nadalr", "password", "Rafael", "Nadal", "rafael.nadal@example.org", validated=True)
    u10 = User("ryanm", "password", "Matt", "Ryan", "matt.ryan@example.org", validated=True)
    session.add(u1)
    session.add(u2)
    session.add(u3)
    session.add(u4)
    session.add(u5)
    session.add(u6)
    session.add(u7)
    session.add(u8)
    session.add(u9)
    session.add(u10)
    session.flush()
    u1.add_change(admin)
    u2.add_change(admin)
    u3.add_change(admin)
    u4.add_change(admin)
    u5.add_change(admin)
    u6.add_change(admin)
    u7.add_change(admin)
    u8.add_change(admin)
    u9.add_change(admin)
    u10.add_change(admin)
    session.flush()
    session.commit()
    requestors = [u1, u2, u3, u4, u5, u6, u7, u8, u9, u10]

    job_types = ["Investigator", "Analyst", "Consultant"]

    for u in requestors:
        job = randint(0,2)
        team = randint(0,5)
        u.job_title = job_types[job]
        u.team = Team.get_all().all()[team]

        u.add_change(admin)
        ur1 = UserRoles(u, "Investigator", True)
        ur2 = UserRoles(u, "QA", True)
        ur3 = UserRoles(u, "Case Manager", True)
        ur4 = UserRoles(u, "Requester", False)
        ur5 = UserRoles(u, "Authoriser", True)
        ur6 = UserRoles(u, "Administrator", True)
        session.add(ur1)
        session.add(ur2)
        session.add(ur3)
        session.add(ur4)
        session.add(ur5)
        session.add(ur6)
        session.flush()
        ur1.add_change(admin)
        ur2.add_change(admin)
        ur3.add_change(admin)
        ur4.add_change(admin)
        ur5.add_change(admin)
        ur6.add_change(admin)
        session.flush()
    session.commit()
    print "10 Requestors added to Foreman."
    return requestors


def create_test_cases(case_managers, requestors, investigators, authorisers):
    backgrounds = [
        """Employee {} has been accused of harassment and bullying. Please conduct an investigation into the
         matter. """,
        """It is believed that employee {} has been surfing inappropriate websites during their lunch break.
        Please provide a report on their internet activities and anything else that may be required.""",
        """We believe that employee {} has a virus on their workstation <>.
        The IDS system has picked up on unusually high volumes of encrypted internet traffic. Please quarantine this
        machine and investigate the malware. """,
        """All emails between the employee {} and the external company '[]' to be searched, as well as all documents on
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
        """Unusual activity - file edits, name changes, deletions, has occurred on the drive (). Please investigate this
        activity. """]
    justifications = [
        "This case is required by the Legal department as part of a civil case where disclosure of information is required.",
        "This case is required as policy dictates any gross misconduct must be investigated by the internal forensics team.",
        "This project is justified as it has been approved by the CEO."]
    network_locations = ['shared', 'logs', 'team', 'uploads', 'management', 'presentations', 'important', 'records']
    companies = ['Babbleopia', 'topiczoom', 'Avaba', 'Yombee', 'Dynanti', 'Yavu', 'Jumpverse', 'LampConstructor',
                 'LawFieldz']
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
    print "Adding 50 cases:"
    for i in xrange(0, 50):
        case_manager = case_managers[randint(0, len(case_managers) - 1)]
        requestor = requestors[randint(0, len(requestors) - 1)]
        justification = justifications[randint(0, len(justifications) - 1)]
        background = backgrounds[randint(0, len(backgrounds) - 1)]
        rand_user = random_users[randint(0, len(random_users) - 1)]
        background = background.replace("{}", rand_user)
        background = background.replace("[]", companies[randint(0, len(companies) - 1)])
        background = background.replace("<>", "CORPWORKPC" + str(randint(1000, 9999)))
        background = background.replace("()", path.join("\\corporatenetwork",
                                                        network_locations[randint(0, len(network_locations) - 1)],
                                                        network_locations[randint(0, len(network_locations) - 1)]))
        classification = CaseClassification.get_classifications()[
            randint(0, len(CaseClassification.get_classifications()) - 1)]
        case_type = CaseType.get_case_types()[randint(0, len(CaseType.get_case_types()) - 1)]
        private = randint(0,10)
        if private <= 1:
            is_private = True
        else:
            is_private = False

        created = datetime.now() - timedelta(days=randint(0,100), hours=randint(0,23), seconds=randint(0,59),
                                           minutes=randint(0,59))
        new_case = Case(ForemanOptions.get_next_case_name(), requestor, background=background, reference=None,
                        private=is_private, location=None, classification=classification, case_type=case_type,
                        justification=justification, created=created)
        session.add(new_case)
        session.flush()
        new_case.add_change(requestor)
        session.commit()

        n = UserCaseRoles(requestor, new_case, UserCaseRoles.REQUESTER)
        session.add(n)
        auth = authorisers[randint(0, len(authorisers) - 1)]
        a = UserCaseRoles(auth, new_case, UserCaseRoles.AUTHORISER)
        session.add(a)
        new_case.authorise(auth, "Case Creation", "PENDING")

        n.add_change(requestor)
        a.add_change(requestor)
        n1 = UserCaseRoles(case_manager, new_case, UserCaseRoles.PRINCIPLE_CASE_MANAGER)
        session.add(n1)
        n1.add_change(case_manager)
        have_secondary_case_manager = randint(0, 1)
        if have_secondary_case_manager == 1:
            case_manager_2 = case_managers[randint(0, len(case_managers) - 1)]
            while case_manager_2.id == case_manager.id:
                case_manager_2 = case_managers[randint(0, len(case_managers) - 1)]
            n1 = UserCaseRoles(case_manager_2, new_case, UserCaseRoles.SECONDARY_CASE_MANAGER)
            session.add(n1)
            n1.add_change(case_manager)
        session.flush()

        rand = randint(0, 6)
        if rand >= 1:
            new_case.authorise(auth, "Looks acceptable. Please go ahead.", "AUTH")
        else:
            if randint(0,1) == 0:
                new_case.authorise(auth, "I don't think this meets our requirements.", "NOAUTH")

        if new_case.authorised.case_authorised != "NOAUTH":
            if rand >=2:
                new_case.set_status(CaseStatus.OPEN, new_case.principle_case_manager)
                inv = create_test_tasks(new_case, investigators, rand_user)
                create_evidence(new_case, inv, rand_user)
            if rand >= 5:
                new_case.set_status(CaseStatus.CLOSED, new_case.principle_case_manager)
            if rand >= 6:
                new_case.set_status(CaseStatus.ARCHIVED, new_case.principle_case_manager)
        print "Case added to Foreman."

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


def create_test_tasks(case, investigators, rand_user):
    task_types = TaskType.get_all().all()
    numTasks = randint(1, 6)
    inv = case.principle_case_manager
    for i in range(0, numTasks):
        task_type = task_types[randint(0, len(task_types)-1)]
        task_name = ForemanOptions.get_next_task_name(case)
        task_background = generate_task_background(task_type.task_type, rand_user)
        today = datetime.now()
        difference = today - case.creation_date
        date = case.creation_date + timedelta(days=randint(0, difference.days))
        new_task = Task(case, task_type, task_name, case.principle_case_manager, background=task_background, date=date)
        session.add(new_task)
        print "\tTask added to Case."
        session.flush()
        new_task.add_change(case.principle_case_manager)

        new_task.set_status(TaskStatus.QUEUED, case.principle_case_manager)
        rand = randint(0, 10)
        if rand > 2 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
            new_task.set_status(TaskStatus.ALLOCATED, case.principle_case_manager)
            rand = randint(0, 1)
            inv = investigators[randint(0, len(investigators) - 1)]
            qa = investigators[randint(0, len(investigators) - 1)]
            while qa.id == inv.id:
                qa = investigators[randint(0, len(investigators) - 1)]
            u = UserTaskRoles(inv, new_task, UserTaskRoles.PRINCIPLE_INVESTIGATOR)
            u1 = UserTaskRoles(qa, new_task, UserTaskRoles.PRINCIPLE_QA)
            session.add(u)
            session.add(u1)
            session.flush()
            u.add_change(case.principle_case_manager)
            u1.add_change(case.principle_case_manager)
            session.commit()

            second_inv = randint(0,1)
            if second_inv == 1:
                inv2 = investigators[randint(0, len(investigators) - 1)]
                while inv2.id == inv.id or inv2.id == qa.id:
                    inv2 = investigators[randint(0, len(investigators) - 1)]
                u2 = UserTaskRoles(inv2, new_task, UserTaskRoles.SECONDARY_INVESTIGATOR)
                session.add(u2)
                session.flush()
                u2.add_change(case.principle_case_manager)
                session.commit()
            else:
                inv2 = None

            second_qa= randint(0,1)
            if second_qa == 1:
                qa2 = investigators[randint(0, len(investigators) - 1)]
                while qa2.id == inv.id or (inv2 is not None and qa2.id == inv2.id) or qa2.id == qa.id:
                    qa2 = investigators[randint(0, len(investigators) - 1)]
                u3 = UserTaskRoles(qa2, new_task, UserTaskRoles.SECONDARY_QA)
                session.add(u3)
                session.flush()
                u3.add_change(case.principle_case_manager)
                session.commit()

            if rand == 1 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                new_task.set_status(TaskStatus.PROGRESS, new_task.principle_investigator)
                rand = randint(0, 1)
                rand1 = randint(0, 1)
                if rand1 == 1:
                    d = path.join(TaskUpload.ROOT, TaskUpload.DEFAULT_FOLDER, str(new_task.case_id) + "_" + str(new_task.id))
                    if not path.exists(d):
                        mkdir(d)
                    with open(path.join(d, "example_upload.txt"), "w") as f:
                        f.write("The ACPO guidelines!")

                    upload = TaskUpload(inv.id, new_task.id, new_task.case_id, "example_upload.txt",
                                        "Added to remind other investigators of the ACPO guidelines", "ACPO Guidelines")
                    session.add(upload)
                    session.commit()
                if rand == 1 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                    new_task.set_status(TaskStatus.QA, new_task.principle_investigator)
                    rand = randint(0, 1)
                    if rand == 1 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                        new_task.pass_QA("Well done, case work looks fine.", new_task.principle_QA)
                        if new_task.secondary_QA:
                            new_task.pass_QA("I agree, all looks good. QA pass.", new_task.secondary_QA)
                        #new_task.set_status(TaskStatus.DELIVERY, new_task.principle_QA)
                        rand = randint(0, 1)
                        if rand == 1 or case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                            new_task.set_status(TaskStatus.COMPLETE, new_task.principle_investigator)
                            if case.status == CaseStatus.ARCHIVED or case.status == CaseStatus.CLOSED:
                                new_task.set_status(TaskStatus.CLOSED, case.principle_case_manager)
    return inv


def create_evidence(case, inv, rand_user):
    numEvidence = randint(0,2)
    ref = 1
    for i in range(0, numEvidence):
        bagno = str(randint(100, 999))

        now = datetime.now()
        evi = EvidenceType.get_evidence_types()[randint(0, len(EvidenceType.get_evidence_types()) - 1)]
        e = Evidence(case, "SCH-20140228-HDD_00"+str(ref), evi,
                     "Hard drive from {}'s main machine".format(rand_user),
                     case.requester.fullname, "Main Evidence Cabinet",
                     case.principle_case_manager, "B000"+bagno, True)
        ref += 1
        session.add(e)
        print "\tEvidence added to case."
        e.add_change(case.principle_case_manager)
        session.flush()
        e.create_qr_code()
        e.check_in(inv.fullname, inv, now, "Initial check in to the storage cabinet")
        try:
            mkdir(path.abspath(path.join(ROOT_DIR, "files", "evidence_photos")))
        except:
            pass
        photo_location = path.abspath(path.join(ROOT_DIR, "files", "evidence_photos", str(e.id)))
        try:
            stat(photo_location)
        except:
            mkdir(photo_location)
        amount = randint(1, 3)
        for x in xrange(0, amount):
            rand1 = randint(1, 9)
            shutil.copy(path.join(ROOT_DIR, "static", "example_images", "evidence_example ({}).jpg".format(rand1)),
                        photo_location)
            upload = EvidencePhotoUpload(inv.id, e.id, "evidence_example ({}).jpg".format(rand1), "A comment", "Image " + str(x))
            session.add(upload)
            session.commit()



def create_test_data():
    load_initial_values_test()
    admin = create_admin_user()
    investigators = create_test_investigators(admin)
    case_managers = create_test_case_managers(admin)
    requestors = create_test_requestors(admin)
    authorisers = create_test_authorisers(admin)
    create_test_cases(case_managers, requestors, investigators, authorisers)
