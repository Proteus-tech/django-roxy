from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from httplib2 import Http, Response
from mock import Mock, patch

from roxy.views import proxy


# Urls for tests
urlpatterns = patterns('',
    url(r'', proxy('localhost:8009')),
)


@patch('httplib2.Http.request')
class TestRequest(TestCase):
    urls = 'roxy.tests.test_views'

    def setUp(self):
        super(TestRequest, self).setUp()
        self.mock_response = create_mock_response()

    def test_get(self, mock_request):
        """
        Test GET request.

        Request checklist:
        1. URL. The domain should be replaced by end server domain. Path must stay the same.
        2. Query is ?some=data
        2. Method should be 'GET'.
        3. Data should be empty.
        4. All headers are forwarded (including 'Content-Type').

        Response checklist:
        1.
        2.
        3.
        4.
        """
        self.mock_response['Set-Cookie'] = 'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8; expires=Tue, 26-Jul-2011 18:28:47 GMT; Max-Age=1209600; Path=/'
        self.mock_response['Location'] = 'http://someserver.com/login/?next=/'
        mock_request.return_value = self.mock_response, 'Mocked response content'

        response = self.client.get('/some/path', {'some': 'data'},
            HTTP_COOKIE = 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
            HTTP_ACCEPT = 'text/plain',
            HTTP_CACHE_CONTROL = 'no-cache',
            HTTP_HOST = 'testserver',
            CONTENT_LENGTH = '',
        )

        mock_request.assert_called_with(u'http://localhost:8009/some/path?some=data', 'GET', body=bytearray(b''),
            headers={
                'Accept': 'text/plain',
                'Cache-Control': 'no-cache',
                'Cookie': 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
                'Content-Type': 'text/html; charset=utf-8',
                'Host': 'localhost:8009',
            })

        self.assertEqual(response.content, 'Mocked response content')
        self.assertEqual(response['Set-Cookie'], 'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8; expires=Tue, 26-Jul-2011 18:28:47 GMT; Max-Age=1209600; Path=/')
        self.assertEqual(response['Location'], 'http://someserver.com/login/?next=/')

    def test_post(self, mock_request):
        """
        Test POST request.

        Request checklist:
        1. URL. The domain should be replaced by end server domain. Path must stay the same.
        2. Method should be 'POST'.
        3. Data should be in bytearray equivalence.
        4. All headers are forwarded (including 'Content-Type').

        Response checklist:
        1.
        2.
        3.
        4.
        """
        self.mock_response['Set-Cookie'] = 'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8; expires=Tue, 26-Jul-2011 18:28:47 GMT; Max-Age=1209600; Path=/'
        self.mock_response['Location'] = 'http://someserver.com/login/?next=/'
        mock_request.return_value = self.mock_response, 'Mocked response content'

        response = self.client.post('/some/path', {'some': 'data'}, content_type='application/json',
            HTTP_COOKIE = 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
            HTTP_ACCEPT = 'text/plain',
            HTTP_CACHE_CONTROL = 'no-cache',
            HTTP_HOST = 'testserver'
        )

        mock_request.assert_called_with(u'http://localhost:8009/some/path', 'POST', body=bytearray(b"{\'some\': \'data\'}"),
            headers={
                'Accept': 'text/plain',
                'Cache-Control': 'no-cache',
                'Cookie': 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
                'Content-Length': 16,
                'Content-Type': 'application/json',
                'Host': 'localhost:8009',
            })

        self.assertEqual(response.content, 'Mocked response content')
        self.assertEqual(response['Set-Cookie'], 'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8; expires=Tue, 26-Jul-2011 18:28:47 GMT; Max-Age=1209600; Path=/')
        self.assertEqual(response['Location'], 'http://someserver.com/login/?next=/')


class TestRedirectionStatus(TestCase):
    def setUp(self):
        mock_http_request(self, 302, location='http://someserver.com/login/?next=/')

    def tearDown(self):
        del Http.request
        Http.request = self.original_http_request

    def test_proxy(self):
        """
        Test that proxy supports anykind of URL
        """
        # TODO: test only mask location if location value is set to origin??
        response = self.client.get('/')
        self.assertEqual(302, response.status_code)
        self.assertEqual('http://testserver/login/?next=/', response['location'])


