#!/usr/bin/env python
#
# Upload emails using IMAP append.

import os
import sys
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from pathlib import Path
from time import time
from typing import Dict, Generator, Iterator, List, Tuple

SERVER = os.getenv('IMAP_HOSTNAME')
USERNAME = os.getenv('IMAP_USERNAME')
PASSWORD = os.getenv('IMAP_PASSWORD')
MAILBOX = os.getenv('IMAP_MAILBOX')

Filename = str
IMAPResult = Dict[Tuple, Filename]


def auth() -> IMAP4:
    try:
        mbox = IMAP4_SSL(SERVER)
        mbox.login(USERNAME, PASSWORD)
    except ConnectionRefusedError as e:
        print('Could not connect to server:', e)
        sys.exit(2)

    return mbox


def mbox_append(mbox: IMAP4, b_msg: bytes):
    return mbox.append(MAILBOX, None, Time2Internaldate(time()), b_msg)


def read_emails_fs(path: str) -> Generator:
    """
    Read emails from path.
    """
    dir_iter = Path(path).iterdir()
    try:
        while _file := next(dir_iter):
            yield (_file.read_bytes(), _file.name)
    except StopIteration:
        return None


def populate_emails(emails: Iterator) -> List[IMAPResult]:
    mbox = auth()
    resp = list(
        dict(result=mbox_append(mbox, b_msg), filename=filename)
        for b_msg, filename in emails
    )
    return resp


if __name__ == '__main__':
    from pprint import pprint

    if not (SERVER and USERNAME):
        print('Credentials not set')
        sys.exit(1)

    pprint(populate_emails(read_emails_fs('samples/')))
