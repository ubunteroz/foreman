from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
from monthdelta import MonthDelta

# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController, jsonify
from ..model.caseModel import Task, ForemanOptions, Case, CaseStatus, TaskStatus
from ..model.generalModel import TaskCategory, CaseType
from ..model.userModel import UserRoles


class ReportController(BaseController):

    def _create_breadcrumbs(self):
        BaseController._create_breadcrumbs(self)
        self.breadcrumbs.append({'title': 'Reports', 'path': self.urls.build('report.report')})

    def report(self):
        self.check_permissions(self.current_user, 'Report', 'view')

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
                                Case.get_num_cases_opened_on_date(start_date, status, case_type=None)])
        for category in categories:
            cases_opened.append([start_date.strftime("%B %Y"), category,
                                 Case.get_num_cases_opened_on_date(start_date, CaseStatus.OPEN, case_type=category)])
            cases_closed.append([start_date.strftime("%B %Y"), category,
                                 Case.get_num_cases_opened_on_date(start_date, CaseStatus.CLOSED, case_type=category)])
            cases_archived.append([start_date.strftime("%B %Y"), category,
                                   Case.get_num_cases_opened_on_date(start_date, CaseStatus.ARCHIVED,
                                                                     case_type=category)])
        max_months = 11
        while start_date.month != today_date.month and max_months != 0:
            start_date = start_date + MonthDelta(1)
            months.append(start_date.strftime("%B %Y"))
            for status in CaseStatus.all_statuses:
                total_cases.append([start_date.strftime("%B %Y"), status,
                                    Case.get_num_cases_opened_on_date(start_date, status, case_type=None)])
            for category in categories:
                cases_opened.append([start_date.strftime("%B %Y"), category,
                                     Case.get_num_cases_opened_on_date(start_date, CaseStatus.OPEN,
                                                                       case_type=category)])
                cases_closed.append([start_date.strftime("%B %Y"), category,
                                     Case.get_num_cases_opened_on_date(start_date, CaseStatus.CLOSED,
                                                                       case_type=category)])
                cases_archived.append([start_date.strftime("%B %Y"), category,
                                       Case.get_num_cases_opened_on_date(start_date, CaseStatus.ARCHIVED,
                                                                         case_type=category)])
            max_months -= 1

        return self.return_response('pages', 'report.html', cases_opened=cases_opened, cases_closed=cases_closed,
                                    months=months, cases_archived=cases_archived, total_cases=total_cases,
                                    active_tab=active_tab)

    @jsonify
    def jason_tasks_assigned_to_inv(self):
        self.check_permissions(self.current_user, 'Report', 'view')

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
                    "Number of Tasks": int(Task.get_num_created_tasks_for_given_month_user_is_investigator_for(investigator, category, start_date)),
                    "Task Type": category})
        return tasks_assigned_inv

    @jsonify
    def jason_tasks_qaed(self):
        self.check_permissions(self.current_user, 'Report', 'view')

        try:
            start_date_str = self.request.args.get('start_date', "")
            start_date = datetime.strptime(start_date_str, "%B %Y")
        except ValueError:
            start_date = datetime.now()
        tasks_assigned_inv = []
        for investigator in UserRoles.get_investigators():
            tasks_assigned_inv.append({
                "QA Partner": investigator.fullname,
                "Number of QAs": Task.get_num_completed_qas_for_given_month(investigator, start_date)})
        return tasks_assigned_inv


    @jsonify
    def jason_direct_report_tasks(self):
        self.check_permissions(self.current_user, "User", 'view_directs_timesheets')
        today = datetime.now()
        try:
            start_date_str = self.request.args.get('start_date', "")
            start_date = datetime.strptime(start_date_str, "%Y%m%d")
            end_date = start_date + timedelta(days=7)
            if end_date > today:
                end_date = today
        except ValueError:
            start_date = today
            end_date = today
        task_status = self.request.args.get('task_type', "")
        tasks_assigned_inv = []
        for category in TaskCategory.get_categories():
            for investigator in self.current_user.direct_reports:
                if investigator.is_examiner():
                    tasks_assigned_inv.append({
                        "Investigator": investigator.fullname,
                        "Number of Tasks": Task.get_num_tasks_by_user_for_date_range(investigator, category, start_date,
                                                                                     end_date, task_status),
                        "Task Type": category})
        return tasks_assigned_inv

    @jsonify
    def jason_direct_report_cases(self):
        self.check_permissions(self.current_user, "User", 'view_directs_timesheets')
        today = datetime.now()
        try:
            start_date_str = self.request.args.get('start_date', "")
            start_date = datetime.strptime(start_date_str, "%Y%m%d")
            end_date = start_date + timedelta(days=7)
            if end_date > today:
                end_date = today
        except ValueError:
            start_date = today
            end_date = today
            return []
        case_status = self.request.args.get('case_type', "")
        cases_assigned_manager = []
        for category in CaseType.get_case_types():
            for case_manager in self.current_user.direct_reports:
                if case_manager.is_case_manager():
                    cases_assigned_manager.append({
                        "Case Manager": case_manager.fullname,
                        "Number of Cases": int(Case.get_num_completed_case_by_user(case_manager, category, start_date,
                                                                                   end_date, case_status)),
                        "Case Type": category})
        return cases_assigned_manager
