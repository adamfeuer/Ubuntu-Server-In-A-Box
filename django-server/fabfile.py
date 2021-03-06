import os
from fabric.api import *
from fabric.contrib.console import confirm

print "Welcome to Ubuntu 11.10 - Server In A Box"
print "========================================="

from settings import *

# Download URLs and other settings {{{
pypi_url = 'http://pypi.python.org/packages/source'
pip_vers = 'pip-0.8.2'
pip_url  = pypi_url+'/p/pip/'+pip_vers+'.tar.gz'
pip_md5  = 'df1eca0abe7643d92b5222240bed15f6'

root_host      =  'root@' + server_hostname
main_host      =  main_username+'@'+server_hostname
deploy_host    =  deploy_username + '@'+server_hostname

# pseudo inline-function for bash
get_cur_timestamp = '$(date +%Y-%m-%d_%H%M%S)'



# MAIN TASKS
################################################################
# Shortcuts - tasks that call the high level generic tasks below

def setup(update=True): 
    """
    Bootstrap an entire server from a blank Ubuntu 11.10 Server distro
    """
    setup_init(update)
    setup_users()
    setup_server()


def setup_init(update=True): 
    # Preparation
    # ---------------------------------------------------
    # install the root user, config and working dirs
    init_system()

    # this is basically a dependency actually
    # because it has add-apt-repository
    aptget_misc_deps()

    # Install security updates
    if update:
        aptget_software_updates()

    aptget_compiler()
    aptget_common_dev_headers()
    aptget_git()


def setup_server(): 
    """
    Installs and configures web servers
    """
    set_fqdn()
    setup_python() # includes virtualenv, django and wsgi
    setup_apache()
    setup_nginx()
    setup_webapps_location()
    setup_ssl_cert()
    make_virtual_environments()
    install_webroot()


def clean_all(): 
    """
    Sort of like make clean but more like uninstall.

    This tries to remove all custom configs, delete 
    all users, and restore original configs from the 
    backups made by this script.
    """
    clean()
    clean_users()
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
    env.host_string = root_host

    regen_tarballs()

    init_root_user();

    with settings(hide('warnings'), warn_only=True):
        local('mkdir -p '+local_backup_dir)
        local('mkdir -p '+local_tar_dir)
        run('mkdir -p '+remote_backup_dir)
        run('mkdir -p '+remote_config_dir)


def setup_users(): 
    """
    Install basic user accounts
    """
    install_etc_skel()
    install_master_users()
    install_team_users()
    install_team_sudoers()



# Web Servers
def setup_apache(): 
    """
    Installs and configures Apache HTTPD
    """
    aptget_lamp()
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
def setup_python(target_host=deploy_host): 
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
    configure_python_virtualenv(target_host)






# REAL TASKS
################################################################
# Stuff that actually does the work

# Core Configuration
# Users {{{
# root
def init_root_user(): 
    """
    Configure a root user account for convenient access, requires root password.

    Installs your SSH key for the root user. Uploads the custom
    home directory skeleton for new users. Creates backup
    and config directories.
    """
    env.host_string = root_host

    local('ssh-copy-id ' + root_host)

    # these both use root by default
    add_prompt_to_user()
    select_prompt()


def clean_root_user(): 
    """
    Try to clean up any of the custom user configurations for root

    Remove the custom vim configuration if it exists. Remove sudoers file.
    Delete various other shell customization files.
    """
    env.host_string = root_host

    run('rm -rf .vim .vimrc .viminfo .ssh .colors_prompts .bash_prompt')
    run('if [ -e ~/.bashrc.bak ]; then rm -rf ~/.bashrc; mv ~/.bashrc.bak ~/.bashrc; fi')



# users
def install_master_users(): 
    """
    Install deploy and main users depending on ``single_user_mode``
    """
    env.host_string = root_host

    if single_user_mode:
        add_custom_user(deploy_username, deploy_password)

        # same login as root
        clone_root_pubkey(deploy_username, '/home/'+deploy_username)

        # root permissions
        run('adduser '+deploy_username+' sudo')

    else:
        add_custom_user(deploy_username, deploy_password)
        add_custom_user(main_username, main_password)

        # same login as root
        clone_root_pubkey(deploy_username, '/home/'+deploy_username)
        clone_root_pubkey(main_username, '/home/'+main_username)

        # root permissions
        run('adduser '+main_username+' sudo')


def clean_master_users(): 
    """
    Remove the deploy and main user accounts
    """
    env.host_string = root_host

    with settings(hide('warnings'), warn_only=True):
        run('deluser '+deploy_username)
        run('rm -rf /home/'+deploy_username)

        if not single_user_mode:
            run('deluser '+main_username)
            run('rm -rf /home/'+main_username)



# team
def install_team_users(): 
    """
    Setup team user accounts for each member

    If this is a shared workgroup server with multiple user
    accounts, then set up each initial user account with
    proper group and permissions to work on the same files
    """
    env.host_string = root_host

    run('addgroup '+team_groupname)

    run('adduser '+deploy_username+' '+team_groupname)
    run('adduser '+deploy_username+' '+server_groupname)
    if single_user_mode:
        run('adduser '+server_groupname+' '+team_groupname)
    else:
        run('adduser '+main_username+' '+team_groupname)
        run('adduser '+main_username+' '+server_groupname)

    for name in team_users:
        add_custom_user(name, team_password)
        run('adduser '+name+' '+server_groupname)
        run('adduser '+name+' '+team_groupname)


def clean_team_users(): 
    """
    Remove any team user accounts
    """
    env.host_string = root_host

    with settings(hide('warnings'), warn_only=True):
        run('deluser '+deploy_username)
        run('deluser '+main_username)
        run('rm -rf /home/'+deploy_username)
        run('rm -rf /home/'+main_username)

        for name in team_users:
            run('deluser '+name)
            run('rm -rf /home/'+name)



# sudoers
def install_team_sudoers(): 
    """
    Give team members some limited webserver related priviliges

    Install our own custom sudoers config for the team to
    allow team members to stop and start the web server.
    """
    env.host_string = root_host

    alias_list  = ','.join(team_sudo_cmds)
    cmd_alias   = 'Cmnd_Alias WEB_SERVER_CMDS = '+alias_list
    sudoer_line = '%'+team_groupname+' ALL=(ALL) NOPASSWD: WEB_SERVER_CMDS'

    run("echo '"+cmd_alias+"' > /etc/sudoers.d/"+team_groupname)
    run("echo '"+sudoer_line+"' >> /etc/sudoers.d/"+team_groupname)
    run("chmod 440 /etc/sudoers.d/"+team_groupname)


def clean_team_sudoers(): 
    """
    Remove the extra team privileges
    """
    env.host_string = root_host

    run('if [ -e /etc/sudoers.d/'+team_groupname+' ]; then rm -rf /etc/sudoers.d/'+team_groupname+'; fi')


# home skeleton
def install_etc_skel(): 
    """
    Uploads the new user skeleton directory to the remote_config_dir
    """
    env.host_string = root_host

    put(local_tar_dir+'/skel.tar.gz', remote_config_dir)
    with cd(remote_config_dir):
        run('tar -zxf skel.tar.gz')
        run('rm -rf skel.tar.gz')


def clean_etc_skel(): 
    """
    Removes the user configuration skeleton dir

    Removes the skeleton from the config directory. Maybe don't need
    this since we've got a clean config task already?
    """
    env.host_string = root_host

    run('rm -rf '+remote_config_dir+'/skel')




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
    env.host_string = root_host
    with settings(hide('warnings'), warn_only=True):
        if run('[ ! -e '+remote_backup_dir+'/apache2.tar.gz ]').succeeded:
            with cd('/etc'):
                run('tar -czf '+remote_backup_dir+'/apache2.tar.gz apache2')

def restore_apache_config(): 
    """
    Restore original apache config from backup if the backup exists
    """
    env.host_string = root_host

    with settings(hide('warnings'), warn_only=True):
        if run('[ -e '+remote_backup_dir+'/apache2.tar.gz ]').succeeded:
            # remove custom apache config
            run('rm -rf /etc/apache2')
            run('mv '+remote_backup_dir+'/apache2.tar.gz /etc')
            with cd('/etc'):
                run('tar -zxf apache2.tar.gz')
                run('rm -rf apache2.tar.gz')

def install_apache_config(): 
    """
    Setup Apache config files
    """
    env.host_string = root_host
    backup_apache_config()
    put(local_path="conf/wsgi/ports.conf", remote_path="/etc/apache2")
    # re-chown the webroot since we uploaded localhost as root
    configure_open_share(deploy_username, server_groupname, webroot_dir)
    # allow team and or admins to add and edit vhosts
    if single_user_mode:
        configure_open_share(deploy_username, team_groupname, '/etc/apache2/sites-available')
    else:
        configure_restricted_share('root', team_groupname, '/etc/apache2/sites-available')



def restart_apache():
    env.host_string = root_host
    run('service apache2 restart')

        
