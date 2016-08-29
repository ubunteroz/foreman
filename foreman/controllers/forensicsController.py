from collections import OrderedDict
from os import path, mkdir
import random
import string

# local imports
from baseController import BaseController, lookup, jsonify
from ..model import Task, Case, TaskNotes, UserRoles, UserMessage, TaskUpload, ForemanOptions
from ..forms.forms import QACheckerForm, AddTaskNotesForm, AssignQADuringForensicsForm, AssignQAFormSingle, AskForQAForm
from ..forms.forms import UploadTaskFile
from ..utils.utils import session, multidict_to_dict, config, upload_file
from ..utils.mail import email


class ForensicsController(BaseController):

    def _create_task_specific_breadcrumbs(self, task, case):
        self.breadcrumbs.append({'title': 'Cases', 'path': self.urls.build('case.view_all')})
        self.breadcrumbs.append({'title': case.case_name,
                                 'path': self.urls.build('case.view', dict(case_id=case.id))})
        self.breadcrumbs.append({'title': task.task_name,
                                 'path': self.urls.build('task.view', dict(case_id=case.id,
                                                                           task_id=task.id))})
    
    def work(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'add_notes')
            self._create_task_specific_breadcrumbs(task, task.case)
            self.breadcrumbs.append({'title': "Conduct Investigation",
                                 'path': self.urls.build('forensics.work', dict(case_id=task.case.id,
                                                                           task_id=task.id))})

            form_type = multidict_to_dict(self.request.args)
            success = False
            start = False
            success_qa = False
            success_upload = False
            active_tab = int(form_type['active_tab']) if 'active_tab' in form_type else 0
            email_alert_flag = False

            options = ForemanOptions.get_options()
            url = config.get('admin', 'website_domain') + self.urls.build('task.view', dict(task_id=task.id,
                                                                                            case_id=task.case.id))

            if options.email_alert_case_man_task_completed:
                email_alert_flag = True

            if 'add_notes' in form_type and form_type['add_notes'] == "true" and self.validate_form(AddTaskNotesForm()):
                task.add_note(self.form_result['notes'], self.current_user)
                session.flush()
                success = True
            elif 'assign_QA' in form_type and form_type['assign_QA'] == "true" and form_type['assign_num'] == "2" \
                    and self.validate_form(AssignQADuringForensicsForm()):
                task.investigator_assign_qa(self.form_result['investigator'], self.form_result['investigator2'], self.current_user)
                success_qa = True
            elif 'assign_QA' in form_type and form_type['assign_QA'] == "true" and form_type['assign_num'] == "1" \
                    and self.validate_form(AssignQAFormSingle()):
                task.investigator_assign_qa(self.form_result['investigator'], None, self.current_user, single=True)
                success_qa = True
            elif 'request_qa' in form_type and form_type['request_qa'] == "true" and self.validate_form(AskForQAForm()):
                task.request_QA(self.current_user)
                qa_partners = self.form_result['qa_partners']
                if qa_partners == "both":
                    for qa_partner in task.QAs:
                        mail = UserMessage(self.current_user, qa_partner, self.form_result['subject'],
                                           self.form_result['body'])
                        session.add(mail)
                        email([qa_partner.email], self.form_result['subject'], self.form_result['body'],
                              config.get('email', 'from_address'))
                elif qa_partners is not None:
                    mail = UserMessage(self.current_user, qa_partners, self.form_result['subject'],
                                       self.form_result['body'])
                    session.add(mail)
                    email([qa_partners.email], self.form_result['subject'], self.form_result['body'],
                          config.get('email', 'from_address'))
            elif 'upload_file' in form_type and form_type['upload_file'] == "true":
                if self.validate_form(UploadTaskFile()):
                    f = self.form_result['file']
                    new_directory = path.join(TaskUpload.ROOT, TaskUpload.DEFAULT_FOLDER,
                                              str(task.case.id) + "_" + str(task.id))
                    file_name = upload_file(f, new_directory)

                    upload = TaskUpload(self.current_user.id, task.id, task.case.id, file_name,
                                        self.form_result['comments'], self.form_result['file_title'])
                    session.add(upload)
                    session.commit()
                    success_upload = True
                active_tab = 2
            elif "status" in form_type:
                if form_type["status"] == "start_work":
                    task.start_work(self.current_user)
                    start = True
                elif form_type["status"] == "deliver":
                    task.deliver_task(self.current_user)
                    if options.email_alert_case_man_task_completed:
                        self.send_email_alert(task.case.case_managers, "A task in your case has been completed",
                                              """Task {} in case {} has been completed.

The task can be viewed here: {}""".format(task.task_name, task.case.case_name, url))
            if len(task.QAs) == 2:
                qa_partners = [("both", "Message both")] + [(qa.id, qa.fullname) for qa in task.QAs]
            elif len(task.QAs) == 1:
                qa_partners = [(qa.id, qa.fullname) for qa in task.QAs]
            else:
                qa_partners = None

            qa_partner_list = [(user.id, user.fullname) for user in UserRoles.get_qas() if user not in task.QAs and
                               user != self.current_user]
            case_note_dates = list(OrderedDict.fromkeys([notes.date_time.strftime("%d %b %Y") for notes in task.notes]))
            return self.return_response('pages', 'update_forensics.html', task=task, success=success, start=start,
                                       qa_partner_list=qa_partner_list, success_qa=success_qa, qa_partners=qa_partners,
                                       case_note_dates=case_note_dates, success_upload=success_upload,
                                       active_tab=active_tab, errors=self.form_error, email_alert_flag=email_alert_flag)
        else:
            return self.return_404()

    def qa(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'qa')
            self._create_task_specific_breadcrumbs(task, task.case)
            self.breadcrumbs.append({'title': "Conduct QA",
                                 'path': self.urls.build('forensics.qa', dict(case_id=task.case.id,
                                                                           task_id=task.id))})

            if self.validate_form(QACheckerForm()):
                if self.form_result['qa_decision']:
                    task.pass_QA(self.form_result['notes'], self.current_user)
                    qa_result = "passed"
                else:
                    task.fail_QA(self.form_result['notes'], self.current_user)
                    qa_result = "failed"
                return self.return_response('pages', 'qa_task.html', task=task, success=True, qa_result=qa_result)
            else:
                return self.return_response('pages', 'qa_task.html', task=task, errors=self.form_error)
        else:
            return self.return_404()

