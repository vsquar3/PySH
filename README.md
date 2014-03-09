PySH
==========

PySH (pronounced "psh") is an experimental attempt at a new type of system shell. Requires Python 3.

### Why? ###
I started working on this because I dislike how limiting SH is as a language. Bash and similar shells are excellent due to the power in IO redirection and how integral other applications and libraries have made it, but doing anything beyond simple IO requires you to be familiar with its archaic syntax which many alternative shells have their own spin on. I thought if I could combine the IO piping features of Bash with the syntactic sugar and power of Python then the shell would take on a new, more exciting form for at least myself personally.

### Usage ###
The number of symbols unused in Python syntax are few, so syntactical additions present in PySH appear rather arbitrary and are subject to radical change as development progresses.
Its based off code.py, so in usage it is almost identical to a regular Python shell. The differences are listed below:

* ``` !`some_string` ``` - Will attempt to execute program in a similar way to a bourne-like shell, eg ``` !`"zsh"` ``` would start a new ZShell instance
 * For convenience, ``` !zsh ``` is equivalent to ``` !`"zsh"` ```
* ``` `some_string` ``` - Will return the output of executed string, similar to that in bourne-like shells. eg ``` `"echo test"` ``` would return ``` "test\n" ```
* ``` $VAR ``` - Environment variables, eg
 * ``` print($HOME) ``` - prints home path
 * ``` $TEST = "1" ``` - sets TEST to "1"
* ``` "~" ``` - Filters to the home path. Escapable
* ``` exit ``` or ``` quit ``` - Filters to ```exit()```

### Still to come ###
* IO redirection, including stdout piping to other applications
* Better readline support
