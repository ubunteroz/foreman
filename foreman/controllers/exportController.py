
# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController
from foreman.model import CaseAuthorisation, TaskNotes, TaskUpload, EvidenceHistory, ChainOfCustody, EvidencePhotoUpload
from ..utils.case_note_renders import render_rtf, render_csv, render_pdf
from ..utils.report_renders import render_rtf_report


class ExportController(BaseController):

    error_msg = "Sorry, your administrator has not installed the package to render this type of file."

    def notes_pdf(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'view')
            stringio = render_pdf(task.notes)
            if stringio is None:
                return Response(self.error_msg, mimetype='text/html', status=200)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='application/pdf', status=200)
        else:
            return self.return_404()

    def notes_rtf(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'view')
            stringio = render_rtf(task.notes)
            if stringio is None:
                return Response(self.error_msg, mimetype='text/html', status=200)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='application/rtf', status=200)
        else:
            return self.return_404()

    def notes_csv(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'view')
            stringio = render_csv(task.notes)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='text/csv', status=200)
        else:
            return self.return_404()

    def report(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'report')

            case_history, task_histories, evidence_histories = self._get_data_for_case_report(case)
            return self.return_response('pages', 'case_report.html', case=case, case_history=case_history,
                                        task_histories=task_histories, evidence_histories=evidence_histories)
        else:
            return self.return_404()

    def case_report_rtf(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'report')
            histories = self._get_data_for_case_report(case)
            stringio = render_rtf_report(case, histories)
            if stringio is None:
                return Response(self.error_msg, mimetype='text/html', status=200)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='application/rtf', status=200)
        else:
            return self.return_404()

    def _get_data_for_case_report(self, case):
        c_hist = self._get_case_history_changes(case)
        m_hist = self._get_all_user_history_changes(case)
        a_hist = CaseAuthorisation.get_changes(case)
        case_history = c_hist + m_hist + a_hist
        case_history.sort(key=lambda d: d['date_time'])

        task_histories = []
        for task in case.tasks:
            t_hist = self._get_task_history_changes(task)
            n_hist = TaskNotes.get_changes(task)
            tu_hist = TaskUpload.get_changes(task)
            u_hist = self._get_all_task_user_history_changes(task)
            task_hist = t_hist + n_hist + u_hist + tu_hist
            task_hist.sort(key=lambda d: d['date_time'])
            task_histories.append(task_hist)

        evidence_histories = []
        for evidence in case.evidence:
            s_hist = self._get_evidence_history_changes(evidence)
            c_hist = ChainOfCustody.get_changes(evidence)
            p_hist = EvidencePhotoUpload.get_changes(evidence)
            evidence_hist = s_hist + c_hist + p_hist
            evidence_hist.sort(key=lambda d: d['date_time'])
            evidence_histories.append(evidence_hist)

        return case_history, task_histories, evidence_histories


