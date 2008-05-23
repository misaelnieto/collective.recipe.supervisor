This recipe when used will do the following:

 * install ``supervisor`` and all its dependecies.

 * generates the supervisord and supervisorctl scripts in the bin directory 

 * generates a configuration file to be used by supervisord and supervisorctl
   scripts

Supported options
=================

The recipe supports the following options:

port
    The port nummber supervisord listen to. ie: 9001. Can be given as host:port
    like 127.0.0.1:9001. Defaults to 127.0.0.1:9001

user
    The username required for authentication to supervisord

password
    The password required for authentication to supervisord

supervisord-conf
    Full path to where the recipe puts the supervisord configuration file. 
    Defaults to ${buildout:directory}/bin/supervisord.conf

logfile
    The full path to the supervisord log file. Defaults to 
    ${buildout:directory}/var/log/supervisord.log

pidfile
    The pid file of supervisord. Defaults to 
    ${buildout:directory}/var/supervisord.pid

logfile-maxbytes
    The maximum number of bytes that may be consumed by the activity log file 
    before it is rotated. Defaults to 50MB

logfile-backups
    The number of backups to keep around resulting from activity log file 
    rotation. Defaults to 10

loglevel
   The logging level. Can be one of critical, error, warn, info, debug, trace, 
   or blather. Defaults to info

nodaemon
   If true, supervisord will start in the foreground instead of daemonizing.
   Defaults to false

serverurl
   The URL that should be used to access the supervisord server. Defaults to
   http://127.0.0.1:9001

programs
   A list of programs you want the supervisord to control. One per line. 
   The format of a line is as follow:
   
       priority process_name command [[args] [directory] [[redirect_stderr]]]
   
   The [args] is any number of arguments you want to pass to the ``command``
   It has to be given between [] (ie.: [-v fg]). See examples below.
   If not given the redirect_stderr defaults to false.
   If not given the directory option defaults to the directory containing the
   the command.

   In most cases you will only need to give the 4 first parts:

       priority process_name command [[args]]



Example usage
=============

We'll start by creating a buildout that uses the recipe::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = supervisor
    ...
    ... [zeo]
    ... location = /a/b/c
    ... [instance1]
    ... location = /e/f
    ... [instance2]
    ...
    ... [supervisor]
    ... recipe = collective.recipe.supervisor
    ... port = 9001
    ... user = mustapha
    ... password = secret
    ... serverurl = http://supervisor.mustap.com
    ... programs =
    ...       10 zeo ${buildout:bin-directory}/zeo [fg] ${zeo:location}
    ...       20 instance1 ${buildout:bin-directory}/instance1 [fg] ${instance1:location} true
    ...       30 instance2 ${buildout:bin-directory}/instance2 [fg] true
    ...       40 maildrophost ${buildout:bin-directory}/maildropctl true
    ...       50 other ${buildout:bin-directory}/other /tmp
    ...       60 other2 ${buildout:bin-directory}/other2 /tmp2 true
    ...       70 other3 ${buildout:bin-directory}/other3 [-n -h -v --no-detach] /tmp3 true
    ... """)


Running the buildout gives us::

    >>> print system(buildout)
    Installing supervisor.
    Getting distribution for 'supervisor'.
    ...
    Generated script '/sample-buildout/bin/supervisorctl'.
    Generated script '/sample-buildout/bin/supervisord'.
    <BLANKLINE>

You can now just run the supervisord like this::

    $ bin/supervisord

and control it with supervisorctl::

    $ bin/supervisorctl

now, get a look to the generated supervisord.conf file::

    >>> cat('bin', 'supervisord.conf')
    <BLANKLINE>
    [inet_http_server]
    port = 9001
    username = mustapha
    password = secret
    <BLANKLINE>
    [supervisord]
    logfile = /sample-buildout/var/log/supervisord.log
    logfile_maxbytes = 50MB
    logfile_backups = 10
    loglevel = info
    pidfile = /sample-buildout/var/supervisord.pid
    nodaemon = false
    <BLANKLINE>
    [supervisorctl]
    serverurl = http://supervisor.mustap.com
    <BLANKLINE>
    [rpcinterface:supervisor]
    supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
    <BLANKLINE>
    <BLANKLINE>
    [program:zeo]
    command = /sample-buildout/bin/zeo fg
    process_name = zeo
    directory = /a/b/c
    priority = 10
    redirect_stderr = false
    <BLANKLINE>
    <BLANKLINE>
    [program:instance1]
    command = /sample-buildout/bin/instance1 fg
    process_name = instance1
    directory = /e/f
    priority = 20
    redirect_stderr = true
    <BLANKLINE>
    <BLANKLINE>
    [program:instance2]
    command = /sample-buildout/bin/instance2 fg
    process_name = instance2
    directory = /sample-buildout/bin
    priority = 30
    redirect_stderr = true
    <BLANKLINE>
    <BLANKLINE>
    [program:maildrophost]
    command = /sample-buildout/bin/maildropctl
    process_name = maildrophost
    directory = /sample-buildout/bin
    priority = 40
    redirect_stderr = true
    <BLANKLINE>
    <BLANKLINE>
    [program:other]
    command = /sample-buildout/bin/other
    process_name = other
    directory = /tmp
    priority = 50
    redirect_stderr = false
    <BLANKLINE>
    <BLANKLINE>
    [program:other2]
    command = /sample-buildout/bin/other2
    process_name = other2
    directory = /tmp2
    priority = 60
    redirect_stderr = true
    <BLANKLINE>
    <BLANKLINE>
    [program:other3]
    command = /sample-buildout/bin/other3 -n -h -v --no-detach
    process_name = other3
    directory = /tmp3
    priority = 70
    redirect_stderr = true
    <BLANKLINE>


and if we look to generated supervisord script we will see that the 
configuration file is given as argument with the '-c' option::

    >>> cat('bin', 'supervisord')
    ...
    <BLANKLINE>
    ...
    <BLANKLINE>
    import sys; sys.argv.extend(["-c","/sample-buildout/bin/supervisord.conf"])
    <BLANKLINE>
    import supervisor.supervisord
    <BLANKLINE>
    if __name__ == '__main__':
        supervisor.supervisord.main()

