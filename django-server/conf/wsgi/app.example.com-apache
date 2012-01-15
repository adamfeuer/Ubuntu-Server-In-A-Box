<VirtualHost *:9000>
   ServerAdmin webmaster@localhost
   ServerName APP.EXAMPLE.COM

   # Tell Apache this is a HTTPS request without actually using HTTPS on the localhost
   SetEnvIf X-Forwarded-Protocol "^https$" HTTPS=on

   WSGIDaemonProcess domain-prod display-name=APPNAME-prod-%{GROUP} maximum-requests=10000
   WSGIProcessGroup domain-prod
   WSGIScriptAlias / /opt/webapps/APP.EXAMPLE.COM/apache/django.wsgi-APP.EXAMPLE.COM

   <Directory /opt/webapps/APP.EXAMPLE.COM/apache>
      Order deny,allow
      Allow from all
   </Directory>

   # static files
   Alias /robots.txt /opt/webapps/APP.EXAMPLE.COM/APPNAME/static/robots.txt 
   Alias /favicon.ico /opt/webapps/APP.EXAMPLE.COM/APPNAME/static/favicon.ico
   Alias /media/admin/ /opt/webapps/APP.EXAMPLE.COM/APPNAME/static/admin/
   Alias /media/ /opt/webapps/APP.EXAMPLE.COM/APPNAME/media/

   <Directory /opt/webapps/APP.EXAMPLE.COM/APPNAME/media>
      Order deny,allow
      Allow from all
   </Directory>

   <Directory /opt/webapps/APP.EXAMPLE.COM/APPNAME/static>
      Order deny,allow
      Allow from all
   </Directory>

   ErrorLog /var/log/apache2/APP.EXAMPLE.COM-error.log
   CustomLog /var/log/apache2/APP.EXAMPLE.COM-access.log combined

</VirtualHost>
