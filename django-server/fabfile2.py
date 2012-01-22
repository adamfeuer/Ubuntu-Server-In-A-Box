import os
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.operations import _prefix_commands, _prefix_env_vars

"""
Base configuration
"""
env.project_name = 'surveytool'
env.apache_config_path = '/etc/apache2/sites-available'

env.main_username    = 'user0' # this is the sudo user
env.main_password    = 'password'
env.deploy_username  = 'deploy'
env.deploy_password  = 'password'

env.team_users       = [ 'user1', 'user2' ]
env.team_password    = 'password'

env.appname = 'surveytool'
env.virtual_environments = ['research.liveingreatness.com']
env.git_repo = 'git://github.com/adamfeuer/surveytool.git'
env.local_config_file_path = '~/.surveytoolrc'

env.ssl_organization_name = "Team Team Research"
env.ssl_contact = "postmaster@liveingreatness.com"

env.single_user_mode = False

env.team_groupname   = 'webdevelopers'
env.deploy_username  = 'deploy'

env.team_sudo_cmds = [
    "/usr/sbin/a2ensite",
    "/usr/sbin/a2dissite",
    "/usr/sbin/a2enmod",
    "/usr/sbin/a2dismod",
    "/usr/sbin/service nginx start",
    "/usr/sbin/service nginx stop",
    "/usr/sbin/service nginx restart",
    "/usr/sbin/service apache2 restart",
    "/usr/sbin/service apache2 reload",
    "/usr/sbin/service apache2 start",
    "/usr/sbin/service apache2 stop"
]

env.local_backup_dir  = os.path.abspath('./.bak')
env.local_tar_dir     = os.path.abspath('./.tarballs')
env.local_config_dir  = os.path.abspath('./conf')

env.remote_backup_dir = '/var/dumps/django-server-fabfile'
env.remote_config_dir = '/var/local/django-server-fabfile'

env.server_groupname               = 'www-data'
env.webroot_dir                    = '/var/www'
env.webapps_location               = '/opt/webapps'
env.virtual_environments_location  = '~/.virtualenvs'

# Download URLs and other settings {{{
env.pypi_url = 'http://pypi.python.org/packages/source'
env.pip_vers = 'pip-0.8.2'
env.pip_url  = '%(pypi_url)s/p/pip/%(pip_vers)s.tar.gz' % env
env.pip_md5  = 'df1eca0abe7643d92b5222240bed15f6'

# pseudo inline-function for bash
env.get_cur_timestamp = '$(date +%Y-%m-%d_%H%M%S)'


"""
Environments
"""
def production():
    """
    Work on production environment
    """
    env.settings = 'production'
    env.manage_settings = 'conf.prod.settings'
    env.server_hostname = 'research1'
    env.server_domain = 'liveingreatness.com'
    env.hosts = ['research1.liveingreatness.com']
    env.server_ip_address = '173.230.147.232'
    common_environment_settings()

def staging():
    """
    Work on staging environment
    """
    env.settings = 'staging'
    env.manage_settings = 'conf.staging.settings'
    env.server_hostname = 'research-staging1'
    env.server_domain = 'liveingreatness.com'
    env.hosts = ['research-staging1.liveingreatness.com'] 
    env.server_ip_address = '173.230.147.232'
    common_environment_settings()

def dev():
    """
    Work on dev environment
    """
    env.settings = 'test'
    env.manage_settings = 'conf.dev.settings'
    env.server_hostname = 'test2'
    env.server_domain = 'dev'
    env.hosts = ['test2.dev'] 
    env.server_ip_address = '192.168.0.246'
    common_environment_settings()

def common_environment_settings():
    env.user = env.main_username
    env.hostname = '%(server_hostname)s.%(server_domain)s' % env
    env.site_name = env.hostname
    env.staging_site_name = '%(server_hostname)s-staging.%(server_domain)s' % env
    env.env_path = '/opt/webapps/%(hostname)s' % env
    env.log_path = '/opt/webapps/%(hostname)s/logs' % env
    env.proj_root = '%(env_path)s/%(project_name)s' % env
    env.server_fqdn = env.hostname
    
"""
Branches
"""
def stable():
    """
    Work on stable branch.
    """
    env.branch = 'stable'

def master():
    """
    Work on development branch.
    """
    env.branch = 'master'

def branch(branch_name):
    """
    Work on any specified branch.
    """
    env.branch = branch_name

"""
Virtual Environment Commands - setup
"""
def setup():
    """
    Setup a fresh virtualenv, install everything we need, and fire up the database.
    
    Does NOT perform the functions of deploy().
    """
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    
    setup_directories()
    setup_virtualenv()
    clone_repo()
    checkout_latest()
    destroy_database()
    create_database()
    load_data()
    update_requirements()
    install_apache_conf()

def setup_directories():
    """
    Create directories necessary for deployment.
    """
    sshagent_run('mkdir -p %(path)s' % env)
    sshagent_run('mkdir -p %(env_path)s' % env)
    run ('mkdir -p %(log_path)s;' % env)
    sudo('chgrp -R www-data %(log_path)s; chmod -R g+w %(log_path)s;' % env)
    sshagent_run('ln -s %(log_path)s %(path)s/logs' % env)
    
