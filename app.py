#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys
reload( sys )

sys.setdefaultencoding('gbk')


import os
import json
import base64
import ConfigParser
import datetime
from urlparse import urljoin

from flask import *
from sqlalchemy import and_

from models import *
# from lib.base import RabbitMQ, Elasticsearch
from lib.common import retrive_content
from lib.filter import omit_long_filter

app = Flask(__name__)


def init_app_service():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(base_dir, 'config.ini')
    config = ConfigParser.ConfigParser()
    config.read(config_path)

    init_db(app, config)
    # init_mq(app, config)
    # init_es(app, config)

    app.jinja_env.filters['omit_long'] = omit_long_filter
    app.secret_key = os.urandom(24)
    db.init_app(app)
    db.create_all(app=app)


def init_db(app, config):
    db_config = {
        'host': config.get('database', 'host'),
        'port': config.getint('database', 'port'),
        'username': config.get('database', 'username'),
        'password': config.get('database', 'password'),
        'database': config.get('database', 'database')
    }
    database = 'mysql://%(username)s:%(password)s@%(host)s:%(port)d/%(database)s' % db_config
    app.config['SQLALCHEMY_DATABASE_URI'] = database
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# def init_mq(app, config):
#     mq_config = {
#         'host': config.get('rabbitmq', 'host'),
#         'port': config.getint('rabbitmq', 'port'),
#         'username': config.get('rabbitmq', 'username'),
#         'password': config.get('rabbitmq', 'password'),
#         'queue': config.get('rabbitmq', 'queue')
#     }
#     app.config['RABBITMQ_CONFIG'] = mq_config


# def init_es(app, config):
#     es_config = {
#         'host': config.get('elasticsearch', 'host'),
#         'port': config.getint('elasticsearch', 'port'),
#         'doc_type': config.get('elasticsearch', 'doc_type'),
#         'index_case_unchecked': config.get('elasticsearch', 'index_case_unchecked'),
#         'index_case_valuable': config.get('elasticsearch', 'index_case_valuable'),
#         'index_crash': config.get('elasticsearch', 'index_crash')
#     }
#     app.config['ELASTICSEARCH_CONFIG'] = es_config


# def republish_unchecked_cases():
#     mq_config = app.config['RABBITMQ_CONFIG']
#     es_config = app.config['ELASTICSEARCH_CONFIG']
#     mq = RabbitMQ(**mq_config)
#     es = Elasticsearch(**es_config)
#     case_docs_unchecked = es.get_all_docs(es.CASE_UNCHECKED)
#     for case_doc in case_docs_unchecked:
#         case_msg = json.dumps({
#             'host_id': case_doc['host_id'],
#             'crash_id': case_doc['crash_id'],
#             'case_url': case_doc['case_url'],
#             'created_at': case_doc['created_at']
#         })
#         mq.publish(case_msg)
#     mq.close()


# def get_mq():
#     mq = getattr(g, '_rabbitmq', None)
#     if mq is None:
#         config = app.config['RABBITMQ_CONFIG']
#         mq = g._rabbitmq = RabbitMQ(**config)
#     return mq


# def get_es():
#     es = getattr(g, '_elasticsearch', None)
#     if es is None:
#         config = app.config['ELASTICSEARCH_CONFIG']
#         es = g._elasticsearch = Elasticsearch(**config)
#     return es


# @app.teardown_appcontext
# def close_connection(exception):
#     mq = getattr(g, '_rabbitmq', None)
#     if mq is not None:
#         mq.close()


@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    def date_before(days):
        return datetime.date.today() - datetime.timedelta(days=days)

    labels = []
    datas = []
    for days in xrange(6, -1, -1):
        date = date_before(days)
        labels.append(date.strftime('%m/%d'))
        count = Crash.query.filter(and_(Crash.status == CRASH_POSITIVE, db.func.date(Crash.created_at) == date)).count()
        datas.append(count)

    sum_worker = Worker.query.count()
    sum_proc = Worker.query.with_entities(db.func.sum(Worker.proc_count)).one()[0] or 0
    sum_crash = Crash.query.filter(Crash.status == CRASH_POSITIVE).count()
    sum_case = Worker.query.with_entities(db.func.sum(Worker.case_count)).one()[0] or 0

    if request.args.get('format') == 'json':
        return jsonify({
            'chart': {'labels': labels, 'datas': datas},
            'sum_worker': int(sum_worker),
            'sum_proc': int(sum_proc),
            'sum_crash': int(sum_crash),
            'sum_case': int(sum_case)
        }), 200
    else:
        return render_template('dashboard.html',
                               sum_worker=sum_worker,
                               sum_proc=sum_proc,
                               sum_crash=sum_crash,
                               sum_case=sum_case,
                               chart_labels=json.dumps(labels),
                               chart_datas=json.dumps(datas))


