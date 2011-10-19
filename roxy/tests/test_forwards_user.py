from mock import patch, Mock

from django.contrib.auth.models import User
from django.test import TestCase


class _MockReturn(dict):
    def __init__(self):
        self['content-type'] = 'text/plain'
        self.status = 200

class UserForwarding(TestCase):
    def setUp(self):
        self.user = User(username='testuser')
        self.user.set_password('pass')
        self.user.save()
        super(UserForwarding, self).setUp()

    def test_no_user(self):
        def no_user_header(url, method, body, headers):
            self.assertNotIn('X-FOST-User', headers.keys())
            return _MockReturn(), 'ok'
        with patch('roxy.views._http.request', no_user_header):
            self.client.get('/')

    def test_with_user(self):
        self.client.login(username = 'testuser', password = 'pass')
        def no_user_header(url, method, body, headers):
            self.assertIn('X-FOST-User', headers.keys())
            return _MockReturn(), 'ok'
        with patch('roxy.views._http.request', no_user_header):
            self.client.get('/')

