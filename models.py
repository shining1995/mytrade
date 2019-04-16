import os
import datetime
from tradetools.FoundationHelper import get_jingzhi

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

WORKER_STOP = 0
WORKER_RUN = 1

CRASH_UNCHECKED = 0
CRASH_NEGATIVE = 1
CRASH_POSITIVE = 2


class Worker(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    ip = db.Column(db.String(15))
    bind_port = db.Column(db.Integer)
    proc_count = db.Column(db.Integer)
    case_count = db.Column(db.Integer, default=0)
    log_path = db.Column(db.String(4096))
    status = db.Column(db.Integer)
    started_at = db.Column(db.DateTime)
    resource = db.relationship('Resource', backref='host', uselist=False)
    crashes = db.relationship('Crash', backref='host', lazy='dynamic')

    def __init__(self, id=None, ip=None, bind_port=None, proc_count=None, log_path=None, status=WORKER_RUN):
        self.id = id
        self.ip = ip
        self.bind_port = bind_port
        self.proc_count = proc_count
        self.log_path = log_path
        self.status = status
        self.started_at = datetime.datetime.now()

    def __repr__(self):
        return '<Worker %r>' % self.ip


class Resource(db.Model):
    id = db.Column(db.Integer, autoincrement='auto', primary_key=True)
    host_id = db.Column(db.String(36), db.ForeignKey('worker.id'))
    cpu_count = db.Column(db.Integer)
    cpu_usage = db.Column(db.Float)
    mem_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __init__(self, worker=None, cpu_count=None, cpu_usage=None, mem_usage=None, disk_usage=None):
        self.host = worker
        self.cpu_count = cpu_count
        self.cpu_usage = cpu_usage
        self.mem_usage = mem_usage
        self.disk_usage = disk_usage
        self.updated_at = datetime.datetime.now()

    def __repr__(self):
        return '<Resource %r>' % self.ip


class Crash(db.Model):
    id = db.Column(db.Integer, autoincrement='auto', primary_key=True)
    host_id = db.Column(db.String(36), db.ForeignKey('worker.id'))
    crash_path = db.Column(db.String(4096))
    crash_name = db.Column(db.String(255))
    case_path = db.Column(db.String(4096))
    case_name = db.Column(db.String(255))
    status = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)

    def __init__(self, worker=None, crash_path=None, case_path=None, status=CRASH_UNCHECKED):
        self.host = worker
        self.crash_path = crash_path
        self.crash_name = os.path.basename(self.crash_path)
        self.case_path = case_path
        self.case_name = os.path.basename(self.case_path)
        self.status = status
        self.created_at = datetime.datetime.now()

    def __repr__(self):
        return '<Crash %r>' % self.ip


class IokitOpen(db.Model):
    id = db.Column(db.Integer, autoincrement='auto', primary_key=True)
    service_name = db.Column(db.String(255))
    type = db.Column(db.Integer)
    class_name = db.Column(db.String(255))
    xnu_version_start = db.Column(db.Integer)
    submit_time = db.Column(db.DateTime)
    verify_open = db.Column(db.String(255))

    def __init__(self, service_name=None, type=None, class_name=None, xnu_version_start=None):
        self.service_name = service_name
        self.type = type
        self.class_name = class_name
        self.xnu_version_start = xnu_version_start
        self.submit_time = datetime.datetime.now()

    def __repr__(self):
        return '<IokitOpen %r>' % self.id


class IokitConnect(db.Model):
    id = db.Column(db.Integer, autoincrement='auto', primary_key=True)
    class_name = db.Column(db.String(255))
    selector = db.Column(db.Integer)

    scalar_input_count = db.Column(db.Integer)
    scalar_output_count = db.Column(db.Integer)
    struct_input_size = db.Column(db.Integer)
    struct_output_size = db.Column(db.Integer)

    ool_input_size = db.Column(db.Integer)
    ool_output_size = db.Column(db.Integer)
    md5_no_content = db.Column(db.String(255))
    xnu_version_start = db.Column(db.Integer)
    xnu_version_end = db.Column(db.Integer)

    submit_time = db.Column(db.DateTime)
    most_success = db.Column(db.String(255))
    fuzzing_round = db.Column(db.Integer)
    fuzzing_success_rate = db.Column(db.Float)

    def __init__(self, class_name=None, selector=None, scalar_input_count=None, scalar_output_count=None,
                 struct_input_size=None, struct_output_size=None,
                 ool_input_size=None, ool_output_size=None, md5_no_content=None, xnu_version_start=None,
                 xun_version_end=None, most_success=None, fuzzing_round=None, fuzzing_success_rate=None):
        self.class_name = class_name
        self.selector = selector
        self.scalar_input_count = scalar_input_count
        self.scalar_output_count = scalar_output_count
        self.struct_input_size = struct_input_size
        self.struct_output_size = struct_output_size
        self.ool_input_size = ool_input_size
        self.ool_output_size = ool_output_size
        self.md5_no_content = md5_no_content
        self.xnu_version_start = xnu_version_start
        self.xun_version_end = xun_version_end
        self.most_success = most_success
        self.fuzzing_round = fuzzing_round
        self.fuzzing_success_rate = fuzzing_success_rate
        self.submit_time = datetime.datetime.now()

    def __repr__(self):
        return '<IokitConnect %r>' % self.id


######################
class Record(db.Model):
    id = db.Column(db.Integer, autoincrement='auto', primary_key=True)
    base = db.Column(db.Float)
    beishu = db.Column(db.Float)
    code = db.Column(db.String(255))
    buy_date = db.Column(db.DateTime)
    follow = db.Column(db.Float)
    jingzhi = db.Column(db.Float)
    gushu = db.Column(db.Float)

    submit_time = db.Column(db.DateTime)

    def __init__(self, id, date, base, beishu, follow, code):
        self.id = id
        self.base = float(base)
        self.beishu = float(beishu)
        self.code = code
        self.buy_date = date if date else (datetime.date.today()).strftime('%Y-%m-%d')
        self.follow = float(follow) if follow else self.base * float(beishu)
        self.jingzhi = float(get_jingzhi(code, self.buy_date))
        self.gushu = round(float(self.follow) / float(self.jingzhi) if self.jingzhi != -1 else -1, 4)
        self.submit_time = datetime.datetime.now()

    def __repr__(self):
        return '<record %r>' % self.id


