"""
Reverse proxy app
"""
from django.http import HttpRequest


HttpRequest._orig_load_post_and_files = HttpRequest._load_post_and_files
def _load_post_and_files(self):
    self.raw_post_data
    return self._orig_load_post_and_files()
HttpRequest._load_post_and_files = _load_post_and_files