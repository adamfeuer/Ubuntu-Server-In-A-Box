import os, sys
import site
 
# put virtualenv on pythonpath
site.addsitedir('/opt/webapps/APP.EXAMPLE.COM/lib/python2.7/site-packages')
site.addsitedir('/opt/webapps/APP.EXAMPLE.COM')
site.addsitedir('/opt/webapps/APP.EXAMPLE.COM/APPNAME')
 
# redirect print statements to apache log
sys.stdout = sys.stderr
 
os.environ['DJANGO_SETTINGS_MODULE'] = 'APPNAME.conf.prod.settings'

import django.core.handlers.wsgi
 
application = django.core.handlers.wsgi.WSGIHandler()

