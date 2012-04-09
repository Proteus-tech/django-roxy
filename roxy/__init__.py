"""
Reverse proxy app
"""
from django.http import HttpRequest
from httplib2 import Http as httplib2_Http


HttpRequest._orig_load_post_and_files = HttpRequest._load_post_and_files    # pylint: disable=W0212
def _load_post_and_files(self):
    """
    Fix cannot access raw post data if content type is multipart.
    The exception raised was "You cannot access body after reading from request's data stream".
    """
    # This statement have a side-effect that loads raw post data to _raw_post_data
    # pylint: disable=W0104
    self.raw_post_data
    return self._orig_load_post_and_files()    # pylint: disable=W0212
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