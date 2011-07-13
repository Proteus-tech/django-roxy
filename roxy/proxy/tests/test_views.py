from django.conf import settings
from django.test.client import Client
from httplib2 import Http, Response
from mock import Mock, patch
from proxy.views import join_url, clone_cookies, update_response_header
from unittest2 import TestCase

class TestViews(TestCase):

    def test_join_url(self):
        """
        Ensure that the URL sent to requesting host is the origin server
        """
        path = '/services'
        expected = "http://%s/services" % settings.ORIGIN_SERVER
        self.assertEqual(expected, join_url(path))

    def test_join_url_with_params(self):
        """
        Ensure that request params are forwarded 
        """
        path = '/services/?status__code__exact=&venue__city__id__exact=&venue__id__exact=&q=212131&o='
        expected = "http://%s/services/?status__code__exact=&venue__city__id__exact=&venue__id__exact=&q=212131&o=" % settings.ORIGIN_SERVER
        self.assertEqual(expected, join_url(path))

    def test_join_secure_url(self):
        """
        Ensure that the secure URL sent to requesting host is the origin server
        """
        path = '/services'
        is_secure = True
        expected = "https://%s/services" % settings.ORIGIN_SERVER
        self.assertEqual(expected, join_url(path, is_secure))

    def test_clone_cookies__one_element(self):
        cookies = {'sessionid': '2af7395fba66995ad1376bf0e401b9a0'}
        self.assertEqual('sessionid=2af7395fba66995ad1376bf0e401b9a0', clone_cookies(cookies))


    def test_clone_cookies__many_elements(self):
        cookies = {'sessionid': 'a4516258966ea20a6a11aefbf2f576c4',
                   'expires': 'Tue, 26-Jul-2011 15:33:39 GMT',
                   'Max-Age': '1209600',
                   'Path': '/'
                  }
        expected = 'Path=/;sessionid=a4516258966ea20a6a11aefbf2f576c4;expires=Tue, 26-Jul-2011 15:33:39 GMT;Max-Age=1209600'
        self.assertEqual(expected, clone_cookies(cookies))



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
        client = Client()
        response = client.get('/some/freaking/url')
        self.assertEqual(200, response.status_code)


class TestPost(TestCase):

    def setUp(self):
        kwargs ={'Set-Cookie':'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8; expires=Tue, 26-Jul-2011 18:28:47 GMT; Max-Age=1209600; Path=/',
         'location':'http://someserver.com/login/?next=/'}
        mock_http_request(self,**kwargs)
    
    def tearDown(self):
        del Http.request
        Http.request = self.original_http_request

    def test_cookies_header_is_forwarded(self):
        """
        Test that if request comes with cookies, the cookies is forwared to origin server
        """
        client = Client()
        cookies = {'sessionid': 'a4516258966ea20a6a11aefbf2f576c4'}
        client.cookies.load(cookies) 
        client.post('/', {'some':'data'})
        args = Http.request.call_args[0]
        kwargs = Http.request.call_args[1]
        self.assertIn('Cookie', kwargs['headers'].keys())

    def test_set_cookie_header_is_forwarded(self):
        """
        Make sure that all headers are forwarded,
        especially 'set-cookies', if not forwarded login functionality won't work!
        """
        client = Client()
        response = client.post('/', {'some':'data'})
        msg = "'Set-Cookie' should be forwarded or login may fail"
        self.assertEqual(response.get('Set-Cookie',None),
                         'sessionid=ab3ffd358676a5ef2fbcebad3809c9d8; expires=Tue, 26-Jul-2011 18:28:47 GMT; Max-Age=1209600; Path=/',
                         msg)


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
        client = Client()
        response = client.get('/')
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
    