def backup_nginx_config(): 
    """
    Backs up the nginx configuration dir into the backup directory
    """
    env.host_string = root_host

    if run('[ ! -e '+remote_backup_dir+'/nginx.tar.gz ]').succeeded:
        with cd('/etc'):
            run('tar -czf '+remote_backup_dir+'/nginx.tar.gz nginx')

def restore_nginx_config(): 
    """
    Restore original nginx config from backup if the backup exists
    """
    env.host_string = root_host

    with settings(hide('warnings'), warn_only=True):
        if run('[ -e '+remote_backup_dir+'/nginx.tar.gz ]').succeeded:
            # remove custom apache config
            run('rm -rf /etc/nginx')
            run('mv '+remote_backup_dir+'/nginx.tar.gz /etc')
            with cd('/etc'):
                run('tar -zxf nginx.tar.gz')
                run('rm -rf nginx.tar.gz')

def install_nginx_config(): 
    """
    Install nginx conf that will proxy app and app-staging to
    Apache running on port 9000

    """
    env.host_string = root_host
    backup_nginx_config()
    site_avail_file = '/etc/nginx/sites-available/'+site_name
    with cd('/etc/nginx'):
        put(local_path = 'conf/wsgi/nginx/nginx.conf', remote_path='/etc/nginx/nginx.conf')
        put(local_path='conf/wsgi/nginx/app.example.com', remote_path=site_avail_file)
    run('ln -s /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s' % (site_name, site_name))
    replace_in_file(site_avail_file, 'APP.EXAMPLE.COM', site_name)
    replace_in_file(site_avail_file, 'APP-STAGING.EXAMPLE.COM', staging_site_name)
    replace_in_file(site_avail_file, 'SERVER_IP_ADDRESS', server_ip_address)
    
    if single_user_mode:
        configure_open_share(deploy_username, team_groupname, '/etc/nginx/sites-available')
    else:
        configure_restricted_share('root', team_groupname, '/etc/nginx/sites-available')
    run('service nginx restart')

def upload_website_apache_localhost(host=root_host): 
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
    env.host_string = root_host
    run('apt-get update')
    run('yes | apt-get upgrade')


def aptget_compiler(): 
    """
    We'll need a compiler and basic build tools if we want
    to compile software.
    """
    env.host_string = root_host
    run('yes | apt-get install build-essential gcc g++ make')


def aptget_common_dev_headers(): 
    """
    Install database, image and xml dev headers for compiling modules

    """
    env.host_string = root_host
    run('yes | apt-get install libmysqlclient-dev libpq-dev libmagickwand-dev libxml2-dev libxslt1-dev python-dev libcurl4-openssl-dev')


def aptget_databases(): 
    """
    Install the common databases: MySQL, Postgres and SQLite
    """
    run('yes | apt-get install mysql-server mysql-client postgresql sqlite sqlite3')


def aptget_lamp(): 
    """
    Install Apache along with CGI 
    """
    env.host_string = root_host
    run('yes | apt-get install apache2 apache2-dev libapache2-mod-wsgi')


def a2enmod_rewrite(): 
    """
    Enable the Rewrite module
    """
    env.host_string = root_host
    run('a2enmod rewrite')
    restart_apache()


def a2enmod_proxy(): 
    """
    Enable the Proxy and Proxy HTTP modules
    """
    env.host_string = root_host
    run('a2enmod proxy')
    run('a2enmod proxy_http')
    restart_apache()


def a2enmod_wsgi(): 
    """
    Install and enable the apache WSGI module for running python apps
    """
    env.host_string = root_host
    run('a2enmod wsgi')
    restart_apache()


def aptget_nginx(): 
    """
    Update to the lates nginx repo and install nginx
    """
    env.host_string = root_host
    run('yes | apt-get install nginx-common nginx-extras')


def aptget_uwsgi(): 
    """
    Update to the latest uwsgi repo and install uwsgi
    """
    env.host_string = root_host
    run('yes | apt-get install uwsgi-python')


def aptget_mail_server(): 
    """
    Install the commonly desired tools for setting up a mail server
    """
    env.host_string = root_host
    run('yes | apt-get install dovecot-postfix postfix-doc postfix-mysql')


def aptget_vim73(): 
    """
    Install the latest vim which right now is 7.3

    Update to the latest vim repo and install the latest vim
    plus a couple common utilities that my vim config uses:

    * ``ctags`` exuberrant ctags
    * ``par`` the paragraph formatter
    """
    env.host_string = root_host
    run('yes | apt-get install vim ctags par')


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
    env.host_string = root_host
    run('apt-get update')
    run('yes | apt-get install python-software-properties mlocate tmux ncurses-term curl')



