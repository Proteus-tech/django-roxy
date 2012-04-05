from django.conf import settings
from django.test import TestCase
from httplib2 import Http, Response
from mock import Mock, patch
from roxy.views import join_url, update_response_header


class TestViews(TestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.foo_origin = settings.ORIGIN_SERVER1
        self.bar_origin = settings.ORIGIN_SERVER2

    def test_join_url(self):
        """
        Ensure that the URL sent to requesting host is the origin server
        """
        path = '/services'
        expected = "http://%s/services" % self.foo_origin
        self.assertEqual(expected, join_url(path, self.foo_origin))

    def test_join_url_with_params(self):
        """
        Ensure that request params are forwarded 
        """
        path = '/services/?status__code__exact=&venue__city__id__exact=&venue__id__exact=&q=212131&o='
        expected = "http://%s/services/?status__code__exact=&venue__city__id__exact=&venue__id__exact=&q=212131&o=" % self.foo_origin
        self.assertEqual(expected, join_url(path, self.foo_origin))

    def test_join_secure_url(self):
        """
        Ensure that the secure URL sent to requesting host is the origin server
        """
        path = '/services'
        is_secure = True
        expected = "https://%s/services" % self.foo_origin
        self.assertEqual(expected, join_url(path, self.foo_origin, is_secure))


class TestOKStatus(TestCase):
    def setUp(self):
        mock_http_request(self)

    def tearDown(self):
        del Http.request
        Http.request = self.original_http_request

    def test_proxy(self):
        """
        Test that proxy supports anykind of URL
        """
        response = self.client.get('/some/freaking/url')
        self.assertEqual(200, response.status_code)

    @patch('roxy.views.join_url')
    def test_proxy(self, mock_join_url):
        """
        Test that proxy can be called with any server as given in urls.py
        #  in our urls.py

        origin_one = proxy(settings.ORIGIN_SERVER1)
        origin_two = proxy(settings.ORIGIN_SERVER2)
        url(r'^origin_server_1/', origin_one, name='proxy1'),
        url(r'^origin_server_2/', origin_two , name='proxy2'),
        url(r'^', origin_two , name='proxy3'),

        """


        response = self.client.get('/origin_server_1/')
        self.assertEqual(200, response.status_code)
        mock_join_url.assert_called_with('/origin_server_1/', settings.ORIGIN_SERVER1, False)


        response = self.client.get('/origin_server_2/')
        self.assertEqual(200, response.status_code)
        mock_join_url.assert_called_with('/origin_server_2/', settings.ORIGIN_SERVER2, False)

        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        mock_join_url.assert_called_with('/', settings.ORIGIN_SERVER2, False)


@patch('httplib2.Http.request')
class TestRequest(TestCase):
    urls = 'roxy.tests.urls'

    def setUp(self):
        super(TestRequest, self).setUp()
        self.mock_response = create_mock_response()

    def test_get(self, mock_request):
        """
        Test POST request.

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
        )

        mock_request.assert_called_with(u'http://localhost:8009/some/path?some=data', 'GET', body=bytearray(b''),
            headers={
                'Accept': 'text/plain',
                'Cache-Control': 'no-cache',
                'Cookie': 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
                'Content-Type': 'text/html; charset=utf-8',
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
        )

        mock_request.assert_called_with(u'http://localhost:8009/some/path', 'POST', body=bytearray(b"{\'some\': \'data\'}"),
            headers={
                'Accept': 'text/plain',
                'Cache-Control': 'no-cache',
                'Cookie': 'sessionid=a4516258966ea20a6a11aefbf2f576c4',
                'Content-Length': 16,
                'Content-Type': 'application/json',
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
        response = self.client.get('/')
        self.assertEqual(302, response.status_code)
        self.assertEqual('http://testserver/login/?next=/', response['location'])

        response = self.client.get('/')
        self.assertEqual(302, response.status_code)
        self.assertEqual('http://testserver/login/?next=/', response['location'])


class TestUpdateResponseHeaders(TestCase):
    def test_should_exclude_hop_by_hop_headers(self):
        """
        keys in _hop_headers (ie. connection, keep-alive) should be excluded from headers to avoid
        hop-by-hop assertion error
        """
        stub_response = {}
        headers = {'set-cookie':'sessionid=123','connection':1, 'keep-alive':1}
        update_response_header(stub_response, headers)
        self.assertNotIn('connection', stub_response)
        self.assertNotIn('keep-alive', stub_response)

    def test_update_response_headers(self):
        """
        keys should be included in response's headers
        """
        stub_response = {}
        headers = {'set-cookie':'sessionid=123','content-type':'text/html'}
        update_response_header(stub_response, headers)
        self.assertIn('set-cookie', stub_response)
        self.assertIn('content-type', stub_response)

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