'''
Created on 17 May 2019

@author: magda
'''


import re

""" URL pattern borrowed from https://gist.github.com/gruber/249502 """

# URL_PATTERN = re.compile(r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
IP_PATTERN = re.compile(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+')
UNICODE_PATTERN = re.compile(r'\\+u[A-Fa-f0-9]{4}')
HEX_PATTERN = re.compile(r'\\+x[A-Fa-f0-9]{2}')
ESC_CHAR_PATTERN = re.compile(r'\\+[nrt"\']')

URL_STRING = "URLSTRING"
IP_STRING = "IPSTRING"
UNICODE_STRING = " UNICODESTRING "
HEX_STRING = "HEXSTRING"
ESC_CHAR_TOKEN = " ESCHARTOKEN "


def replace_url(sequence):
    return re.sub(URL_PATTERN, URL_STRING, sequence)


def replace_ip(sequence):
    return re.sub(IP_PATTERN, IP_STRING, sequence)


def replace_unicode(sequence):
    return re.sub(UNICODE_PATTERN, UNICODE_STRING, sequence)


def replace_standard_tokens(sequence):
    return replace_unicode(replace_ip(replace_url(sequence)))


def original_to_tokens(sequence, pattern, special_token):
    escaped_chars = pattern.findall(sequence)
    copy = pattern.sub(special_token, sequence)
    return escaped_chars, copy


def escaped_chars_to_tokens(sequence):
    return original_to_tokens(sequence, ESC_CHAR_PATTERN, ESC_CHAR_TOKEN)


def unicode_to_tokens(sequence):
    return original_to_tokens(sequence, UNICODE_PATTERN, UNICODE_STRING)


def tokens_to_original(replaced_items, sequence, special_token):
    if replaced_items:
        for item in replaced_items:
            sequence = sequence.replace(special_token.strip(), item, 1)
    return sequence


def tokens_to_escaped_chars(escaped_chars, sequence):
    return tokens_to_original(escaped_chars, sequence, ESC_CHAR_TOKEN)


def tokens_to_unicode_strings(unicode_strings, sequence):
    return tokens_to_original(unicode_strings, sequence, UNICODE_STRING)
