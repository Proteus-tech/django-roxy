"""
views that handle reverse proxy
"""
from django.http import HttpResponse
from django.conf.global_settings import DEFAULT_CONTENT_TYPE
from httplib2 import Http, urlparse

# django 1.4 rename _hop_headers to _hoppish. so define here, these  Hop-by-hop Headers are defined in rfc2616,
# not to be forwarded by proxies
_hop_headers = {
    'connection':1, 'keep-alive':1, 'proxy-authenticate':1,
    'proxy-authorization':1, 'te':1, 'trailers':1, 'transfer-encoding':1,
    'upgrade':1
}

def proxy(origin_server, prefix=None):
    """
    Builder for the actual Django view. Use this in your urls.py.
    """
    def get_page(request, *args, **kwargs):
        """
        reverse proxy Django view
        """
        path = request.get_full_path().replace(prefix, '', 1) if prefix else request.get_full_path()
        target_url = join_url(path, origin_server, request.is_secure())

        # Construct headers
        headers = {}
        if request.META.has_key('CONTENT_TYPE'):
            headers['Content-Type'] = request.META['CONTENT_TYPE']
        if request.META.has_key('CONTENT_LENGTH'):
            headers['Content-Length'] = request.META['CONTENT_LENGTH']
        for header, value in request.META.items():
            if header.startswith('HTTP_'):
                name = header.replace('HTTP_', '').replace('_', '-').title()
                headers[name] = value

        ########################################################################
        # TODO: Move this to somewhere else, e.g. middleware
        if request.user.is_authenticated():
            headers['X-FOST-User'] = request.user.username
        ########################################################################

        # Send request
        http = Http()
        http.follow_redirects = False
        httplib2_response, content = http.request(
            target_url, request.method,
            body=bytearray(request.raw_post_data),
            headers=headers)

        # Construct Django HttpResponse
        content_type = httplib2_response.get('content-type', DEFAULT_CONTENT_TYPE)
        response = HttpResponse(content, status=httplib2_response.status, content_type=content_type)

        update_response_header(response, httplib2_response)
        update_messages_cookie(request, headers, httplib2_response, response)

        if httplib2_response.status in [301, 302]:
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

def update_response_header(response, headers):
    """
    update response header with given headers

    ignore hop headers to avoid django hop-by-hop assertion error as
    hop-by-hop should not be forwarded by proxy
    """
    ignored_keys = ['status', 'content-location'] + _hop_headers.keys()
    for key, value in headers.items():
        if key not in ignored_keys:
            response[key] = value

def update_messages_cookie(request, headers, httplib2_response, response):
    """
    If the request has messages cookie, and now the response from the backend says that it should be deleted,
    we should delete the cookie
    """
    if request.method == 'GET' and headers.get('Cookie') and headers['Cookie'].find('messages='):
        response_set_cookie = httplib2_response.get('set-cookie','')
        if (response_set_cookie.find('messages=') == -1) or (response_set_cookie.find('messages=;') != -1):
            response.delete_cookie('messages')

