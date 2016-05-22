#!/usr/bin/env python

# local imports
from ..model import Evidence, EvidenceStatus, UserRoles
from mail import email
from utils import config, session


def retention_notifier(evidence_list=None):
    admins = UserRoles.get_admins()
    if evidence_list is None:
        evidence_list = Evidence.get_filter_by(current_status=EvidenceStatus.ARCHIVED)
    for evidence in evidence_list:
        if evidence.reminder_due():
            to = [evidence.user.email] + [a.email for a in admins]
            title = "Evidence {} has reached its retention period".format(evidence.reference)
            body = """
            Hello,

            The following piece of evidence has reached its retention period. This evidence can now be destroyed.
            Please update the status of the evidence once completed.

            Reference: {}
            Case: {}
            Evidence Type: {}
            Date Evidence Added: {}
            Date Evidence Archived: {}

            Thanks,
            Foreman
            {}""".format(evidence.reference, evidence.case.case_name if evidence.case else "N/A",
                         evidence.type, evidence.date, evidence.archive_date,
                         config.get('admin', 'website_domain'))

            email(to, title, body, config.get('email', 'from_address'))
            evidence.retention_reminder_sent = True
            session.flush()
            session.commit()

scheduled = ['retention_notifier']