# python
def install_python_distribute(): 
    """
    Installs the "distribute" python package, a setuptools clone

    Install setuptools so we can build pip and other packages.
    I prefer using distribute.
    """
    env.host_string = root_host
    run('curl -O http://python-distribute.org/distribute_setup.py')
    run('python distribute_setup.py')


def install_python_pip(): 
    """
    Download and install a recent version of the pip utility
    """
    env.host_string = root_host
    the_file = pip_vers + '.tar.gz'
    run('wget ' + pip_url)

    with settings(warn_only=True):
        md5_compute = run('md5sum '+the_file)
        md5_string  = pip_md5+'  '+the_file
        result      = run('[ "'+md5_compute+'" = "'+md5_string+'" ]')
    if result.failed and not confirm("Bad pip tarball. `Continue anyway?"):
        abort("Aborting at user request.")

    run('tar -zxf ' + the_file)
    with cd(pip_vers):
        run('python setup.py install')


def install_python_virtualenv(): 
    """
    Install virtualenv and virtual env wrapper from pip
    """
    env.host_string = root_host
    run('pip install virtualenv virtualenvwrapper')


def setup_webapps_location(): 
    """
    Make the webapps location
    """
    env.host_string = root_host
    run('mkdir -p ' + webapps_location)
    run('chown -R %s:%s %s' % (server_groupname, server_groupname, webapps_location))




def configure_python_virtualenv(target_host): 
    """
    Add virtualenv capabilites to this user.
    
    Mostly this just adds the config settings to the ~/.bashrc to
    provide access to ``workon`` and ``mkvirtualenv``. This is
    only applicable on a per user basis.
    """
    env.host_string = target_host 
    run('mkdir -p '+virtual_environments_location, shell=False)
    run('echo >> ~/.bashrc')
    run('echo \'export WORKON_HOME='+virtual_environments_location+'\' >> ~/.bashrc')
    run('echo \'export VIRTUALENV_USE_DISTRIBUTE=1\' >> ~/.bashrc')
    run('echo \'source /usr/local/bin/virtualenvwrapper.sh\' >> ~/.bashrc')





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

    target_dir = os.path.join(local_tar_dir, srcdir)
    target     = os.path.join(target_dir, source+'.tar.gz')
    srcdir     = os.path.join(local_config_dir, srcdir)

    local('if [ -e '+target+' ]; then mv '+target+' '+target+'.tar.gz.bak.'+get_cur_timestamp+'; fi')
    local('mkdir -p '+target_dir)

    with settings(hide('warnings'), warn_only=True):
        if local('[ -e "'+srcdir+'" ]').succeeded:
            with lcd(srcdir):
                local('tar -czf '+target+' '+source+'')

