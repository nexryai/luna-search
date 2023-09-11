import requests
from html import escape

from bs4 import BeautifulSoup
from flask import (
    Flask,
    render_template,
    make_response,
    redirect,
    request
)
import libfrea
from searx import webutils
from searx.search import initialize as search_initialize, SearchQuery, Search, EngineRef

from luna import log
from luna.helpers import detect_lang
from luna.services.emergency import EmergencyService
from luna.services.smartcard import get_wikidata_id_from_query
from luna.services.url import UrlService
from luna.services.weather import WeatherService
from luna.thread import LunaThread


class SearchService:
    def get_wikidata_id(self, query: str):
        url = f"https://www.wikidata.org/w/index.php?go=Go&search={query}"

        # リクエストを送信してページの内容を取得
        response = requests.get(url)

        # ページの内容をBeautiful Soupで解析
        soup = BeautifulSoup(response.content, "html.parser")

        # mw-search-result-headingクラスのdiv要素をすべて取得
        result_divs = soup.find_all("div", class_="mw-search-result-heading")

        # 各div要素内のaタグのhref属性の値を取得
        for div in result_divs:
            link = div.find("a")  # div要素内の最初のaタグを取得
            if link:
                href = link.get("href")  # aタグのhref属性の値を取得
                return href.split("/")[2]

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

    def search(self, query: str, category: str, pageno: str, search_language: str, accept_language: str):

        if category == "image":
            use_engines = [EngineRef("duckduckgo images", "images"),
                           EngineRef("brave", "images")]

        elif category == "reddit":
            query = f"site:reddit.com {query}"
            use_engines = [EngineRef("google", "general"),
                           EngineRef("duckduckgo", "general"),
                           EngineRef("brave", "general"),
                           EngineRef("qwant", "general")]

        elif "ja" in accept_language:
            # Accept-LanguageヘッダーにjaがあるならGooエンジンを有効にする
            # 区切り文字が2個以下なら日本語の結果のみ表示する ←特定条件で精度が下がるのでやめる
            # if query.count(" ") <= 2:
            #    search_language = "ja"

            use_engines = [EngineRef("google", "general"),
                           EngineRef("goo", "general"),
                           EngineRef("duckduckgo", "general"),
                           EngineRef("wikipedia", "general")]
        else:
            use_engines = [EngineRef("google", "general"),
                           EngineRef("duckduckgo", "general"),
                           EngineRef("wikipedia", "general")]


        search_query = SearchQuery(
            query=query,
            lang=search_language,
            safesearch=0,
            pageno=int(pageno),
            time_range="",
            engineref_list=use_engines
        )

        search = Search(search_query)  # pylint: disable=redefined-outer-name
        search_result = search.search()

        try:
            snipp = search_result.answers[0]
        except:
            snipp = None

        try:
            infobox = search_result.infoboxes[0]
        except:
            infobox = None

        results = search_result.get_ordered_results()

        # 結果の最適化
        frea = SearchService()
        results = frea.optimize(results)

        counts = 0
        for result in results:
            del results[counts]["parsed_url"]

            if 'content' in result and result['content']:
                result['content'] = escape(result['content'][:1024])
            if 'title' in result and result['title']:
                result['title'] = escape(result['title'] or '')

            if 'url' in result:
                result['pretty_url'] = webutils.prettify_url(result['url'])
            if result.get('publishedDate'):  # do not try to get a date from an empty string or a None type
                try:  # test if publishedDate >= 1900 (datetime module bug)
                    result['pubdate'] = result['publishedDate'].strftime('%Y-%m-%d %H:%M:%S%z')
                except ValueError:
                    result['publishedDate'] = None
                else:
                    result['publishedDate'] = webutils.searxng_l10n_timespan(result['publishedDate'])

            counts += 1

        log.dbg("Search result was ready!")

        return {"results": results,
                "snipp": snipp,
                "infobox": infobox}
