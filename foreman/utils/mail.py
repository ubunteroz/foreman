# python imports
import smtplib
from email.MIMEText import MIMEText
from email.Header import Header
# foreman imports
from utils import config


def send_email(to_addrs, subject, msg, from_addr, cc=None, bcc=None):
    """ Send an email """
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = from_addr

    assert isinstance(to_addrs, list)
    msg['To'] = ', '.join(to_addrs)

    if cc:
        msg['CC'] = ', '.join(cc)
        to_addrs.extend(cc)
    if bcc:
        to_addrs.extend(bcc)

    smtp = smtplib.SMTP()
    smtp.connect(config.get('email', 'email_host'))
    smtp.sendmail(from_addr, to_addrs, msg.as_string())
    smtp.quit()


def print_email(to_addrs, subject, msg, from_addr, cc=None, bcc=None):
    """ Used to print the email rather than send, for testing purposes """
    s = '**Email Text**'
    s += '\nFrom: ' + from_addr
    s += '\nTo: ' + ', '.join(to_addrs)
    if cc:
        s += '\nCC: ' + ', '.join(cc)
    if bcc:
        s += '\nBCC: ' + ', '.join(bcc)
    s += '\nSubject: ' + subject
    s += '\n\n'
    s += msg
    s += '\n**End Email**'
    print s.encode('utf-8')


def email(to_addrs, subject, msg, from_addr, cc=None, bcc=None):
    send_live_email = config.getboolean('email', 'send_email')

    modified_subject = "[Foreman] " + subject
    # ensures all emails from Foreman start the same, so users can filter them in their email client

    if send_live_email:
        send_email(to_addrs, modified_subject, MIMEText(msg.encode('utf-8'), _charset='utf-8'), from_addr, cc, bcc)
    else:
        print_email(to_addrs, modified_subject, msg, from_addr, cc, bcc)