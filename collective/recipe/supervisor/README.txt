This recipe when used will do the following:

 * install ``supervisor`` and all its dependecies.

 * generates the supervisord, supervisorctl, and memmon scripts in the bin 
   directory 

 * generates a configuration file to be used by supervisord and supervisorctl
   scripts

Supported options
=================

The recipe supports the following options:

sections
    List of enabled supervisor sections.
    Defaults to "http ctl rpc"

plugins
    Extra eggs you want the recipe to install. ie: superlance
        
port
    The port nummber supervisord listen to. ie: 9001. Can be given as host:port
    like 127.0.0.1:9001. Defaults to 127.0.0.1:9001

user
    The username required for authentication to supervisord

password
    The password required for authentication to supervisord

supervisord-conf
    Full path to where the recipe puts the supervisord configuration file. 
    Defaults to ${buildout:directory}/parts/${name}/supervisord.conf

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
   
       priority process_name [(process_opts)] command [[args] [directory] [[redirect_stderr]]
                                     [user]]
   
   The [args] is any number of arguments you want to pass to the ``command``
   It has to be given between [] (ie.: [-v fg]). See examples below.
   If not given the redirect_stderr defaults to false.
   If not given the directory option defaults to the directory containing the
   the command.
   The optional process_opts argument sets additional options on the proccess
   in the supervisord configuration.  
   It has to be given between ``()`` and must contain options in ``key=value`` format
   with spaces only for separating options - ie.: (autostart=false startsecs=10).
   The optional user argument gives the userid that the process should be run
   as (if supervisord is run as root).

   In most cases you will only need to give the 4 first parts:

       priority process_name command [[args]]

eventlisteners
    A list of eventlisteners you'd like supervisord to run as subprocesses to
    subscribe to event notifications. One per line. Relevant supervisor 
    documentation about events at 
    http://supervisord.org/manual/current/events.html.
    
        processname events command [[args]]
    
    ``events`` is a comma-separated list (without spaces) of event type names 
    that the listener is "interested" in receiving notifications for.
    
    Supervisor provides one event listener called memmon which can be used to
    restart supervisord child process once they reach a certain memory limit.
    An example of defining a memmon event listener, which analyzes memory usage 
    every 60 seconds and restarts as needed could look like:
    
       MemoryMonitor TICK_60 ${buildout:bin-directory}/memmon [-p process_name=200MB]
    



Example usage
=============

