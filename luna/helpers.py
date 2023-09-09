import http

from bs4 import BeautifulSoup
from urllib.parse import unquote
import random
from _config import *
from flask import escape, Markup
import requests
import re
from os.path import exists


# search highlights
def highlight_query_words(string, query):
    query_words = [re.escape(word) for word in query.lower().split()]
    words = string.split()
    highlighted = []
    query_regex = re.compile('|'.join(query_words))
    highlighted_words = []
    for word in words:
        cleaned_word = word.strip().lower()
        if query_regex.search(cleaned_word) and cleaned_word not in highlighted:
            highlighted_words.append(Markup(f'<span class="highlight">{escape(word)}</span>'))
            highlighted.append(cleaned_word)
        else:
            highlighted_words.append(escape(word))
    return Markup(' '.join(highlighted_words))


def latest_commit():
    if exists(".git/refs/heads/main"):
        with open('./.git/refs/heads/main') as f:
            return f.readline()
    return "Not in main branch"


def detect_lang(texts):
    # korean
    if re.search("[\uac00-\ud7a3]", texts):
        return "ko"
    # japanese
    if re.search("[\u3040-\u30ff]", texts):
        return "ja"
    # chinese
    if re.search("[\u4e00-\u9FFF]", texts):
        return "zh"

    return "other"