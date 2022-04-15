#!/usr/bin/env python
#
# Upload emails using IMAP append.

import os
import sys
from email.message import EmailMessage
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from time import time

SERVER = os.getenv('IMAP_HOSTNAME')
USERNAME = os.getenv('IMAP_USERNAME')
PASSWORD = os.getenv('IMAP_PASSWORD')
MAILBOX = os.getenv('IMAP_MAILBOX')


def auth() -> IMAP4:
    try:
        mbox = IMAP4_SSL(SERVER)
        mbox.login(USERNAME, PASSWORD)
    except ConnectionRefusedError as e:
        print('Could not connect to server:', e)
        sys.exit(2)

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

    if not (SERVER and USERNAME):
        print('Credentials not set')
        sys.exit(1)

    pprint(populate_emails())
