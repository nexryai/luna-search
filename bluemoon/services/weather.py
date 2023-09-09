import datetime
import requests
from zoneinfo import ZoneInfo

import pygeonlp.api


class WeatherService:
    def get_from_query(self, query: str) -> dict:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0'
        header = {
            'User-Agent': user_agent
        }

        pygeonlp.api.init()
        get_location = pygeonlp.api.geoparse(format(query))

        try:
            get_location[0]['geometry']['coordinates']
        except:
            raise ValueError

        lon = get_location[0]['geometry']['coordinates'][0]
        lat = get_location[0]['geometry']['coordinates'][1]

        # get weather data from met norway
        met_api_request_url = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=" + str(
            lat) + "&lon=" + str(lon)
        met_api_response = requests.get(met_api_request_url, headers=header)
        weather_json = met_api_response.json()

        get_date = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        now_date = get_date.strftime('%Y%m%d%H')

        get_d2_date = datetime.timedelta(days=1)
        get_d3_date = datetime.timedelta(days=2)

        date_year = get_date.year
        date_month = get_date.month
        date_day = get_date.day
        date_hour = get_date.hour

        date_d2_month = (get_date + get_d2_date).month
        date_d2_day = (get_date + get_d2_date).day
        date_d3_month = (get_date + get_d3_date).month
        date_d3_day = (get_date + get_d3_date).day

        # 翌日9時までの時間(h)
        d2_key = 24 + 9 - date_hour
        d3_key = 48 + 9 - date_hour

        weather = weather_json['properties']['timeseries'][0]['data']['next_12_hours']['summary']['symbol_code']
        temp_now = weather_json['properties']['timeseries'][0]['data']['instant']['details']['air_temperature']

        weather_d2 = weather_json['properties']['timeseries'][d2_key]['data']['next_12_hours']['summary']['symbol_code']
        weather_d3 = weather_json['properties']['timeseries'][d3_key]['data']['next_12_hours']['summary']['symbol_code']

        def get_max_temp(day):
            max_temp = -float('inf')
            for i in range(23):
                day_index = i + (24 * day - date_hour)
                i_temp = weather_json['properties']['timeseries'][day_index]['data']['instant']['details'][
                    'air_temperature']
                if max_temp < i_temp:
                    max_temp = i_temp

            return max_temp

        def get_min_temp(day):
            min_temp = float('inf')
            for i in range(23):
                day_index = i + (24 * day - date_hour)
                i_temp = weather_json['properties']['timeseries'][day_index]['data']['instant']['details'][
                    'air_temperature']
                if min_temp > i_temp:
                    min_temp = i_temp

            return min_temp

        maxtemp_d2 = get_max_temp(1)
        mintemp_d2 = get_min_temp(1)
        maxtemp_d3 = get_max_temp(2)
        mintemp_d3 = get_min_temp(2)

        return {'weather': weather, 'temp_now': temp_now, 'weather_d2': weather_d2, 'weather_d3': weather_d3,
                    'maxtemp_d2': maxtemp_d2, 'mintemp_d2': mintemp_d2, 'maxtemp_d3': maxtemp_d3,
                    'mintemp_d3': mintemp_d3, 'd2_disp': str(date_d2_month) + '/' + str(date_d2_day),
                    'd3_disp': str(date_d3_month) + '/' + str(date_d3_day),
                    'lon': lon, 'lat': lat}