@patch('httplib2.Http.request')
class TestHopHeaders(TestCase):
    urls = 'roxy.tests.test_views'

    def setUp(self):
        super(TestHopHeaders, self).setUp()
        self.mock_response = create_mock_response()

    def test_hop_headers(self, mock_request):
        """
        Test hop-by-hop headers (e.g. Connection, Keep-Alive) should be ignored by roxy both request and response
        """
        self.mock_response['Connection'] = 'Fake connection'
        self.mock_response['Keep-Alive'] = 'Fake keep-alive'
        self.mock_response['Proxy-Authenticate'] = 'Fake proxy-authenticate'
        self.mock_response['Proxy-Authorization'] = 'Fake proxy-authorization'
        self.mock_response['TE'] = 'Fake te'
        self.mock_response['Trailers'] = 'Fake trailers'
        self.mock_response['Transfer-Encoding'] = 'Fake transfer-encoding'
        self.mock_response['Upgrade'] = 'Fake upgrade'
        self.mock_response['Set-Cookie'] = 'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8;'
        mock_request.return_value = self.mock_response, 'Mocked response content'

        response = self.client.get('/some/path', {'some': 'data'},
            HTTP_COOKIE = 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
            HTTP_ACCEPT = 'text/plain',
            HTTP_CACHE_CONTROL = 'no-cache',
            HTTP_CONNECTION = 'Fake connection',
            HTTP_KEEP_ALIVE = 'Fake keep-alive',
            HTTP_PROXY_AUTHENTICATE = 'Fake proxy-authenticate',
            HTTP_PROXY_AUTHORIZATION = 'Fake proxy-authorization',
            HTTP_TE = 'Fake te',
            HTTP_TRAILERS = 'Fake trailers',
            HTTP_TRANSFER_ENCODING = 'Fake transfer-encoding',
            HTTP_UPGRADE = 'Fake upgrade',
        )

        mock_request.assert_called_with(u'http://localhost:8009/some/path?some=data', 'GET', body=bytearray(b''),
            headers={
                'Accept': 'text/plain',
                'Cache-Control': 'no-cache',
                'Cookie': 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
                'Content-Type': 'text/html; charset=utf-8',
            })

        self.assertEqual(response.content, 'Mocked response content')
        self.assertEqual(response['Set-Cookie'], 'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8;')
        self.assertFalse(response.has_header('Connection'))
        self.assertFalse(response.has_header('Keep-Alive'))
        self.assertFalse(response.has_header('Proxy-Authenticate'))
        self.assertFalse(response.has_header('Proxy-Authorization'))
        self.assertFalse(response.has_header('TE'))
        self.assertFalse(response.has_header('Trailers'))
        self.assertFalse(response.has_header('Transfer-Encoding'))
        self.assertFalse(response.has_header('Upgrade'))


class TestMessagesCookie(TestCase):
    def setUp(self):
        self.patch_http_request = patch('httplib2.Http.request')
        self.mock_http_request = self.patch_http_request.start()

    def tearDown(self):
        self.patch_http_request.stop()

    def test_getting_page_with_messages_cookie(self):
        info = {}
        info['status'] = 200
        mock_response = Response(info)
        mock_response['set-cookie'] = 'csrftoken=82890e1660bc8ed4c2a65d8bbeaa8675; expires=Sun, 18-Nov-2012 17:22:50 GMT; Max-Age=31449600; Path=/, sessionid=f6d552348682acfea47aa2c203319e7a; expires=Sun, 04-Dec-2011 17:22:50 GMT; Max-Age=1209600; Path=/, messages=; expires=Thu, 01-Jan-1970 00:00:00 GMT; Max-Age=0; Path=/'
        self.mock_http_request.return_value = (mock_response,'')

        request_cookies = '__utma=96992031.73512554.1298128014.1298718782.1298921649.6; djdt=hide; sessionid=b5a63ebae5793e6c68d1d48980c6baf0; csrftoken=803112d8898d80a5612912957ec61db8; messages="e0821c371745ee46ec2cd2e317e451acfb02ef4a$[[\\"__json_message\\"\\05420\\054\\"2 companies have been merged\\"]]"'
        response = self.client.get('/admin/company/company/',**{'HTTP_COOKIE':request_cookies})
        self.assertIn('messages="e0821c371745ee46ec2cd2e317e451acfb02ef4a$[[\\"__json_message\\"\\05420\\054\\"2 companies have been merged\\"]]"',self.mock_http_request.call_args[1]['headers']['Cookie'])

    def test_getting_page_with_messages_cookie_as_last_cookie(self):
        def always_return_messages_last_clone_cookies(request_cookies):
            cookies = []
            print request_cookies
            for key, value in request_cookies.items():
                if key != 'messages':
                    cookies.append('%s=%s' % (key, value))
            cookie_value = ';'.join(cookies)
            if request_cookies.get('messages'):
                cookie_value = '%s;messages=%s' % (cookie_value,request_cookies['messages'])
            return cookie_value


        info = {}
        info['status'] = 200
        mock_response = Response(info)
        mock_response['set-cookie'] = 'csrftoken=82890e1660bc8ed4c2a65d8bbeaa8675; expires=Sun, 18-Nov-2012 17:22:50 GMT; Max-Age=31449600; Path=/, sessionid=f6d552348682acfea47aa2c203319e7a; expires=Sun, 04-Dec-2011 17:22:50 GMT; Max-Age=1209600; Path=/, messages=; expires=Thu, 01-Jan-1970 00:00:00 GMT; Max-Age=0; Path=/'
        self.mock_http_request.return_value = (mock_response,'')

        request_cookies = '__utma=96992031.73512554.1298128014.1298718782.1298921649.6; djdt=hide; sessionid=b5a63ebae5793e6c68d1d48980c6baf0; csrftoken=803112d8898d80a5612912957ec61db8; messages="e0821c371745ee46ec2cd2e317e451acfb02ef4a$[[\\"__json_message\\"\\05420\\054\\"2 companies have been merged\\"]]"'

        response = self.client.get('/admin/company/company/',**{'HTTP_COOKIE':request_cookies})
        
        self.assertIn('messages="e0821c371745ee46ec2cd2e317e451acfb02ef4a$[[\\"__json_message\\"\\05420\\054\\"2 companies have been merged\\"]]"',self.mock_http_request.call_args[1]['headers']['Cookie'])


def mock_http_request(test, code=200, content_type='text/html', **kwargs):
    info = {}
    info['status'] = code 
    mock_response = Response(info)
    mock_response['content-type'] = content_type 
    for key, value in kwargs.items():
        mock_response[key] = value 
    return_value = (mock_response, 'OK')
    test.original_http_request = Http.request
    Http.request = Mock(return_value=return_value)
    
def create_mock_response(status_code=200, content_type='text/html'):
    response = Response({'status': status_code})
    response['content-type'] = content_type
    return response