def setup_virtualenv():
    """
    Setup a fresh virtualenv.
    """
    sshagent_run('virtualenv -p %(python)s --no-site-packages %(env_path)s;' % env)
    sshagent_run('source %(env_path)s/bin/activate; easy_install -U setuptools; easy_install pip;' % env)

def clone_repo():
    """
    Do initial clone of the git repository.
    """
    sshagent_run('git clone git@github.com:adamfeuer/%(project_name)s.git %(proj_root)s' % env)

def checkout_latest():
    """
    Pull the latest code on the specified branch.
    """
    sshagent_run('cd %(proj_root)s; git checkout %(branch)s; git pull origin %(branch)s' % env)

def update_requirements():
    """
    Install the required packages using pip.
    """
    ve_run("pip install -r %(proj_root)s/requirements.pip" % env)

def install_apache_conf():
    """
    Install the apache site config file.
    """
    sudo('cp %(proj_root)s/apache/%(hostname)s %(apache_config_path)s' % env)

"""
Commands - deployment
"""
def deploy():
    """
    Deploy the latest version of the site to the server and restart Apache2.
    
    Does not perform the functions of load_new_data().
    """
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    
    with settings(warn_only=True):
        maintenance_up()

    checkout_latest()
    update_requirements()
    syncdb()
    reset_permissions()

    maintenance_down()
    
def maintenance_up():
    """
    Install the Apache maintenance configuration.
    """
    sudo('cp %(proj_root)s/apache/%(hostname)s-maintenance %(apache_config_path)s/%(hostname)s' % env)
    restart()

def restart_apache(): 
    """
    Restart the Apache2 server.
    """
    sudo('service apache2 restart')
    
def maintenance_down():
    """
    Reinstall the normal site configuration.
    """
    install_apache_conf()
    restart_apache()
    
"""
Commands - rollback
"""
def rollback(commit_id):
    """
    Rolls back to specified git commit hash or tag.
    
    There is NO guarantee we have committed a valid dataset for an arbitrary
    commit hash.
    """
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    
    maintenance_up()
    checkout_latest()
    git_reset(commit_id)
    maintenance_down()
    
def git_reset(commit_id):
    """
    Reset the git repository to an arbitrary commit hash or tag.
    """
    env.commit_id = commit_id
    sshagent_run("cd %(proj_root)s; git reset --hard %(commit_id)s" % env)

"""
Commands - data
"""
def load_new_data():
    """
    Erase the current database and load new data from the SQL dump file.
    """
    require('settings', provided_by=[production, staging])
    
    maintenance_up()
    destroy_database()
    create_database()
    load_data()
    maintenance_down()
    
def create_database():
    """
    Creates the user and database for this project.
    """
    sshagent_run('echo "CREATE USER %(project_name)s WITH PASSWORD \'%(database_password)s\';" | psql postgres' % env)
    sshagent_run('createdb -O %(project_name)s %(project_name)s -T template_postgis' % env)
    
def destroy_database():
    """
    Destroys the user and database for this project.
    
    Will not cause the fab to fail if they do not exist.
    """
    with settings(warn_only=True):
        sshagent_run('dropdb %(project_name)s' % env)
        sshagent_run('dropuser %(project_name)s' % env)
        
def load_data():
    """
    Loads data from the repository into PostgreSQL.
    """
    sshagent_run('psql -q %(project_name)s < %(path)s/repository/data/psql/dump.sql' % env)
    sshagent_run('psql -q %(project_name)s < %(path)s/repository/data/psql/finish_init.sql' % env)
    
"""
Commands - miscellaneous
"""

def version():
    """Show last commit to repo on server"""
    with cd(env.proj_root):
        sshagent_run('git log -1')

def syncdb():
    with cd(env.proj_root):
        ve_run("%(proj_root)s/bin/manage.py syncdb --migrate --settings=%(manage_settings)s" % env)

def reset_permissions():
    sudo("chown -R www-data:www-data %(env_path)s" % env)
    sudo("chown -R www-data:www-data /var/log/apache2")

def echo_host():
    """
    Echo the current host to the command line.
    """
    sshagent_run('echo %(settings)s; echo %(hosts)s' % env)

"""
Deaths, destroyers of worlds
"""
def shiva_the_destroyer():
    """
    Remove all directories, databases, etc. associated with the application.
    """
    with settings(warn_only=True):
        sshagent_run('rm -Rf %(path)s' % env)
        sshagent_run('rm -Rf %(log_path)s' % env)
        sshagent_run('dropdb %(project_name)s' % env)
        sshagent_run('dropuser %(project_name)s' % env)
        sudo('rm %(apache_config_path)s' % env)
        restart_apache()

"""
Commands - operating system setup

Shortcuts - tasks that call the high level generic tasks below

"""

def setup_server(update=True): 
    """
    Bootstrap an entire server from a blank Ubuntu 11.10 Server distro
    """
    setup_server_init(update)
    setup_users()
    setup_web_server()


def setup_server_init(update=True): 
    # install the root user, config and working dirs
    init_system()
    install_master_users()
    aptget_misc_deps()
    if update:
        aptget_software_updates()
    aptget_compiler()
    aptget_common_dev_headers()
    aptget_git()

def setup_web_server(): 
    """
    Installs and configures web servers
    """
    set_fqdn()
    setup_python() # includes virtualenv, django and wsgi
    setup_apache()
    setup_webapps_location()
    setup_ssl_cert()
    setup_nginx()
    #make_virtual_environments()
      # setup databases
    #install_webroot()



def clean_all(): 
    """
    This tries to remove all custom configs, delete 
    all users, and restore original configs from the 
    backups made by this script.
    """
    clean()
    clean_team_users()
    clean_webroot()
    clean_apache()
    clean_nginx()
    clean_ssl()
    clean_virtual_environments()


# GENERIC TASKS
################################################################
# Tasks that call other tasks that actually get work done

# System Init
def init_system(): 
    """
    Initialialize the bare necessities, i.e. root user etc

    Configures your admin user. Uploads the custom
    home directory skeleton for new users. Creates backup
    and config directories.
    """
    regen_tarballs()
    init_root_user();

    with settings(hide('warnings'), warn_only=True, user='root'):
        local('mkdir -p %(local_backup_dir)s' % env)
        local('mkdir -p %(local_tar_dir)s' % env)
        run('mkdir -p %(remote_backup_dir)s' % env)
        run('mkdir -p %(remote_config_dir)s' % env)


def setup_users(): 
    """
    Install basic user accounts
    """
    install_etc_skel()
    install_team_users()
    install_team_sudoers()

# Web Servers
def setup_apache(): 
    """
    Installs and configures Apache HTTPD
    """
    aptget_apache()
    a2enmod_rewrite()
    a2enmod_proxy()
    a2enmod_wsgi()
    install_apache_config()
    setup_apache_logs()
    restart_apache()


def setup_nginx(): 
    """
    Installs and configures nginx
    """
    aptget_nginx()
    install_nginx_config()



# Python
def setup_python(): 
    """
    Installs python, virtualenv and WSGI.

    Also installs the basic django modules system wide using pip. Installs
    virtualenv for the deploy user.
    """

    # install the deps for basic sanity
    install_python_distribute()
    install_python_pip()
    install_python_virtualenv()

    # setup the deploy user with virtualenv
    configure_python_virtualenv()

# REAL TASKS
################################################################
# Stuff that actually does the work

# Core Configuration
# Users
# root
def init_root_user(): 
    """
    Configure a root user account for convenient access, requires root password.
    """
    local('ssh-copy-id root@' + env.hostname)

def clean_root_user(): 
    """
    Try to clean up any of the custom user configurations for root

    Remove the custom vim configuration if it exists. Remove sudoers file.
    Delete various other shell customization files.
    """
    run('rm -rf .vim .vimrc .viminfo .ssh .colors_prompts .bash_prompt')
    run('if [ -e ~/.bashrc.bak ]; then rm -rf ~/.bashrc; mv ~/.bashrc.bak ~/.bashrc; fi')


# users
def install_master_users(): 
    """
    Install deploy and main users
    """
    with settings(user='root'):
       add_custom_user(env.deploy_username, env.deploy_password)
       add_custom_user(env.main_username, env.main_password)
       # same login as root
       clone_root_pubkey(env.deploy_username, '/home/%(deploy_username)s' % env)
       clone_root_pubkey(env.main_username, '/home/%(main_username)s' % env)
       # sudo permissions for main user - we will use this user from now on
       run('adduser %(main_username)s sudo' % env)
       env.sudo_conf = "%(main_username)s ALL = (root) NOPASSWD: ALL" % env
       run('echo "%(sudo_conf)s" >> /tmp/%(main_username)s' % env)
       run('chmod 0440 /tmp/%(main_username)s' % env)
       run('mv /tmp/%(main_username)s /etc/sudoers.d' % env)

def clean_master_users(): 
    """
    Remove the deploy and main user accounts
    """
   
    with settings(hide('warnings'), warn_only=True):
        run('deluser %(deploy_username)s' % env)
        run('rm -rf /home/%(deploy_username)s' % env)
        run('deluser %(main_username)s' % env)
        run('rm -rf /home/%(main_username)s' % env)

# team
def install_team_users(): 
    """
    Setup team user accounts for each member

    If this is a shared workgroup server with multiple user
    accounts, then set up each initial user account with
    proper group and permissions to work on the same files
    """
    sudo('addgroup %(team_groupname)s' % env)
    sudo('adduser %(deploy_username)s %(team_groupname)s' % env)
    sudo('adduser %(deploy_username)s %(server_groupname)s' % env)
    sudo('adduser %(main_username)s %(team_groupname)s' % env)
    sudo('adduser %(main_username)s %(server_groupname)s' % env)
    for name in env.team_users:
        add_custom_user(name, env.team_password)
        with settings(team_user_name=name):
            sudo('adduser %(team_user_name)s %(server_groupname)s' % env)
            sudo('adduser %(team_user_name)s %(team_groupname)s' % env)

