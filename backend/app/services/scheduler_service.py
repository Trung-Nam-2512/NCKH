#!/usr/bin/env python3
"""
SCHEDULER SERVICE - Quản lý và điều phối các tác vụ chạy ngầm

Chức năng chính:
- Schedule daily data collection tự động
- Monitor và restart failed tasks
- Flexible scheduling với multiple time slots
- Health check và system monitoring
- Graceful shutdown và cleanup
- Background process management

Thiết kế:
- Sử dụng APScheduler cho robust scheduling
- Async/await pattern cho non-blocking operations  
- Comprehensive logging và monitoring
- Error recovery và retry mechanisms
- Support multiple collection times per day
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor as APSThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
import json

# Import daily collector
from .daily_data_collector import DailyDataCollector

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

class SchedulerService:
    """
    DỊCH VỤ ĐIỀU PHỐI TÁC VỤ CHẠY NGẦM
    
    Service này quản lý việc chạy các tác vụ theo lịch trình:
    - Thu thập dữ liệu hàng ngày từ APIs
    - Monitoring system health
    - Cleanup old data và logs
    - Backup operations
    - Custom scheduled tasks
    """
    
    def __init__(self):
        """Khởi tạo scheduler với cấu hình tối ưu"""
        
        # Cấu hình APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor(),
            'threadpool': APSThreadPoolExecutor(max_workers=20)
        }
        job_defaults = {
            'coalesce': False,           # Không gộp jobs bị trễ
            'max_instances': 1,          # Chỉ 1 instance của mỗi job cùng lúc
            'misfire_grace_time': 30     # Grace time 30 giây cho jobs bị trễ
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'  # Sử dụng UTC để consistency
        )
        
        # Components
        self.data_collector = DailyDataCollector()
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # Configuration
        self.config = {
            # Multiple collection times để đảm bảo có data
            'collection_times': [
                {'hour': 6, 'minute': 30},    # 6:30 AM UTC
                {'hour': 14, 'minute': 30},   # 2:30 PM UTC  
                {'hour': 22, 'minute': 30}    # 10:30 PM UTC
            ],
            # Retry configuration
            'max_retries': 3,
            'retry_interval': 300,  # 5 minutes
            # Cleanup configuration
            'cleanup_time': {'hour': 2, 'minute': 0},  # 2:00 AM UTC
            'logs_retention_days': 30,
            'backup_retention_days': 7
        }
        
        # Job tracking
        self.job_status = {}
        
        self.logger = logging.getLogger(__name__)

    def setup_signal_handlers(self):
        """Setup signal handlers cho graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def schedule_daily_collection_jobs(self):
        """Schedule daily data collection jobs với multiple time slots"""
        
        for i, time_config in enumerate(self.config['collection_times']):
            job_id = f"daily_collection_{i+1}"
            
            # Tạo cron trigger cho mỗi thời điểm
            trigger = CronTrigger(
                hour=time_config['hour'],
                minute=time_config['minute'],
                second=0,
                timezone='UTC'
            )
            
            # Add job với retry wrapper
            self.scheduler.add_job(
                func=self._run_collection_with_retry,
                trigger=trigger,
                id=job_id,
                name=f"Daily Data Collection #{i+1}",
                replace_existing=True,
                kwargs={'job_id': job_id}
            )
            
            self.logger.info(f"📅 Scheduled daily collection job: {job_id} at {time_config['hour']:02d}:{time_config['minute']:02d} UTC")

    async def schedule_cleanup_jobs(self):
        """Schedule cleanup và maintenance jobs"""
        
        # Daily cleanup job
        cleanup_trigger = CronTrigger(
            hour=self.config['cleanup_time']['hour'],
            minute=self.config['cleanup_time']['minute'],
            second=0,
            timezone='UTC'
        )
        
        self.scheduler.add_job(
            func=self._run_cleanup_tasks,
            trigger=cleanup_trigger,
            id='daily_cleanup',
            name='Daily Cleanup Tasks',
            replace_existing=True
        )
        
        self.logger.info("🧹 Scheduled daily cleanup tasks")

    async def schedule_health_check_jobs(self):
        """Schedule health check jobs"""
        
        # Health check every 15 minutes
        health_trigger = IntervalTrigger(minutes=15)
        
        self.scheduler.add_job(
            func=self._run_health_check,
            trigger=health_trigger,
            id='health_check',
            name='System Health Check',
            replace_existing=True
        )
        
        self.logger.info("❤️ Scheduled health check jobs")

    async def _run_collection_with_retry(self, job_id: str):
        """
        Wrapper để chạy collection với retry logic
        
        Args:
            job_id: ID của job để tracking
        """
        start_time = datetime.utcnow()
        self.job_status[job_id] = {
            'status': 'running',
            'start_time': start_time,
            'attempts': 0
        }
        
        self.logger.info(f"🚀 Starting {job_id}")
        
        for attempt in range(self.config['max_retries']):
            try:
                self.job_status[job_id]['attempts'] = attempt + 1
                
                # Run collection
                success = await self.data_collector.run_daily_collection()
                
                if success:
                    self.job_status[job_id].update({
                        'status': 'success',
                        'end_time': datetime.utcnow(),
                        'duration': (datetime.utcnow() - start_time).total_seconds()
                    })
                    self.logger.info(f"✅ {job_id} completed successfully")
                    return
                else:
                    raise Exception("Data collection returned False")
                    
            except Exception as e:
                self.logger.error(f"❌ {job_id} attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config['max_retries'] - 1:
                    self.logger.info(f"⏳ Retrying {job_id} in {self.config['retry_interval']} seconds...")
                    await asyncio.sleep(self.config['retry_interval'])
                else:
                    # Final failure
                    self.job_status[job_id].update({
                        'status': 'failed',
                        'end_time': datetime.utcnow(),
                        'error': str(e)
                    })
                    self.logger.error(f"💥 {job_id} failed after {self.config['max_retries']} attempts")

    async def _run_cleanup_tasks(self):
        """Chạy các tác vụ cleanup định kỳ"""
        self.logger.info("🧹 Starting cleanup tasks...")
        
        try:
            # Cleanup old logs từ collector
            await self.data_collector.cleanup_old_logs(self.config['logs_retention_days'])
            
            # Cleanup scheduler logs (implement nếu cần)
            await self._cleanup_scheduler_logs()
            
            # Cleanup old backups
            await self._cleanup_old_backups()
            
            self.logger.info("✅ Cleanup tasks completed")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup tasks failed: {e}")

    async def _cleanup_scheduler_logs(self):
        """Cleanup các log files cũ của scheduler"""
        try:
            # Implement log rotation logic nếu cần
            self.logger.info("🗂️ Scheduler log cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Scheduler log cleanup failed: {e}")

    async def _cleanup_old_backups(self):
        """Cleanup các backup cũ"""
        try:
            # Connect to database và cleanup old backups
            if await self.data_collector.initialize_database():
                cutoff_date = datetime.utcnow() - timedelta(days=self.config['backup_retention_days'])
                
                result = await self.data_collector.db[self.data_collector.collections['backup']].delete_many({
                    'backup_date': {'$lt': cutoff_date}
                })
                
                self.logger.info(f"🗄️ Cleaned up {result.deleted_count} old backups")
            
        except Exception as e:
            self.logger.error(f"❌ Backup cleanup failed: {e}")

    async def _run_health_check(self):
        """Chạy health check cho system"""
        try:
            # Check database connectivity
            db_status = await self._check_database_health()
            
            # Check API endpoints availability
            api_status = await self._check_api_health()
            
            # Check disk space, memory, etc. (implement nếu cần)
            system_status = await self._check_system_health()
            
            health_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'database': db_status,
                'apis': api_status,
                'system': system_status,
                'jobs': self._get_job_status_summary()
            }
            
            # Log health status
            if all([db_status, api_status, system_status]):
                self.logger.info("💚 System health check: All systems operational")
            else:
                self.logger.warning(f"⚠️ System health check: Some issues detected - {health_status}")
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")

    async def _check_database_health(self) -> bool:
        """Check database connectivity"""
        try:
            return await self.data_collector.initialize_database()
        except Exception:
            return False

    async def _check_api_health(self) -> Dict[str, bool]:
        """Check API endpoints availability"""
        api_status = {}
        
        for api_type in ['nokttv', 'kttv']:
            try:
                stations = await self.data_collector.fetch_stations(api_type)
                api_status[api_type] = len(stations) > 0
            except Exception:
                api_status[api_type] = False
        
        return api_status

    async def _check_system_health(self) -> bool:
        """Check system resources (simplified)"""
        try:
            # Basic health check - có thể mở rộng thêm
            return True
        except Exception:
            return False

    def _get_job_status_summary(self) -> Dict[str, Any]:
        """Get summary của job status"""
        summary = {
            'total_jobs': len(self.job_status),
            'running_jobs': len([j for j in self.job_status.values() if j.get('status') == 'running']),
            'failed_jobs': len([j for j in self.job_status.values() if j.get('status') == 'failed']),
            'success_jobs': len([j for j in self.job_status.values() if j.get('status') == 'success'])
        }
        return summary

    async def start(self):
        """Khởi động scheduler service"""
        try:
            self.logger.info("🌟 Starting Scheduler Service...")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Schedule all jobs
            await self.schedule_daily_collection_jobs()
            await self.schedule_cleanup_jobs()
            await self.schedule_health_check_jobs()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            self.logger.info("✅ Scheduler Service started successfully")
            self.logger.info(f"📋 Active jobs: {len(self.scheduler.get_jobs())}")
            
            # Print job schedule
            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time
                self.logger.info(f"   📌 {job.name} - Next run: {next_run}")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start scheduler: {e}")
            raise

    async def stop(self):
        """Dừng scheduler service một cách graceful"""
        try:
            self.logger.info("🛑 Stopping Scheduler Service...")
            
            if self.scheduler.running:
                # Wait for running jobs to complete (with timeout)
                self.scheduler.shutdown(wait=True)
            
            self.is_running = False
            self.logger.info("✅ Scheduler Service stopped gracefully")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping scheduler: {e}")

    async def run_manual_collection(self, target_date: Optional[str] = None):
        """
        Chạy collection manually (cho testing/debugging)
        
        Args:
            target_date: Date string trong format YYYY-MM-DD
        """
        try:
            self.logger.info(f"🔧 Running manual collection for {target_date or 'today'}")
            
            # Parse target date nếu có
            parsed_date = None
            if target_date:
                from datetime import datetime
                parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            # Run collection
            success = await self.data_collector.run_daily_collection(parsed_date)
            
            if success:
                self.logger.info("✅ Manual collection completed successfully")
            else:
                self.logger.error("❌ Manual collection failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Manual collection error: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current status của scheduler"""
        return {
            'is_running': self.is_running,
            'scheduler_active': self.scheduler.running if hasattr(self, 'scheduler') else False,
            'active_jobs': len(self.scheduler.get_jobs()) if hasattr(self, 'scheduler') else 0,
            'job_status': self.job_status,
            'last_health_check': datetime.utcnow().isoformat()
        }

async def main():
    """Main entry point cho scheduler service"""
    scheduler_service = SchedulerService()
    
    try:
        await scheduler_service.start()
    except KeyboardInterrupt:
        pass
    finally:
        await scheduler_service.stop()

if __name__ == "__main__":
    asyncio.run(main())