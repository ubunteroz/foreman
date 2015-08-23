from os import path
from datetime import datetime
from sqlalchemy import asc, desc
# local imports
from baseController import BaseController
from ..utils.utils import ROOT_DIR, multidict_to_dict, session
from ..model import Evidence, Case, EvidenceHistory, ForemanOptions, EvidencePhotoUpload, EvidenceType
from ..forms.forms import ChainOfCustodyForm, EditEvidenceForm, EditEvidenceQRCodesForm, EvidenceAssociateForm, \
    AddEvidenceForm, AddEvidencePhotoForm
from ..utils.utils import upload_file


class EvidenceController(BaseController):
    def _create_task_specific_breadcrumbs(self, evidence, case):
        if case is not None:
            self.breadcrumbs.append({'title': 'Cases', 'path': self.urls.build('case.view_all')})
            self.breadcrumbs.append({'title': case.case_name,
                                     'path': self.urls.build('case.view', dict(case_id=case.id))})
            self.breadcrumbs.append({'title': evidence.reference,
                                     'path': self.urls.build('evidence.view', dict(case_id=case.id,
                                                                                   evidence_id=evidence.id))})
        else:
            self.breadcrumbs.append({'title': "Evidence",
                                     'path': self.urls.build('evidence.view_all')})
            self.breadcrumbs.append({'title': evidence.reference,
                                     'path': self.urls.build('evidence.view_caseless', dict(evidence_id=evidence.id))})

    def add_no_case(self):
        return self.add(None)

    def add(self, case_id):
        if case_id is not None:
            case = self._validate_case(case_id)
            if case is not None:
                self.check_permissions(self.current_user, case, 'add-evidence')
            else:
                return self.return_404()
        else:
            case = None
            self.check_permissions(self.current_user, 'Evidence', 'add')

        if self.validate_form(AddEvidenceForm()):
            evi = Evidence(case, self.form_result['reference'], self.form_result['type'].evidence_type,
                           self.form_result['comments'], self.form_result['originator'], self.form_result['location'],
                           self.current_user, self.form_result['bag_num'], self.form_result['qr'])
            session.add(evi)
            session.flush()
            evi.create_qr_code()
            evi.add_change(self.current_user)
            return self.custody_in(evi.id, True, initial=True)
        else:
            evidence_type_options = [(et.id, et.evidence_type) for et in EvidenceType.get_all() if
                                     et.evidence_type != "Undefined"]
            return self.return_response('pages', 'add_evidence.html', case=case, errors=self.form_error,
                                        evidence_type_options=evidence_type_options)

    def edit(self, evidence_id):
        evidence = self._validate_evidence(evidence_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'edit')
            self._create_task_specific_breadcrumbs(evidence, evidence.case)
            self.breadcrumbs.append({'title': "Edit", 'path': self.urls.build('evidence.edit',
                                                                              dict(evidence_id=evidence_id))})
            form_type = multidict_to_dict(self.request.args)
            evidence_type_options = [(et.id, et.evidence_type) for et in EvidenceType.get_all() if
                                     et.evidence_type != "Undefined"]
            success = False
            active_tab = 0
            default_qr_code_text = evidence.generate_qr_code_text()

            if 'form' in form_type and form_type['form'] == "edit_evidence":
                if self.validate_form(EditEvidenceForm()):
                    evidence.reference = self.form_result['reference']
                    evidence.evidence_bag_number = self.form_result['bag_num']
                    evidence.type = self.form_result['type'].evidence_type
                    evidence.originator = self.form_result['originator']
                    evidence.comment = self.form_result['comments']
                    evidence.location = self.form_result['location']
                    evidence.add_change(self.current_user)
                    success = True

            elif 'form' in form_type and form_type['form'] == "edit_qr":
                active_tab = 1
                if self.validate_form(EditEvidenceQRCodesForm()):
                    evidence.qr_code_text = self.form_result['qr_code_text']
                    evidence.qr_code = self.form_result['qr_code']
                    if evidence.qr_code:
                        evidence.create_qr_code()
                    evidence.add_change(self.current_user)
                    success = True

            evidence_history = self._get_evidence_history_changes(evidence)
            len_qr_hist = False
            for history in evidence_history:
                if not isinstance(history['change_log'], basestring):
                    for entry in history['change_log'].keys():
                        if 'QR Code' in entry:
                            len_qr_hist = True
                            break
            return self.return_response('pages', 'edit_evidence.html', evidence=evidence, active_tab=active_tab,
                                        evidence_history=evidence_history,
                                        success=success, evidence_type_options=evidence_type_options,
                                        default_qr_code_text=default_qr_code_text, qr_evidence_history=len_qr_hist)
        else:
            return self.return_404(reason="""You have tried to access an invalid evidence reference.
            Alternatively, you have tried to edit evidence that is from a closed or archived case.
            Reopen the case to edit the evidence.""")

    def disassociate(self, case_id, evidence_id):
        evidence = self._validate_evidence(evidence_id, case_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'dis-associate')
            self._create_task_specific_breadcrumbs(evidence, evidence.case)
            self.breadcrumbs.append({'title': "Disassociate from case",
                                     'path': self.urls.build('evidence.disassociate',
                                                             dict(evidence_id=evidence_id, case_id=case_id))})
            closed = False

            case = evidence.case
            confirm_close = multidict_to_dict(self.request.args)
            if 'confirm' in confirm_close and confirm_close['confirm'] == "true":
                evidence.disassociate()
                evidence.add_change(self.current_user)
                closed = True

            return self.return_response('pages', 'disassociate_evidence.html', evidence=evidence, closed=closed,
                                        case=case)
        else:
            return self.return_404()

    def remove(self, evidence_id):
        evidence = self._validate_evidence(evidence_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'remove')
            self._create_task_specific_breadcrumbs(evidence, evidence.case)
            self.breadcrumbs.append({'title': "Remove", 'path': self.urls.build('evidence.remove',
                                                                                dict(evidence_id=evidence_id))})

            closed = False
            reference = evidence.reference

            confirm_close = multidict_to_dict(self.request.args)
            if 'confirm' in confirm_close and confirm_close['confirm'] == "true":
                session.delete(evidence)
                session.flush()
                closed = True

                return self.return_response('pages', 'remove_evidence.html', closed=closed, reference=reference)
            return self.return_response('pages', 'remove_evidence.html', evidence=evidence, closed=closed)
        else:
            return self.return_404()

    def view(self, case_id, evidence_id):
        evidence = self._validate_evidence(evidence_id, case_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'view')
            self._create_task_specific_breadcrumbs(evidence, evidence.case)
            photo_location = path.join(ROOT_DIR, 'static', 'evidence_photos', str(evidence.id))
            return self.return_response('pages', 'view_evidence.html', evidence=evidence, photo_location=photo_location)
        else:
            return self.return_404()

    def view_caseless(self, evidence_id):
        return self.view(None, evidence_id)

    def view_all(self):
        self.check_permissions(self.current_user, 'Evidence', 'view-all')
        self.breadcrumbs.append({'title': 'Evidence', 'path': self.urls.build('evidence.view_all')})

        sort_by = multidict_to_dict(self.request.args).get('sort_by', 'date')
        evidence = Evidence.get_all_evidence(self.current_user, self.check_permissions)
        if sort_by == "date":
            evidence = sorted(evidence, key=lambda evidence: evidence.date_added, reverse=True)
        if sort_by == "date_old":
            evidence = sorted(evidence, key=lambda evidence: evidence.date_added)
        elif sort_by == "case":
            evidence = sorted(evidence, key=lambda evidence: evidence.case_id, reverse=True)
        elif sort_by == "user":
            evidence = sorted(evidence, key=lambda evidence: evidence.user_id)

        return self.return_response('pages', 'view_evidences.html', evidence=evidence, sort_by=sort_by)

    def associate(self, evidence_id):
        evidence = self._validate_evidence(evidence_id)
        if evidence is not None and evidence.case_id is None:
            self.check_permissions(self.current_user, evidence, 'associate')
            self._create_task_specific_breadcrumbs(evidence, evidence.case)
            self.breadcrumbs.append({'title': "Associate with case",
                                     'path': self.urls.build('evidence.associate', dict(evidence_id=evidence_id))})

            reassign_cases = [(r_case.id, r_case.case_name) for r_case in Case.get_all()]
            if self.validate_form(EvidenceAssociateForm()):
                evidence.associate(self.form_result['case_reassign'])
                evidence.add_change(self.current_user)
                return self.return_response('pages', 'associate_evidence.html', evidence=evidence, success=True,
                                            reassign_cases=reassign_cases)
            else:
                return self.return_response('pages', 'associate_evidence.html', evidence=evidence,
                                            errors=self.form_error, reassign_cases=reassign_cases)
        else:
            return self.return_404()

    def custody_in(self, evidence_id, check_in=True, initial=False):

        evidence = self._validate_evidence(evidence_id)

        if evidence is not None and (evidence.current_status is None or evidence.current_status.check_in != check_in):
            self.check_permissions(self.current_user, evidence, 'check-in-out')

            if not initial and self.validate_form(ChainOfCustodyForm()):
                full_date = datetime.combine(self.form_result['date'], self.form_result['time'])
                if check_in:
                    evidence.check_in(self.form_result['user'], self.current_user, full_date,
                                      self.form_result['comments'], self.form_result['attach'],
                                      self.form_result['label'])
                else:
                    evidence.check_out(self.form_result['user'], self.current_user, full_date,
                                       self.form_result['comments'], self.form_result['attach'],
                                       self.form_result['label'])
                if evidence.case is not None:
                    return self.view(evidence.case.id, evidence_id)
                else:
                    return self.view_caseless(evidence_id)
            else:
                self._create_task_specific_breadcrumbs(evidence, evidence.case)
                if check_in:
                    self.breadcrumbs.append({'title': "Check in evidence",
                                             'path': self.urls.build('evidence.custody_in',
                                                                     dict(evidence_id=evidence_id))})
                else:
                    self.breadcrumbs.append({'title': "Check out evidence",
                                             'path': self.urls.build('evidence.custody_out',
                                                                     dict(evidence_id=evidence_id))})
                return self.return_response('pages', 'evidence_custody_change.html', evidence=evidence,
                                            checkin=check_in, errors=self.form_error)
        else:
            return self.return_404()

    def custody_out(self, evidence_id):
        return self.custody_in(evidence_id, False)

    def view_photo(self, evidence_id, upload_id):
        upload = self._validate_evidence_photo(evidence_id, upload_id)
        if upload is not None:
            self.check_permissions(self.current_user, upload.evidence, 'view')
            self._create_task_specific_breadcrumbs(upload.evidence, upload.evidence.case)
            self.breadcrumbs.append({'title': upload.file_title,
                                     'path': self.urls.build('evidence.view_photo',
                                                             dict(evidence_id=evidence_id, upload_id=upload_id))})
            return self.return_response('pages', 'view_evidence_photo.html', upload=upload)
        else:
            return self.return_404()

    def delete_photo(self, evidence_id, upload_id):
        upload = self._validate_evidence_photo(evidence_id, upload_id)
        if upload is not None:
            self.check_permissions(self.current_user, upload.evidence, 'delete_file')
            self._create_task_specific_breadcrumbs(upload.evidence, upload.evidence.case)
            self.breadcrumbs.append({'title': upload.file_title,
                                     'path': self.urls.build('evidence.view_photo',
                                                             dict(evidence_id=evidence_id, upload_id=upload_id))})
            self.breadcrumbs.append({'title': "Delete",
                                     'path': self.urls.build('evidence.delete_photo',
                                                             dict(evidence_id=evidence_id, upload_id=upload_id))})
            closed = False
            confirm_close = multidict_to_dict(self.request.args)
            if 'confirm' in confirm_close and confirm_close['confirm'] == "true":
                upload.delete(self.current_user)
                closed = True

            return self.return_response('pages', 'delete_evidence_photo.html', upload=upload, closed=closed)
        else:
            return self.return_404()

    def add_photo(self, evidence_id):
        evidence = self._validate_evidence(evidence_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'add_file')
            self._create_task_specific_breadcrumbs(evidence, evidence.case)
            self.breadcrumbs.append({'title': "Add photo",
                                     'path': self.urls.build('evidence.add_photo', dict(evidence_id=evidence_id))})
        else:
            return self.return_404()

        success_upload = False
        upload = None
        if self.validate_form(AddEvidencePhotoForm()):
            f = self.form_result['file']
            new_directory = path.join(EvidencePhotoUpload.ROOT, EvidencePhotoUpload.DEFAULT_FOLDER, str(evidence.id))
            file_name = upload_file(f, new_directory)

            upload = EvidencePhotoUpload(self.current_user.id, evidence.id, file_name, self.form_result['comments'],
                                         self.form_result['file_title'])
            session.add(upload)
            session.commit()
            success_upload = True

        return self.return_response('pages', 'add_evidence_photos.html', errors=self.form_error, evidence=evidence,
                                    success_upload=success_upload, upload=upload)

    @staticmethod
    def _get_evidence_history_changes(evidence):
        history = EvidenceHistory.get_changes(evidence)
        history.sort(key=lambda d: d['date_time'])
        return history
