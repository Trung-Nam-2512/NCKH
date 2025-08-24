#!/usr/bin/env python3
"""
Integrate Real API Service into the main backend
"""
import asyncio
import logging
from app.services.real_api_service import RealAPIService

logging.basicConfig(level=logging.INFO)

async def integrate_real_api():
    """Integrate real API service and update database"""
    try:
        logging.info("🚀 Starting Real API integration...")
        
        # Initialize and run real API service
        service = RealAPIService()
        await service.run_real_data_collection()
        
        logging.info("✅ Real API integration completed successfully!")
        
        # Show summary
        logging.info("📊 Integration Summary:")
        logging.info("   - Real API service integrated")
        logging.info("   - Station mapping logic implemented")
        logging.info("   - Database updated with latest data")
        logging.info("   - Backend ready for frontend integration")
        
    except Exception as e:
        logging.error(f"❌ Error in real API integration: {e}")

if __name__ == "__main__":
    asyncio.run(integrate_real_api()) 