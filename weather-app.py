import tornado.ioloop
import tornado.web
import tornado.log
import os
import requests
import json

from jinja2 import \
  Environment, PackageLoader, select_autoescape
ENV = Environment(
    loader=PackageLoader('weather-app', 'templates'),
    autoescape=select_autoescape(['html', 'xml']))

#returns json data from API for Houston , TX based on City ID
response = requests.get(
    'https://api.openweathermap.org/data/2.5/weather?units=imperial&id=4699066&APPID=1e1e9213cbe1601262c8d3628ed8fc3c'
).json()
print(response)


class TemplateHandler(tornado.web.RequestHandler):
    def render_template(self, tpl, context):
        template = ENV.get_template(tpl)
        self.write(template.render(**context))


class RequestHandler(TemplateHandler):
    def get(self):
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')

        context = {}

        self.render_template("request.html", context)


class ResultHandler(TemplateHandler):
    #Why do we need both of these again?
    def get(self):
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template("result.html", {})

    def post(self):
        city = self.get_body_argument('city')
        #I think I need to make a function to run here to input the city info
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template("result.html", {})


def make_app():
    return tornado.web.Application(
        [
            #home page
            (r"/", RequestHandler),
            (r"/page2", ResultHandler),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {
                'path': 'static'
            }),
        ],
        autoreload=True)


if __name__ == "__main__":
    tornado.log.enable_pretty_logging()
    app = make_app()
    PORT = int(os.environ.get('PORT', '8888'))
    app.listen(PORT)
    tornado.ioloop.IOLoop.current().start()
