import tornado.ioloop
import tornado.web
import tornado.autoreload
import os
import sys, getopt
import smtplib
import pdfkit
import signal
import yaml
from itertools import chain

_CSS = []
_JS = []

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", css=_CSS, js=_JS)

class MailHandler(tornado.web.RequestHandler):
    def post(self):
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)

            email = self.get_argument('email')
            name = self.get_argument('sender')
            message = self.get_argument('message')

            if email and name and message:
                __EMAIL = cfg['mail']['user']

                server = smtplib.SMTP(cfg['mail']['host'], 587)
                server.starttls()
                server.login(__EMAIL, cfg['mail']['pw'])

                msg = '\r\n'.join([
                    'From: My website',
                    'To: ' + __EMAIL,
                    'Subject: New Message from website',
                    '',
                    'Name: ' + name.encode('utf-8'),
                    'E-Mail: ' + email.encode('utf-8'),
                    '',
                    message.encode('utf-8')
                ])

                server.sendmail("mail@server.de", __EMAIL, msg)
                server.quit()

                self.write({'ok': True})

"""
class PdfHandler(tornado.web.RequestHandler):
    def post(self):
        css = [
            'static/css/bootstrap.min.css',
            'static/css/extras.css',
            'static/css/material-icons.css',
            'static/css/style.css'
        ]

        pdfkit.from_file('templates/index.html', 'out.pdf', css=css)
        self.set_header('Content-Type', 'application/pdf')
        self.set_header('Content-Disposition', 'attachment; filename="out.pdf"')
        self.write(b64decode(escape.url_unescape(self.request.body.split("=")[1])))
"""

settings = {'debug': False,
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            'template_path': os.path.join(os.path.dirname(__file__), 'templates')}

handlers = [(r'/', MainHandler),
            (r'/mail', MailHandler),
            #(r'/pdf', PdfHandler)
            #(r'/favicon.ico', tornado.web.StaticFileHandler, {'path': favicon_path}),
            ]

additional_settings = {'port': 8000,
                      'minified': False}

def signal_handler(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()

def init():
    global _CSS
    global _JS
    _JS = []
    _CSS = []

    if additional_settings['minified']:
        _CSS = ['css/style.min.css']
        _JS = ['js/script.min.js']
    else:

        css_path = os.path.join('static', 'css')
        js_path = os.path.join('static', 'js')

        libs = ['jquery/jquery-1.11.3.min.js', 'pixi/pixi.min.js'];

        _CSS = [os.path.join('css', file) for file in os.listdir(css_path) if os.path.isfile(os.path.join(css_path,file)) and file.find('.min') == -1]

        # add libs
        _JS += [os.path.join('js','lib', lib) for lib in libs];

        # add scripts
        _JS += ["js/{}".format(file) for file in os.listdir(js_path) if os.path.isfile(os.path.join(js_path,file)) and file.find('.min') == -1]

if __name__ == "__main__":
    myopts, args = getopt.getopt(sys.argv[1:], "p:md", ['port=', 'minified', 'debug'])

    for arg, val in myopts:
        if arg in ('-p', '--port'):
            additional_settings['port'] = val
        if arg in ('-m', '--minified'):
            additional_settings['minified'] = True
        if arg in ('-d', '--debug'):
            settings['debug'] = True

    init()
    app = tornado.web.Application(handlers, **settings)

    def fn():
        init()

    app.listen(additional_settings['port'])
    print "Server restarted.."
    tornado.autoreload.add_reload_hook(fn)
    tornado.autoreload.start()

    for dir, _, files in os.walk('static'):
        [tornado.autoreload.watch(dir + '/' + f) for f in files if not f.startswith('.')]

    for dir, _, files in os.walk('templates'):
        [tornado.autoreload.watch(dir + '/' + f) for f in files if not f.startswith('.')]

    tornado.ioloop.IOLoop.current().start()