@app.route('/resources')
def resources():
    resources = Resource.query.all()

    if request.args.get('format') == 'json':
        return jsonify({  # 这个就是按照json的格式标准化
            resource.host.id: {
                'cpu_count': resource.cpu_count,
                'cpu_usage': resource.cpu_usage,
                'mem_usage': resource.mem_usage,
                'disk_usage': resource.disk_usage,
                'updated_at': resource.updated_at.ctime(),

            } for resource in resources
        }), 200
    else:
        return render_template('resources.html', resources=resources)


@app.route('/resources/<uuid:uuid>', methods=['POST'])
def resource_of_worker(uuid):
    host_id = str(uuid)
    worker = Worker.query.get_or_404(host_id)
    resource = worker.resource

    if not resource:
        resource = Resource(worker=worker,
                            cpu_count=request.form['cpu_count'],
                            cpu_usage=request.form['cpu_usage'],
                            mem_usage=request.form['mem_usage'],
                            disk_usage=request.form['disk_usage'])
        db.session.add(resource)
        db.session.commit()
        return 'success', 200
    else:
        resource.cpu_count = int(request.form['cpu_count'])
        resource.cpu_usage = float(request.form['cpu_usage'])
        resource.mem_usage = float(request.form['mem_usage'])
        resource.disk_usage = float(request.form['disk_usage'])
        db.session.commit()
        return 'success', 200


@app.route('/workers')
def workers():
    now = datetime.datetime.now()
    time_alive = datetime.timedelta(hours=1)

    workers = [{
        'id': worker.id,
        'ip': worker.ip,
        'proc_count': worker.proc_count,
        'crash_count': worker.crashes.filter(Crash.status == CRASH_POSITIVE).count(),
        'is_alive': worker.status == 1 and (now - worker.resource.updated_at) <= time_alive,
        'runtime': now - worker.started_at,
        'started_at': worker.started_at.ctime(),
        'updated_at': worker.resource.updated_at.ctime(),
    } for worker in Worker.query.all()]

    print(workers)
    return render_template('workers.html', workers=workers)


@app.route('/workers/<uuid:uuid>', methods=['GET', 'POST'])
def worker_control(uuid):
    if request.method == 'GET':
        host_id = str(uuid)
        worker = Worker.query.get_or_404(host_id)

        if request.args['action'] == 'run':
            worker.started_at = datetime.datetime.now()
            worker.status = WORKER_RUN
            flash('start fuzzers on %s, the worker will receive command soon.' % worker.ip)
            db.session.commit()
            return redirect(url_for('workers'))
        elif request.args['action'] == 'stop':
            worker.status = WORKER_STOP
            flash('stop fuzzers on %s, the worker will receive command soon.' % worker.ip)
            db.session.commit()
            return redirect(url_for('workers'))
        elif request.args['action'] == 'query_status':
            if worker.status == WORKER_RUN:
                return 'running', 200
            elif worker.status == WORKER_STOP:
                return 'stopped', 200
        else:
            abort(400)

    elif request.method == 'POST':
        host_id = str(uuid)
        worker = Worker.query.get(host_id)
        bind_port = int(request.form['bind_port'])
        proc_count = int(request.form['proc_count'])
        log_path = request.form['log_path']

        if not worker:
            worker = Worker(host_id, request.remote_addr, bind_port, proc_count, log_path)
            db.session.add(worker)
            app.logger.info('register %s' % request.remote_addr)
            db.session.commit()
            return 'success', 200
        else:
            worker.ip = request.remote_addr
            worker.bind_port = bind_port
            worker.proc_count = proc_count
            worker.log_path = log_path
            worker.status = WORKER_RUN
            db.session.commit()
            return 'success', 200


@app.route('/crashes')
def crashes():
    page = request.args.get('page', 1, int)
    pagination = Crash.query.filter(Crash.status == CRASH_POSITIVE).order_by(Crash.created_at.desc()).paginate(page,
                                                                                                               per_page=20)
    crashes = pagination.items
    return render_template('crashes.html',
                           crashes=crashes,
                           page=page,
                           pages=pagination.pages)