We'll start by creating a buildout that uses the recipe::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = supervisor
    ... index = http://pypi.python.org/simple
    ... [zeo]
    ... location = /a/b/c
    ... [instance1]
    ... location = /e/f
    ... [instance2]
    ... location = /g/h
    ...
    ... [supervisor]
    ... recipe = collective.recipe.supervisor
    ... plugins =
    ...       superlance
    ... port = 9001
    ... user = mustapha
    ... password = secret
    ... serverurl = http://supervisor.mustap.com
    ... programs =
    ...       10 zeo ${zeo:location}/bin/runzeo ${zeo:location}
    ...       20 instance1 ${instance1:location}/bin/runzope ${instance1:location} true
    ...       30 instance2 (autostart=false) ${instance2:location}/bin/runzope true
    ...       40 maildrophost ${buildout:bin-directory}/maildropctl true
    ...       50 other ${buildout:bin-directory}/other [-n 100] /tmp
    ...       60 other2 ${buildout:bin-directory}/other2 [-n 100] true
    ...       70 other3 (startsecs=10) ${buildout:bin-directory}/other3 [-n -h -v --no-detach] /tmp3 true www-data
    ... eventlisteners =
    ...       Memmon TICK_60 ${buildout:bin-directory}/memmon [-p instance1=200MB]
    ...       HttpOk TICK_60 ${buildout:bin-directory}/httpok [-p site1 -t 20 http://localhost:8080/]
    ... """)

Chris Mc Donough said::

     Note however that the "instance" script Plone uses to start Zope when
     passed "fg" appears to use os.system, so the process that supervisor is 
     controlling isnt actually Plone, it's the controller script. This means 
     that "stop" and "start" tend to not do what you want. It's far better to 
     use "runzope", which actually execs the Python process which becomes Zope
     See also 
     http://supervisord.org/manual/current/subprocesses.html#nondaemonizing_of_subprocesses

Running the buildout gives us::

    >>> print system(buildout)
    Getting distribution for 'zc.recipe.egg'.
    ...
    Installing supervisor.
    Getting distribution for 'superlance'.
    ...
    Getting distribution for 'supervisor'.
     ...
    Generated script '/sample-buildout/bin/httpok'.
    Generated script '/sample-buildout/bin/memmon'.
    Generated script '/sample-buildout/bin/crashmail'.
    Generated script '/sample-buildout/bin/supervisord'.
    Generated script '/sample-buildout/bin/supervisorctl'.
    <BLANKLINE>

Check that we have the 'crashmail', 'memmon' and 'httpok' scripts from superlance::

    >>> ls(sample_buildout, 'bin')
    -  buildout
    -  crashmail
    -  httpok
    -  memmon
    -  supervisorctl
    -  supervisord
    

You can now just run the supervisord like this::

    $ bin/supervisord

and control it with supervisorctl::

    $ bin/supervisorctl

Memory monitoring via supervisor's memmon event listener will be executed via
supervisord with the following::

    $ bin/memmon

now, get a look to the generated supervisord.conf file::

    >>> cat('parts', 'supervisor', 'supervisord.conf') #doctest: +REPORT_NDIFF
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
    supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface
    <BLANKLINE>
    <BLANKLINE>
    [program:zeo]
    command = /a/b/c/bin/runzeo 
    process_name = zeo
    directory = /a/b/c
    priority = 10
    redirect_stderr = false
    <BLANKLINE>
    <BLANKLINE>
    [program:instance1]
    command = /e/f/bin/runzope
    process_name = instance1
    directory = /e/f
    priority = 20
    redirect_stderr = true
    <BLANKLINE>
    <BLANKLINE>
    [program:instance2]
    command = /g/h/bin/runzope
    process_name = instance2
    directory = /g/h/bin
    priority = 30
    redirect_stderr = true
    autostart = false
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
    command = /sample-buildout/bin/other -n 100
    process_name = other
    directory = /tmp
    priority = 50
    redirect_stderr = false
    <BLANKLINE>
    <BLANKLINE>
    [program:other2]
    command = /sample-buildout/bin/other2 -n 100
    process_name = other2
    directory = /sample-buildout/bin
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
    user = www-data
    startsecs = 10
    <BLANKLINE>
    <BLANKLINE>
    [eventlistener:Memmon]
    command = /sample-buildout/bin/memmon -p instance1=200MB
    events = TICK_60
    process_name=Memmon
    environment=SUPERVISOR_USERNAME=mustapha,SUPERVISOR_PASSWORD=secret,SUPERVISOR_SERVER_URL=http://supervisor.mustap.com
    <BLANKLINE>
    [eventlistener:HttpOk]
    command = /sample-buildout/bin/httpok -p site1 -t 20 http://localhost:8080/
    events = TICK_60
    process_name=HttpOk
    environment=SUPERVISOR_USERNAME=mustapha,SUPERVISOR_PASSWORD=secret,SUPERVISOR_SERVER_URL=http://supervisor.mustap.com



and if we look to generated supervisord script we will see that the 
configuration file is given as argument with the '-c' option::

    >>> cat('bin', 'supervisord')
    ...
    <BLANKLINE>
    ...
    <BLANKLINE>
    import sys; sys.argv.extend(["-c","/sample-buildout/parts/supervisor/supervisord.conf"])
    <BLANKLINE>
    import supervisor.supervisord
    <BLANKLINE>
    if __name__ == '__main__':
        supervisor.supervisord.main()

The control script contains all specified options, like server url and 
username. This allows to run it as is::

    >>> cat('bin', 'supervisorctl')
    ...
    <BLANKLINE>
    ...
    <BLANKLINE>
    import sys; sys.argv[1:1] = ["-c","/sample-buildout/parts/supervisor/supervisord.conf","-u","mustapha","-p","secret","-s","http://supervisor.mustap.com"]
    <BLANKLINE>
    import supervisor.supervisorctl
    <BLANKLINE>
    if __name__ == '__main__':
        supervisor.supervisorctl.main(sys.argv[1:])

Memmon delegates all work to the egg's memmon Python script itself::

    >>> cat('bin', 'memmon')
    ...
    <BLANKLINE>
    ...
    <BLANKLINE>
    import superlance.memmon
    <BLANKLINE>
    if __name__ == '__main__':
        superlance.memmon.main()

The log directory is created by the recipe::

    >>> ls(sample_buildout, 'var')
    d  log

You can also specify a custom port to run the supervisor on, and the control
script will automatically try to connect to the specified port:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = supervisor
    ... index = http://pypi.python.org/simple/
    ...
    ... [supervisor]
    ... recipe = collective.recipe.supervisor
    ... port = 9005
    ... programs =
    ...       50 other ${buildout:bin-directory}/other [-n 100] /tmp
    ... """)

Here we specified that the supervisor will be launched on port 9005. We can see
that this is also set in the control script:

    >>> _ = system(buildout)
    >>> cat('bin', 'supervisorctl')
    ...
    <BLANKLINE>
    ...
    <BLANKLINE>
    import sys; sys.argv[1:1] = ["-c","/sample-buildout/parts/supervisor/supervisord.conf","-u","","-p","","-s","http://localhost:9005"]
    <BLANKLINE>
    import supervisor.supervisorctl
    <BLANKLINE>
    if __name__ == '__main__':
        supervisor.supervisorctl.main(sys.argv[1:])
