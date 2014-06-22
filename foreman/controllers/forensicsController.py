from collections import OrderedDict
from os import path

# local imports
from baseController import BaseController, lookup, jsonify
from ..model import Task, Case, TaskNotes, UserRoles, UserMessage, TaskStatus
from ..forms.forms import QACheckerForm, AddTaskNotesForm, AssignQAForm, AssignQAFormSingle, AskForQAForm
from ..utils.utils import session, multidict_to_dict, config
from ..utils.case_note_renders import render_rtf, render_csv, render_pdf
from ..utils.mail import email


class ForensicsController(BaseController):
    
    def work(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'work')
            qa_partner_list = [(user.id, user.fullname) for user in UserRoles.get_qas() if user not in task.QAs]

            form_type = multidict_to_dict(self.request.args)
            success = False
            start = False
            success_qa = False

            if 'add_notes' in form_type and form_type['add_notes'] == "true" and self.validate_form(AddTaskNotesForm()):
                task.add_note(self.form_result['notes'], self.current_user)
                session.flush()
                success = True
            elif 'assign_QA' in form_type and form_type['assign_QA'] == "true" and form_type['assign_num'] == "2" \
                    and self.validate_form(AssignQAForm()):
                task.assign_QA(self.form_result['investigator'], self.form_result['investigator2'], self.current_user)
                success_qa = True
            elif 'assign_QA' in form_type and form_type['assign_QA'] == "true" and form_type['assign_num'] == "1" \
                    and self.validate_form(AssignQAFormSingle()):
                task.assign_QA(self.form_result['investigator'], None, self.current_user, single=True)
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
            elif "status" in form_type:
                if form_type["status"] == "start_work":
                    task.start_work(self.current_user)
                    start = True
                elif form_type["status"] == "deliver":
                    task.deliver_task(self.current_user)

            if len(task.QAs) == 2:
                qa_partners = [("both", "Message both")] + [(qa.id, qa.fullname) for qa in task.QAs]
            elif len(task.QAs) == 1:
                qa_partners = [(qa.id, qa.fullname) for qa in task.QAs]
            else:
                qa_partners = None

            rtf_location = csv_location = pdf_location = None
            if len(task.notes) != 0:
                pdf = render_rtf(task.notes)
                if pdf:
                    pdf_location = r"file:///" + path.abspath(pdf).replace("\\", "/")
                rtf = render_rtf(task.notes)
                if rtf:
                    rtf_location = r"file:///" + path.abspath(rtf).replace("\\", "/")
                csv_location = r"file:///" + path.abspath(render_csv(task.notes)).replace("\\", "/")

            case_note_dates = list(OrderedDict.fromkeys([notes.date_time.strftime("%d %b %Y") for notes in task.notes]))
            return self.return_response('pages', 'update_forensics.html', task=task, success=success, start=start,
                                       qa_partner_list=qa_partner_list, success_qa=success_qa, qa_partners=qa_partners,
                                       case_note_dates=case_note_dates, rtf_location=rtf_location,
                                       csv_location=csv_location, pdf_location=pdf_location)
        else:
            return self.return_404()

    def qa(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'qa')

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

