"""
Reverse proxy app
"""
from django.http import HttpRequest
import httplib2

###
# Fix cannot access raw post data if content type is multipart
# the exception raised was "You cannot access body after reading from request's data stream"
###
HttpRequest._orig_load_post_and_files = HttpRequest._load_post_and_files
def _load_post_and_files(self):
    self.raw_post_data
    return self._orig_load_post_and_files()
HttpRequest._load_post_and_files = _load_post_and_files

###
# Fix: django cookie message with double quote does not show when request via roxy
# patch httplib2 normalize headers to not interpret '\\\"' as '\\"'
###
httplib2._orig_normalize_headers = httplib2._normalize_headers
def _normalize_headers(headers):
    headers = httplib2._orig_normalize_headers(headers)
    return dict([(key, value.replace('\\\\"', '\\\\\\"')) for (key, value) in headers.iteritems()])
httplib2._normalize_headers = _normalize_headers