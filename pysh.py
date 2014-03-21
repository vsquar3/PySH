#!/usr/bin/env python3

import code
import sys
import traceback
import re
import readline
import errno
import tokenize
from site import _Printer
from io import BytesIO

import os_alt as os
import subprocess_alt as subprocess
import tokenize

DEBUG = False #shows PySH files in traceback stack when true



class PySH_builtins:
    environ = os.environ
    __version__ = (0, 1)
    __path__ = os.path.dirname(__file__)

    copyright = _Printer("copyright", "PySH: Copyleft 2014 Bob131\nPython 3: See http://docs.python.org/3/copyright.html")
    license = _Printer("license", "PySH: GPLv3\nPython 3: See http://docs.python.org/3/license.html")

    def call(call_str="", stdin=None, shell=False):
        if type(call_str) == bytes:
            call_str = call_str.decode("UTF-8").replace("\\\\", "\\")
        call_str = call_str.replace("\\\\", "\\")

        if os.path.isdir(call_str):
            raise IsADirectoryError(errno.EISDIR, "Path is a directory", call_str.split(" ")[0])

        if call_str.startswith("cd "):
            return PySH_builtins.change_dir(call_str.replace("cd ", ""))
        else:
            strings = re.finditer("(?<=[\"\']).*?(?=[\"\'])", call_str)
            call_str = re.sub("(?<=[\"\']).*?(?=[\"\'])", "", call_str)
            call_str = re.split("(?<!\\\\|^\")\s+", call_str)
            for preserved in strings:
                print(preserved.group(0))
                call_str = call_str[:preserved.start()] + preserved.group(0) + call_str[preserved.start()+1:]
            print(call_str)
            if not shell:
                return subprocess.check_output(call_str, stdin=stdin, stderr=subprocess.STDOUT, shell=False).decode("UTF-8").strip()
            else:
                return subprocess.call(call_str, stdin=stdin, shell=False)

    def call_sh(call_str="", stdin=None):
        PySH_builtins.call(call_str, stdin, shell=True)

    def change_dir(path):
        os.chdir(path)
        return True



class PySH(code.InteractiveConsole):
    def __init__(self, locals):
        code.InteractiveConsole.__init__(self, locals)

    def _filter(self, line):
        def tilda_filter(string):
            for match in re.finditer("(?<!\\\\)~\w+", string):
                path = list(x for x in open("/etc/passwd", "r").read().split("\n") if x.split(":")[0] == match.group(0)[1:])[0].split(":")[5]
                string = string[:match.start()] + path + string[match.end():]
            for match in re.finditer("(?<!\\\\)~", string):
                string = string[:match.start()] + os.getenv("HOME") + string[match.end():]
            string = string.replace("\\~", "~")
            return string

        def inlinetokens_get(tokens, i, offset):
            inlinetokens = []
            for kind, val, _, _, _ in tokens[i+offset:]:
                if not val == "`":
                    inlinetokens.append((kind, val))
                else:
                    break
            return inlinetokens

        if line.strip().startswith("!") and not line.strip().startswith("!`"):
            line = "%s!`%s`" % (re.findall("^\s*", line)[0], tilda_filter(line.strip()[1:]).encode("unicode-escape"))
            line = self._filter(line)
            return line
        else:
            newtokens = []
            skipnext = 0
            i = 1

            tokens = list(tokenize.tokenize(BytesIO(line.encode("UTF-8")).readline))

            for token in tokens:
                try:
                    if skipnext == 0:
                        if token.string == "$" and tokens[i].string.isidentifier():
                            newtokens.extend([(tokenize.NAME, "__pysh_builtins__.environ"), (tokenize.OP, "["), (tokenize.STRING, "'%s'" % tokens[i].string), (tokenize.OP, "]")])
                            skipnext += 1
                        elif token.type == tokenize.STRING:
                            newtokens.append((tokenize.STRING, tilda_filter(token.string)))
                        elif token.string == "!" and tokens[i].string == "`" and not tokens[i+1].string == "`":
                            inlinetokens = inlinetokens_get(tokens, i, 1)
                            newtokens.extend([(tokenize.NAME, "__pysh_builtins__.call_sh"), (tokenize.OP, "(")])
                            newtokens.extend(inlinetokens)
                            newtokens.extend([(tokenize.OP, ")")])
                            skipnext += 2 + len(inlinetokens)
                        elif token.string == "`" and not tokens[i].string == "`" and not tokens[i-2].string == "`":
                            inlinetokens = inlinetokens_get(tokens, i, 0)
                            newtokens.extend([(tokenize.NAME, "__pysh_builtins__.call"), (tokenize.OP, "(")])
                            newtokens.extend(inlinetokens)
                            newtokens.extend([(tokenize.OP, ")")])
                            skipnext += 1 + len(inlinetokens)
                        elif token.string == "exit" or token.string == "quit":
                            newtokens.extend([(tokenize.NAME, "exit"), (tokenize.OP, "("), (tokenize.OP, ")")])
                        else:
                            raise IndexError
                    else:
                        skipnext -= 1 
                except IndexError:
                    newtokens.append((token.type, token.string))
                i+=1

            return tokenize.untokenize(newtokens).decode("UTF-8")

    def interact(self):
        """Adapted from code.InteractiveConsole.interact"""

        self.write("PySH %s.%s" % PySH_builtins.__version__)
        self.write(" | ")
        self.write("Python %s.%s.%s-%s\n" % sys.version_info[:4])

        #set new builtin values
        self.runsource("__builtins__['copyright'] = __pysh_builtins__.copyright")
        self.runsource("__builtins__['license'] = __pysh_builtins__.license")

        self.write("Type \"help\", \"copyright\", \"credits\" or \"license\" for more information.\n")

        #setup new env vars
        self.push("$USERNAME = $USER")
        self.push("$SHELL = %s" % str(__file__.encode("unicode-escape"))[1:])

        more = False
        while 1:
            try:
                try:
                    line = self.raw_input("%s %s %s " % (os.getenv("USER"), os.getcwd().replace(os.getenv("HOME"), "~"), (">>>" if not more else "...")))
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

        line = self._filter(str(line))
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
            if not PySH_builtins.__path__ in line:
                newlines.append(line)
            elif DEBUG == True:
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
