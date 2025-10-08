import os
import traceback
import multiprocessing
from typing import Callable, Optional

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot

def process_executor(queue: multiprocessing.Queue, task_id: str, target_func: Callable, *args, **kwargs):
    def progress_emitter(message: str):
        queue.put(('progress', message))

    original_print = print
    def redirected_print(*p_args, **p_kwargs):
        message = " ".join(map(str, p_args))
        progress_emitter(message)
        original_print(*p_args, **p_kwargs)

    __builtins__['print'] = redirected_print

    try:
        progress_emitter(f"进程 {os.getpid()} 已启动，准备执行任务: {task_id}")
        result = target_func(*args, **kwargs)
        queue.put(('finished', (task_id, 'success', result)))
    except Exception as e:
        error_msg = f"子进程任务 '{task_id}' 发生严重错误: {e}\n{traceback.format_exc()}"
        progress_emitter(error_msg)
        queue.put(('finished', (task_id, 'error', error_msg)))

class ProcessWorker(QObject):
    finished = pyqtSignal(str, str, object)
    progress = pyqtSignal(str)

    def __init__(self, task_id: str, target_func: Callable, *args, **kwargs):
        super().__init__()
        self.task_id = task_id
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs
        self.process: Optional[multiprocessing.Process] = None
        self.queue: Optional[multiprocessing.Queue] = None
        self.timer: Optional[QTimer] = None

    def run(self):
        try:
            self.queue = multiprocessing.Queue()
            self.process = multiprocessing.Process(target=process_executor, args=(self.queue, self.task_id, self.target_func, *self.args), kwargs=self.kwargs)
            self.process.start()
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._check_queue)
            self.timer.start(100)
        except Exception as e:
            self.progress.emit(f"启动子进程时失败: {e}")
            self.finished.emit(self.task_id, "error", f"启动子进程失败: {e}")

    @pyqtSlot()
    def _check_queue(self):
        if self.queue is None:
            return
        while not self.queue.empty():
            try:
                signal_type, data = self.queue.get_nowait()
                if signal_type == 'progress':
                    self.progress.emit(data)
                elif signal_type == 'finished':
                    self.finished.emit(data[0], data[1], data[2])
                    self.stop()
                    return
            except Exception:
                pass

        if self.timer and self.process and not self.process.is_alive():
            self.finished.emit(self.task_id, 'error', '子进程意外终止。')
            self.stop()

    def stop(self):
        if self.timer:
            self.timer.stop()
            self.timer = None

        if self.process and self.process.is_alive():
            try:
                self.process.terminate()
                self.process.join(timeout=1)
            except Exception as e:
                self.progress.emit(f"清理子进程时出错: {e}")
        self.process = None

        if self.queue:
            self.queue.close()
            self.queue = None