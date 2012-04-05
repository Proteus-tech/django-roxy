from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from roxy.views import proxy

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'piquetest.views.home', name='home'),
    # url(r'^piquetest/', include('piquetest.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

#    url(r'^categories/?$', proxy('localhost:8001')),
#    url(r'^static', proxy('localhost:8001')),
#    url(r'^media', proxy('localhost:8001')),
#    url(r'', proxy('blake:8000')),
    url(r'', proxy('localhost:8001')),
)
