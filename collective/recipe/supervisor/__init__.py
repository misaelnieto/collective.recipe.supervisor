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

        #inet_http_server
        port = self.options.get('port', '127.0.0.1:9001')
        user = self.options.get('user', '')
        password = self.options.get('password', '')
        #supervisord
        buildout_dir = self.buildout['buildout']['directory']
        logfile = self.options.get('logfile', os.path.join(buildout_dir,
                                                           'var',
                                                           'log',
                                                           'supervisord.log'))
        pidfile = self.options.get('pidfile', os.path.join(buildout_dir,
                                                           'var',
                                                           'supervisord.pid'))

        logfile_maxbytes = self.options.get('logfile-maxbytes', '50MB')
        logfile_backups = self.options.get('logfile-backups', '10')
        loglevel = self.options.get('loglevel', 'info')
        nodaemon = self.options.get('nodaemon', 'false')
        #supervisorctl
        serverurl = self.options.get('serverurl', 'http://localhost:9001')

        config_data = config_template % dict(port = port,
                                           user = user,
                                           password = password,
                                           logfile = logfile,
                                           pidfile = pidfile,
                                           logfile_maxbytes = logfile_maxbytes,
                                           logfile_backups = logfile_backups,
                                           loglevel = loglevel,
                                           nodaemon = nodaemon,
                                           serverurl = serverurl,
                                         )
        #programs
        programs = [p for p in self.options.get('programs', '').splitlines()
                            if p]
        pattern = re.compile("(?P<priority>\d+)"
                             "\s+"
                             "(?P<processname>[^\s]+)"
                             "\s+"
                             "(?P<command>[^\s]+)"
                             "(\s+\[(?P<args>(?!true|false)[^\]]+)\])?"
                             "(\s+(?P<directory>(?!true|false)[^\s]+))?"
                             "(\s+(?P<redirect>(true|false)))?")

        for program in programs:
            match = pattern.match(program)
            if not match:
                raise(ValueError, "Program line incorrect: %s" % program)

            parts = match.groupdict()

            config_data += program_template % \
                           dict(program = parts.get('processname'),
                                command = parts.get('command'),
                                priority = parts.get('priority'),
                                redirect_stderr = parts.get('redirect') or \
                                                  'false',
                                directory = parts.get('directory') or \
                                         os.path.dirname(parts.get('command')),
                                args = parts.get('args') or '',
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

        # Put all options into the ctl script
        init = '["-c","%s","-u","%s","-p","%s","-s","%s"]' % \
                (conf_file, user, password, serverurl)

        ctlscript = zc.recipe.egg.Egg(self.buildout,
                    self.name,
                    {'eggs': 'supervisor',
                     'scripts': 'supervisorctl=%sctl' % self.name,
                     'initialization': 'import sys; sys.argv[1:1] = %s' % init,
                     'arguments': 'sys.argv[1:]'})

        return list(dscript.install()) + \
               list(ctlscript.install()) + \
               [conf_file]

    def update(self):
        """Updater"""
        pass


config_template = """
[inet_http_server]
port = %(port)s
username = %(user)s
password = %(password)s

[supervisord]
logfile = %(logfile)s
logfile_maxbytes = %(logfile_maxbytes)s
logfile_backups = %(logfile_backups)s
loglevel = %(loglevel)s
pidfile = %(pidfile)s
nodaemon = %(nodaemon)s

[supervisorctl]
serverurl = %(serverurl)s

[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface

"""

program_template = """
[program:%(program)s]
command = %(command)s %(args)s
process_name = %(program)s
directory = %(directory)s
priority = %(priority)s
redirect_stderr = %(redirect_stderr)s

"""
