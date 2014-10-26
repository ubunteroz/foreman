from os import listdir
from os.path import isfile, join
from datetime import datetime
from monthdelta import monthdelta

# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController, jsonify
from ..model.caseModel import Task, ForemanOptions, Case, CaseStatus
from ..model.generalModel import TaskCategory, CaseType
from ..model.userModel import UserRoles


class ReportController(BaseController):

    def report(self):
        start_date = ForemanOptions.get_date_created()
        today_date = datetime.now()
        months = [start_date.strftime("%B %Y")]
        categories = CaseType.get_case_types()
        cases_opened = []
        cases_closed = []
        cases_archived = []
        total_cases = []
        active_tab = 0
        for status in CaseStatus.all_statuses:
            total_cases.append([start_date.strftime("%B %Y"), status,
                                Case.get_num_cases_opened_on_date(start_date, status, case_type=None, by_month=True)])
        for category in categories:
            cases_opened.append([start_date.strftime("%B %Y"), category,
                                 Case.get_num_cases_opened_on_date(start_date, CaseStatus.OPEN, case_type=category,
                                                               by_month=True)])
            cases_closed.append([start_date.strftime("%B %Y"), category,
                                 Case.get_num_cases_opened_on_date(start_date, CaseStatus.CLOSED, case_type=category,
                                                               by_month=True)])
            cases_archived.append([start_date.strftime("%B %Y"), category,
                                   Case.get_num_cases_opened_on_date(start_date, CaseStatus.ARCHIVED, case_type=category,
                                                                 by_month=True)])
        max_months = 11
        while start_date.month != today_date.month and max_months != 0:
            start_date = start_date + monthdelta(1)
            months.append(start_date.strftime("%B %Y"))
            for status in CaseStatus.all_statuses:
                total_cases.append([start_date.strftime("%B %Y"), status,
                                    Case.get_num_cases_opened_on_date(start_date, status, case_type=None, by_month=True)])
            for category in categories:
                cases_opened.append([start_date.strftime("%B %Y"), category,
                                     Case.get_num_cases_opened_on_date(start_date, CaseStatus.OPEN, case_type=category,
                                                                   by_month=True)])
                cases_closed.append([start_date.strftime("%B %Y"), category,
                                     Case.get_num_cases_opened_on_date(start_date, CaseStatus.CLOSED, case_type=category,
                                                                   by_month=True)])
                cases_archived.append([start_date.strftime("%B %Y"), category,
                                       Case.get_num_cases_opened_on_date(start_date, CaseStatus.ARCHIVED,
                                                                     case_type=category, by_month=True)])
            max_months -= 1

        return self.return_response('pages', 'report.html', cases_opened=cases_opened, cases_closed=cases_closed,
                                    months=months, cases_archived=cases_archived, total_cases=total_cases,
                                    active_tab=active_tab)

    @jsonify
    def jason_tasks_assigned_to_inv(self):
        try:
            start_date_str = self.request.args.get('start_date', "")
            start_date = datetime.strptime(start_date_str, "%B %Y")
        except ValueError:
            start_date = datetime.now()
        tasks_assigned_inv = []
        for category in TaskCategory.get_categories():
            for investigator in UserRoles.get_investigators():
                tasks_assigned_inv.append({
                    "Investigator": investigator.fullname,
                    "Number of Tasks": int(Task.get_num_tasks_by_user(investigator, category, start_date)),
                    "Task Type": category})
        return tasks_assigned_inv

    @jsonify
    def jason_tasks_qaed(self):
        try:
            start_date_str = self.request.args.get('start_date', "")
            start_date = datetime.strptime(start_date_str, "%B %Y")
        except ValueError:
            start_date = datetime.now()
        tasks_assigned_inv = []
        for investigator in UserRoles.get_investigators():
            tasks_assigned_inv.append({
                "QA Partner": investigator.fullname,
                "Number of QAs": Task.get_num_completed_qas(investigator, start_date)})
        return tasks_assigned_inv