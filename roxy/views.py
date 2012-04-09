"""
views that handle reverse proxy
"""
from django.http import HttpResponse
from django.conf.global_settings import DEFAULT_CONTENT_TYPE
from urlobject import URLObject

from roxy import Http

# django 1.4 rename _hop_headers to _hoppish. so define here, these  Hop-by-hop Headers are defined in rfc2616,
# not to be forwarded by proxies
_hop_headers = {
    'connection':1, 'keep-alive':1, 'proxy-authenticate':1,
    'proxy-authorization':1, 'te':1, 'trailers':1, 'transfer-encoding':1,
    'upgrade':1
}

def proxy(origin_server):
    """
    Builder for the actual Django view. Use this in your urls.py.
    """
    def get_page(request):
        """
        reverse proxy Django view
        """
        request_url = URLObject(request.build_absolute_uri())
        target_url = request_url.with_netloc(origin_server)

        # Construct headers
        headers = {}
        for header, value in request.META.items():
            if header.startswith('HTTP_') or header in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                name = header.replace('HTTP_', '').replace('_', '-').title()
                if name.lower() not in _hop_headers:
                    headers[name] = value

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
            location_url = URLObject(httplib2_response['location'])
            response['location'] = location_url.with_netloc(request.get_host())
        return response
    return get_page


def update_response_header(response, headers):
    """
    update response header with given headers

    ignore hop headers to avoid django hop-by-hop assertion error as
    hop-by-hop should not be forwarded by proxy
    """
    ignored_keys = ['status', 'content-location'] + _hop_headers.keys()
    for key, value in headers.items():
        if key.lower() not in ignored_keys:
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