def clean_team_users(): 
    """
    Remove any team user accounts
    """
    with settings(hide('warnings'), warn_only=True):
        for name in env.team_users:
            sudo('deluser %s' % name)
            sudo('rm -rf /home/%s' % name)
        sudo('delgroup %(team_groupname)s' % env)
            
# sudoers
def install_team_sudoers(): 
    """
    Give team members some limited webserver related priviliges
    """
    alias_list  = ','.join(env.team_sudo_cmds)
    cmd_alias   = 'Cmnd_Alias WEB_SERVER_CMDS = %s' % alias_list
    sudoer_line = '%(team_groupname)s ALL=(ALL) NOPASSWD: WEB_SERVER_CMDS' % env

    with settings(cmd_alias=cmd_alias, sudoer_line=sudoer_line):
        sudo("echo '%(cmd_alias)s' > /tmp/%(team_groupname)s" % env)
        sudo("echo '%(sudoer_line)s' >> /tmp/%(team_groupname)s" % env)
        sudo("chmod 440 /tmp/%(team_groupname)s" % env)
        sudo("chown root:root /tmp/%(team_groupname)s" % env)
        sudo("mv /tmp/%(team_groupname)s /etc/sudoers.d" % env)

def clean_team_sudoers(): 
    """
    Remove the extra team privileges
    """
    sudo('rm -rf /etc/sudoers.d/%(team_groupname)s' % env)


# home skeleton
def install_etc_skel(): 
    """
    Uploads the new user skeleton directory to the remote_config_dir
    """
    with settings(user = 'root'):
        put('%(local_tar_dir)s/skel.tar.gz' % env, env.remote_config_dir)
    with cd(env.remote_config_dir):
        sudo('tar -zxf skel.tar.gz')

        sudo('rm -rf skel.tar.gz')


def clean_etc_skel(): 
    """
    Removes the user configuration skeleton dir

    Removes the skeleton from the config directory. Maybe don't need
    this since we've got a clean config task already?
    """
    sudo('rm -rf %(remote_config_dir)s/skel' % env)


# Servers 
def backup_webroot(): 
    """
    Backs up the webroot if it exists.

    Title should be self explanatory, this backs up the main server
    webroot directory if it exists.
    """
    env.host_string = root_host

    with settings(hide('warnings'), warn_only=True):
        if len(webroot_dir) and run('[ -e '+webroot_dir+' ]').succeeded:
            with cd(webroot_dir):
                run('tar -czf '+remote_backup_dir+'/webroot.tar.gz ./')

def restore_webroot(): 
    """
    Restore original webroot from backup if the backup exists
    """
    env.host_string = root_host

    with settings(hide('warnings'), warn_only=True):
        if run('[ -e '+remote_backup_dir+'/webroot.tar.gz ]').succeeded:
            run('rm -rf '+webroot_dir)
            run('mkdir -p '+webroot_dir)
            run('mv '+remote_backup_dir+'/webroot.tar.gz '+webroot_dir)
            with cd(webroot_dir):
                run('tar -zxf webroot.tar.gz')
                run('rm -rf webroot.tar.gz')

def install_webroot(): 
    """
    Create initial webroot directory layout for Apache and Django

    The currently installed folders are

    * ``webroot/apache``
    """
    env.host_string = root_host

    backup_webroot()
    run('if [ -e "'+webroot_dir+'" ]; then rm -rf '+webroot_dir+'; fi')
    run('mkdir -p '+webroot_dir+'/apache')

    # allow team and web server to edit files in webroot
    configure_open_share(deploy_username, server_groupname, webroot_dir)


def backup_apache_config(): 
    """
    Backs up the apache config to the backup directory
    """
    with settings(hide('warnings'), warn_only=True):
        if sudo ('[ ! -e %(remote_backup_dir)s/apache2.tar.gz ]' % env).succeeded:
            with cd('/etc'):
                sudo('tar -czf %(remote_backup_dir)s/apache2.tar.gz apache2' % env)

def restore_apache_config(): 
    """
    Restore original apache config from backup if the backup exists
    """
    with settings(hide('warnings'), warn_only=True):
        if sudo('[ -e %(remote_backup_dir)s/apache2.tar.gz ]' % env).succeeded:
            # remove custom apache config
            sudo('rm -rf /etc/apache2')
            sudo('mv %(remote_backup_dir)s/apache2.tar.gz /etc' % env)
            with cd('/etc'):
                sudo('tar -zxf apache2.tar.gz')
                sudo('rm -rf apache2.tar.gz')

def install_apache_config(): 
    """
    Setup Apache config files
    """
    backup_apache_config()
    with settings(user='root'):
        put(local_path="conf/wsgi/apache/ports.conf", remote_path="/etc/apache2")
    # re-chown the webroot since we uploaded localhost as root
    configure_open_share(env.deploy_username, env.server_groupname, env.webroot_dir)
    # allow team and or admins to add and edit vhosts
    configure_restricted_share('root', env.team_groupname, '/etc/apache2/sites-available')
    sudo("echo 'ServerName %(hostname)s' > /etc/apache2/conf.d/fqdn" % env)

