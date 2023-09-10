import threading
from html import escape
import json
import requests
import random

from flask import (
    Flask,
    render_template,
    make_response,
    redirect,
    request
)
from flask.wrappers import Response
from searx import webutils
from searx.search import initialize as search_initialize, SearchQuery, Search, EngineRef
from searx.webapp import werkzeug_reloader

from _config import *
from luna.helpers import detect_lang
from luna.services.emergency import EmergencyService
from luna.services.smartcard import get_wikidata_id_from_query
from luna.services.weather import WeatherService
from luna.services.search import SearchService
from luna import helpers
from luna import log
from luna.thread import LunaThread

app = Flask(__name__, static_folder="static", static_url_path="")
app.jinja_env.filters['highlight_query_words'] = helpers.highlight_query_words
app.jinja_env.globals.update(int=int)

COMMIT = helpers.latest_commit()


@app.errorhandler(500)
def internal_error(error):

    return render_template('error.jinja2')


@app.errorhandler(404)
def not_found(error):
    return render_template('404.jinja2'), 404


@app.route('/settings')
def settings():
    # default theme if none is set
    theme = request.cookies.get('theme', DEFAULT_THEME)
    lang = request.cookies.get('lang')
    safe = request.cookies.get('safe')
    new_tab = request.cookies.get('new_tab')
    domain = request.cookies.get('domain')
    javascript = request.cookies.get('javascript')
    return render_template('settings.jinja2',
                           theme=theme,
                           lang=lang,
                           safe=safe,
                           new_tab=new_tab,
                           domain=domain,
                           javascript=javascript,
                           commit=COMMIT,
                           repo_url=REPO,
                           current_url=request.url
                           )


@app.route('/save-settings', methods=['POST'])
def save_settings():
    # get the selected theme from the form
    theme = request.form.get('theme')
    new_tab = request.form.get('new_tab')
    past_location = request.form.get('past')

    # set the theme cookie
    response = make_response(redirect(request.referrer))
    if theme is not None:
        response.set_cookie('theme', theme, max_age=COOKIE_AGE, httponly=True, secure=app.config.get("HTTPS"))
    if new_tab is not None:
        response.set_cookie('new_tab', new_tab, max_age=COOKIE_AGE, httponly=True, secure=app.config.get("HTTPS"))
    response.headers["Location"] = past_location

    return response


@app.route("/suggestions")
def suggestions():
    query = request.args.get("q", "").strip()
    response = requests.get(f"https://ac.duckduckgo.com/ac?q={query}&type=list")
    return json.loads(response.text)


@app.route("/wikipedia")
def wikipedia():
    query = request.args.get("q", "").strip()
    response = helpers.makeHTMLRequest(f"https://wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&titles={query}&pithumbsize=500")
    return json.loads(response.text)


@app.route("/img_proxy")
def img_proxy():
    # Get the URL of the image to proxy
    url = request.args.get("url", "").strip()

    # Only allow proxying image from startpage.com, upload.wikimedia.org and imgs.search.brave.com
    if not (url.startswith("https://s1.qwant.com/") or url.startswith("https://s2.qwant.com/") or url.startswith("https://upload.wikimedia.org/wikipedia/commons/") or url.startswith("https://yt.revvy.de")):
        return Response("Error: invalid URL", status=400)

    # Choose one user agent at random
    user_agent = random.choice(user_agents)
    headers = {"User-Agent": user_agent}

    # Fetch the image data from the specified URL
    response = requests.get(url, headers=headers)

    # Check that the request was successful
    if response.status_code == 200:
        # Create a Flask response with the image data and the appropriate Content-Type header
        return Response(response.content, mimetype=response.headers["Content-Type"])
    else:
        # Return an error response if the request failed
        return Response("Error fetching image", status=500)


