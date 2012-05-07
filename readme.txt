=======
INSTALL
=======
>>> pip install https://svn.felspar.com/public/django-roxy/trunk/

=======
USAGE
=======
To see the magic of little roxy, all you need to do is special way to call it in urls.py.  By just map the origin server
url with 'proxy' view from roxy.

>>> proxy("<origin server>")

In urls.py it could be something like this:

::

    from roxy.views import proxy

    origin_one = proxy('http://localhost:8002')
    origin_two = proxy('http://someplace.com')

    urlpatterns = patterns('',
        # Examples:
        url(r'^origin_server_1/', origin_one, name='proxy1'),
        url(r'^origin_server_2/', origin_two , name='proxy2'),
        url(r'^origin_server_3/', proxy('https://www.places.com'), name='proxy3'),
    )

