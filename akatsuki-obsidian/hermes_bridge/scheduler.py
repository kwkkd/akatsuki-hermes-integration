import json
import logging
import time
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("akatsuki.scheduler")

SCHEDULE_STORE = ""

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    AsyncIOScheduler = object


class OperationScheduler:
    def __init__(self, store_path: str = ""):
        self._store_path = Path(store_path or Path(__file__).resolve().parent.parent.parent / "data" / "schedules.json")
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, dict] = {}
        self._scheduler = AsyncIOScheduler() if HAS_APSCHEDULER else None
        self._executor: Optional[Callable] = None
        self._load_jobs()

    def set_executor(self, fn: Callable):
        self._executor = fn

    def _load_jobs(self):
        if self._store_path.exists():
            try:
                self._jobs = json.loads(self._store_path.read_text())
            except Exception:
                self._jobs = {}

    def _save_jobs(self):
        self._store_path.write_text(json.dumps(self._jobs, indent=2))

    def add_job(self, job_id: str, playbook: str, target: str,
                cron: str, objective: str = "") -> dict:
        self._jobs[job_id] = {
            "id": job_id,
            "playbook": playbook,
            "target": target,
            "cron": cron,
            "objective": objective or f"Auto: {playbook} on {target}",
            "enabled": True,
            "created": int(time.time()),
            "last_run": 0,
            "last_status": "",
        }
        self._save_jobs()
        if self._scheduler and HAS_APSCHEDULER:
            try:
                trigger = CronTrigger.from_crontab(cron)
                self._scheduler.add_job(
                    self._run_job,
                    trigger,
                    args=[job_id],
                    id=job_id,
                    replace_existing=True,
                )
            except Exception as e:
                logger.warning(f"Failed to schedule job {job_id}: {e}")
        return self._jobs[job_id]

    def _run_job(self, job_id: str):
        job = self._jobs.get(job_id)
        if not job or not job.get("enabled"):
            return
        logger.info(f"Running scheduled job: {job_id}")
        if self._executor:
            try:
                result = self._executor(
                    target=job["target"],
                    playbook=job["playbook"],
                    objective=job.get("objective", ""),
                )
                job["last_status"] = "success"
                job["last_result"] = str(result)[:500]
            except Exception as e:
                job["last_status"] = "failed"
                job["last_error"] = str(e)
                logger.error(f"Scheduled job {job_id} failed: {e}")
        job["last_run"] = int(time.time())
        self._save_jobs()

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._save_jobs()
            if self._scheduler:
                self._scheduler.remove_job(job_id)
            return True
        return False

    def pause_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            self._jobs[job_id]["enabled"] = False
            self._save_jobs()
            if self._scheduler:
                self._scheduler.pause_job(job_id)
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            self._jobs[job_id]["enabled"] = True
            self._save_jobs()
            if self._scheduler:
                self._scheduler.resume_job(job_id)
            return True
        return False

    def list_jobs(self) -> list[dict]:
        return list(self._jobs.values())

    def get_job(self, job_id: str) -> Optional[dict]:
        return self._jobs.get(job_id)

    def start(self):
        if self._scheduler:
            self._scheduler.start()
            logger.info(f"Scheduler started with {len(self._jobs)} jobs")

    def stop(self):
        if self._scheduler:
            self._scheduler.shutdown()
            logger.info("Scheduler stopped")


scheduler = OperationScheduler()


def get_scheduler() -> OperationScheduler:
    return scheduler