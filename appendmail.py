#!/usr/bin/env python
#
# Upload emails using IMAP append.

import os
from email.message import EmailMessage
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from time import time

SERVER = os.getenv('IMAP_HOSTNAME', 'localhost')
USERNAME = os.getenv('IMAP_USERNAME', 'testuser')
PASSWORD = os.getenv('IMAP_PASSWORD', 'pass')
MAILBOX = os.getenv('IMAP_MAILBOX', 'INBOX')


def auth() -> IMAP4:
    mbox = IMAP4_SSL(SERVER)
    mbox.login(USERNAME, PASSWORD)
    return mbox


def mbox_append(mbox: IMAP4, msg: EmailMessage):
    return mbox.append(MAILBOX, None, Time2Internaldate(time()), msg.as_bytes())


def read_emails():
    """
    Read emails from path.
    """
    return []


def populate_emails():
    mbox = auth()
    emails = read_emails()
    resp = tuple(mbox_append(mbox, eml) for eml in emails)
    return emails, resp


if __name__ == '__main__':
    from pprint import pprint
    pprint(populate_emails())
