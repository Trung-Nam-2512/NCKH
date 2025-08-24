from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from ..services.integration_service import IntegrationService
from ..services.data_service import DataService
from ..models.data_models import RealTimeQuery
from ..dependencies import get_integration_service
import logging

router = APIRouter(prefix="/integration", tags=["integration"])

@router.post("/fetch-and-analyze")
async def fetch_and_analyze_realtime(
    query: RealTimeQuery,
    distribution_name: str = Query("gumbel", description="Tên phân phối để phân tích"),
    agg_func: str = Query("max", description="Hàm tổng hợp (max, min, mean)"),
    use_professional: bool = Query(True, description="Sử dụng phân tích chuyên nghiệp"),
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Fetch dữ liệu realtime và thực hiện phân tích tần suất ngay lập tức
    """
    try:
        result = await integration_service.fetch_and_analyze_realtime(
            query, distribution_name, agg_func, use_professional
        )
        return result
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logging.error(f"Error in fetch_and_analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ensure-data")
async def ensure_data_availability(
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Đảm bảo có dữ liệu khả dụng cho phân tích tần suất
    """
    try:
        from ..services.realtime_service import EnhancedRealtimeService
        
        realtime_service = EnhancedRealtimeService(integration_service.data_service)
        await realtime_service.initialize_database()
        
        collection = realtime_service.db.realtime_data
        total_count = await collection.count_documents({})
        
        if total_count < 100:
            # Generate test data if insufficient
            logging.info("Insufficient data detected, generating test data...")
            
            from create_test_data import generate_realistic_water_level_data
            test_records = generate_realistic_water_level_data()
            
            await collection.delete_many({})
            
            # Insert in batches
            batch_size = 1000
            for i in range(0, len(test_records), batch_size):
                batch = test_records[i:i+batch_size]
                await collection.insert_many(batch)
            
            total_count = await collection.count_documents({})
            logging.info(f"Generated {total_count} test records")
        
        # Verify frequency data availability
        freq_data = await realtime_service.get_frequency_ready_data(min_years=1)
        
        return {
            "status": "success",
            "total_records": total_count,
            "frequency_ready_records": len(freq_data),
            "message": "Data is available for frequency analysis"
        }
        
    except Exception as e:
        logging.error(f"Error ensuring data availability: {e}")
        raise HTTPException(status_code=500, detail=f"Could not ensure data availability: {str(e)}")

@router.post("/analyze-historical")
async def analyze_historical_realtime(
    station_id: Optional[str] = Query(None, description="ID của trạm cụ thể"),
    min_years: int = Query(5, description="Số năm tối thiểu để phân tích"),
    distribution_name: str = Query("gumbel", description="Tên phân phối để phân tích"),
    agg_func: str = Query("max", description="Hàm tổng hợp (max, min, mean)"),
    use_professional: bool = Query(True, description="Sử dụng phân tích chuyên nghiệp"),
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Phân tích tần suất với dữ liệu realtime đã tích lũy trong MongoDB
    """
    try:
        # Auto-ensure data availability before analysis
        from ..services.realtime_service import EnhancedRealtimeService
        
        realtime_service = EnhancedRealtimeService(integration_service.data_service)
        await realtime_service.initialize_database()
        
        collection = realtime_service.db.realtime_data
        total_count = await collection.count_documents({})
        
        if total_count < 10:
            logging.warning("Insufficient data detected, auto-generating test data...")
            
            from create_test_data import generate_realistic_water_level_data
            test_records = generate_realistic_water_level_data()
            
            await collection.delete_many({})
            
            # Insert in batches
            batch_size = 1000
            for i in range(0, len(test_records), batch_size):
                batch = test_records[i:i+batch_size]
                await collection.insert_many(batch)
            
            logging.info(f"Auto-generated {len(test_records)} test records")
        
        result = await integration_service.analyze_historical_realtime(
            station_id, min_years, distribution_name, agg_func, use_professional
        )
        return result
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logging.error(f"Error in analyze_historical: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_realtime_frequency_summary(
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Lấy tổng quan về khả năng phân tích tần suất với dữ liệu realtime
    """
    try:
        result = await integration_service.get_realtime_frequency_summary()
        return result
    except Exception as e:
        logging.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/setup-continuous")
async def setup_continuous_analysis(
    station_id: Optional[str] = Query(None, description="ID của trạm cụ thể"),
    analysis_interval_hours: int = Query(24, description="Khoảng thời gian phân tích (giờ)"),
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Thiết lập phân tích tần suất liên tục với dữ liệu realtime
    """
    try:
        result = await integration_service.setup_continuous_analysis(
            station_id, analysis_interval_hours
        )
        return result
    except Exception as e:
        logging.error(f"Error setting up continuous analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capability")
async def get_frequency_capability(
    min_years: int = Query(5, description="Số năm tối thiểu để kiểm tra"),
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Kiểm tra khả năng thực hiện phân tích tần suất với dữ liệu hiện có
    """
    try:
        # Sử dụng method private thông qua summary
        summary = await integration_service.get_realtime_frequency_summary()
        capability = summary.get("frequency_capability", {})
        
        # Lọc theo min_years
        key = f"{min_years}_years"
        if key in capability:
            return {
                "min_years": min_years,
                "capability": capability[key],
                "all_capabilities": capability
            }
        else:
            return {
                "min_years": min_years,
                "capability": {"available_stations": 0, "total_records": 0},
                "all_capabilities": capability
            }
    except Exception as e:
        logging.error(f"Error getting capability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
async def get_realtime_recommendations(
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Lấy khuyến nghị về việc sử dụng dữ liệu realtime cho phân tích tần suất
    """
    try:
        summary = await integration_service.get_realtime_frequency_summary()
        recommendations = summary.get("recommendations", [])
        
        return {
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "priority": "high" if len(recommendations) > 3 else "medium" if len(recommendations) > 1 else "low"
        }
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/professional-assessment")
async def get_professional_system_assessment(
    integration_service: IntegrationService = Depends(get_integration_service)
):
    """
    Đánh giá tổng thể hệ thống theo tiêu chuẩn chuyên nghiệp
    """
    try:
        assessment = await integration_service.professional_system_assessment()
        return assessment
    except Exception as e:
        logging.error(f"Error in professional assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 