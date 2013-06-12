from datetime import timedelta, datetime
import pytz
import requests
import time
import logging

logging.basicConfig(level=logging.DEBUG)


def _send_authenticated_pingdom_request(path, user, password, app_key, url_params):
    response = requests.get(
        url = "https://api.pingdom.com/api/2.0/" + path,
        auth = (user, password),
        headers = {
            'App-key': app_key
        },
        params = url_params
    )

    response.raise_for_status()

    return response.json()


class Pingdom(object):
    def __init__(self, config):
        self.user = config['user']
        self.password = config['password']
        self.app_key = config['app_key']
        self.API_LOCATION = "https://api.pingdom.com/api/2.0/"


    def _make_request(self, path, url_params={}):
        response = requests.get(
            url=self.API_LOCATION + path,
            auth=(self.user, self.password),
            headers={
                "App-Key": self.app_key
            },
            params=url_params
        )
        return response

    def _build_response(self, response):
        hours = response['summary']['hours']
        new_hours = []
        for hour in hours:
            hour.update({'starttime': datetime.fromtimestamp(
                hour['starttime'],
                tz=pytz.UTC
            )})
            new_hours.append(hour)
        return new_hours

    def uptime_for_last_24_hours(self, name, day):
        app_code = self.check_id(name)
        previous_day = day - timedelta(days=1)
        params={
                "includeuptime": "true",
                "from": time.mktime(previous_day.timetuple()),
                "to": time.mktime(day.timetuple()),
                "resolution": "hour"
        }
        path = "summary.performance/" + str(app_code)

        try:
            return self._build_response(_send_authenticated_pingdom_request(
                path=path,
                user=self.user,
                password=self.password,
                app_key=self.app_key,
                url_params=params
            ))
        except requests.exceptions.HTTPError as e:
            logging.error("Request to pingdom failed: %s" % str(e))

    def check_id(self, name):
        checks = _send_authenticated_pingdom_request(
            path="checks",
            user=self.user,
            password=self.password,
            app_key=self.app_key,
            url_params=None
        )

        check_to_find = [check for check in checks["checks"]
             if check["name"] == name]

        return check_to_find[0]["id"]