def backup_nginx_config(): 
    """
    Backs up the nginx configuration dir into the backup directory
    """
    if sudo('[ ! -e %(remote_backup_dir)s/nginx.tar.gz ]' % env).succeeded:
        with cd('/etc'):
            sudo('tar -czf %(remote_backup_dir)s/nginx.tar.gz nginx' % env)

def restore_nginx_config(): 
    """
    Restore original nginx config from backup if the backup exists
    """
    with settings(hide('warnings'), warn_only=True):
        if sudo('[ -e %(remote_backup_dir)s/nginx.tar.gz ]' % env).succeeded:
            # remove custom apache config
            sudo('rm -rf /etc/nginx')
            sudo('mv %(remote_backup_dir)s/nginx.tar.gz /etc' % env)
            with cd('/etc'):
                sudo('tar -zxf nginx.tar.gz')
                sudo('rm -rf nginx.tar.gz')

def install_nginx_config(): 
    """
    Install nginx conf that will proxy app and app-staging to
    Apache running on port 9000

    """
    backup_nginx_config()
    site_avail_file = '/etc/nginx/sites-available/%s' % env.site_name
    with settings(user='root'):
        with cd('/etc/nginx'):
            put(local_path = 'conf/wsgi/nginx/nginx.conf', remote_path='/etc/nginx/nginx.conf')
            put(local_path='conf/wsgi/nginx/app.example.com', remote_path=site_avail_file)
    sudo('ln -s /etc/nginx/sites-available/%(site_name)s /etc/nginx/sites-enabled/%(site_name)s' % env)
    replace_in_file(site_avail_file, 'APP.EXAMPLE.COM', env.site_name)
    replace_in_file(site_avail_file, 'APP-STAGING.EXAMPLE.COM', env.staging_site_name)
    replace_in_file(site_avail_file, 'SERVER_IP_ADDRESS', env.server_ip_address)
    
    configure_restricted_share('root', env.team_groupname, '/etc/nginx/sites-available')
    sudo('service nginx restart')

def upload_website_apache_localhost(): 
    """
    Uploads the actual publicly accessible files for the default localhost

    Installs a set of skeleton files for the default vhost, aka
    localhost, for apache. Right now this is basically just ``info.php``
    which has a call to ``phpinfo()`` and a default index file
    so you can see that the server is working.
    """
    env.host_string = host

    run('mkdir -p '+webroot_dir+'/apache/localhost')
    put(local_tar_dir+'/apache/localhost/public.tar.gz', webroot_dir+'/apache/localhost')
    with cd(webroot_dir+'/apache/localhost'):
        run('tar -zxf public.tar.gz')
        run('rm -rf public.tar.gz')

# apt-get
def aptget_software_updates(): 
    """
    Download and install the latest security patches for Ubuntu.
    """
    sudo('apt-get update')
    sudo('yes | apt-get upgrade')


def aptget_compiler(): 
    """
    We'll need a compiler and basic build tools if we want
    to compile software.
    """
    sudo('yes | apt-get install build-essential gcc g++ make')


def aptget_common_dev_headers(): 
    """
    Install database, image and xml dev headers for compiling modules

    """
    sudo('yes | apt-get install libmysqlclient-dev libpq-dev libmagickwand-dev libxml2-dev libxslt1-dev python-dev libcurl4-openssl-dev')


def aptget_databases(): 
    """
    Install the common databases: MySQL, Postgres and SQLite
    """
    sudo('yes | apt-get install mysql-server mysql-client postgresql sqlite sqlite3')


def aptget_apache(): 
    """
    Install Apache along with wsgi
    """
    sudo('yes | apt-get install apache2 apache2-dev libapache2-mod-wsgi')

def aptget_git():
   """
   Install git
   """
   sudo('yes | apt-get install git')
    

def a2enmod_rewrite(): 
    """
    Enable the Rewrite module
    """
    sudo('a2enmod rewrite')
    restart_apache()


def a2enmod_proxy(): 
    """
    Enable the Proxy and Proxy HTTP modules
    """
    sudo('a2enmod proxy')
    sudo('a2enmod proxy_http')
    restart_apache()


def a2enmod_wsgi(): 
    """
    Install and enable the apache WSGI module for running python apps
    """
    sudo('a2enmod wsgi')
    restart_apache()


def aptget_nginx(): 
    """
    Update to the lates nginx repo and install nginx
    """
    sudo('yes | apt-get install nginx-common nginx-extras')

def aptget_mail_server(): 
    """
    Install the commonly desired tools for setting up a mail server
    """
    sudo('yes | apt-get install dovecot-postfix postfix-doc postfix-mysql')


def aptget_vim(): 
    """
    Install the latest vim
    plus a couple common utilities that my vim config uses:

    * ``ctags`` exuberrant ctags
    * ``par`` the paragraph formatter
    """
    sudo('yes | apt-get install vim ctags par')


