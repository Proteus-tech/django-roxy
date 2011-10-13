from django.conf import settings
from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from roxy.views import proxy

origin_one = proxy(settings.ORIGIN_SERVER1)
origin_two = proxy(settings.ORIGIN_SERVER2)

urlpatterns = patterns('',
    # Examples:
    url(r'^origin_one/', origin_two, name='proxy1'),
    url(r'^', origin_one, name='proxy2'),
    # url(r'^roxy/', include('roxy.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
