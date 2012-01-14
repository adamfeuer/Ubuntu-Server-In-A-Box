import os, sys
import site
 
# put virtualenv on pythonpath
site.addsitedir('/opt/webapps/app.example.com/lib/python2.7/site-packages')
site.addsitedir('/opt/webapps/app.example.com')
site.addsitedir('/opt/webapps/app.example.com/appname')
 
# redirect print statements to apache log
sys.stdout = sys.stderr
 
os.environ['DJANGO_SETTINGS_MODULE'] = 'appname.conf.prod.settings'

import django.core.handlers.wsgi
 
application = django.core.handlers.wsgi.WSGIHandler()

