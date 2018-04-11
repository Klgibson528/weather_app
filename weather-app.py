import tornado.ioloop
import tornado.web
import tornado.log
import os
import requests
import json
import psycopg2


from jinja2 import \
  Environment, PackageLoader, select_autoescape
ENV = Environment(
    loader=PackageLoader('weather-app', 'templates'),
    autoescape=select_autoescape(['html', 'xml']))


def search(city):
    ans = requests.get(
        'https://api.openweathermap.org/data/2.5/weather?units=imperial&q={}&APPID=1e1e9213cbe1601262c8d3628ed8fc3c'.
        format(city)).json()
    return ans


def cache_data(result):
    conn = psycopg2.connect("dbname=weather user=postgres")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO weather (city, temp, wind) VALUES (%s, %s, %s)",
        (result['name'], result['main']['temp'], result['wind']['speed']))
    conn.commit()
    cur.close()
    conn.close()


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

    def get_request(self, response):
        self.response = response


class ResultHandler(TemplateHandler):
    def get(self):
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template("result.html", {})

    def post(self):
        city = self.get_body_argument('city')
        try:
            conn = psycopg2.connect("dbname='weather' user='postgres'")
        except:
            print("I am unable to connect to the database.")

        cur = conn.cursor()
        data = cur.execute("SELECT * FROM weather")

        if city in data:
            try:
                conn = psycopg2.connect("dbname='weather' user='postgres'")
            except:
                print("I am unable to connect to the database.")

            cur = conn.cursor()
            temp = cur.execute(
                "SELECT temp FROM weather WHERE city = '%s'").format(city)
            wind = cur.execute(
                "SELECT wind FROM weather WHERE city = '%s'").format(city)
            results = {'name': city, 'temp': temp, 'speed': wind}
            print('cache')
            self.set_header('Cache-Control',
                            'no-store, no-cache, must-revalidate, max-age=0')
            self.render_template("cache.html", {'result': result})
        else:
            result = search(city)
            cache_data(result)
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
