"""
views that handle reverse proxy
"""
from django.http import HttpResponse
from django.core.servers.basehttp import _hop_headers
from django.conf.global_settings import DEFAULT_CONTENT_TYPE
from httplib2 import Http, urlparse

_http = Http()
_http.follow_redirects = False

def proxy(origin_server, prefix=None):
    """
    Builder for the actual Django view. Use this in your urls.py.
    """
    def get_page(request):
        """
        reverse proxy Django view
        """
        path = request.get_full_path().replace(prefix, '', 1) if prefix else request.get_full_path()
        target_url = join_url(path, origin_server, request.is_secure())
        headers = {}
        if request.COOKIES:
            cookie_value = adjust_messages_cookie(clone_cookies(request.COOKIES))
            headers = {'Cookie': cookie_value}

        if request.method == 'POST' or request.method == 'PUT':
            headers['Content-Type'] = request.META['CONTENT_TYPE']
        if request.user.is_authenticated():
            headers['X-FOST-User'] = request.user.username
        httplib2_response, content = _http.request(
            target_url, request.method, body=request.raw_post_data, headers=headers)
        content_type = httplib2_response.get('content-type',DEFAULT_CONTENT_TYPE)
        response = HttpResponse(content, status=httplib2_response.status, content_type=content_type)

        update_response_header(response, httplib2_response)

        update_messages_cookie(request,headers,httplib2_response,response)

        if httplib2_response.status in [302]:
            url = httplib2_response['location']
            masked_location = masked_url(url, request.get_host(), prefix)
            response['location'] = masked_location
        return response
    return get_page

def join_url(path, origin_server, is_secure=False):
    """
    return tartget_url of origin server
    """
    protocol = 'http'
    if is_secure:
        protocol = 'https'
    return  ('%s://%s%s') % (protocol, origin_server, path)

def masked_url(url, host, prefix):
    """
    Mask given url with host

    http://www.google.com/search?... -> http://<host>/search?...
    """
    splited_url = urlparse.urlsplit(url)
    # _replace is an only method to edit properties of namedtuple :(
    # pylint: disable=E1103,W0212
    # no error
    masked_splited_url = splited_url._replace(netloc = '%s/%s' % (host, prefix) if prefix else host)
    # pylint: enable=E1103,W0212
    # error
    return masked_splited_url.geturl()

def clone_cookies(request_cookies):
    """
    return value to be set in Cookie header to pass on
    """
    cookies = []
    for key, value in request_cookies.items():
        cookies.append('%s=%s' % (key, value))
    cookie_value = ';'.join(cookies)
    return cookie_value

def update_response_header(response, headers):
    """
    update response header with given headers

    ignore hop headers to avoid django hop-by-hop assertion error
    """
    ignored_keys = ['status', 'content-location'] + _hop_headers.keys()
    for key, value in headers.items():
        if key not in ignored_keys:
            response[key] = value


def adjust_messages_cookie(cookie_value):
    messages_key = 'messages='
    # find messages
    messages_pos = cookie_value.find(messages_key)
    if messages_pos != -1:
        # find the end of messages
        comma_pos = cookie_value.find(';',messages_pos)
        # content before message
        content_before = cookie_value[:messages_pos+len(messages_key)]
        content_after = cookie_value[comma_pos:]
        messages_content = cookie_value[messages_pos+len(messages_key):comma_pos]
        adjusted_cookie_value = '%s"%s"%s' % (content_before,messages_content.replace('"','\\"'),content_after)
        return adjusted_cookie_value
    else:
        return cookie_value

def update_messages_cookie(request,headers,httplib2_response,response):
    """
    If the request has messages cookie, and now the response from the backend says that it should be deleted,
    we should delete the cookie
    """
    if request.method == 'GET' and headers.get('Cookie') and headers['Cookie'].find('messages=') \
        and httplib2_response.get('set-cookie','').find('messages=;') != -1:

        response.delete_cookie('messages')



