from django.test import TestCase
import requests

BASE_URL = "http://localhost:8000/submit"
PREFIX = "/submit"


class TestServerRequests(TestCase):
    def test_index_page(self):
        r = requests.get(BASE_URL)
        self.assertEquals(200, r.status_code)

    def _logout(self):
        r = requests.get(BASE_URL + "/logout/")
        self.assertEquals(200, r.status_code)

    def _check_demo_login_flow(self, r):
        self.assertEquals(200, r.status_code)
        self.assertEquals(302, r.history[0].status_code)
        self.assertEquals(PREFIX + '/login/passthrough/', r.history[0].headers['Location'])
        self.assertEquals(302, r.history[1].status_code)
        self.assertEquals(BASE_URL + '/complete/passthrough', r.history[1].headers['Location'])
        self.assertEquals(301, r.history[2].status_code)
        self.assertEquals(PREFIX + '/complete/passthrough/', r.history[2].headers['Location'])
        self.assertEquals(302, r.history[3].status_code)
        self.assertEquals(BASE_URL + '/dashboard/', r.history[3].headers['Location'])

    def test_demo_admin_login(self):
        for login_type in ["admin", "owner", "tutor", "student"]:
            r = requests.get(BASE_URL + "/demo/{0}/".format(login_type))
            self._check_demo_login_flow(r)
            self._logout()