def aptget_misc_deps(): 
    """
    Updates package list and installs: locate, tmux, add-apt-repository

    Some   various  handy   things   I   alwas  want,   plus
    ``add-apt-repository`` is currently  a dependency of the
    ubuntu packaging tasks, so do  not remove that or remove
    calls to this function

    Also installs ``ncurses-term`` for the extra terminfo entries
    like gnome-256color so that we can still SSH from gnome-terminal
    with a proper terminfo value and things don't get wonky
    """
    sudo('apt-get update')
    sudo('yes | apt-get install python-software-properties mlocate tmux ncurses-term curl')

# python
def install_python_distribute(): 
    """
    Installs the "distribute" python package, a setuptools clone

    Install setuptools so we can build pip and other packages.
    I prefer using distribute.
    """
    sudo('curl -O http://python-distribute.org/distribute_setup.py')
    sudo('python distribute_setup.py')


def install_python_pip(): 
    """
    Download and install a recent version of the pip utility
    """
    the_file = env.pip_vers + '.tar.gz'
    sudo('wget %s' % env.pip_url)

    with settings(warn_only=True):
        md5_compute = sudo('md5sum %s' % the_file)
        md5_string  = '%s  %s' % (env.pip_md5, the_file)
        result      = sudo('[ "'+md5_compute+'" = "'+md5_string+'" ]')
    if result.failed and not confirm("Bad pip tarball. `Continue anyway?"):
        abort("Aborting at user request.")

    sudo('tar -zxf ' + the_file)
    with cd(env.pip_vers):
        sudo('python setup.py install')


def install_python_virtualenv(): 
    sudo('pip install virtualenv virtualenvwrapper')

def setup_webapps_location(): 
    sudo('mkdir -p %(webapps_location)s' % env)
    sudo('chown -R %(server_groupname)s:%(server_groupname)s %(webapps_location)s' % env)

def configure_python_virtualenv(): 
    """
    Add virtualenv capabilites to this user.
    """
    run("mkdir -p %(virtual_environments_location)s" % env)
    run("echo >> ~/.bashrc")
    run("echo 'export WORKON_HOME=%(virtual_environments_location)s' >> ~/.bashrc" % env)
    run("echo 'export VIRTUALENV_USE_DISTRIBUTE=1' >> ~/.bashrc")
    run("echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bashrc")

# SUPPORT TASKS
################################################################
# Modular and repeatable helpers that other tasks can use

def regen_tarball(srcdir, source): 
    """
    Generate a tarball of a config dir

    This is a helper function for regenerating all the config tarballs for upload

    Files end up in

    * ``conf/tarballs``
    """

    target_dir = os.path.join(env.local_tar_dir, srcdir)
    target     = os.path.join(target_dir, source+'.tar.gz')
    srcdir     = os.path.join(env.local_config_dir, srcdir)

    local('if [ -e '+target+' ]; then mv '+target+' '+target+'.tar.gz.bak.'+env.get_cur_timestamp+'; fi')
    local('mkdir -p '+target_dir)

    with settings(hide('warnings'), warn_only=True):
        if local('[ -e "'+srcdir+'" ]').succeeded:
            with lcd(srcdir):
                local('tar -czf '+target+' '+source+'')

def regen_tarballs(): 
    """
    Tarball the config tarballs for ease of upload

    This script uploads a number of tarballs that are used to configure
    the server with the settings you want. This method freshly regenerates
    those tarballs from scratch and keeps timestamped backups of any
    tarballs that might already exist. The current tarballs are

    * ``conf/skel``
    """
    local('mkdir -p %(local_backup_dir)s' % env)
    local('mkdir -p %(local_tar_dir)s' % env)

    configs = [
        {'source': 'skel',            'srcdir': ''},
    ]

    import os
    for config in configs:
        regen_tarball(source=config['source'], srcdir=config['srcdir'])


def docs(): 
    """
    Regenerate the sphinx based documentation for this fabfile
    """
    with lcd('../sphinx-docs'):
        local('rm -rf ../docs/ && yes "" | sphinx-build -b html . ../docs')

# Tests 
def test_local(): 
    """
    Test echo on localhost. Reports the git user settings and the environment $SHELL variable.
    """
    git_username = local('git config --global --get user.name', capture=True)
    local("echo 'Git User: "+git_username+"'")
    local('echo "Current Shell: $SHELL"')


def test_remote(user='root'): 
    """
    Test a remote host, takes user account login name as a single argument
    """
    env.host_string = user+'@'+server_fqdn

    git_username    = run('git config --global --get user.name')
    run("echo 'Git User: "+git_username+"'")
    run('echo "Current Shell: $SHELL"')



# Cleaning
def clean(keys=False): 
    """
    This is more like make clean. This deletes all the custom config files generated by regen_configs()
    """

    print '''
    fab clean
        WARNING, this task will delete your 
        generated configs and backup files

    '''
    if not confirm('Are you sure you want to do this?'):
        return

    # local cache
    local('rm -rf '+local_tar_dir)
    local('rm -rf '+local_backup_dir)

    # compiled python files
    local('find ../ -type f -iname "*.pyc" -exec rm -rf "{}" +')

    if keys:
        local('rm -rf '+local_config_dir+'/keys/shell/*')


