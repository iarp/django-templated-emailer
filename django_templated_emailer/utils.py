import re
import requests


def unique_emails(*args, joiner=None):
    """ Returns a set of unique email addresses to avoid duplicated entries.

    Pass any type of string or iterable of email addresses as a non-keyworded parameter and it'll return a unique set.
    Strings will attempt to be split on semi-colon, comma, or pipe character.
    Supply a string value to joiner and it'll return a string joined by joiner value.

    >>> unique_emails('email1@domain.com', 'email2@domain.com', 'email1@domain.com;email2@domain.com')
    {'email1@domain.com', 'email2@domain.com'}

    >>> unique_emails('no-reply@moha.ca', 'info@moha.ca', 'no-reply@moha.ca;info@moha.ca', joiner=',')
    'no-reply@moha.ca,info@moha.ca'

    Args:
        *args: string or iterable of email addresses.
        joiner: string or None to join the email addresses into a single string.

    Returns:
        string or set of unique email addresses.
    """
    ueq = set()
    for arg in args:

        if not arg:
            continue

        try:
            arg = re.split('[;,|]', arg)
        except:
            pass

        for email in arg:

            if not isinstance(email, str):
                continue

            if re.match(r'[^@]+@[^@]+\.[^@]+', email):
                ueq.add(email.lower().strip())

    if joiner is not None:
        return joiner.join(ueq)

    return ueq


def download_file(url, filename, write_mode='wb', **kwargs):
    with requests.get(url) as response, open(filename, write_mode, **kwargs) as out_file:
        if response.status_code == 200:
            out_file.write(response.content)
