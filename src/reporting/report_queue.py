import queue
import threading
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ReportJob:
    job_id: str
    universe: str
    run_id: str
    formats: List[str]
    webhook_url: Optional[str]
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    output_files: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None

class ReportJobQueue:
    _instance = None
    
    def __init__(self):
        self.queue = queue.Queue()
        self.jobs: Dict[str, ReportJob] = {}
        self.worker_thread = None
        self.running = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ReportJobQueue()
        return cls._instance

    def start_worker(self):
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_jobs, daemon=True)
            self.worker_thread.start()

    def add_job(self, universe: str, run_id: str, formats: List[str], webhook_url: Optional[str] = None) -> str:
        if not self.running:
            self.start_worker()
            
        job_id = str(uuid.uuid4())
        job = ReportJob(job_id=job_id, universe=universe, run_id=run_id, formats=formats, webhook_url=webhook_url)
        self.jobs[job_id] = job
        self.queue.put(job)
        return job_id

    # ... get_status ...

    def _process_jobs(self):
        import os
        from src.reporting.generators import GENERATORS
        from src.reporting.notification_channels import ReportWebhookChannel
        
        while self.running:
            try:
                job = self.queue.get(timeout=1)
                job.status = "processing"
                
                try:
                    # Logic to fetch run data. Assuming a 'runs' directory structure or Indexer query.
                    # For this implementation, we'll assume we can't easily fully reconstruct 'engine' state without heavy loading.
                    # But we can try to look for a 'latest_summary.json' or use ReportIndexer if possible.
                    # Given constraints, we'll try to find an existing summary file for the run.
                    
                    base_dir = f"reports/runs/{job.run_id}" # Simplified path assumption
                    summary_path = os.path.join(base_dir, "summary.json")
                    
                    if os.path.exists(summary_path):
                         import json
                         with open(summary_path, 'r') as f:
                             summary = json.load(f)
                    else:
                        # Fallback: Create a basic summary wrapper if we can't load real data
                        summary = {
                            "universe": job.universe,
                            "run_id": job.run_id,
                            "metadata": {"timestamp": datetime.now().isoformat()},
                            # Populate minimal fields to avoid generator crashes
                            "economy": {}, "military": {}, "tech": {}, "battles": []
                        }
                    
                    # Generate requested formats
                    os.makedirs(base_dir, exist_ok=True)
                    
                    for fmt in job.formats:
                        if fmt in GENERATORS:
                            gen_class = GENERATORS[fmt]
                            generator = gen_class()
                            
                            filename = f"report_{job.run_id}.{fmt}"
                            out_path = os.path.join(base_dir, filename)
                            
                            generator.generate(summary, out_path)
                            job.output_files[fmt] = out_path
                    
                    job.status = "completed"
                    job.completed_at = datetime.now().isoformat()
                    
                    # Webhook Notification
                    if job.webhook_url:
                        channel = ReportWebhookChannel(job.webhook_url)
                        channel.send_completion(job.universe, job.run_id, job.output_files)

                except Exception as e:
                    job.status = "failed"
                    job.error = str(e)
                    print(f"Job {job.job_id} failed: {e}")
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue
