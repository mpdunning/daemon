#!/usr/bin/env python
# daemon.py

import atexit
from __future__ import print_function
import os
import signal
import sys
import time

class Daemon:
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.pidfile = pidfile
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def daemonize(self):
        """Set up daemon."""
        # First fork (detaches from parent)
        try:
            if os.fork() > 0:
                raise SystemExit(0)   # Parent exit
        except OSError as e:
            raise RuntimeError('fork #1 failed.')
        
        os.chdir('/')
        os.umask(0)
        os.setsid()
        
        # Second fork (relinquish session leadership)
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as e:
            raise RuntimeError('fork #2 failed.')
        
        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()

        # Replace file descriptors for stdin, stdout, and stderr
        with open(self.stdin, 'r', 0) as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open(self.stdout, 'w', 0) as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
        with open(self.stderr, 'w', 0) as f:
            os.dup2(f.fileno(), sys.stderr.fileno())

        # Write the PID file
        self.pid = os.getpid()
        with open(self.pidfile, 'w') as f:
            print(self.pid, file=f)

        # Arrange to have the PID file removed on exit/signal
        atexit.register(lambda: os.remove(self.pidfile))

        # Signal handler for termination (required)
        def sigterm_handler(signo, frame):
            raise SystemExit(1)

        signal.signal(signal.SIGTERM, sigterm_handler)

    def _get_pid_from_file(self):
        try:
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
        # File doesn't exist
        except IOError:
            pid = None
        # File exists, but PID is not a number
        except ValueError:
            print('Error: PID file {0} exists but PID is not a number.'.format(self.pidfile))
            raise SystemExit(1)
        return pid

    def start(self):
        """Start daemon."""
        pid = self._get_pid_from_file()
        print(pid)
        if pid is None:
            sys.stderr.write('Daemon starting...\n')
            self.daemonize()
            self.run()
        else:
            sys.stderr.write('Daemon already running...PID: {0}, PID file: {1}\n'.format(pid, self.pidfile))
        
    def status(self):
        """Get status of daemon."""
        pid = self._get_pid_from_file()
        if pid is None:
            sys.stderr.write('Daemon not running.\n')
        else:
            sys.stderr.write('Daemon running...PID: {0}, PID file: {1}\n'.format(pid, self.pidfile))
        
    def stop(self):
        """Stop daemon."""
        pid = self._get_pid_from_file()
        if pid is None:
            sys.stderr.write('Daemon not running.\n')
        else:
            sys.stderr.write('Stopping daemon...\n')
            os.kill(pid, signal.SIGTERM)
        
    def run(self):
        """Does the work. Subclasses should override this method."""
        raise NotImplementedError('run: Subclasses must override this method.')


if __name__ == '__main__':
    """Self-test code."""
    
    args = 'start|stop|status'
    def show_usage():
        """Print usage."""
        print('Usage: {0} {1}'.format(sys.argv[0], args), file=sys.stderr)
    if len(sys.argv) != 2:
        show_usage()
        raise SystemExit(1)

    class MyDaemon(Daemon):
        def run(self):
            """Print pid to file, then start the work loop."""
            sys.stdout.write('Daemon started with pid {0}\n'.format(self.pid))
            # Loop forever, doing some simulated work
            while True:
                sys.stdout.write('Daemon Alive! {0}\n'.format(time.ctime()))
                time.sleep(2)
                sys.stdout.flush()
                
    daemon = MyDaemon(pidfile='/tmp/daemon.pid', stdout='/tmp/daemon.log', stderr='/tmp/daemon.log')

    if sys.argv[1] == 'start':
        daemon.start()
    elif sys.argv[1] == 'stop':
        daemon.stop()
    elif sys.argv[1] == 'status':
        daemon.status()
    else:
        print('Unknown command: {0!r}'.format(sys.argv[1]), file=sys.stderr)
        show_usage()
        raise SystemExit(1)





