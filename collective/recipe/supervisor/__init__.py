# -*- coding: utf-8 -*-
"""Recipe supervisor"""

import os
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
        buildout_dir =  self.buildout['buildout']['directory']
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

        config_data = config_template % dict (port = port,
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
        programs = [p for p in self.options.get('programs', '').split(os.linesep) if p]
        for program in programs:
            redirect_stderr = 'false'
            line = program.split() 
            ln = len(line)
            if ln == 3:
                priority, process_name, command = line
                directory = os.path.dirname(command)
            elif ln == 4:
                priority, process_name, command, directory = line
            elif ln == 5:
                priority, process_name, command, directory, redirect_stderr = line
            else:
                raise ValueError, "collective.recipe.supervisor: wrong options number in: %s" % program

            config_data += program_template % dict(program = process_name,
                                                   command = command,
                                                   priority = priority,
                                                   redirect_stderr = redirect_stderr,
                                                   directory = directory
                                                  )

        conf_file = os.path.join(self.buildout['buildout']['bin-directory'], 'supervisord.conf')
        if self.options.get('supervisord-conf', None) is not None:
            conf_file = self.options.get('supervisord-conf')
            if not os.path.exists(os.path.dirname(conf_file)):
                os.makedirs(os.path.dirname(conf_file))

        open(conf_file, 'w').write(config_data)

        script = zc.recipe.egg.Egg(self.buildout, 
                                   self.name, 
                                   {'eggs': 'supervisor', 
                                    'scripts': 'supervisord=supervisord supervisorctl=supervisorctl',
                                    'initialization': 'import sys; sys.argv.extend(["-c","%s"])' % conf_file,}
                                  )

        return list(script.install()) + [conf_file]

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
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
    
"""

program_template = """
[program:%(program)s]
command = %(command)s
process_name = %(program)s
directory = %(directory)s
priority = %(priority)s
redirect_stderr = %(redirect_stderr)s

"""




