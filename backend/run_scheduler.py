#!/usr/bin/env python3
"""
PRODUCTION SCRIPT ĐỂ CHẠY SCHEDULER

Script này được thiết kế để chạy scheduler trong production environment:
- Tự động khởi động scheduler service
- Monitor và restart nếu có lỗi
- Graceful shutdown handling
- Comprehensive logging
- Process daemonization support
- Health monitoring

Usage:
    python run_scheduler.py                    # Chạy foreground
    python run_scheduler.py --daemon           # Chạy background
    python run_scheduler.py --test             # Chạy test mode
    python run_scheduler.py --manual-collect   # Trigger manual collection
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
from datetime import datetime
import json
from pathlib import Path

# Add app to Python path
sys.path.append(os.path.dirname(__file__))

from app.services.scheduler_service import SchedulerService
from app.services.daily_data_collector import DailyDataCollector

def setup_logging(log_level="INFO", log_file="scheduler_production.log"):
    """Setup comprehensive logging cho production"""
    
    # Tạo log directory nếu chưa có
    log_path = Path(log_file).parent
    log_path.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - PID:%(process)d - %(funcName)s:%(lineno)d - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress noisy loggers
    logging.getLogger('motor').setLevel(logging.WARNING)
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

async def run_scheduler_service(test_mode=False):
    """
    Main function để chạy scheduler service
    
    Args:
        test_mode: Nếu True, chỉ chạy test và exit
    """
    logger = logging.getLogger(__name__)
    scheduler_service = None
    
    try:
        logger.info("🚀 Starting Daily Data Collector Scheduler...")
        logger.info(f"📅 Start time: {datetime.utcnow().isoformat()}")
        logger.info(f"🐍 Python version: {sys.version}")
        logger.info(f"📂 Working directory: {os.getcwd()}")
        
        if test_mode:
            logger.info("🧪 Running in TEST MODE")
        
        # Khởi tạo scheduler
        scheduler_service = SchedulerService()
        
        if test_mode:
            # Test mode: chạy manual collection rồi exit
            logger.info("🔧 Running manual test collection...")
            success = await scheduler_service.run_manual_collection()
            
            if success:
                logger.info("✅ Test collection completed successfully")
                return True
            else:
                logger.error("❌ Test collection failed")
                return False
        else:
            # Production mode: start scheduler
            logger.info("🌟 Starting production scheduler...")
            await scheduler_service.start()
            
        return True
        
    except KeyboardInterrupt:
        logger.info("📡 Received keyboard interrupt (Ctrl+C)")
        return True
    except Exception as e:
        logger.error(f"💥 Fatal error in scheduler: {e}", exc_info=True)
        return False
    finally:
        if scheduler_service:
            try:
                logger.info("🛑 Shutting down scheduler...")
                await scheduler_service.stop()
                logger.info("✅ Scheduler shutdown completed")
            except Exception as e:
                logger.error(f"❌ Error during shutdown: {e}")

async def run_manual_collection(target_date=None):
    """Chạy manual collection một lần"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔧 Running manual data collection...")
        
        collector = DailyDataCollector()
        
        # Parse target date nếu có
        parsed_date = None
        if target_date:
            from datetime import datetime
            try:
                parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                logger.info(f"🎯 Target date: {parsed_date}")
            except ValueError:
                logger.error(f"❌ Invalid date format: {target_date}. Use YYYY-MM-DD")
                return False
        
        success = await collector.run_daily_collection(parsed_date)
        
        if success:
            logger.info("✅ Manual collection completed successfully")
            return True
        else:
            logger.error("❌ Manual collection failed")
            return False
            
    except Exception as e:
        logger.error(f"💥 Manual collection error: {e}", exc_info=True)
        return False

def create_systemd_service(script_path, user="root"):
    """
    Tạo systemd service file cho scheduler
    
    Args:
        script_path: Đường dẫn đến script này
        user: User để chạy service
    """
    service_content = f"""[Unit]
Description=NCKH Hydrological Data Collector Scheduler
After=network.target mongodb.service
Wants=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={os.path.dirname(script_path)}
Environment=PYTHONPATH={os.path.dirname(script_path)}
ExecStart=/usr/bin/python3 {script_path}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nckh-scheduler

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "/etc/systemd/system/nckh-scheduler.service"
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Systemd service file created: {service_file}")
        print("\nTo enable and start the service:")
        print("sudo systemctl daemon-reload")
        print("sudo systemctl enable nckh-scheduler")
        print("sudo systemctl start nckh-scheduler")
        print("\nTo check status:")
        print("sudo systemctl status nckh-scheduler")
        print("sudo journalctl -u nckh-scheduler -f")
        
        return True
        
    except PermissionError:
        print("❌ Permission denied. Run with sudo to create systemd service")
        return False
    except Exception as e:
        print(f"❌ Error creating systemd service: {e}")
        return False

def main():
    """Main entry point với argument parsing"""
    parser = argparse.ArgumentParser(
        description="NCKH Daily Data Collector Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Run scheduler normally
  %(prog)s --test                       # Run test collection and exit
  %(prog)s --manual-collect             # Run manual collection once
  %(prog)s --manual-collect --date 2024-01-15  # Collect for specific date
  %(prog)s --daemon                     # Run as daemon (background)
  %(prog)s --create-service             # Create systemd service file
  %(prog)s --log-level DEBUG            # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--test', 
        action='store_true', 
        help='Run in test mode (single collection then exit)'
    )
    
    parser.add_argument(
        '--manual-collect',
        action='store_true',
        help='Run manual collection once then exit'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Target date for manual collection (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon (background process)'
    )
    
    parser.add_argument(
        '--create-service',
        action='store_true',
        help='Create systemd service file and exit'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    parser.add_argument(
        '--log-file',
        default='scheduler_production.log',
        help='Log file path'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level, args.log_file)
    
    # Handle --create-service
    if args.create_service:
        script_path = os.path.abspath(__file__)
        success = create_systemd_service(script_path)
        sys.exit(0 if success else 1)
    
    # Handle --manual-collect
    if args.manual_collect:
        success = asyncio.run(run_manual_collection(args.date))
        sys.exit(0 if success else 1)
    
    # Handle daemon mode (simplified - real daemonization would need more work)
    if args.daemon:
        logger.info("🔄 Running in daemon-like mode...")
        # Note: For real daemon, use python-daemon library hoặc systemd
    
    # Run main scheduler
    try:
        success = asyncio.run(run_scheduler_service(args.test))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("📡 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()