@app.route('/crashes/<uuid:uuid>', methods=['GET', 'POST'])
def crashes_of_worker(uuid):
    if request.method == 'GET':
        host_id = str(uuid)
        worker = Worker.query.get_or_404(host_id)
        page = request.args.get('page', 1, int)
        pagination = worker.crashes.filter(Crash.status == CRASH_POSITIVE).order_by(Crash.created_at.desc()).paginate(
            page, per_page=20)
        crashes = pagination.items
        return render_template('crashes_of_worker.html',
                               worker=worker,
                               crashes=crashes,
                               page=page,
                               pages=pagination.pages)

    elif request.method == 'POST':
        host_id = str(uuid)
        worker = Worker.query.get_or_404(host_id)

        new_case = request.form.get('new_case', 0, int)
        if new_case > 0:
            worker.case_count += new_case
            db.session.commit()

        crash_path = request.form.get('crash_path')
        case_path = request.form.get('case_path')
        if crash_path and case_path:
            crash = Crash(worker=worker,
                          crash_path=crash_path,
                          case_path=case_path)
            worker.crashes.append(crash)
            db.session.commit()
            app.logger.info('%s upload crash %s' % (worker.ip, crash.crash_name))

            backend_url = request.host_url
            backend_case_path = url_for('crash_detail', uuid=worker.id, crash_id=crash.id, type='case', format='html')
            case_url = urljoin(backend_url, backend_case_path)

            # case_content = retrive_content(case_url)
            # case_doc = {
            #     'crash_id': crash.id,
            #     'host_id': host_id,
            #     'host_ip': worker.ip,
            #     'case_url': case_url,
            #     'case_content': case_content,
            #     'created_at': crash.created_at
            # }
            # es = get_es()
            # es.update_or_create(es.CASE_UNCHECKED, case_doc, host_id=host_id, crash_id=crash.id)

            # case_msg = json.dumps({
            #     'host_id': worker.id,
            #     'crash_id': crash.id,
            #     'case_url': case_url,
            #     'created_at': datetime.datetime.now().isoformat()
            # })
            # mq = get_mq()
            # mq.publish(case_msg)
            app.logger.info('case %s published' % case_url)
            return 'success', 200

        elif new_case > 0:
            return 'success', 200
        else:
            abort(400)


@app.route('/crashes/<uuid:uuid>/<int:crash_id>', methods=['GET', 'POST'])
def crash_detail(uuid, crash_id):
    if request.method == 'GET':
        host_id = str(uuid)
        worker = Worker.query.get_or_404(host_id)
        crash = worker.crashes.filter_by(id=crash_id).one()

        if request.args['type'] == 'crash':
            # es = get_es()
            # crash_doc = es.get_doc(es.CRASH, host_id=host_id, crash_id=crash.id)

            # if crash_doc:
            #     crash_log = crash_doc['checker_crash_log']
            # else:
            #     worker_crash_log_url = urljoin('http://%s:%d/' % (worker.ip, worker.bind_port), crash.crash_path)
            #     crash_log = retrive_content(worker_crash_log_url)
            crash_log = 'NO CONTENT'  # for testing

            response = make_response(crash_log)
            response.headers['Content-Type'] = 'text/plain'
            return response

        elif request.args['type'] == 'case':
            # es = get_es()
            # case_doc = es.get_doc(es.CASE_UNCHECKED, host_id=host_id, crash_id=crash.id)
            # if not case_doc:
            #     case_doc = es.get_doc(es.CASE_VALUABLE, host_id=host_id, crash_id=crash.id)

            # if case_doc:
            #     case_content = case_doc['case_content']
            # else:
            #     worker_case_url = urljoin('http://%s:%d/' % (worker.ip, worker.bind_port), crash.case_path)
            #     case_content = retrive_content(worker_case_url)
            case_content = 'NO CONTENT'  # for testing

            if request.args.get('format') == 'html':
                response = make_response(case_content)
                response.headers['Content-Type'] = 'text/html'
                return response
            else:
                response = make_response(case_content)
                response.headers['Content-Type'] = 'text/plain'
                return response
        else:
            abort(400)

    elif request.method == 'POST':
        host_id = str(uuid)
        worker = Worker.query.get_or_404(host_id)
        crash = worker.crashes.filter_by(id=crash_id).one()

        if request.form['status'] == 'positive':
            crash.status = CRASH_POSITIVE
            db.session.commit()

            # es = get_es()
            # es.copy(es.CASE_UNCHECKED, es.CASE_VALUABLE, host_id=host_id, crash_id=crash.id)
            # es.delete(es.CASE_UNCHECKED, host_id=host_id, crash_id=crash.id)

            # backend_url = request.host_url
            # backend_case_path = url_for('crash_detail', uuid=worker.id, crash_id=crash.id, type='case', format='html')
            # case_url = urljoin(backend_url, backend_case_path)
            # worker_crash_log_url = urljoin('http://%s:%d/' % (worker.ip, worker.bind_port), crash.crash_path)
            # checker_crash_log = base64.b64decode(request.form['output'])
            # crash_doc = {
            #     'crash_id': crash.id,
            #     'host_id': host_id,
            #     'host_ip': worker.ip,
            #     'case_url': case_url,
            #     'worker_crash_log_url': worker_crash_log_url,
            #     'checker_crash_log': checker_crash_log,
            #     'created_at': crash.created_at
            # }
            # es.update_or_create(es.CRASH, crash_doc, host_id=host_id, crash_id=crash.id)
            return 'success', 200

        elif request.form['status'] == 'negative':
            crash.status = CRASH_NEGATIVE
            db.session.commit()
            # es = get_es()
            # es.delete(es.CASE_UNCHECKED, host_id=host_id, crash_id=crash.id)
            return 'success', 200
        else:
            abort(400)


