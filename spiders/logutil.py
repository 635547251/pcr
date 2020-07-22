import logging
import logging.handlers
import os
import queue
import time
from threading import Thread

from ..config import log_dir_path, log_encoding, log_level, log_name

format_str = "%(asctime)s|%(levelname)s|%(process)d|%(filename)s:%(lineno)d|%(message)s"

g_stdout_handler = None
g_file_handler = None
g_queue_handler = None


def init_logging(log_q):
    set_log_queue(log_q)
    set_log_stdout(True)
    set_level(log_level)


def set_log_stdout(flag: bool):
    '''
    设置是否打印到标准输出
    '''
    global g_stdout_handler
    root = logging.getLogger()
    if flag is False and g_stdout_handler is not None:
        root.removeHandler(g_stdout_handler)
        g_stdout_handler = None

    if flag is True and g_stdout_handler is None:
        # 注意 QueueHandler必须放在所有Handler之后
        # 原因 QueueHandler 中的 prepare 方法会 将record.messsge日志信息修改为format之后的日志信息
        #      其他Handler放在QueuHandler之后, handler会对record.message再格式化一次，导致日志中存在两个前缀
        # 详见 QueueHandler的prepare的实现
        root.removeHandler(g_queue_handler)

        g_stdout_handler = logging.StreamHandler()
        g_stdout_handler.setFormatter(logging.Formatter(format_str))
        root.addHandler(g_stdout_handler)
        if g_queue_handler:
            root.addHandler(g_queue_handler)


def set_log_queue(q):
    '''
    设置日志队列
    '''
    global g_queue_handler
    root = logging.getLogger()
    if g_queue_handler:
        root.removeHandler(g_queue_handler)
        g_queue_handler = None

    if q:
        g_queue_handler = QueueHandler(q)
        g_queue_handler.setFormatter(logging.Formatter(format_str))
        root.addHandler(g_queue_handler)


def set_level(level: str):
    logging.getLogger().setLevel(level)


def log_process_func(log_queue):
    """
    日志进程主方法
    :param log_queue: 进程共享日志队列
    :return:
    """
    log_path = os.path.join(log_dir_path, log_name)

    th = logging.handlers.TimedRotatingFileHandler(log_path, when='MIDNIGHT', encoding=log_encoding)
    th.setLevel(log_level)
    listener = QueueListener(log_queue, th, respect_handler_level=True)
    listener.start()
    while True:
        time.sleep(2)


class QueueHandler(logging.Handler):
    def __init__(self, queue):
        logging.Handler.__init__(self)
        self.queue = queue

    def enqueue(self, record):
        self.queue.put(record)

    def prepare(self, record):
        msg = self.format(record)
        record.message = msg
        record.msg = msg
        record.args = None
        record.exc_info = None
        return record

    def emit(self, record):
        try:
            self.enqueue(self.prepare(record))
        except Exception as e:
            print(e)
            self.handleError(record)


class QueueListener(object):
    _sentinel = None

    def __init__(self, queue, *handlers, respect_handler_level=False):
        self.queue = queue
        self.handlers = handlers  # handler元组
        self._thread = None
        self.respect_handler_level = respect_handler_level

    # 出列
    def dequeue(self, block):
        return self.queue.get(block)

    def start(self):
        self._thread = t = Thread(target=self._monitor)
        t.daemon = True
        t.start()

    def prepare(self, record):
        return record

    def handle(self, record):
        record = self.prepare(record)  # 取值
        for handler in self.handlers:
            if not self.respect_handler_level:
                process = True
            else:
                process = record.levelno >= handler.level
            if process:
                handler.handle(record)

    def _monitor(self):
        q = self.queue
        has_task_done = hasattr(q, 'task_done')
        while True:
            try:
                record = self.dequeue(True)  # 出列
                if record is self._sentinel:  # 取完直接返回
                    break
                self.handle(record)
                if has_task_done:
                    q.task_done()
            except queue.Empty:
                break

    def enqueue_sentinel(self):
        self.queue.put_nowait(self._sentinel)

    def stop(self):
        self.enqueue_sentinel()
        self._thread.join()
        self._thread = None
