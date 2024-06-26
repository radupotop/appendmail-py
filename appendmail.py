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
from datetime import datetime
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from pathlib import Path
from typing import Generator, Iterator, List, Tuple, TypedDict

# Define ENV VARS
SERVER = os.environ['IMAP_HOSTNAME']
USERNAME = os.environ['IMAP_USERNAME']
PASSWORD = os.environ['IMAP_PASSWORD']
MAILBOX = os.environ['IMAP_MAILBOX']

# Define custom Types
OpStatus = str
OpDetails = List[bytes]
ImapOpResponse = Tuple[OpStatus, OpDetails]
PopulateResult = TypedDict(
    'PopulateResult', {'filename': str, 'date': str | None, 'result': ImapOpResponse}
)
EmailsFromFS = Tuple[str, bytes, str | None, str | None]
EmailsFromFSGenerator = Generator[EmailsFromFS, None, None]

DATE_HEADER_REGEX = r'\nDate: ?([a-zA-Z]*,? ?\d{1,2} [a-zA-Z]{3,} \d{4} \d{1,2}:\d{2}:\d{2} ?[+-]?\d{0,4})'
LABELS_REGEX = r'X-GMAIL-LABELS: "\\\\?([\w]+)"'

LOG_CONFIG = dict(
    format='%(message)s',
    encoding='utf-8',
    level=logging.INFO,
)


def auth() -> IMAP4:
    status = [None, None]
    try:
        mbox = IMAP4_SSL(SERVER)
        status = mbox.login(USERNAME, PASSWORD)
    except Exception as e:
        logging.error('Could not connect to server: %s', e)
        sys.exit(1)

    logging.info('Logged-in to server: %s, %s', SERVER, status)
    return mbox


def email_time_to_timestamp(dt: str) -> int:
    """Get UNIX timestamp from RFC 5322 email datetime format."""
    tt = email.utils.parsedate_tz(dt)
    return calendar.timegm(tt) - tt[9] if tt else None


def to_imap_datetime(dt: str) -> str:
    """
    Convert date_time to IMAP4 INTERNALDATE representation.
    Return string in form: '"DD-Mmm-YYYY HH:MM:SS +HHMM"'
    """
    if dt_parsed := email_time_to_timestamp(dt):
        return Time2Internaldate(dt_parsed)


def parse_headers(bytes_msg: bytes) -> Tuple[str | None, str | None]:
    """
    Parse headers from email.
    UTF-8 decoding errors are safe to ignore since we only want a few headers.
    """
    decoded_msg = bytes_msg.decode('utf-8', 'ignore')
    found_date = re.findall(DATE_HEADER_REGEX, decoded_msg)
    found_labels = re.findall(LABELS_REGEX, decoded_msg)
    return (
        to_imap_datetime(found_date[0]) if found_date else None,
        found_labels[0] if found_labels else None,
    )


def mbox_append(
    mbox: IMAP4, msg_bytes: bytes, imap_date: str, imap_labels: str
) -> ImapOpResponse:
    return mbox.append(MAILBOX, imap_labels, imap_date, msg_bytes)


def check_path(input_dir: str) -> Path:
    resolved_path = Path(input_dir).resolve()
    if not resolved_path.is_dir():
        logging.error('Input directory does not exist: %s', resolved_path)
        sys.exit(1)
    return resolved_path


def read_emails_fs(resolved_path: Path) -> EmailsFromFSGenerator:
    """
    Read emails from local filesystem path.
    """
    logging.info('Reading emails from path: %s', resolved_path)
    dir_iter = resolved_path.iterdir()
    try:
        while _file := next(dir_iter):
            file_bytes = _file.read_bytes()
            yield (_file.name, file_bytes, *parse_headers(file_bytes))
    except StopIteration:
        return None


def populate_emails(
    mbox: IMAP4,
    emails: EmailsFromFSGenerator,
) -> Iterator[PopulateResult]:
    return (
        dict(
            filename=filename,
            date=parsed_date,
            result=mbox_append(mbox, file_bytes, parsed_date, labels),
        )
        for filename, file_bytes, parsed_date, labels in emails
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='Read email messages from directory')
    parser.add_argument('--log', help='Log file')
    args = parser.parse_args()

    if args.log:
        logfile = Path(args.log).resolve()
        logfile.touch()
        LOG_CONFIG['filename'] = str(logfile)
    logging.basicConfig(**LOG_CONFIG)

    if not (SERVER and USERNAME):
        logging.error('Credentials not set')
        sys.exit(2)

    mbox = auth()
    emails_from_fs = read_emails_fs(check_path(args.input_dir))
    result = populate_emails(mbox, emails_from_fs)
    logging.info('START %s', datetime.now())
    for msg_res in result:
        logging.info(msg_res)
    logging.info('DONE %s', datetime.now())