def clean_remote_config_dir(): 
    """
    Remove the main configuration uploads dir
    """
    env.host_string = root_host

    run('if [ -e '+remote_config_dir+' ]; then rm -rf '+remote_config_dir+'; fi')

def clean_remote_backup_dir(): 
    """
    Remove the main remote backup dir
    """
    env.host_string = root_host

    run('if [ -e '+remote_backup_dir+' ]; then rm -rf '+remote_backup_dir+'; fi')


# User and Permissions Helpers
def configure_restricted_share(user, group, directory): 
    """
    Set group ownership of a directory
    """
    sudo('chown '+user+'.'+group+' '+directory)
    sudo('chmod g+w '+directory)


def configure_open_share(user, group, directory): 
    """
    Recursively set and enforce group ownership of a directory
    """
    sudo('chown -R '+user+'.'+group+' '+directory)
    sudo('chmod -R g+w '+directory)
    sudo('find '+directory+' -type d -exec chmod g+s "{}" +')


def clone_root_pubkey(user, home): 
    """
    Copy pubkey from root to avoid password prompt

    Copy our current key from the root user to another user to
    avoid the need for a password when logging in.
    """
    run('mkdir -p '+home+'/.ssh')
    run('cp /root/.ssh/authorized_keys '+home+'/.ssh/authorized_keys')
    run('chown -R '+user+'.'+user+' '+home+'/.ssh')

def add_custom_user(user, password, fancy=True): 
    """
    Add a user with a preconfigured home directory

    Add a user account with a skeleton directory structure
    from the config in the local skel dir
    """
    with settings(custom_user=user, custom_password=password):
        sudo('useradd --skel %(remote_config_dir)s/skel --create-home --home-dir /home/%(custom_user)s --shell /bin/bash %(custom_user)s' % env)
        sudo('yes "%(custom_password)s" | passwd %(custom_user)s' % env)

def backup_user_home(user): 
    """
    Backup a users home dir to the backup dir

    If no backup yet exists for the given user's home directory
    then create a backup for that user in remote_backup_dir/home_user.tar.gz
    """
    env.host_string = root_host

    bak_file = remote_backup_dir+'/home_'+user+'.tar.gz'
    with settings(hide('warnings'), warn_only=True):
        if run('[ ! -e '+bak_file+' ]').succeeded:
            if run('[ -e /home/'+user+' ]').succeeded:
                with cd('/home'):
                    run('tar -czf '+bak_file+' '+user)


def restore_user_home(user): 
    """
    Restore a user's original home directory from the backup dir

    If a backup exists for the user's home directory, delete the
    current home directory and restore from the backup.
    """
    env.host_string = root_host

    bak_file = remote_backup_dir+'/home_'+user+'.tar.gz'
    with settings(hide('warnings'), warn_only=True):
        if run('[ -e '+bak_file+' ]').succeeded:
            if run('[ -e /home/'+user+' ]').succeeded:
                with cd('/home'):
                    run('rm -rf '+user)
                    run('tar -xzf '+bak_file)


def reskel_existing_user(user, home=''): 
    """
    Add custom user configuration to an existing user

    Backup the user's home directory and install
    fresh files from the custom skeleton instead
    """
    env.host_string = root_host

    if not len(home):
        home = '/home/'+user

    backup_user_home(user)

    # may want to add an option to override this
    # so hydration is non destructive
    run('rm -rf '+home)
    run('mkdir '+home)

    filenames = local('find skel -type f', capture=True).split('\n')
    for f in filenames:
        put(f, home)

    run('chown -R '+user+'.'+user+' '+home)



# nginx/apache/django setup
            
def set_fqdn():
    """
    Set server's fully-qualified domain name
    """
    replace_in_file("/etc/hosts", "ubuntu", "%(server_hostname)s %(hostname)s" % env)
    sudo("echo %(server_hostname)s > /etc/hostname" % env)
    sudo("hostname %(server_hostname)s" % env)

def setup_ssl_cert():
    sudo("apt-get install openssl")
    with cd(env.webapps_location):
        sudo("mkdir ssl")
        with settings(user='root'):
            put(local_path="conf/ssl/sslcert.conf", remote_path="%(webapps_location)s/ssl" % env)
        replace_in_file('ssl/sslcert.conf', 'Example, Inc.', env.ssl_organization_name)
        replace_in_file('ssl/sslcert.conf', 'server.example.com', env.hostname)
        replace_in_file('ssl/sslcert.conf', 'postmaster@example.com', env.ssl_contact)
        sudo("openssl req -new -x509 -days 365 -nodes -config ssl/sslcert.conf -out ssl/nginx.pem -keyout ssl/nginx.key")
        sudo("chmod 600 ssl/*")

def clean_ssl():
    env.host_string = root_host
    run("rm -rf %s/ssl" % webapps_location )

def replace_in_file(remote_file_path, target, replacement):
    sudo("sed -i 's/%s/%s/g' %s" % (target, replacement, remote_file_path))
    
