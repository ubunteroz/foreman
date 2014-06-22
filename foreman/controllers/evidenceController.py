from os import path
from datetime import datetime
# local imports
from baseController import BaseController
from ..utils.utils import ROOT_DIR, multidict_to_dict, session
from ..model import Evidence, Case, EvidenceHistory, ForemanOptions
from ..forms.forms import ChainOfCustodyForm, EditEvidenceForm, EditEvidencePhotosForm, EditEvidenceQRCodesForm, EvidenceAssociateForm, \
    AddEvidenceForm


class EvidenceController(BaseController):

    def add(self, case_id):
        case = self._validate_case(case_id)
        if case is not None:
            self.check_permissions(self.current_user, case, 'add-evidence')
            if self.validate_form(AddEvidenceForm()):
                for entry in self.form_result['photo']:
                    if entry is not None:
                        photos = True
                        break
                else:
                    photos = False
                evi = Evidence(case, self.form_result['reference'], self.form_result['type'],
                               self.form_result['comments'], self.form_result['originator'], self.form_result['location'],
                               self.current_user, self.form_result['bag_num'], photos, self.form_result['qr'])
                session.add(evi)
                session.flush()
                evi.add_change(self.current_user)
                return self.custody_in(case.case_name, evi.reference, True, initial=True)
            else:
                evidence_type_options = [(evi.evidence_type.replace(" ", "").lower(), evi.evidence_type) for evi in
                                         ForemanOptions.get_evidence_types()]
                return self.return_response('pages', 'add_evidence.html', case=case, errors=self.form_error,
                                            evidence_type_options=evidence_type_options)
        else:
            return self.return_404()

    def edit(self, case_id, evidence_id):
        evidence = self._validate_evidence(evidence_id, case_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'edit')

            photo_location = path.join(ROOT_DIR, 'static', 'evidence_photos', str(evidence.id))
            form_type = multidict_to_dict(self.request.args)
            evidence_type_options = [(evi.evidence_type.replace(" ", "").lower(), evi.evidence_type) for evi in
                                         ForemanOptions.get_evidence_types()]
            success = False
            active_tab = 0
            default_qr_code_text = evidence.generate_qr_code_text()

            if 'form' in form_type and form_type['form'] == "edit_evidence":
                if self.validate_form(EditEvidenceForm()):
                    evidence.reference = self.form_result['reference']
                    evidence.evidence_bag_number = self.form_result['bag_num']
                    evidence.type = self.form_result['type']
                    evidence.originator = self.form_result['originator']
                    evidence.comment = self.form_result['comments']
                    evidence.location = self.form_result['location']
                    evidence.add_change(self.current_user)
                    success = True

            elif 'form' in form_type and form_type['form'] == "edit_image":
                active_tab = 1
                if self.validate_form(EditEvidencePhotosForm()):
                    success = True

            elif 'form' in form_type and form_type['form'] == "edit_qr":
                active_tab = 2
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
                                        photo_location=photo_location, evidence_history=evidence_history,
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
            closed = False

            case = evidence.case
            confirm_close = multidict_to_dict(self.request.args)
            if 'confirm' in confirm_close and confirm_close['confirm'] == "true":
                evidence.disassociate()
                closed = True

            return self.return_response('pages', 'disassociate_evidence.html', evidence=evidence, closed=closed, case=case)
        else:
            return self.return_404()

    def remove(self, evidence_id):
        evidence = self._validate_evidence(evidence_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'remove')

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

            photo_location = path.join(ROOT_DIR, 'static', 'evidence_photos', str(evidence.id))
            return self.return_response('pages', 'view_evidence.html', evidence=evidence, photo_location=photo_location)
        else:
            return self.return_404()

    def view_caseless(self, evidence_id):
        return self.view(None, evidence_id)

    def view_all(self):
        evidence = Evidence.get_all(descending=True)
        return self.return_response('pages', 'view_evidences.html', evidence=evidence)

    def associate(self, evidence_id):
        evidence = self._validate_evidence(evidence_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'dis-associate')

            reassign_cases = [(r_case.id, r_case.case_name) for r_case in Case.get_all()]
            if self.validate_form(EvidenceAssociateForm()):
                evidence.associate(self.form_result['case_reassign'])
                return self.return_response('pages', 'associate_evidence.html', evidence=evidence, success=True,
                                            reassign_cases=reassign_cases)
            else:
                return self.return_response('pages', 'associate_evidence.html', evidence=evidence,
                                            errors=self.form_error, reassign_cases=reassign_cases)
        else:
            return self.return_404()

    def custody_in(self, case_id, evidence_id, check_in=True, initial=False):
        evidence = self._validate_evidence(evidence_id, case_id)
        if evidence is not None:
            self.check_permissions(self.current_user, evidence, 'check-in-out')

            if not initial and self.validate_form(ChainOfCustodyForm()):
                self.form_result['attach'] = None
                full_date = datetime.combine(self.form_result['date'], self.form_result['time'])
                if check_in:
                    evidence.check_in(self.form_result['user'], self.current_user, full_date,
                                      self.form_result['comments'], self.form_result['attach'],
                                      self.form_result['label'])
                else:
                    evidence.check_out(self.form_result['user'], self.current_user, full_date,
                                       self.form_result['comments'], self.form_result['attach'],
                                       self.form_result['label'])
                return self.view(case_id, evidence_id)
            else:
                return self.return_response('pages', 'evidence_custody_change.html', evidence=evidence,
                                            checkin=check_in, errors=self.form_error)
        else:
            return self.return_404()

    def custody_out(self, case_id, evidence_id):
        return self.custody_in(case_id, evidence_id, False)

    @staticmethod
    def _get_evidence_history_changes(evidence):
        history = EvidenceHistory.get_changes(evidence)
        history.sort(key=lambda d: d['date_time'])
        return history

