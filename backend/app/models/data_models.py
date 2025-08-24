from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class UploadManualPayload(BaseModel):
    data: List[Dict[str, Any]]

class StatsResponse(BaseModel):
    stats: Union[List[Dict[str, Any]], Dict[str, Any]]
    has_month: Optional[bool] = None

class FrequencyCurveResponse(BaseModel):
    theoretical_curve: List[Dict[str, Any]]
    empirical_points: List[Dict[str, Any]]

class QQPPResponse(BaseModel):
    qq: List[Dict[str, Any]]
    pp: List[Dict[str, Any]]

class QuantileDataResponse(BaseModel):
    years: List[int]
    qmax_values: List[float]
    histogram: Dict[str, List[Any]]
    theoretical_curve: Dict[str, List[float]]

# Có thể thêm models khác nếu cần



class Station(BaseModel):
    uuid: str
    code: str
    name: str
    number: str
    latitude: float
    longitude: float
    area: str
    city: str
    address: str
    altitude: Optional[float] = None
    waterStationType: Optional[str] = None

class RealTimeMeasurement(BaseModel):
    depth: float
    time_point: str

class RealTimeStationData(BaseModel):
    value: List[RealTimeMeasurement]
    station_id: str

class RealTimeResponse(BaseModel):
    id: str
    Data: List[RealTimeStationData]

class RealTimeQuery(BaseModel):
    start_time: str
    end_time: str
    station_id: Optional[str] = None  # For per-station fetch