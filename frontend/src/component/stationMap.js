import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Spinner, Badge } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faMapMarkedAlt,
    faCopy,
    faCheck,
    faExclamationTriangle,
    faInfoCircle,
    faLocationArrow
} from '@fortawesome/free-solid-svg-icons';
import '../assets/stationMap.css';
import '../assets/advancedStationMap.css';

const StationMap = () => {
    const [stations, setStations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedStation, setSelectedStation] = useState(null);
    const [copiedId, setCopiedId] = useState(null);
    const [mapCenter, setMapCenter] = useState({ lat: 10.8231, lng: 106.6297 }); // HCMC center

    useEffect(() => {
        fetchStations();
    }, []);

    const fetchStations = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:8000/realtime/stations');
            if (!response.ok) {
                throw new Error('Failed to fetch stations');
            }
            const data = await response.json();
            setStations(data.stations || []);
        } catch (err) {
            setError('Không thể tải danh sách trạm: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleStationClick = (station) => {
        setSelectedStation(station);
        setCopiedId(null);
    };

    const copyStationId = async (stationId) => {
        try {
            await navigator.clipboard.writeText(stationId);
            setCopiedId(stationId);
            setTimeout(() => setCopiedId(null), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const getStationStatusColor = (status) => {
        switch (status) {
            case 'active': return 'success';
            case 'inactive': return 'danger';
            case 'maintenance': return 'warning';
            default: return 'secondary';
        }
    };

    const getStationStatusText = (status) => {
        switch (status) {
            case 'active': return 'Hoạt động';
            case 'inactive': return 'Không hoạt động';
            case 'maintenance': return 'Bảo trì';
            default: return 'Không xác định';
        }
    };

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">Loading...</span>
                </Spinner>
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="danger">
                <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
                {error}
            </Alert>
        );
    }

    return (
        <div className="station-map-container">
            <Card>
                <Card.Header className="bg-primary text-white">
                    <FontAwesomeIcon icon={faMapMarkedAlt} className="me-2" />
                    Bản đồ trạm đo thủy văn
                </Card.Header>
                <Card.Body>
                    <div className="row">
                        {/* Map Section */}
                        <div className="col-md-8">
                            <div className="map-container" style={{
                                height: '500px',
                                backgroundColor: '#f8f9fa',
                                border: '2px solid #dee2e6',
                                borderRadius: '8px',
                                position: 'relative',
                                overflow: 'hidden'
                            }}>
                                {/* Placeholder for actual map implementation */}
                                <div className="d-flex justify-content-center align-items-center h-100">
                                    <div className="text-center">
                                        <FontAwesomeIcon
                                            icon={faMapMarkedAlt}
                                            size="3x"
                                            className="text-muted mb-3"
                                        />
                                        <h5 className="text-muted">Bản đồ trạm đo</h5>
                                        <p className="text-muted">
                                            {stations.length} trạm đang hoạt động
                                        </p>
                                        <small className="text-muted">
                                            Click vào trạm để xem thông tin chi tiết
                                        </small>
                                    </div>
                                </div>

                                {/* Station markers (simulated) */}
                                {stations.slice(0, 10).map((station, index) => (
                                    <div
                                        key={station.station_id}
                                        className="station-marker"
                                        style={{
                                            position: 'absolute',
                                            left: `${20 + (index % 5) * 15}%`,
                                            top: `${20 + Math.floor(index / 5) * 20}%`,
                                            cursor: 'pointer',
                                            zIndex: 10
                                        }}
                                        onClick={() => handleStationClick(station)}
                                    >
                                        <div className="station-dot" style={{
                                            position: 'relative',
                                            width: '24px',
                                            height: '24px',
                                            borderRadius: '50%',
                                            background: `radial-gradient(circle at 30% 30%, ${station.status === 'active' ? '#28a745' : '#dc3545'}, ${station.status === 'active' ? '#28a745dd' : '#dc3545dd'})`,
                                            border: '3px solid white',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.3), 0 2px 4px rgba(0,0,0,0.2)',
                                            transition: 'transform 0.2s',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <svg viewBox="0 0 24 24" fill="white" style={{ width: '12px', height: '12px' }}>
                                                <path d="M12,2c-5.33,4.55-8,8.48-8,11.8c0,4.98,3.8,8.2,8,8.2s8-3.22,8-8.2C20,10.48,17.33,6.55,12,2z M12,20c-3.35,0-6-2.57-6-6.2c0-2.34,1.95-5.44,6-9.14c4.05,3.7,6,6.79,6,9.14C18,17.43,15.35,20,12,20z" />
                                            </svg>
                                            <div style={{
                                                position: 'absolute',
                                                top: '1px',
                                                right: '1px',
                                                width: '6px',
                                                height: '6px',
                                                backgroundColor: station.status === 'active' ? '#28a745' : '#dc3545',
                                                borderRadius: '50%',
                                                border: '1px solid white',
                                                boxShadow: '0 1px 2px rgba(0,0,0,0.3)'
                                            }}></div>
                                        </div>
                                        <div className="station-label" style={{
                                            position: 'absolute',
                                            top: '25px',
                                            left: '50%',
                                            transform: 'translateX(-50%)',
                                            backgroundColor: 'white',
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            fontSize: '10px',
                                            whiteSpace: 'nowrap',
                                            boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                                            display: selectedStation?.station_id === station.station_id ? 'block' : 'none'
                                        }}>
                                            {station.station_id}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Station List */}
                        <div className="col-md-4">
                            <div className="station-list">
                                <h6 className="mb-3">
                                    <FontAwesomeIcon icon={faLocationArrow} className="me-2" />
                                    Danh sách trạm ({stations.length})
                                </h6>

                                <div className="station-items" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                    {stations.map((station) => (
                                        <div
                                            key={station.station_id}
                                            className={`station-item p-2 mb-2 border rounded ${selectedStation?.station_id === station.station_id ? 'border-primary bg-light' : ''
                                                }`}
                                            style={{ cursor: 'pointer' }}
                                            onClick={() => handleStationClick(station)}
                                        >
                                            <div className="d-flex justify-content-between align-items-center">
                                                <div>
                                                    <strong>{station.station_id}</strong>
                                                    <div className="text-muted small">
                                                        {station.name || 'Trạm đo thủy văn'}
                                                    </div>
                                                </div>
                                                <Badge bg={getStationStatusColor(station.status)}>
                                                    {getStationStatusText(station.status)}
                                                </Badge>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Selected Station Details */}
                    {selectedStation && (
                        <Card className="mt-3 border-primary">
                            <Card.Header className="bg-primary text-white">
                                <FontAwesomeIcon icon={faInfoCircle} className="me-2" />
                                Thông tin trạm: {selectedStation.station_id}
                            </Card.Header>
                            <Card.Body>
                                <div className="row">
                                    <div className="col-md-6">
                                        <h6>Thông tin cơ bản</h6>
                                        <table className="table table-sm">
                                            <tbody>
                                                <tr>
                                                    <td><strong>ID Trạm:</strong></td>
                                                    <td>
                                                        {selectedStation.station_id}
                                                        <Button
                                                            size="sm"
                                                            variant="outline-secondary"
                                                            className="ms-2"
                                                            onClick={() => copyStationId(selectedStation.station_id)}
                                                        >
                                                            <FontAwesomeIcon
                                                                icon={copiedId === selectedStation.station_id ? faCheck : faCopy}
                                                            />
                                                        </Button>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Tên trạm:</strong></td>
                                                    <td>{selectedStation.name || 'N/A'}</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Trạng thái:</strong></td>
                                                    <td>
                                                        <Badge bg={getStationStatusColor(selectedStation.status)}>
                                                            {getStationStatusText(selectedStation.status)}
                                                        </Badge>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Vĩ độ:</strong></td>
                                                    <td>{selectedStation.latitude || 'N/A'}</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Kinh độ:</strong></td>
                                                    <td>{selectedStation.longitude || 'N/A'}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                    <div className="col-md-6">
                                        <h6>Thống kê dữ liệu</h6>
                                        <table className="table table-sm">
                                            <tbody>
                                                <tr>
                                                    <td><strong>Số đo gần nhất:</strong></td>
                                                    <td>{selectedStation.last_measurement || 'N/A'}</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Độ sâu hiện tại:</strong></td>
                                                    <td>{selectedStation.current_depth || 'N/A'} m</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Cập nhật lần cuối:</strong></td>
                                                    <td>{selectedStation.last_updated || 'N/A'}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                <div className="mt-3">
                                    <Alert variant="info" className="mb-0">
                                        <FontAwesomeIcon icon={faInfoCircle} className="me-2" />
                                        <strong>Hướng dẫn:</strong> Copy ID trạm và sử dụng trong phần "Phân tích theo trạm"
                                        để thực hiện phân tích tần suất cho trạm này.
                                    </Alert>
                                </div>
                            </Card.Body>
                        </Card>
                    )}
                </Card.Body>
            </Card>
        </div>
    );
};

export default StationMap; 