def make_virtual_environments(): 
    env.host_string = root_host
    for virtual_environment_name in virtual_environments:
        env_path = make_virtual_environment(virtual_environment_name)
        with cd(env_path):
            run('mkdir logs')
            run('mkdir apache')
        install_wsgi_config(virtual_environment_name, env_path)
        source_path = clone_repo(env_path)
        install_virtual_env_requirements(env_path, source_path)
        install_django_app_config_file(virtual_environment_name)
        make_keyczar_keys(virtual_environment_name, env_path)
        setup_apache_wsgi(virtual_environment_name)
    set_user_and_group(server_groupname, server_groupname, webapps_location)

def install_wsgi_config(virtual_environment_name, env_path): 
    env.host_string = root_host
    wsgi_config_path = env_path + "/apache/django.wsgi-%s" % virtual_environment_name
    put(local_path="conf/wsgi/django.wsgi", remote_path=wsgi_config_path)
    replace_in_file(wsgi_config_path, "APP.EXAMPLE.COM", virtual_environment_name)
    replace_in_file(wsgi_config_path, "APPNAME", appname)

def clean_wsgi_config(env_path):
    env.host_string = root_host
    run ("rm -rf %s/apache" % env_path)
    
def set_user_and_group(user, group, path):
    sudo("chown -R %s:%s %s" % (user, group, path))
    sudo("chmod -R ug+rw %s" % path)
        
def make_virtual_environment(virtual_env_base_name):
    virtual_env_path = webapps_location + '/' + virtual_env_base_name
    sudo("virtualenv " + virtual_env_path)
    return virtual_env_path

def clean_virtual_environments():
    env.host_string = root_host
    for environment in virtual_environments:
        clean_virtual_environment(environment)

def clean_virtual_environment(virtual_env_base_name):
    virtual_env_path = webapps_location + '/' + virtual_env_base_name
    sudo("rm -rf " + virtual_env_path)

def clone_repo(virtual_env_path):
    env.host_string = root_host
    source_path = virtual_env_path + '/' + appname
    run("git clone " + git_repo + ' ' + source_path)
    return source_path
    
def install_virtual_env_requirements(virtual_env_path, source_path):
    env.host_string = root_host
    requirements_file_path = source_path + '/' + "requirements.pip"
    run("source  " + virtual_env_path + "/bin/activate; pip install -r " + requirements_file_path)

def setup_apache_wsgi(virtual_environment_name):
    env.host_string = root_host
    put(local_path="conf/wsgi/app.example.com-apache", remote_path="/etc/apache2/sites-available/%s" % virtual_environment_name)
    apache_site_file = '/etc/apache2/sites-available/%s' % virtual_environment_name
    replace_in_file(apache_site_file, 'APP.EXAMPLE.COM', virtual_environment_name)
    replace_in_file(apache_site_file, 'APPNAME', appname)
    run("a2ensite %s" % virtual_environment_name)
    run("service apache2 reload")

def clean_apache_wsgi():
    env.host_string = root_host
    for name in virtual_environments:
        with cd("/etc/apache2/sites-available"):
            run("a2dissite %s" % name)
            run("rm %s" % name)

def install_django_app_config_file(virtual_environment_name):
    env.host_string = root_host
    config_file_name = appname + '.config'
    config_path = webapps_location+'/'+virtual_environment_name+'/'+config_file_name
    put(local_path=local_config_file_path, remote_path=config_path)
    set_user_and_group(server_groupname, server_groupname, config_path)

def clean_django_app_config_file(virtual_environment_name):
    env.host_string = root_host
    config_file_name = appname + '.config'
    config_path = webapps_location+'/'+virtual_environment_name+'/'+config_file_name
    run('rm -f '+ config_path)

def make_keyczar_keys(virtual_environment_name,env_path):
    env.host_string = root_host 
    app_path = env_path+'/'+appname
    activate_path = env_path+'/bin/activate'
    keyczart_path = app_path+'/bin/keyczart'
    keys_path = app_path+'/keys'
    run('source ' + activate_path + ' && ' + keyczart_path + ' ' + keys_path)
    
def clean_keyczar_keys(virtual_environment_name):
    env.host_string = root_host 
    run('rm -rf '+webapps_location+'/'+virtual_environment_name+'/'+appname+'/keys')

def setup_apache_logs():
    set_user_and_group(env.server_groupname, env.server_groupname, '/var/log/apache2')

"""
Utility methods
"""
def host_type():
    sshagent_run('uname -s')

def ve_run(cmd):
    """
    Helper function.
    Runs a command using the virtualenv environment
    """
    require('env_path')
    return sshagent_run('source %s/bin/activate; %s' % (env.env_path, cmd))

def sshagent_run(cmd):
    """
    Helper function.
    Runs a command with SSH agent forwarding enabled.

    Note:: Fabric (and paramiko) can't forward your SSH agent.
    This helper uses your system's ssh to do so.
    """
    # Handle context manager modifications
    wrapped_cmd = _prefix_commands(_prefix_env_vars(cmd), 'remote')
    try:
        host, port = env.host_string.split(':')
        return local(
            "ssh -p %s -A %s@%s '%s'" % (port, env.user, host, wrapped_cmd)
        )
    except ValueError:
        return local(
            "ssh -A %s@%s '%s'" % (env.user, env.host_string, wrapped_cmd)
        )