def regen_tarballs(): 
    """
    Tarball the config tarballs for ease of upload

    This script uploads a number of tarballs that are used to configure
    the server with the settings you want. This Method freshly regenerates
    those tarballs from scratch and keeps timestamped backups of any
    tarballs that might already exist. The current tarballs are

    * ``conf/skel``
    * ``conf/apache/localhost/public``
    """
    local('mkdir -p '+local_backup_dir)
    local('mkdir -p '+local_tar_dir)

    configs = [
        {'source': 'skel',            'srcdir': ''},
        {'source': 'public',          'srcdir': 'apache/localhost'},
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
def configure_restricted_share(user, group, d): 
    """
    Set group ownership of a directory

    This is the case in which we want users to be able to add
    files to a directory but not automatically be able to edit
    or change the contents of that directory.
    """
    env.host_string = root_host

    run('chown '+user+'.'+group+' '+d)
    run('chmod g+w '+d)


def configure_open_share(user, group, d): 
    """
    Recursively set and enforce group ownership of a directory

    This is the case where we want all users of the group
    to always be able to have write permissions on all files
    in this directory, even new files created by other people.
    """
    env.host_string = root_host

    run('chown -R '+user+'.'+group+' '+d)
    run('chmod -R g+w '+d)
    run('find '+d+' -type d -exec chmod g+s "{}" +')


def clone_root_pubkey(user, home): 
    """
    Copy pubkey from root to avoid password prompt

    Copy our current key from the root user to another user to
    avoid the need for a password when logging in.
    """
    env.host_string = root_host

    run('mkdir -p '+home+'/.ssh')
    run('cp /root/.ssh/authorized_keys '+home+'/.ssh/authorized_keys')
    run('chown -R '+user+'.'+user+' '+home+'/.ssh')

def add_custom_user(user, passw, fancy=True): 
    """
    Add a user with a preconfigured home directory

    Add a user account with a skeleton directory structure
    from the config in the local skel dir
    """
    env.host_string = root_host

    run('useradd --skel '+remote_config_dir+'/skel --create-home --home-dir /home/'+user+' --shell /bin/bash '+user)
    run('yes "'+passw+'" | passwd ' + user)


def add_prompt_to_user(home='/root', user='root'): 
    """
    Add an awesomely cool shell prompt for a user 

    Our setup comes with a cool prompt but that comes from the
    skeleton directory for new users. If we are already a user, e.g.
    if we're root or the default system user then we've already got
    a home directory and some config files, so we'll need to
    gracefully add our setup with as little invasiveness as possible.

    The ``home`` and ``user`` parameters are used if you are making
    this copy as another user, for example as root. In that case,
    after you are done copying these files, you'll want to hand
    ownership over to the user in question, also you'll want
    the files to be uploaded to the proper home directory.
    """
    env.host_string = root_host

    put(local_config_dir+'/skel/.colors_prompts', home)
    put(local_config_dir+'/skel/.bash_prompt', home)
    put(local_config_dir+'/skel/.gemrc', home)
    with settings(hide('warnings'), warn_only=True):
        if run('[ ! -e '+home+'/.bashrc.bak ]').succeeded:
            run('cp '+home+'/.bashrc '+home+'/.bashrc.bak')
            run('echo >> '+home+'/.bashrc')
            run("echo 'if [ -f "+home+"/.colors_prompts ]; then . "+home+"/.colors_prompts; fi' >> "+home+"/.bashrc")
            run("echo 'if [ -f "+home+"/.bash_prompt ]; then . "+home+"/.bash_prompt; fi' >> "+home+"/.bashrc")

    # in other words if this was done as root
    if home != '~' and len(user) > 0:
        run('chown -R '+user+'.'+user+' '+home)

def select_prompt(name='remote_root', host=root_host):
    """
    Change the ~/.bash_prompt var to use the special red root prompt

    There are currently two prompts to select from, one is a regular
    user prompt that is green and red, and the other is the same
    but the all red to alter you that you are running commands as
    actual root and as so, to be careful.
    """
    env.host_string = host

    # choose the root prompt instead of the user prompt
    run("echo 'export PS1=$"+name+"' > ~/.bash_prompt")


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
    env.host_string = root_host
    fqdn = server_hostname + '.' + server_domain
    replace_in_file("/etc/hosts", "ubuntu", "%s %s" % (server_hostname, fqdn))
    run("echo %s > /etc/hostname" % server_hostname)
    run("hostname %s" % server_hostname )

def setup_ssl_cert():
    fqdn = server_hostname + '.' + server_domain
    env.host_string = root_host
    run("apt-get install openssl")
    with cd(webapps_location):
        run("mkdir ssl")
        put(local_path="conf/ssl/sslcert.conf", remote_path="%s/ssl" % webapps_location)
        replace_in_file('ssl/sslcert.conf', 'Example, Inc.', ssl_organization_name)
        replace_in_file('ssl/sslcert.conf', 'server.example.com', fqdn)
        replace_in_file('ssl/sslcert.conf', 'postmaster@example.com', ssl_contact)
        run("openssl req -new -x509 -days 365 -nodes -config ssl/sslcert.conf -out ssl/nginx.pem -keyout ssl/nginx.key")
        run("chmod 600 ssl/*")

def clean_ssl():
    env.host_string = root_host
    run("rm -rf %s/ssl" % webapps_location )

def replace_in_file(remote_file_path, target, replacement):
    run("sed -i 's/%s/%s/g' %s" % (target, replacement, remote_file_path))
    
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
    sudo("chmod -R ug+rw " + path)
        
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

def aptget_git():
    env.host_string = root_host
    run('yes | apt-get install git')
    
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
    env.host_string = root_host
    set_user_and_group(server_groupname, server_groupname, '/var/log/apache2')

def sshagent_run(cmd):
    """
    Helper function.
    Runs a command with SSH agent forwarding enabled.
    
    Note:: Fabric (and paramiko) can't forward your SSH agent. 
    This helper uses your system's ssh to do so.
    """

    for h in env.hosts:
        try:
            # catch the port number to pass to ssh
            host, port = h.split(':')
            local('ssh -p %s -A %s "%s"' % (port, host, cmd))
        except ValueError:
            local('ssh -A %s "%s"' % (h, cmd))
