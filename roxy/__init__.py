"""
Reverse proxy app
"""
from django.http import HttpRequest
from httplib2 import Http as httplib2_Http

###
# Fix cannot access raw post data if content type is multipart
# the exception raised was "You cannot access body after reading from request's data stream"
###
HttpRequest._orig_load_post_and_files = HttpRequest._load_post_and_files
def _load_post_and_files(self):
    self.raw_post_data
    return self._orig_load_post_and_files()
HttpRequest._load_post_and_files = _load_post_and_files


class Http(httplib2_Http):
    """
    Derive class to override _normalize_headers
    """

    def _normalize_headers(self, headers):
        """
        Do not normalize headers since roxy is just a proxy.
        """
        return headers