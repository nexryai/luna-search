import ast
import os
import time

from lxml import etree
import redis as pyredis
import requests
from urllib import request as request_html

from bluemoon import log


class EmergencyService:
    def __init__(self):
        self.redis = pyredis.Redis(host=os.getenv("REDIS_HOST", "127.0.0.1"),
                                   port=int(os.getenv("REDIS_PORT", "6379")),
                                   db=int(os.getenv("REDIS_DB", "1")))

    def get(self) -> dict:
        tsunami_result_str = self.redis.get("tsunami_status").decode("UTF-8")
        jalert_result_str = self.redis.get("jalert_status").decode("UTF-8")

        result = {'tsunami': ast.literal_eval(tsunami_result_str),
                  'jalert': ast.literal_eval(jalert_result_str)}

        return result

    def set_tsunami_info(self):
        api_url = 'https://api.p2pquake.net/v2/jma/tsunami?limit=1&offset=0&order=-1'

        # For debug
        # api_url = 'https://api.p2pquake.net/v2/jma/tsunami?limit=1&offset=8&order=-1'

        try:
            result = requests.get(api_url, timeout=5).json()
        except Exception as e:
            response = {'alert': False, 'error': True}
        else:
            if result[0]["cancelled"]:
                response = {'alert': False}
            else:
                grade = result[0]["areas"][0]["grade"]
                if grade == "Watch":
                    grade_disp = "津波注意報"
                elif grade == "Warning":
                    grade_disp = "津波警報"
                elif grade == "MajorWarning":
                    grade_disp = "大津波警報"
                else:
                    grade_disp = "津波に関する情報"

                response = {'alert': True, 'grade': grade_disp}

        self.redis.set("tsunami_status", str(response))

    def set_jalert_info(self):
        try:
            html = request_html.urlopen('https://emergency-weather.yahoo.co.jp/weather/jp/jalert/')

            # For debug
            # html = request_html.urlopen('https://web.archive.org/web/20230415044515/https://emergency-weather.yahoo.co.jp/weather/jp/jalert/')

            contents = html.read()

            htmltxt = contents.decode()
            et = etree.fromstring(htmltxt, parser=etree.HTMLParser())
            content = et.xpath("/html/body/div/div[2]/section[1]/div/div[2]/p/text()")

        except:
            log.error("Error. (ab6c07de-554d-420a-b47d-4312a189785a)")
            return

        if len(content) <= 2:
            response = {'alert': False}

            chk = et.xpath("/html/body/div/div[2]/section[1]/div/div[2]/p/span/text()")
            try:
                chk[1]
            except IndexError:
                pass
            else:
                log.error("Error. (ef1240d4-9508-4439-b111-5be16b2eed6c)")
        else:
            response = {'alert': True, 'text': '\n'.join(content)}

        self.redis.set("jalert_status", str(response))

    def start_monitor(self):
        while True:
            self.set_tsunami_info()
            self.set_jalert_info()
            log.info("info updated!")
            time.sleep(45)
