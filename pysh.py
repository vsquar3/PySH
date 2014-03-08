#!/usr/bin/env python3

import code
import sys
import os
import traceback
import re
import readline
import subprocess
import errno
from site import _Printer

class PySH_builtins:
    __version__ = (0, 1)
    from os import environ

    copyright = _Printer("copyright", "PySH: Copyleft 2014 Bob131\nPython 3: See http://docs.python.org/3/copyright.html")
    license = _Printer("license", "PySH: GPLv3\nPython 3: See http://docs.python.org/3/license.html")

    def call(call_str, stdin=None, shell=False):
        if os.path.isdir(call_str):
            raise IsADirectoryError(errno.EISDIR, "Path is a directory", call_str.split(" ")[0])

        if call_str.startswith("cd "):
            return PySH_builtins.change_dir(call_str.replace("cd ", ""))
        else:
            if not shell:
                return subprocess.check_output(call_str.split(" "), stdin=stdin, stderr=subprocess.STDOUT, shell=False)
            else:
                return subprocess.call(call_str.split(" "), stdin=stdin, shell=False)

    def call_sh(call_str, stdin=None):
        PySH_builtins.call(call_str, stdin, shell=True)

    def change_dir(path):
        os.chdir(path)
        return True



class PySH(code.InteractiveConsole):
    def __init__(self, locals):
        code.InteractiveConsole.__init__(self, locals)

    def _filter(self, line, more):
        for string in re.findall("[\"\'].+?[\"\']", line):
            oldstr = string
            string = string.replace("~", os.getenv("HOME")).replace("\\%s" % os.getenv("HOME"), "~")
            line = line.replace(oldstr, string)

        for expr in [re.sub("[^`][\"\'].+?[\"\'][^`]", "", line)]:
            oldexpr = expr
            expr = expr.replace("~", "\"%s\"" % os.getenv("HOME")).replace("\\\"%s\"" % os.getenv("HOME"), "~")
            for match in re.findall("`(.+?)`", expr):
                newrep = match.replace(match, "__pysh_builtins__.call_sh(%s)" % match)
                expr = expr.replace("`%s`" % match, newrep)
            for match in re.findall("\$(\w+)", expr):
                expr = expr.replace("$%s" % match, "__pysh_builtins__.environ['%s']" % match)
            for match in re.findall("^(exit|quit)$", expr):
                expr = expr.replace(match, "exit()")
            line = line.replace(oldexpr, expr)

        return line

    def interact(self):
        """Adapted from code.InteractiveConsole.interact"""

        self.write("PySH %s.%s" % PySH_builtins.__version__)
        self.write(" | ")
        self.write("Python %s.%s.%s-%s\n" % sys.version_info[:4])

        #set new builtin values
        self.runsource("__builtins__['copyright'] = __pysh_builtins__.copyright")
        self.runsource("__builtins__['license'] = __pysh_builtins__.license")

        self.write("Type \"help\", \"copyright\", \"credits\" or \"license\" for more information.\n")

        more = False
        while 1:
            try:
                try:
                    line = self.raw_input("%s %s %s " % (os.getenv("USER"), os.getcwd().replace(os.getenv("HOME"), "~"), (">>>" if not more else "...")))
                    line = self._filter(line, more)
                except EOFError:
                    self.write("\n")
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = False

    def showtraceback(self):
        """Adapted from code.InteractiveInterpreter.showtraceback"""

        try:
            type, value, tb = sys.exc_info()
            sys.last_type = type
            sys.last_value = value
            sys.last_traceback = tb
            tblist = traceback.extract_tb(tb)
            del tblist[:1]
            lines = traceback.format_list(tblist)
            if lines:
                lines.insert(0, "Traceback (most recent call last):\n")
            lines.extend(traceback.format_exception_only(type, value))
        finally:
            tblist = tb = None
        newlines = []
        for line in lines[:-1]:
            if not sys.argv[0] in line:
                newlines.append(line)
            else:
                break
        newlines.append(lines[-1])
        self.write(''.join(newlines))



if __name__ == "__main__":
    if sys.version_info[0] > 2:
        shell = PySH(locals={"__pysh_builtins__": PySH_builtins})
        shell.interact()
    else:
        print("Python v3 required. Exiting")
