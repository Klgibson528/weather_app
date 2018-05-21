import tornado.ioloop
import tornado.web
import tornado.log
import os
import requests
import json
import datetime
import queries


from jinja2 import \
  Environment, PackageLoader, select_autoescape
ENV = Environment(
    loader=PackageLoader('weather-app', 'templates'),
    autoescape=select_autoescape(['html', 'xml']))

api_key = os.environ.get('API_KEY')


class TemplateHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.session = queries.Session(
            'postgresql://postgres@localhost:5432/weather')

    def render_template(self, tpl, context):
        template = ENV.get_template(tpl)
        self.write(template.render(**context))

# work below here
class RequestHandler(TemplateHandler):
    def get(self):
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')

        context = {}

        self.render_template("request.html", context)

    def get_request(self, response):
        self.response = response


class ResultHandler(TemplateHandler):
    def search(self, city):
        ans = requests.get(
            'https://api.openweathermap.org/data/2.5/weather?units=imperial&q={}&APPID={}'.
            format(city, api_key)).json()
        return ans

    def cache_data(self, result):
        conn = psycopg2.connect("dbname=weather user=postgres")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO weather (city, temp, wind) VALUES (%s, %s, %s)",
            (result['name'], result['main']['temp'], result['wind']['speed']))
        conn.commit()
        cur.close()
        conn.close()


    def get(self):
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template("result.html", {})

    def post(self):
        city = self.get_body_argument('city')
        # self.get_cache(city)
        conn = psycopg2.connect("dbname='weather' user='postgres'")
        cur = conn.cursor()
        data = cur.execute("SELECT city FROM weather")
        conn.commit()
        cur.close()
        conn.close()
        print(data)
        
        result = self.search(city)
        self.cache_data(result)
        print('new')
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template("result.html", {'result': result})


def make_app():
    return tornado.web.Application(
        [
            #home page
            (r"/", RequestHandler),
            (r"/request", ResultHandler),
            (r"/cache", ResultHandler),
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