"""
views that handle reverse proxy
"""
from django.conf import settings
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

_httplib2_constructor_kwargs = getattr(settings, 'ROXY_HTTPLIB2_CONSTRUCTOR_KWARGS', {})

def proxy(origin_server):
    """
    Builder for the actual Django view. Use this in your urls.py.
    """
    def get_page(request):
        """
        reverse proxy Django view
        """
        request_url = URLObject(request.build_absolute_uri())
        origin_url = URLObject(origin_server)
        # if origin server is not a url then assume it's netloc? to make it compat with previous version
        target_url = request_url.with_netloc(origin_server)
        if origin_url.scheme:
            target_url = request_url.with_netloc(origin_url.netloc).with_scheme(origin_url.scheme)

        # Construct headers
        headers = {}
        for header, value in request.META.items():
            if header.startswith('HTTP_') or header in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                name = header.replace('HTTP_', '').replace('_', '-').title()

                # Not forward empty content-length (esp in get), this causes weird response
                if name.lower() == 'content-length' and value == '':
                    continue

                # An HTTP/1.1 proxy MUST ensure that any request message it forwards does contain an appropriate
                # Host header field that identifies the service being requested by the proxy.
                if name.lower() == 'host':
                    if origin_url.scheme == '':
                        value = origin_server
                    else:
                        value = str(URLObject(origin_server).netloc)

                # Assigning headers' values
                if name.lower() not in _hop_headers.keys():
                    headers[name] = value

        # Send request
        http = Http(**_httplib2_constructor_kwargs)
        http.follow_redirects = False
        if hasattr(request, 'body'):
            request_body = request.body
        else:
            request_body = request.raw_post_data
        httplib2_response, content = http.request(
            target_url, request.method,
            body=bytearray(request_body),
            headers=headers)

        # Construct Django HttpResponse
        content_type = httplib2_response.get('content-type', DEFAULT_CONTENT_TYPE)
        response = HttpResponse(content, status=httplib2_response.status, content_type=content_type)

        update_response_headers(response, httplib2_response)
        update_messages_cookie(request, headers, httplib2_response, response)

        if httplib2_response.status in [301, 302]:
            location_url = URLObject(httplib2_response['location'])
            if origin_url.scheme == '':
                response['location'] = location_url.with_netloc(request.get_host())
            else:
                response['location'] = location_url.with_netloc(request_url.netloc).with_scheme(request_url.scheme)
        return response
    return get_page


def update_response_headers(response, headers):
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

