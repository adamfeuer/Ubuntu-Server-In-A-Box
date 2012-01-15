##
# You should look at the following URL's in order to grasp a solid understanding
# of Nginx configuration files in order to fully unleash the power of Nginx.
# http://wiki.nginx.org/Pitfalls
# http://wiki.nginx.org/QuickStart
# http://wiki.nginx.org/Configuration
#
# Generally, you will want to move this file somewhere, and start with a clean
# file but keep this around for reference. Or just disable in sites-enabled.
#
# Please see /usr/share/doc/nginx-doc/examples/ for more detailed examples.
##

# Apache server
upstream django {
    server         localhost:9000;
}

# Serve static files and redirect any other request to Apache
server {
        listen 80;
        server_name APP.EXAMPLE.COM;

        server_name  APP.EXAMPLE.COM;
        root        /var/www/APP.EXAMPLE.COM/;
        access_log  /var/log/nginx/APP.EXAMPLE.COM.access.log;
        error_log  /var/log/nginx/APP.EXAMPLE.COM.error.log;
        
        # Check if a file exists at /var/www/domain/ for the incoming request.
        # If it doesn't proxy to Apache/Django.
        try_files $uri @django;
        
        # Setup named location for Django requests and handle proxy details
        location @django {
                proxy_pass         http://django;
                proxy_redirect     off;
                proxy_set_header   Host             $host;
                proxy_set_header   X-Real-IP        $remote_addr;
                proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
}

# Serve static files and redirect any other request to Apache
server {
        listen SERVER_IP_ADDRESS:443;
        server_name APP.EXAMPLE.COM;
        ssl on;

        server_name  APP.EXAMPLE.COM;
        root        /var/www/APP.EXAMPLE.COM/;
        access_log  /var/log/nginx/APP.EXAMPLE.COM.access.log;
        error_log  /var/log/nginx/APP.EXAMPLE.COM.error.log;
        
        # Check if a file exists at /var/www/domain/ for the incoming request.
        # If it doesn't proxy to Apache/Django.
        try_files $uri @django;
        
        # Setup named location for Django requests and handle proxy details
        location @django {
                proxy_pass         http://django;
                proxy_redirect     off;
                proxy_set_header   Host             $host;
                proxy_set_header   X-Real-IP        $remote_addr;
                proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
}

# Serve static files and redirect any other request to Apache
server {
        listen 80;
        server_name APP-STAGING.EXAMPLE.COM;

        server_name  APP.EXAMPLE.COM;
        root        /var/www/APP-STAGING.EXAMPLE.COM/;
        access_log  /var/log/nginx/APP-STAGING.EXAMPLE.COM.access.log;
        error_log  /var/log/nginx/APP-STAGING.EXAMPLE.COM.error.log;
        
        # Check if a file exists at /var/www/domain/ for the incoming request.
        # If it doesn't proxy to Apache/Django.
        try_files $uri @django;
        
        # Setup named location for Django requests and handle proxy details
        location @django {
                proxy_pass         http://django;
                proxy_redirect     off;
                proxy_set_header   Host             $host;
                proxy_set_header   X-Real-IP        $remote_addr;
                proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
}

# Serve static files and redirect any other request to Apache
server {
        listen SERVER_IP_ADDRESS:443;
        server_name APP-STAGING.EXAMPLE.COM;
        ssl on;

        server_name  APP.EXAMPLE.COM;
        root        /var/www/APP-STAGING.EXAMPLE.COM/;
        access_log  /var/log/nginx/APP-STAGING.EXAMPLE.COM.access.log;
        error_log  /var/log/nginx/APP-STAGING.EXAMPLE.COM.error.log;
        
        # Check if a file exists at /var/www/domain/ for the incoming request.
        # If it doesn't proxy to Apache/Django.
        try_files $uri @django;
        
        # Setup named location for Django requests and handle proxy details
        location @django {
                proxy_pass         http://django;
                proxy_redirect     off;
                proxy_set_header   Host             $host;
                proxy_set_header   X-Real-IP        $remote_addr;
                proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
}

