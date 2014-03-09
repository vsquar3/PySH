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
                return subprocess.check_output(call_str.split(" "), stdin=stdin, stderr=subprocess.STDOUT, shell=False).decode("UTF-8")
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

    def _filter(self, line):
        if line.strip().startswith("!") and not line.strip().startswith("!`"):
            line = "%s__pysh_builtins__.call_sh(\"%s\")" % (re.findall("^\s*", line)[0], line.strip()[1:].replace("\\\"", "\"").replace("\"", "\\\""))
        else:
            for string in re.findall("[\"\'].+?[\"\']", line):
                oldstr = string
                for match in re.finditer("[^\\\\]~", string):
                    string = string[:match.start()+1] + os.getenv("HOME") + string[match.end():]
                string = string.replace("\\~", "~")
                line = line.replace(oldstr, string)

            for expr in [re.sub("[\"\'].+?[\"\']", "", line)]:
                oldexpr = expr
                for match in re.findall("\$(\w+)", expr):
                    expr = expr.replace("$%s" % match, "__pysh_builtins__.environ['%s']" % match)
                for match in re.findall("^(exit|quit)$", expr):
                    expr = expr.replace(match, "exit()")
                line = line.replace(oldexpr, expr)

            line = re.sub("!`(?P<str>.*?)`", "__pysh_builtins__.call_sh(\g<str>)", line)
            line = re.sub("`(?P<str>.*?)`", "__pysh_builtins__.call(\g<str>)", line)

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
                    line = self.raw_input("\033[92m\033[1m%s \033[95m%s \033[93m%s \033[0m" % (os.getenv("USER"), os.getcwd().replace(os.getenv("HOME"), "~"), (">>>" if not more else "...")))
                except EOFError:
                    self.write("\n")
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = False

    def push(self, line):
        """Adapeted from code.InteractiveConsole.push"""
        line = self._filter(line)
        self.buffer.append(line)
        source = "\n".join(self.buffer)
        more = self.runsource(source, self.filename)
        if not more:
            self.resetbuffer()
        return more

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
        if len(sys.argv) < 2:
            shell.interact()
        else:
            try:
                if not os.path.isdir(sys.argv[1]):
                    text = open(sys.argv[1]).read().split("\n")
                    if text[0].startswith("#!") and not "pysh" in text[0].lower():
                        shell.push("!%s %s" % (text[0].replace("#!", ""), sys.argv[1]))
                        sys.exit()
                    else:
                        for line in text:
                            shell.push(line)
                else:
                    raise OSError(errno.EISDIR, "Path is a directory", sys.argv[1])
            except Exception as e:
                print(e)
                sys.exit()
    else:
        print("Python v3 required. Exiting")
