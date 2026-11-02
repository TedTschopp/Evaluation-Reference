"""Per-session cancellable jobs; at most two run in this Streamlit process."""
import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass,field
from eval_lab.engine import execute_run
from eval_lab.providers import safe_error

POOL=ThreadPoolExecutor(max_workers=2,thread_name_prefix="eval-lab")
SLOTS=threading.BoundedSemaphore(2)

@dataclass
class Job:
    events: queue.Queue=field(default_factory=lambda:queue.Queue(maxsize=1000))
    done: threading.Event=field(default_factory=threading.Event)
    cancelled: threading.Event=field(default_factory=threading.Event)
    loop: object=None
    task: object=None
    bundle: object=None
    error: str|None=None
    def cancel(self):
        self.cancelled.set()
        if self.loop and self.task:
            self.loop.call_soon_threadsafe(self.task.cancel)

def start_job(request):
    if not SLOTS.acquire(blocking=False):
        raise ValueError("Both local evaluation slots are busy. Try again shortly.")
    job=Job()
    def worker():
        async def run():
            job.loop=asyncio.get_running_loop()
            job.task=asyncio.current_task()
            if job.cancelled.is_set():
                raise asyncio.CancelledError()
            async with asyncio.timeout(300):
                job.bundle=await execute_run(request,hosted=False,emit=job.events.put_nowait)
        try:
            asyncio.run(run())
        except asyncio.CancelledError:
            job.error="Run stopped. Incomplete results do not establish release eligibility."
        except Exception as error:
            job.error=safe_error(error)
        finally:
            job.done.set()
            SLOTS.release()
    POOL.submit(worker)
    return job

