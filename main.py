import tornado.web
import tornado.ioloop
import json
import asyncmongo
import time
from collections import defaultdict
import os
import os.path
from functools import partial
from datetime import datetime

class StatisticsViewer(tornado.web.RequestHandler):
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
            raise tornado.web.HTTPError(500)

        current_time = int(time.time())
        values = defaultdict(int)


        for row in response:
            ts = row['ts'] - current_time
            ts = int(ts / 60.0)
            values[ts] += row['count']
        values = sorted([(key, value) for key, value in values.iteritems()], reverse=True)

        name = row['name']

        self.render('template.html', name=name, values=values)

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
        jc = {'name': counter_name,
              'first_seen': time.time(),
              'last_seen': time.time(),
              'count': 1}
        self.db.counterlist.find_one({'name': counter_name}, callback=partial(self._on_name_search, jc))


    @tornado.web.asynchronous
    def post(self):
        jc = None
        temp = self.request.body

        if temp is not None:
            jc = json.loads(temp)

        if not jc:
            self.finish()
            return

        if 'meta' in jc and jc['meta']['type'] == 'exception':
            meta = jc['meta']
            exception_hash = "%s-%s-%d" % (
                    meta['name'],
                    meta['value'],
                    meta['lineno'])
            exception_hash = exception_hash.lower().replace(' ', '')

            query = {
                'name': jc['name'],
                'exception_hash': exception_hash,
            }

            self.db.counterlist.find_one(
                    query,
                    callback=partial(self._on_exception_search, jc))
        else:
            self.db.counterlist.find_one({'name': jc['name']},
                    callback=partial(self._on_name_search, jc))

    def _on_exception_search(self, jc, response, error):
        meta = jc['meta']
        exception_hash = "%s-%s-%d" % (
                meta['name'],
                meta['value'],
                meta['lineno'])
        exception_hash = exception_hash.lower().replace(' ', '')

        if not response:

            to_insert = {
                    'name': jc['name'],
                    'count': 1,
                    'last_seen': time.time(),
                    'first_seen': time.time(),
                    'meta': meta,
                    'exception_hash': exception_hash,
            }
            self.db.counterlist.insert(
                    to_insert,
                    callback=lambda response, error=None: None)

        else:
            query = {
                'name': jc['name'],
                'exception_hash': exception_hash,
            }

            operation = {'$inc': {'count': 1}, '$set': {'last_seen': time.time()}}

            self.db.counterlist.update(
                    query,
                    operation,
                    callback=lambda response, error=None: None)

        count_value_insert = {
                'name': jc['name'],
                'ts': time.time(),
                'count': jc['count'] if 'count' in jc else 1
        }
        self.db.counters.insert(count_value_insert, callback=self._on_post)

    def _on_name_search(self, jc, response, error):
        if not response:
            to_insert = {
                    'name': jc['name'],
                    'count': 1,
                    'last_seen': time.time(),
                    'first_seen': time.time(),
                    'meta': jc['meta'] if 'meta' in jc else None
            }

            self.db.counterlist.insert(
                    to_insert,
                    callback=lambda response, error=None: None)

        else:
            query = {'name': jc['name']}
            # increase the count and update the 'last seen' time
            operation = {'$inc': {'count': 1}, '$set': {'last_seen': time.time()}}
            self.db.counterlist.update(
                    query,
                    operation,
                    callback=lambda response, error=None: None)

        count_value_insert = {
                'name': jc['name'],
                'ts': time.time(),
                'count': jc['count'] if 'count' in jc else 1
        }

        self.db.counters.insert(count_value_insert, callback=self._on_post)

    def _on_post(self, response, error):
        if error:
            raise tornado.web.HTTPError(500)
        self.finish()

class CounterList(tornado.web.RequestHandler):
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
    def get(self):
        self.db.counterlist.find({}, callback=self._on_get)

    def _on_get(self, response, error):
        if error:
            raise tornado.web.HTTPError(500)

        result = []
        for row in response:
            row['first_seen'] = datetime.fromtimestamp(row['first_seen']).strftime("%Y-%m-%d %H:%M")
            row['last_seen'] = datetime.fromtimestamp(row['last_seen']).strftime("%Y-%m-%d %H:%M")
            result.append(row)
        self.render('view_template.html', values=result)


if __name__ == '__main__':
    settings = {
            'debug': True,
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    }

    routes = [
        (r"/list", CounterList),
        (r"/view/([\.,\w]+)", StatisticsViewer),
        (r"/add", StatisticsRecorder),
        (r'/inc/([\.,\w]+)', StatisticsRecorder),
    ]


    application = tornado.web.Application( routes, **settings)
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