@app.route("/", methods=["GET", "POST"])
@app.route("/search", methods=["GET", "POST"])
def search():
    log.dbg("Request Handled")
    if request.method == "GET":
        # get the `q` query parameter from the URL
        query = request.args.get("q", "").strip()
        category = request.args.get("t", "").strip()
        pageno = request.args.get("p", "1").strip()

        # クエリがないならトップページ
        if query == "":
            if request.cookies.get('theme', DEFAULT_THEME) == 'dark_blur':
                css_style = "dark_blur_beta.css"
            else:
                css_style = None
            return render_template("search.jinja2", theme=request.cookies.get('theme', DEFAULT_THEME),
                                   javascript=request.cookies.get('javascript', 'enabled'), DEFAULT_THEME=DEFAULT_THEME,
                                   css_style=css_style, repo_url=REPO, commit=COMMIT)

        query = query.replace("　", " ")

        accept_language = request.headers.get("Accept-Language", "")
        search_language = "en"

        if detect_lang(query) == "ja":
            search_language = "ja"

        # 非同期でスマートカードの情報取得処理
        def smartcard_task(original_query: str, lang: str):
            log.dbg("smartcard_task started on thread")
            if original_query.count(" ") >= 2:
                return None

            wikidata_id = get_wikidata_id_from_query(original_query)

            if wikidata_id is None:
                return None

            from luna.services.smartcard import SmartcardService
            smart_card_processor = SmartcardService(wikidata_id)
            return smart_card_processor.get_info(lang)

        smartcard_thread = LunaThread(target=smartcard_task, args=(query, search_language))
        smartcard_thread.start()

        def infobar_task(original_query: str, lang: str):
            log.dbg("infobar_task started on thread")
            emergency_info = EmergencyService()
            infobar = emergency_info.get()

            if "天気" in query:
                weather_info = WeatherService()
                infobar["weather"] = weather_info.get_from_query(original_query)
            else:
                infobar["weather"] = None

            return infobar

        infobar_thread = LunaThread(target=infobar_task, args=(query, search_language))
        infobar_thread.start()

        search_processor = SearchService()
        r = search_processor.search(query, category, pageno, search_language, accept_language)

        if category == "image":
            return render_template("images.jinja2",
                                   results=r["results"], p=1, title=f"{query} - Luna Search",
                                   q=f"{query}",
                                   theme=request.cookies.get('theme', DEFAULT_THEME),
                                   new_tab=request.cookies.get("new_tab"),
                                   javascript="enabled", DEFAULT_THEME=DEFAULT_THEME,
                                   type="image", search_type="image", repo_url=REPO, lang="ja", safe=0, check="",
                                   snipp=r["snipp"], infobox=r["infobox"]
                                   )

        # スレッドの終了を待機
        log.dbg("Waiting for infobar_thread")
        infobar_thread.join()
        infobar = infobar_thread.get_result()

        log.dbg("Waiting for smartcard_thread")
        smartcard_thread.join()
        smart_card = smartcard_thread.get_result()

        log.dbg(f"{query}: Result OK!!!")

        return render_template("results.jinja2",
                               results=r["results"], p=1, title=f"{query} - Luna Search",
                               q=f"{query}",
                               theme=request.cookies.get('theme', DEFAULT_THEME),
                               new_tab=request.cookies.get("new_tab"),
                               javascript="enabled", DEFAULT_THEME=DEFAULT_THEME,
                               type=category, search_type="text", repo_url=REPO, lang="ja", safe=0, check="",
                               snipp=r["snipp"], infobox=r["infobox"], infobar=infobar, smart_card=smart_card
                               )


if __name__ == "__main__":
    import socket
    from pyfiglet import Figlet

    aa = Figlet(font="thin")
    welcome_aa = aa.renderText("Luna Search")

    print(f"Booting Luna Search Server ver.0.10 (codename: Night Ocean) on {socket.gethostname()}\033[34;1m")
    print(welcome_aa)
    print(
        "\033[90;1m(c) 2023 nexryai\nThis program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;",
        "without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.",
        "See the GNU Affero General Public License for more details.\n\n\033[0m")

    daemon = EmergencyService()

    log.info("Starting monitor daemon...")
    daemon_thread = threading.Thread(target=daemon.start_monitor)
    daemon_thread.daemon = True
    daemon_thread.start()

    log.info("Starting server...")
    log.info(f"Listen on port {PORT}")

    app.run(threaded=True, port=PORT)