@app.route('/logs')
def logs():
    workers = Worker.query.order_by(Worker.ip).all()
    return render_template('logs.html', workers=workers)


@app.route('/logs/<uuid:uuid>')
def log_detail(uuid):
    host_id = str(uuid)
    worker = Worker.query.get_or_404(host_id)
    log_url = urljoin('http://%s:%d/' % (worker.ip, worker.bind_port), worker.log_path)
    content = retrive_content(log_url)
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    return response


@app.route('/passive_corpus')
def passive_corpus():
    count = IokitOpen.query  # total
    print (count)

    # def date_before(days):
    #     return datetime.date.today() - datetime.timedelta(days=days)

    # labels = []
    # datas = []
    # for days in xrange(15, -1, -1):#原值为6
    #     date = date_before(days)
    #     labels.append(date.strftime('%m/%d'))
    #
    #     count1=iokit_open
    #     count = Crash.query.filter(and_(Crash.status == CRASH_POSITIVE, db.func.date(Crash.created_at) == date)).count()
    #     datas.append(count)
    #
    # sum_worker = Worker.query.count()
    # sum_proc = Worker.query.with_entities(db.func.sum(Worker.proc_count)).one()[0] or 0
    # sum_crash = Crash.query.filter(Crash.status == CRASH_POSITIVE).count()
    # sum_case = Worker.query.with_entities(db.func.sum(Worker.case_count)).one()[0] or 0
    #
    # if request.args.get('format') == 'json':
    #     return jsonify({
    #         'chart': {'labels': labels, 'datas': datas},
    #         'sum_worker': int(sum_worker),
    #         'sum_proc': int(sum_proc),
    #         'sum_crash': int(sum_crash),
    #         'sum_case': int(sum_case)
    #     }), 200
    #
    # else:
    #     return render_template('passive_corpus.html',
    #                            sum_worker=sum_worker,
    #                            sum_proc=sum_proc,
    #                            sum_crash=sum_crash,
    #                            sum_case=sum_case,
    #                            chart_labels=json.dumps(labels),
    #                            chart_datas=json.dumps(datas))


@app.route('/iokit_open')
def iokit_open():
    def date_before(days):
        return datetime.date.today() - datetime.timedelta(days=days)

    def get_info_by_date(date):
        total_count = IokitOpen.query.filter(db.cast(IokitOpen.submit_time, db.DATE) <= date).count()
        day_count = IokitOpen.query.filter(db.cast(IokitOpen.submit_time, db.DATE) == date).count()
        total_service_name = IokitOpen.query.group_by(IokitOpen.service_name).count()
        total_class_name = IokitOpen.query.group_by(IokitOpen.class_name).count()
        return total_count, day_count, total_service_name, total_class_name

    labels = []
    datas = []
    for days in xrange(6, -1, -1):
        date = date_before(days)
        labels.append(date.strftime('%m/%d'))
        # count = Crash.query.filter(and_(Crash.status == CRASH_POSITIVE, db.func.date(Crash.created_at) == date)).count()
        datas.append(get_info_by_date(date))
    for i in range(7):
        print(labels[i])
        print(datas[i])
    return render_template('iokit_open.html')


init_app_service()
# republish_unchecked_cases()

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=8080, debug=True)
