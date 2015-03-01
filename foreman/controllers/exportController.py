from os import listdir
from os.path import isfile, join
from datetime import datetime
from monthdelta import monthdelta

# library imports
from werkzeug import Response, redirect

# local imports
from baseController import BaseController
from ..utils.case_note_renders import render_rtf, render_csv, render_pdf

class ExportController(BaseController):

    def pdf(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'view')
            stringio = render_pdf(task.notes)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='application/pdf', status=200)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='application/pdf', status=200)
        else:
            return self.return_404()

    def rtf(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'view')
            stringio = render_rtf(task.notes)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='application/rtf', status=200)
        else:
            return self.return_404()

    def csv(self, case_id, task_id):
        task = self._validate_task(case_id, task_id)
        if task is not None:
            self.check_permissions(self.current_user, task, 'view')
            stringio = render_csv(task.notes)
            return Response(stringio.getvalue(), direct_passthrough=True, mimetype='text/csv', status=200)
        else:
            return self.return_404()


