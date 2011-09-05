import tornado.web
import tornado.ioloop
import json
import asyncmongo
import time
from collections import defaultdict
import os
import os.path

class StatisticsRecorder(tornado.web.RequestHandler):
    @property
    def db(self):
        if not hasattr(self, '_db'):
            self._db = asyncmongo.Client(
                    pool_id='mydb',
                    host='127.0.0.1',
                    port=27017,
                    maxcached=10,
                    maxconnections=50,
                    dbname='calculon')
        return self._db

    @tornado.web.asynchronous
    def get(self, counter_name):
        self.db.counters.find({'name': counter_name}, callback=self._on_get)

    def _on_get(self, response, error):
        if error:
            raise tornado.web.HTTPErorr(500)

        current_time = int(time.time())
        values = defaultdict(int)


        for row in response:
            ts = row['ts'] - current_time
            ts = int(ts / 60.0)
            values[ts] += row['count']
        values = sorted([(key, value) for key, value in values.iteritems()], reverse=True)

        name = row['name']

        self.render('template.html', name=name, values=values)

    @tornado.web.asynchronous
    def post(self):
        jc = None
        temp = self.get_argument("r", None)
        if temp is not None:
            jc = json.loads(temp)

        if not jc:
            return

        jc['ts'] = time.time()
        # by default add 1 tfor every counter, otherwise use whatever is supplied
        if 'count' not  in jc:
            jc['count'] = 1

        self.db.counters.insert(jc, callback=self._on_post)

    def _on_post(self, response, error):
        if error:
            raise tornado.web.HTTPError(500)
        self.finish()

if __name__ == '__main__':
    settings = {
            'debug': True,
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    }

    routes = [
        (r"/([,\w]+)", StatisticsRecorder),
        (r"/", StatisticsRecorder),
    ]


    application = tornado.web.Application( routes, **settings)
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
