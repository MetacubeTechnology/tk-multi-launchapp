# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
App Launch Hook

This hook is executed to launch the applications.
"""

import os
import re
import sys
import subprocess
import tank
from tank import TankError

class AppLaunch(tank.Hook):
    """
    Hook to run an application.
    """
    
    def execute(self, app_path, app_args, version, **kwargs):
        """
        The execute functon of the hook will be called to start the required application
        
        :param app_path: (str) The path of the application executable
        :param app_args: (str) Any arguments the application may require
        :param version: (str) version of the application being run if set in the "versions" settings
                              of the Launcher instance, otherwise None

        :returns: (dict) The two valid keys are 'command' (str) and 'return_code' (int).
        """
        system = sys.platform
        if system == "linux2":
            # on linux, we just run the executable directly
            cmd = "%s %s &" % (app_path, app_args)
        
        elif self.parent.get_setting("engine") in ["tk-flame", "tk-flare"]:
            # flame and flare works in a different way from other DCCs
            # on both linux and mac, they run unix-style command line
            # and on the mac the more standardized "open" command cannot
            # be utilized.
            cmd = "%s %s &" % (app_path, app_args)
            
        elif system == "darwin":
            # on the mac, the executable paths are normally pointing
            # to the application bundle and not to the binary file
            # embedded in the bundle, meaning that we should use the
            # built-in mac open command to execute it
            cmd = "open -n \"%s\"" % (app_path)
            if app_args:
                cmd += " --args \"%s\"" % app_args.replace("\"", "\\\"")


        elif system == "win32" and self.parent.get_setting("engine") in ["tk-fusion"]:
            # used to open only fusion in a very specific way
            # we need to catch the process id from the begining
            cmd = 'wmic process call create "%s" | find "ProcessId"' % (app_path)
            fusion_command = subprocess.check_output(cmd, shell=True)

            if "ProcessId" in fusion_command:
                self.parent.log_debug ("Lauch output: " + str (fusion_command))
                try:
                    ProcessId = re.search ('[0-9]+', fusion_command).group()
                except:
                    raise TankError ("We cant parse the process id: %s" % fusion_command)

                self.parent.log_debug ("Retrieved PID: " + str (ProcessId))
                os.system (os.environ["SGTK_FUSION_BOOTSTRAP"] + " " + str (ProcessId))
            else:
                raise TankError (fusion_command)

        elif system == "win32":
            # on windows, we run the start command in order to avoid
            # any command shells popping up as part of the application launch.
            cmd = "start /B \"App\" \"%s\" %s" % (app_path, app_args)

        # run the command to launch the app
        if self.parent.get_setting("engine") in ["tk-fusion"]:
            self.parent.log_debug ("Overriding exit_code to 0")
            exit_code = 0
        else:
            exit_code = os.system(cmd)

        return {
            "command": cmd,
            "return_code": exit_code
        }
