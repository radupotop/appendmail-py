#!/usr/bin/env python
#
# Upload emails using IMAP append.

import argparse
import calendar
import email.utils
import logging
import os
import re
import sys
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from pathlib import Path
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
PopulateResult = TypedDict(
    'PopulateResult', {'filename': str, 'date': str, 'result': MboxAppendResult}
)

DATE_HEADER_REGEX = r'\nDate: ?([a-zA-Z]*,? ?\d{1,2} [a-zA-Z]{3,} \d{4} \d{1,2}:\d{2}:\d{2} ?[+-]?\d{0,4})'

LOG_CONFIG = dict(
    format='%(message)s',
    encoding='utf-8',
    level=logging.INFO,
)


def auth() -> IMAP4:
    try:
        mbox = IMAP4_SSL(SERVER)
        mbox.login(USERNAME, PASSWORD)
    except Exception as e:
        logging.error('Could not connect to server: %s', e)
        sys.exit(1)

    logging.info('Logged-in to server: %s', SERVER)
    return mbox


def email_time_to_timestamp(dt):
    """Get UNIX timestamp from RFC 5322 email datetime format."""
    tt = email.utils.parsedate_tz(dt)
    return calendar.timegm(tt) - tt[9] if tt else None


def to_imap_datetime(dt):
    if dt_parsed := email_time_to_timestamp(dt):
        return Time2Internaldate(dt_parsed)


def parse_date_header(bytes_msg: bytes):
    # Decoding errors are safe to ignore since we only want the Date header.
    found = re.findall(DATE_HEADER_REGEX, bytes_msg.decode('utf-8', 'ignore'))
    return to_imap_datetime(found[0]) if found else None


def mbox_append(mbox: IMAP4, imap_date: str, msg_bytes: bytes) -> MboxAppendResult:
    return mbox.append(MAILBOX, None, imap_date, msg_bytes)


def read_emails_fs(input_dir: str) -> Generator:
    """
    Read emails from path.
    """
    resolved_path = Path(input_dir).resolve()
    if not resolved_path.is_dir():
        logging.error('Input directory does not exist: %s', resolved_path)
        sys.exit(1)

    logging.info('Reading emails from path: %s', resolved_path)
    dir_iter = resolved_path.iterdir()
    try:
        while _file := next(dir_iter):
            file_bytes = _file.read_bytes()
            yield (_file.name, parse_date_header(file_bytes), file_bytes)
    except StopIteration:
        return None


def populate_emails(mbox: IMAP4, emails: Iterator) -> Iterator[PopulateResult]:
    return (
        dict(
            filename=filename,
            date=parsed_date,
            result=mbox_append(mbox, parsed_date, file_bytes),
        )
        for filename, parsed_date, file_bytes in emails
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='Read email messages from directory')
    parser.add_argument('--log', help='Log file')
    args = parser.parse_args()

    if args.log and Path(args.log).resolve().parent.exists():
        LOG_CONFIG['filename'] = str(args.log)
    logging.basicConfig(**LOG_CONFIG)

    if not (SERVER and USERNAME):
        logging.error('Credentials not set')
        sys.exit(2)

    mbox = auth()
    emails_from_fs = read_emails_fs(args.input_dir)
    result = populate_emails(mbox, emails_from_fs)
    for msg_res in result:
        logging.info(msg_res)
    logging.info('DONE')
