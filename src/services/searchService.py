from src.helpers import makeHTMLRequest, latest_commit
from urllib.parse import unquote, urlparse
from _config import *
from flask import request, jsonify
import libfrea

from src.services.urlService import UrlService


class SearchService:
    def optimize(self, results: list) -> list:
        i = len(results) - 1

        while i >= 0:
            result = results[i]
            url = UrlService(result["url"])

            if libfrea.is_blocked(url.domain()) or libfrea.is_blocked(url.root_domain()):
                # print(f"kill {url.domain()} {i}")
                del results[i]
            else:
                # print(f"Do not kill {url.root_domain()} {i}")
                pass

            i -= 1

        return results
