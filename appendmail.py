#!/usr/bin/env python
#
# Upload emails using IMAP append.

import argparse
import os
import sys
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from pathlib import Path
from pprint import pprint
from time import time
from typing import Generator, Iterator, List, Tuple, TypedDict

# Define ENV VARS
SERVER = os.getenv('IMAP_HOSTNAME')
USERNAME = os.getenv('IMAP_USERNAME')
PASSWORD = os.getenv('IMAP_PASSWORD')
MAILBOX = os.getenv('IMAP_MAILBOX')

# Define custom Types
OpStatus = str
OpDetails = List[bytes]
MboxAppendResult = Tuple[OpStatus, OpDetails]
PopulateResult = TypedDict('PopulateResult', filename=str, result=MboxAppendResult)


def auth() -> IMAP4:
    try:
        mbox = IMAP4_SSL(SERVER)
        mbox.login(USERNAME, PASSWORD)
    except Exception as e:
        sys.exit('Could not connect to server: %s' % e)

    return mbox


def mbox_append(mbox: IMAP4, b_msg: bytes) -> MboxAppendResult:
    return mbox.append(MAILBOX, None, Time2Internaldate(time()), b_msg)


def read_emails_fs(input_dir: str) -> Generator:
    """
    Read emails from path.
    """
    resolved_path = Path(input_dir).resolve()
    if not resolved_path.is_dir():
        sys.exit('Input directory does not exist: %s' % resolved_path)

    dir_iter = resolved_path.iterdir()
    try:
        while _file := next(dir_iter):
            yield (_file.name, _file.read_bytes())
    except StopIteration:
        return None


def populate_emails(mbox: IMAP4, emails: Iterator) -> List[PopulateResult]:
    resp = list(
        dict(filename=filename, result=mbox_append(mbox, file_bytes))
        for filename, file_bytes in emails
    )
    return resp


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='Read email messages from directory')
    args = parser.parse_args()

    if not (SERVER and USERNAME):
        print('Credentials not set')
        sys.exit(2)

    mbox = auth()
    emails_from_fs = read_emails_fs(args.input_dir)
    result = populate_emails(mbox, emails_from_fs)
    pprint(result)
