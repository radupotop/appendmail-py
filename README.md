Append raw email messages (in Maildir format) to an IMAP mailbox.  
Works well together with [Getmail6][] for migrating messages between IMAP mailboxes.

## Running

Set your credentials in the `.env` file and then run:

```
dotenv run ./appendmail.py ~/Mail/new/ --log migration.log
```

[Getmail6]: https://getmail6.org/
