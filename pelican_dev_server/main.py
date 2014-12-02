"""
Note: For a quality experience your editor must be configured not to modify your
project's filesystem without your command. For instance, Vim saves swap files in
the same directory as the file you're editing by default, and this behavior can
be remedied by explicitly setting a directory in your vimrc (e.g.
`set directory=~/tmp` and you'll have to manually create the directory).
"""
import os
import sys
import time
import argparse
import datetime
import contextlib
import subprocess
import webbrowser

import pelican
import cherrypy
import watchdog.events
import watchdog.observers

parser = argparse.ArgumentParser(description='Development server for Pelican.')
parser.add_argument('-p', '--path', dest='path', required=True,
                    help='Path to pelican project directory.')
parser.add_argument('-d', '--debug', action='store_true')
parser.add_argument('-o', '--open', nargs='?', type=str, dest='browser',
                    const=os.getenv('BROWSER', 'firefox'),
                    help='Open site, optionally specifying browser.')
args = parser.parse_args()

# constants
PELICAN_PATH = args.path
BROWSER = args.browser
DEBUG = args.debug
PELICAN_SETTINGS = pelican.settings.get_settings_from_file(
    os.path.join(PELICAN_PATH, 'pelicanconf.py'))
OUTPUT_PATH = os.path.join(PELICAN_PATH, PELICAN_SETTINGS['OUTPUT_PATH'])

# variables
LAST_UPDATE = datetime.datetime.now()
OBSERVER = None


def main():
    # configure server
    static_dirs = PELICAN_SETTINGS['STATIC_PATHS'] + [PELICAN_SETTINGS['THEME']]
    config = {
        '/' + static_dir: {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(OUTPUT_PATH, static_dir)}
        for static_dir in static_dirs}
    cherrypy.config.update({'engine.autoreload.on': False})
    if not DEBUG:
        cherrypy.config.update({'log.screen': False})
    cherrypy.tree.mount(CherrypyServer(), '/', config=config)

    # configure observer
    global OBSERVER
    OBSERVER = PausingObserver()
    OBSERVER.schedule(PelicanUpdater(), PELICAN_PATH, recursive=True)

    # start threads
    cherrypy.engine.start()
    OBSERVER.start()
    if BROWSER:
        webbrowser.get(BROWSER).open('http://127.0.0.1:8080')

    # control loop
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    # teardown
    OBSERVER.stop()
    os._exit(0)


def get_html_file(path):
    try:
        f = open(path, encoding='latin-1')
        return f
    except IsADirectoryError:
        path = os.path.join(path, 'index.html')

    try:
        f = open(path, encoding='latin-1')
        return f
    except FileNotFoundError:
        raise cherrypy.NotFound()


class CherrypyServer(object):
    @cherrypy.expose
    def default(self, *args):
        path = os.path.join(OUTPUT_PATH, '/'.join(args))

        ws_client_script = """
        <script>
        var event_source = new EventSource('event_source');
        event_source.addEventListener('update', function(event) {
            location.reload();
        });
        </script>
        """

        with get_html_file(path) as f:
            before, body_close, after = f.read().rpartition('</body>')
            return before + ws_client_script + body_close + after

    @cherrypy.expose
    def event_source(self):
        cherrypy.response.headers['Content-Type'] = 'text/event-stream'

        def generator():
            last_update = LAST_UPDATE
            while True:
                time.sleep(.1)
                if last_update < LAST_UPDATE:
                    last_update = LAST_UPDATE
                    yield 'event: update\ndata: _\n\n'

        return generator()
    event_source._cp_config = {'response.stream': True}


class PausingObserver(watchdog.observers.Observer):
    def dispatch_events(self, *args, **kwargs):
        if not getattr(self, '_is_paused', False):
            super(PausingObserver, self).dispatch_events(*args, **kwargs)

    def pause(self):
        self._is_paused = True

    def resume(self):
        time.sleep(self.timeout)  # allow interim events to be queued
        self.event_queue.queue.clear()
        self._is_paused = False

    @contextlib.contextmanager
    def ignore_events(self):
        self.pause()
        yield
        self.resume()


class PelicanUpdater(watchdog.events.FileSystemEventHandler):
    def on_modified(self, event):
        sys.stdout.write('\n')

        with OBSERVER.ignore_events():
            p = subprocess.Popen(['make', 'html'], cwd=PELICAN_PATH,
                                 stdout=subprocess.PIPE, bufsize=1)
            for line in iter(p.stdout.readline, b''):
                sys.stdout.write(line.decode('utf-8'))

        global LAST_UPDATE
        LAST_UPDATE = datetime.datetime.now()
