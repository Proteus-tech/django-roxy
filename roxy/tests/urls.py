from django.conf.urls.defaults import patterns, url
from roxy.views import proxy


urlpatterns = patterns('',
    url(r'', proxy('localhost:8009')),
)