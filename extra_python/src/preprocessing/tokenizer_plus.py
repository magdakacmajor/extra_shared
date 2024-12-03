from __future__ import print_function
from enum import Enum
import javalang
import re
import nltk
import traceback
from utils import re_patterns


class CharType(Enum):
    NUMERIC = 0
    ALPHALOWER = 1
    ALPHAUPPER = 2
    ALPHAOTHER = 3
    NONALPHANUM = 4
    SPACE = 5


def get_character_type(char):
    if not char.isalnum():
        return CharType.SPACE if char.isspace() else CharType.NONALPHANUM
    if char.isnumeric():
        return CharType.NUMERIC
    if char.isalpha():
        if char.islower():
            return CharType.ALPHALOWER
        if char.isupper():
            return CharType.ALPHAUPPER
        return CharType.ALPHAOTHER
    return None


def split_by_char_type(_str, exclude_list=[]):
    hadError = False
    for e in exclude_list:
        if _str.startswith(e):
            return [_str], hadError
    tokens = []
    start = 0
    previous_chtype = get_character_type(_str[start])
    for i in range(1, len(_str)):
        chtype = get_character_type(_str[i])
        if chtype is None:
            print(
                "Unable to handle character type %s, happened after %s" %
                (_str[i], tokens), flush=True)
            hadError = True
            continue
        if chtype == previous_chtype:
            continue
        if chtype == CharType.ALPHALOWER and previous_chtype == CharType.ALPHAUPPER:
            nextStart = i - 1
            if not nextStart == start:
                tokens.append(_str[start:nextStart])
                start = nextStart
        else:
            tokens.append(_str[start:i])
            start = i
        previous_chtype = chtype
    tokens.append(_str[start:len(_str)])
    return tokens, hadError


def split_by_char_type_ignore_case(_str):
    hadError = False
    tokens = []
    start = 0
    previous_chtype = get_character_type(_str[start])
    for i in range(1, len(_str)):
        chtype = get_character_type(_str[i])
        if chtype is None:
            print(
                "Unable to handle character type %s, happened after %s" %
                (_str[i], tokens), flush=True)
            hadError = True
            continue
        if chtype == previous_chtype:
            continue
        tokens.append(_str[start:i])
        start = i
        previous_chtype = chtype
    tokens.append(_str[start:len(_str)])
    return tokens, hadError


def get_basic_tokenizer_pattern():
    #     return re.compile(r'([().;,?!={}""<>+:\-\[\]/])')
    return re.compile(r'([().;,?!%{}""<>+=:\'\[\]/])')
#     return re.compile(r'([().;,?!=%{}""<>+:\^\&\-\[\]/])')
#     return re.compile(r'([().;,?!=%{}""<>+:*\^\&\-\[\]/])')


def tokenize_sequence(method_body,
                      split_identifiers,
                      split_strings=False,
                      exclude_list=[],
                      replace_url_uni=False,):
    hadError = False
    all_escaped = []
    all_unicode = []

    try:
        tokens = list(javalang.tokenizer.tokenize(method_body))
    except Exception as e:
        raise(e)

    parsed_tokens = []
    for token in tokens:
        if isinstance(
                token,
                javalang.tokenizer.Identifier) and split_identifiers:
            (ptokens, hadError) = split_by_char_type(
                token.value, exclude_list=exclude_list)
            if len(ptokens) > 1:
                ptokens = ['»'] + ptokens + ['«']
            if hadError:
                print(
                    "Tokenizer error on processing %s, token %s, after %s" %
                    (method_body, token.value, parsed_tokens), flush=True)

        elif isinstance(token, javalang.tokenizer.String):
            if not split_strings:
                parsed_tokens += ["STRINGTOKEN"]
                continue
            escaped_chars, unicode_strings, token = insert_special_tokens(
                token, replace_url_uni)
            all_escaped += escaped_chars
            all_unicode += unicode_strings
            try:
                subtokens = list(
                    javalang.tokenizer.tokenize(token.value[1:-1]))
                if split_identifiers:
                    parsed_subtokens = []
                    for subtoken in subtokens:
                        if isinstance(
                                subtoken,
                                javalang.tokenizer.Identifier) and split_identifiers:
                            (psubtokens, hadError) = split_by_char_type(
                                subtoken.value, exclude_list=exclude_list)
                            if len(psubtokens) > 1:
                                psubtokens = ['»'] + psubtokens + ['«']
                            if hadError:
                                print(
                                    "Tokenizer-plus error on processing %s, string %s, after %s" %
                                    (method_body, subtoken.value, parsed_subtokens), flush=True)
                        else:
                            psubtokens = [subtoken.value]
                        parsed_subtokens += psubtokens
                else:
                    parsed_subtokens = [
                        subtoken.value for subtoken in subtokens]

            except Exception as e:
                print('Javalang tokenizer returns %s' % str(e))
                print(token.value)
                subtokens = nltk.word_tokenize(token.value[1:-1])
                print('Tokenized with ntlk instead: success')
                print(' '.join(subtokens))
                if split_identifiers:
                    parsed_subtokens = []
                    for subtoken in subtokens:
                        (psubtokens, hadError) = split_by_char_type(
                            subtoken, exclude_list=exclude_list)
                        if len(psubtokens) > 1:
                            psubtokens = ['»'] + psubtokens + ['«']
                        if hadError:
                            print(
                                "Tokenizer-plus error on processing %s, string %s, after %s" %
                                (method_body, subtoken.value, parsed_subtokens), flush=True)
                        parsed_subtokens += psubtokens
                else:
                    parsed_subtokens = subtokens

            ptokens = [token.value[0]] + parsed_subtokens + [token.value[-1]]
        else:
            ptokens = [token.value]
        parsed_tokens += ptokens

    tokenized = re_patterns.tokens_to_escaped_chars(all_escaped, ' '.join(
        parsed_tokens))  # return re.sub( '\s+', ' ', ' '.join(parsed_tokens).strip() )
    tokenized = re_patterns.tokens_to_unicode_strings(all_unicode, tokenized)
    return re.sub('\\s+', ' ', tokenized.strip())


def spilt_subtoken(method_body, subtoken_value, exclude_list):
    (psubtokens, hadError) = split_by_char_type(
        subtoken_value, exclude_list=exclude_list)
    if len(psubtokens) > 1:
        psubtokens = ['»'] + psubtokens + ['«']
        if (hadError):
            print("Tokenizer-plus error on processing %s, string%s" %
                  (method_body, subtoken_value), flush=True)
    return psubtokens


def insert_special_tokens(token, replace_url_uni):
    try:
        if replace_url_uni:
            token.value = re_patterns.replace_standard_tokens(token.value)
            unicode_strings = []
        else:
            unicode_strings, token.value = re_patterns.unicode_to_tokens(
                token.value)
    except Exception:
        traceback.print_exc()
        print('Error on processing unicode strings in:\n %s' % token.value)
    try:
        escaped_chars, token.value = re_patterns.escaped_chars_to_tokens(
            token.value)
    except Exception:
        traceback.print_exc()
        print('Error on processing escaped characters in:\n %s' % token.value)
        escaped_chars = []

    return escaped_chars, unicode_strings, token
