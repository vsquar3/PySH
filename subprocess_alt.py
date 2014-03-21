from subprocess import *

def check_output(*popenargs, timeout=None, **kwargs):
    """Adapted from subprocess.check_output"""
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    with Popen(*popenargs, stdout=PIPE, **kwargs) as process:
        try:
            output, unused_err = process.communicate(timeout=timeout)
        except TimeoutExpired:
            process.kill()
            output, unused_err = process.communicate()
            raise TimeoutExpired(process.args, timeout, output=output)
        except:
            process.kill()
            process.wait()
            raise
        retcode = process.poll()
    return output
