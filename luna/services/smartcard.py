import requests

from luna.data.wikidata import *

class SmartcardService:
    def __init__(self, query: str):
        url = f'https://www.wikidata.org/entity/{query}'
        headers = {'Accept': 'application/json'}

        # GET
        response = requests.get(url, headers=headers)

        # レスポンスのステータスコードを確認
        if response.status_code == 200:
            self.query = query
            self.data = response.json()
        else:
            raise ValueError

    def get_info(self, lang: str):
        entity = self.data['entities'][self.query]

        try:
            label = entity['labels'][lang]['value']
        except KeyError:
            label = entity['labels']["en"]['value']

        if len(entity['descriptions']) != 0:
            try:
                description = entity['descriptions'][lang]['value']
            except KeyError:
                description = entity['descriptions']["en"]['value']
        else:
            description = "No description was found."

        result = {"label": label,
                  "description": description}

        try:
            counts = 0
            result["official_website"] = entity['claims']['P856'][counts]['mainsnak']['datavalue']['value']

            for i in entity['claims']['P856']:
                for x in i['qualifiers']['P407']:
                    if x['datavalue']['value']['id'] == wikidata_langs[lang]:
                        result["official_website"] = entity['claims']['P856'][counts]['mainsnak']['datavalue']['value']

                counts += 1

        except:
            pass

        return result


def get_wikidata_id_from_query(query: str):
    import requests
    from bs4 import BeautifulSoup

    # ターゲットURL
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