# -*- coding: utf-8 -*-
# python imports
from random import randint
import os
import shutil
from datetime import datetime
import time
# local imports
from ..model import Case, User, UserTaskRoles, CaseStatus, TaskStatus, Task, UserCaseRoles, \
    ForemanOptions, UserRoles, Evidence, ChainOfCustody, LinkedCase, EvidenceType
from utils import session, ROOT_DIR

def populate():

    try:
        shutil.rmtree(os.path.abspath(os.path.join(ROOT_DIR, "static", "evidence_photos")))
    except WindowsError:
        pass


    case_background = """<p>Laurent Gbagbo, born on 31 May 1945, in the Mama village of the Ouragahio sous-préfecture,
    Gagnoa department in Côte d’Ivoire. He is an Ivorian national and former President of Cote d’Ivoire.</p>
    <p>Laurent Gbagbo allegedly bears individual criminal responsibility, as indirect co-perpetrator, for four counts of crimes against humanity:</p>
    <ul><li>murder, </li><li>violence,</li><li>persecution</li><li>other inhuman acts; allegedly committed in the context of post-electoral
    violence in the territory of Côte d’Ivoire between 16 December 2010 and 12 April 2011</li></ul>"""
    task_background = """<p>Please investigate the users with log in ids: LOMASSNM, GGHDDD & SGLDOPPL. I require:</p>
    <p>* All their emails between the dates of 15th March 2013 and 18th April 2014<br/>
    * Emails between the three custodians with the keywords "Laurent" OR "Gbagbo"</p>"""

    #Add Investigators
    u1 = User("lowmans", "qwerty", "Sarah", "Holmes", "sarah@lowmanio.co.uk", validated=True)
    u2 = User("holmes", "qwerty", "Steven", "Holmes", "sarah@lowmanio.co.uk", middle="W", validated=True)
    u3 = User("lowmany", "nybble", "Nybble", "Lowman", "sarah@lowmanio.co.uk", validated=True)
    u4 = User("lowmpix", "pixypoo", "Pixel", "Lowman", "sarah@lowmanio.co.uk", middle="F", validated=True)
    session.add(u1)
    session.add(u2)
    session.add(u3)
    session.add(u4)
    invs = [u1, u2, u3, u4]
    session.flush()
    u1.add_change(u1)
    u2.add_change(u1)
    u3.add_change(u1)
    u4.add_change(u1)
    session.flush()

    u2.username = "holmes1"
    u2.add_change(u3)

    for u in invs:
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
        ur1.add_change(u)
        ur2.add_change(u)
        ur3.add_change(u)
        ur4.add_change(u)
        ur5.add_change(u)
        ur6.add_change(u)
        session.flush()

    #Add Case Managers
    u1 = User("campnia", "khgkajgh", "Niall", "Campbell", "sarah@lowmanio.co.uk", validated=True)
    u2 = User("laujohn", "poiuyt", "Laura", "Johnston", "sarah@lowmanio.co.uk", validated=True)
    u3 = User("armstrnn", "moonland", "Neil", "Armstrong", "sarah@lowmanio.co.uk", validated=True)
    session.add(u1)
    session.add(u2)
    session.add(u3)
    managers = [u1, u2, u3]
    session.flush()
    u1.add_change(u1)
    u2.add_change(u1)
    u3.add_change(u1)
    session.flush()

    for u in managers:
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
        time.sleep(1)
        ur1.add_change(u)
        ur2.add_change(u)
        ur3.add_change(u)
        ur4.add_change(u)
        ur5.add_change(u)
        ur6.add_change(u)
        session.flush()
        ur6.removed = False
        ur6.add_change(u)
        time.sleep(1)
        ur6.removed = True
        ur6.add_change(u)


    #Add Requestors
    u1 = User("jfdsgj", "khgkajgh", "Lucy", "Campbell", "sarah@lowmanio.co.uk", validated=True)
    u2 = User("fhjhjhh", "poiuyt", "Mavis", "Bavis", "sarah@lowmanio.co.uk", validated=True)
    u3 = User("jhjhjj", "moonland", "Stuart", "Chambers", "sarah@lowmanio.co.uk", validated=True)
    session.add(u1)
    session.add(u2)
    session.add(u3)
    requestor = [u1, u2, u3]
    session.flush()
    u1.add_change(u1)
    u2.add_change(u1)
    u3.add_change(u1)
    session.flush()

    for u in requestor:
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
        ur1.add_change(u)
        ur2.add_change(u)
        ur3.add_change(u)
        ur4.add_change(u)
        ur5.add_change(u)
        ur6.add_change(u)
        session.flush()


    opts = ForemanOptions("%d %b %Y %H:%M:%S", r"C:\Users\Sarah\Programming\Foreman", "FromList", "NumericIncrement", "A Large Company",
                          "Investigations", c_leading_zeros=3,
                          t_leading_zeros=2, c_list_location="C:\Users\Sarah\Programming\utils\case_names.txt")
    session.add(opts)
    session.flush()
    for i in xrange(0,10):
        newCase = Case(ForemanOptions.get_next_case_name(), u4, background=case_background)
        session.add(newCase)
        session.flush()
        time.sleep(1)
        newCase.add_change(u2)
        n = UserCaseRoles(requestor[0], newCase, UserCaseRoles.REQUESTER)
        n.add_change(requestor[1])
        session.flush()
        x = randint(0,1)
        if x == 1:
            newCase.reference = "HERFDHHDF45777"
            newCase.private = True
            newCase.add_change(u1)
    types = opts.get_task_types()

    session.commit()

    list_cases = Case.get_all()
    for c in list_cases:
        rand = randint(0, 6)
        time.sleep(1)
        c.set_status(CaseStatus.OPEN, u2)
        if rand >= 5:
            time.sleep(1)
            c.set_status(CaseStatus.CLOSED,u1)
        if rand >= 6:
            time.sleep(1)
            c.set_status(CaseStatus.ARCHIVED, u3)
    session.commit()

    property_receipts = 0
    ref = 0

    case = Case.get(4)
    case_2 = Case.get(1)
    case_3 = Case.get(2)
    case_4 = Case.get(5)
    links1 = LinkedCase(case, case_2, "Old case got reopened with new requestor - prev has left org.", u1)
    links2 = LinkedCase(case, case_3, "Old case got reopened with new requestor.", u2)
    links3 = LinkedCase(case, case_3, "Case isn't actually related to old case, different data set.", u3, removed=True)
    links4 = LinkedCase(case_3, case_4, "Duplication of cases - combining.", u2)
    links5 = LinkedCase(case_4, case_3, "Duplication of cases - combining together.", u2)
    session.add(links1)
    session.add(links2)
    session.add(links3)
    session.add(links4)
    session.add(links5)
    session.flush()

    x = 0
    for case in Case.get_all():
        numTasks = randint(1, 6)
        for i in range(0,numTasks):
            taskTypeId = randint(0, len(types)-1)
            task_name = ForemanOptions.get_next_task_name(types[taskTypeId], case)
            newTask = Task(case, types[taskTypeId], task_name + "-" + str(x), u2, background=task_background)
            x += 1
            session.add(newTask)
            session.flush()
            newTask.add_change(u2)
        rand_man = randint(0, len(managers)-1)
        m = UserCaseRoles(managers[rand_man], case, UserCaseRoles.PRINCIPLE_CASE_MANAGER)
        rand_man1 = randint(0, 3)
        session.add(m)
        m.add_change(u)
        oldname = newTask.task_name
        newTask.task_name = "TestNewName1111"
        newTask.add_change(u3)
        if rand_man1 > 2:
            m = UserCaseRoles(managers[(rand_man+1)%len(managers)], case, UserCaseRoles.SECONDARY_CASE_MANAGER)
            session.add(m)
            m.add_change(u)
        newTask.task_name = oldname
        newTask.add_change(u4)

        numEvidence = randint(0,2)
        for i in range(0, numEvidence):
            bagno = str(randint(100, 999))

            if property_receipts < 2:
                attachment = r"C:\Users\Sarah\Programming\utils\receipt004-AF5HD4500.pdf"
                label = "Property Receipt from Requestor"
            else:
                attachment = None
                label = None

            now = datetime.now()
            e_id = randint(0, EvidenceType.get_amount() - 1)
            evi = EvidenceType.get(e_id)
            e = Evidence(case, "SCH-20140228-HDD_00"+str(ref), evi.evidence_type, "Hard drive from Joe's main machine", "PC McNaddy",
                         "Main Evidence Cabinet", u3, "B000"+bagno, True)
            ref += 1
            session.add(e)
            e.add_change(u)
            session.flush()
            e.check_in("Sherlock Holmes", u3, now, "Initial check in to the storage cabinet", attachment=attachment, label=label)
            try:
                os.mkdir(os.path.abspath(os.path.join(ROOT_DIR, "static", "evidence_photos")))
            except:
                pass
            photo_location = os.path.abspath(os.path.join(ROOT_DIR, "static", "evidence_photos", str(e.id)))
            try:
                os.stat(photo_location)
            except:
                os.mkdir(photo_location)
            amount = randint(1, 3)
            for x in xrange(0, amount):
                rand1 = randint(1, 10)
                try:
                    shutil.copy("C:\Users\Sarah\Programming\photos\hdd{}.jpg".format(rand1), photo_location)
                except:
                    pass

            property_receipts += 1

        session.commit()

    list_tasks = Task.get_all()
    for t in list_tasks:
        t.set_status(TaskStatus.QUEUED, u1)
        rand = randint(0, 10)
        if rand > 2:
            t.set_status(TaskStatus.ALLOCATED, u)
            rand = randint(0, 1)
            if rand == 1:
                t.set_status(TaskStatus.PROGRESS, u)
                rand = randint(0, 1)
                if rand == 1:
                    t.set_status(TaskStatus.QA, u1)
                    rand = randint(0, 1)
                    if rand == 1:
                        t.set_status(TaskStatus.DELIVERY,u2)
                        rand = randint(0, 1)
                        if rand == 1:
                            t.set_status(TaskStatus.COMPLETE, u2)

    session.flush()

    for task in Task.get_all():
        rand = randint(0, len(invs)-1)
        rand1 = randint(0, 2)
        rand2 = randint(0, 2)
        if task.status != TaskStatus.QUEUED:
            u = UserTaskRoles(invs[rand], task, UserTaskRoles.PRINCIPLE_INVESTIGATOR)
            u1 = UserTaskRoles(invs[(rand+1) % len(invs)], task, UserTaskRoles.PRINCIPLE_QA)
            session.add(u)
            session.add(u1)
            session.flush()
            u.add_change(invs[(rand+1) % len(invs)])
            u1.add_change(invs[(rand+1) % len(invs)])
            session.flush()

            if rand1 == 2:
                u2 = UserTaskRoles(invs[(rand+2) % len(invs)], task, UserTaskRoles.SECONDARY_QA)
                session.add(u2)
                session.flush()
                u2.add_change(invs[(rand+1) % len(invs)])
                #u2.add_change(invs[(rand+1) % len(invs)], invs[(rand+3) % len(invs)])
            if rand2 == 2:
                u3 = UserTaskRoles(invs[(rand+3) % len(invs)], task, UserTaskRoles.SECONDARY_INVESTIGATOR)
                session.add(u3)
                session.flush()
                u3.add_change(invs[(rand+1) % len(invs)])

    session.commit()