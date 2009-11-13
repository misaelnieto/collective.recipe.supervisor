# -*- coding: utf-8 -*-
"""Recipe supervisor"""

import os
import re
import zc.recipe.egg


class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options

    def install(self):
        """Installer"""
        # XXX Implement recipe functionality here
        # Return files that were created by the recipe. The buildout
        # will remove all returned files upon reinstall.

        # general options
        enable = self.options.get('enable', 'ctl http rpc').split()

        # supervisord
        buildout_dir = self.buildout['buildout']['directory']
        logfile = self.options.get('logfile', os.path.join(buildout_dir,
                                                           'var',
                                                           'log',
                                                           'supervisord.log'))
        pidfile = self.options.get('pidfile', os.path.join(buildout_dir,
                                                           'var',
                                                           'supervisord.pid'))
        log_dir = os.path.abspath(os.path.dirname(logfile))
        pid_dir = os.path.abspath(os.path.dirname(pidfile))
        logfile_maxbytes = self.options.get('logfile-maxbytes', '50MB')
        logfile_backups = self.options.get('logfile-backups', '10')
        loglevel = self.options.get('loglevel', 'info')
        nodaemon = self.options.get('nodaemon', 'false')
        config_data = CONFIG_TEMPLATE % locals()

        # make dirs
        for folder in [log_dir, pid_dir]:
            if not os.path.isdir(folder):
                os.makedirs(folder)

        # inet_http_server
        port = self.options.get('port', '127.0.0.1:9001')
        user = self.options.get('user', '')
        password = self.options.get('password', '')
        if 'http' in enable:
            config_data += HTTP_TEMPLATE % locals()

        # supervisorctl
        if ':' in port:
            default_serverhost = port
        else:
            default_serverhost = 'localhost:%s' % port
        serverurl = self.options.get('serverurl', 'http://%s' % default_serverhost)
        if 'ctl' in enable:
            config_data += CTL_TEMPLATE % locals()

        # rpc
        if 'rpc' in enable:
            config_data += RPC_TEMPLATE % locals()

        # programs
        programs = [p for p in self.options.get('programs', '').splitlines() if p]
        pattern = re.compile("(?P<priority>\d+)"
                             "\s+"
                             "(?P<processname>[^\s]+)"
                             "(\s+\((?P<processopts>([^\)]+))\))?"
                             "\s+"
                             "(?P<command>[^\s]+)"
                             "(\s+\[(?P<args>(?!true|false)[^\]]+)\])?"
                             "(\s+(?P<directory>(?!true|false)[^\s]+))?"
                             "(\s+(?P<redirect>(true|false)))?"
                             "(\s+(?P<user>[^\s]+))?")

        for program in programs:
            match = pattern.match(program)
            if not match:
                raise(ValueError, "Program line incorrect: %s" % program)

            parts = match.groupdict()
            program_user = parts.get('user')
            process_options = parts.get('processopts')
            extras = []

            if program_user:
                extras.append( 'user = %s' % program_user )
            if process_options:
                for part in process_options.split():
                    if part.find('=') == -1:
                        continue
                    (key, value) = part.split('=',1)
                    if key and value:
                        extras.append( "%s = %s" % (key, value) )

            config_data += PROGRAM_TEMPLATE % \
                           dict(program = parts.get('processname'),
                                command = parts.get('command'),
                                priority = parts.get('priority'),
                                redirect_stderr = parts.get('redirect') or \
                                                  'false',
                                directory = parts.get('directory') or \
                                         os.path.dirname(parts.get('command')),
                                args = parts.get('args') or '',
                                extra_config = "\n".join( extras ),
                           )

        # eventlisteners
        eventlisteners = [e for e in self.options.get('eventlisteners', '').splitlines()
                            if e]

        pattern = re.compile("(?P<processname>[^\s]+)"
                             "\s+"
                             "(?P<events>[^\s]+)"
                             "\s+"
                             "(?P<command>[^\s]+)"
                             "(\s+\[(?P<args>[^\]]+)\])?")

        for eventlistener in eventlisteners:
            match = pattern.match(eventlistener)
            if not match:
                raise(ValueError, "Event Listeners line incorrect: %s" % eventlistener)

            parts = match.groupdict()
            
            config_data += EVENTLISTENER_TEMPLATE % \
                           dict(name = parts.get('processname'),
                                events = parts.get('events'),
                                command = parts.get('command'),
                                args = parts.get('args'),
                                user = user, 
                                password = password, 
                                serverurl = serverurl,
                           )
        
        
        conf_file = os.path.join(self.buildout['buildout']['parts-directory'],
                                 self.name, 'supervisord.conf')
        if self.options.get('supervisord-conf', None) is not None:
            conf_file = self.options.get('supervisord-conf')
        if not os.path.exists(os.path.dirname(conf_file)):
            os.makedirs(os.path.dirname(conf_file))

        open(conf_file, 'w').write(config_data)

        dscript = zc.recipe.egg.Egg(self.buildout,
              self.name,
              {'eggs': 'supervisor',
               'scripts': 'supervisord=%sd' % self.name,
               'initialization': 'import sys; sys.argv.extend(["-c","%s"])' % \
                                  conf_file})

        memscript = zc.recipe.egg.Egg(self.buildout,
              self.name,
              {'eggs': 'supervisor',
               'scripts': 'memmon=memmon',})

        # Put all options into the ctl script
        init = '["-c","%s","-u","%s","-p","%s","-s","%s"]' % \
                (conf_file, user, password, serverurl)

        ctlscript = zc.recipe.egg.Egg(self.buildout,
                    self.name,
                    {'eggs': 'supervisor',
                     'scripts': 'supervisorctl=%sctl' % self.name,
                     'initialization': 'import sys; sys.argv[1:1] = %s' % init,
                     'arguments': 'sys.argv[1:]'})
                     
        #install extra eggs if any
        eggs = self.options.get('plugins', '')
        
        extra_eggs = []
        if eggs:
            extra_eggs = list(zc.recipe.egg.Egg(self.buildout,
                                                self.name,
                                                {'eggs':eggs}).install())
            
        

        return list(dscript.install()) + \
               list(memscript.install()) + \
               list(ctlscript.install()) + \
               extra_eggs + \
               [conf_file]

    def update(self):
        """Updater"""
        pass


CONFIG_TEMPLATE = """
[supervisord]
logfile = %(logfile)s
logfile_maxbytes = %(logfile_maxbytes)s
logfile_backups = %(logfile_backups)s
loglevel = %(loglevel)s
pidfile = %(pidfile)s
nodaemon = %(nodaemon)s
"""

CTL_TEMPLATE = """
[supervisorctl]
serverurl = %(serverurl)s
"""

HTTP_TEMPLATE = """
[inet_http_server]
port = %(port)s
username = %(user)s
password = %(password)s
"""

RPC_TEMPLATE = """
[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface
"""

PROGRAM_TEMPLATE = """
[program:%(program)s]
command = %(command)s %(args)s
process_name = %(program)s
directory = %(directory)s
priority = %(priority)s
redirect_stderr = %(redirect_stderr)s
%(extra_config)s
"""

EVENTLISTENER_TEMPLATE = """
[eventlistener:%(name)s]
command = %(command)s %(args)s
events = %(events)s
process_name=%(name)s
environment=SUPERVISOR_USERNAME=%(user)s,SUPERVISOR_PASSWORD=%(password)s,SUPERVISOR_SERVER_URL=%(serverurl)s
"""
