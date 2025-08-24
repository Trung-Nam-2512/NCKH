import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import { Card, Badge, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMapMarkedAlt, faWater, faExclamationTriangle, faInfoCircle } from '@fortawesome/free-solid-svg-icons';
import Config from '../config/config';
import '../assets/stationMap.css';

// Fix icon mặc định của Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const { BaseLayer } = LayersControl;

// Tạo custom icon cho trạm đo thủy văn
const createStationIcon = (status, depth) => {
    let iconColor = '#007bff'; // Mặc định xanh
    let iconSize = [32, 32];
    let pulseAnimation = '';

    // Thay đổi màu và kích thước dựa trên trạng thái và mực nước
    if (status === 'inactive') {
        iconColor = '#6c757d'; // Xám
        iconSize = [28, 28];
    } else if (depth > 0.5) {
        iconColor = '#dc3545'; // Đỏ - mực nước cao
        iconSize = [36, 36];
        pulseAnimation = 'pulse-red';
    } else if (depth > 0.2) {
        iconColor = '#ffc107'; // Vàng - mực nước trung bình
        iconSize = [34, 34];
        pulseAnimation = 'pulse-yellow';
    } else {
        pulseAnimation = 'pulse-blue';
    }

    return L.divIcon({
        html: `
            <div class="station-icon-container ${pulseAnimation}" style="
                position: relative;
                width: ${iconSize[0]}px;
                height: ${iconSize[1]}px;
            ">
                <!-- Background circle with gradient -->
                <div style="
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: radial-gradient(circle at 30% 30%, ${iconColor}, ${iconColor}dd);
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3), 0 2px 4px rgba(0,0,0,0.2);
                "></div>
                
                <!-- Water drop icon -->
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 16px;
                    height: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <svg viewBox="0 0 24 24" fill="white" style="width: 100%; height: 100%;">
                        <path d="M12,2c-5.33,4.55-8,8.48-8,11.8c0,4.98,3.8,8.2,8,8.2s8-3.22,8-8.2C20,10.48,17.33,6.55,12,2z M12,20c-3.35,0-6-2.57-6-6.2c0-2.34,1.95-5.44,6-9.14c4.05,3.7,6,6.79,6,9.14C18,17.43,15.35,20,12,20z"/>
                        <path d="M12,12.5c-1.38,0-2.5-1.12-2.5-2.5s1.12-2.5,2.5-2.5s2.5,1.12,2.5,2.5S13.38,12.5,12,12.5z"/>
                    </svg>
                </div>
                
                <!-- Status indicator dot -->
                <div style="
                    position: absolute;
                    top: 2px;
                    right: 2px;
                    width: 8px;
                    height: 8px;
                    background-color: ${status === 'active' ? '#28a745' : '#dc3545'};
                    border-radius: 50%;
                    border: 1px solid white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                "></div>
            </div>
        `,
        className: 'custom-station-icon',
        iconSize: iconSize,
        iconAnchor: [iconSize[0] / 2, iconSize[1] / 2],
        popupAnchor: [0, -iconSize[1] / 2]
    });
};

const AdvancedStationMap = () => {
    const [stations, setStations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedStation, setSelectedStation] = useState(null);
    const [mapCenter, setMapCenter] = useState([16.0, 108.0]); // Trung tâm Việt Nam
    const [mapboxToken] = useState(Config.MAPBOX_ACCESS_TOKEN);

    useEffect(() => {
        fetchStations();
    }, []);

    const fetchStations = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${Config.BASE_URL}/realtime/stations`);
            if (!response.ok) {
                throw new Error('Failed to fetch stations');
            }
            const data = await response.json();
            setStations(data.stations || []);

            // Cập nhật center map nếu có trạm
            if (data.stations && data.stations.length > 0) {
                const avgLat = data.stations.reduce((sum, s) => sum + s.latitude, 0) / data.stations.length;
                const avgLng = data.stations.reduce((sum, s) => sum + s.longitude, 0) / data.stations.length;
                setMapCenter([avgLat, avgLng]);
            }
        } catch (err) {
            setError('Không thể tải danh sách trạm: ' + err.message);
        } finally {
            setLoading(false);
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

    const getDepthColor = (depth) => {
        if (depth > 0.5) return '#dc3545'; // Đỏ - cao
        if (depth > 0.2) return '#ffc107'; // Vàng - trung bình
        return '#28a745'; // Xanh - thấp
    };

    const getDepthText = (depth) => {
        if (depth > 0.5) return 'Cao';
        if (depth > 0.2) return 'Trung bình';
        return 'Thấp';
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
        <div className="advanced-station-map-container">
            <Card>
                <Card.Header className="bg-primary text-white">
                    <FontAwesomeIcon icon={faMapMarkedAlt} className="me-2" />
                    Bản đồ trạm đo thủy văn nâng cao
                    {mapboxToken.includes('example') && (
                        <small className="ms-2 text-warning">
                            (Để sử dụng bản đồ vệ tinh, cần cấu hình MAPBOX_ACCESS_TOKEN trong .env)
                        </small>
                    )}
                </Card.Header>
                <Card.Body>
                    <Row className="mb-3">
                        <Col md={12}>
                            <div className="map-legend">
                                <h6><FontAwesomeIcon icon={faInfoCircle} className="me-2" />Chú thích:</h6>
                                <div className="legend-items">
                                    <div className="legend-item">
                                        <div className="legend-color" style={{
                                            background: 'radial-gradient(circle at 30% 30%, #007bff, #007bffdd)',
                                            position: 'relative',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <svg viewBox="0 0 24 24" fill="white" style={{ width: '12px', height: '12px' }}>
                                                <path d="M12,2c-5.33,4.55-8,8.48-8,11.8c0,4.98,3.8,8.2,8,8.2s8-3.22,8-8.2C20,10.48,17.33,6.55,12,2z M12,20c-3.35,0-6-2.57-6-6.2c0-2.34,1.95-5.44,6-9.14c4.05,3.7,6,6.79,6,9.14C18,17.43,15.35,20,12,20z" />
                                            </svg>
                                        </div>
                                        <span>Mực nước thấp (&lt; 0.2m)</span>
                                    </div>
                                    <div className="legend-item">
                                        <div className="legend-color" style={{
                                            background: 'radial-gradient(circle at 30% 30%, #ffc107, #ffc107dd)',
                                            position: 'relative',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <svg viewBox="0 0 24 24" fill="white" style={{ width: '12px', height: '12px' }}>
                                                <path d="M12,2c-5.33,4.55-8,8.48-8,11.8c0,4.98,3.8,8.2,8,8.2s8-3.22,8-8.2C20,10.48,17.33,6.55,12,2z M12,20c-3.35,0-6-2.57-6-6.2c0-2.34,1.95-5.44,6-9.14c4.05,3.7,6,6.79,6,9.14C18,17.43,15.35,20,12,20z" />
                                            </svg>
                                        </div>
                                        <span>Mực nước trung bình (0.2-0.5m)</span>
                                    </div>
                                    <div className="legend-item">
                                        <div className="legend-color" style={{
                                            background: 'radial-gradient(circle at 30% 30%, #dc3545, #dc3545dd)',
                                            position: 'relative',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <svg viewBox="0 0 24 24" fill="white" style={{ width: '12px', height: '12px' }}>
                                                <path d="M12,2c-5.33,4.55-8,8.48-8,11.8c0,4.98,3.8,8.2,8,8.2s8-3.22,8-8.2C20,10.48,17.33,6.55,12,2z M12,20c-3.35,0-6-2.57-6-6.2c0-2.34,1.95-5.44,6-9.14c4.05,3.7,6,6.79,6,9.14C18,17.43,15.35,20,12,20z" />
                                            </svg>
                                        </div>
                                        <span>Mực nước cao (&gt; 0.5m)</span>
                                    </div>
                                    <div className="legend-item">
                                        <div className="legend-color" style={{
                                            background: 'radial-gradient(circle at 30% 30%, #6c757d, #6c757ddd)',
                                            position: 'relative',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <svg viewBox="0 0 24 24" fill="white" style={{ width: '12px', height: '12px' }}>
                                                <path d="M12,2c-5.33,4.55-8,8.48-8,11.8c0,4.98,3.8,8.2,8,8.2s8-3.22,8-8.2C20,10.48,17.33,6.55,12,2z M12,20c-3.35,0-6-2.57-6-6.2c0-2.34,1.95-5.44,6-9.14c4.05,3.7,6,6.79,6,9.14C18,17.43,15.35,20,12,20z" />
                                            </svg>
                                        </div>
                                        <span>Trạm không hoạt động</span>
                                    </div>
                                </div>
                            </div>
                        </Col>
                    </Row>

                    <div className="map-container" style={{ height: '600px', width: '100%' }}>
                        <MapContainer
                            center={mapCenter}
                            zoom={6}
                            style={{ height: '100%', width: '100%' }}
                        >
                            <LayersControl position="topright">
                                <BaseLayer checked name="OpenStreetMap">
                                    <TileLayer
                                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    />
                                </BaseLayer>
                                <BaseLayer name="Mapbox Satellite">
                                    <TileLayer
                                        attribution='&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a>'
                                        url={`https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`}
                                        tileSize={512}
                                        zoomOffset={-1}
                                    />
                                </BaseLayer>
                                <BaseLayer name="Mapbox Streets">
                                    <TileLayer
                                        attribution='&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a>'
                                        url={`https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`}
                                        tileSize={512}
                                        zoomOffset={-1}
                                    />
                                </BaseLayer>
                            </LayersControl>

                            {stations.map(station => {
                                const stationIcon = createStationIcon(
                                    station.status,
                                    station.last_measurement || 0
                                );

                                return (
                                    <Marker
                                        key={station.station_id}
                                        position={[station.latitude, station.longitude]}
                                        icon={stationIcon}
                                        eventHandlers={{
                                            click: () => setSelectedStation(station)
                                        }}
                                    >
                                        <Popup>
                                            <div className="station-popup">
                                                <h6><FontAwesomeIcon icon={faWater} className="me-2" />
                                                    Trạm {station.station_id}
                                                </h6>
                                                <p><strong>Tên:</strong> {station.name}</p>
                                                <p><strong>Vị trí:</strong> {station.latitude}, {station.longitude}</p>
                                                <p>
                                                    <strong>Trạng thái:</strong>
                                                    <Badge
                                                        bg={getStationStatusColor(station.status)}
                                                        className="ms-2"
                                                    >
                                                        {getStationStatusText(station.status)}
                                                    </Badge>
                                                </p>
                                                <p>
                                                    <strong>Mực nước hiện tại:</strong>
                                                    <Badge
                                                        bg="info"
                                                        className="ms-2"
                                                        style={{ backgroundColor: getDepthColor(station.last_measurement || 0) }}
                                                    >
                                                        {(station.last_measurement || 0).toFixed(3)}m ({getDepthText(station.last_measurement || 0)})
                                                    </Badge>
                                                </p>
                                                <p><strong>Cập nhật lần cuối:</strong> {new Date(station.last_updated).toLocaleString('vi-VN')}</p>
                                                <p><strong>Tổng số đo:</strong> {station.total_measurements}</p>
                                                <div className="station-stats">
                                                    <small>
                                                        <strong>Thống kê:</strong><br />
                                                        Trung bình: {station.avg_depth?.toFixed(3)}m<br />
                                                        Min: {station.min_depth?.toFixed(3)}m<br />
                                                        Max: {station.max_depth?.toFixed(3)}m
                                                    </small>
                                                </div>
                                            </div>
                                        </Popup>
                                    </Marker>
                                );
                            })}
                        </MapContainer>
                    </div>

                    {selectedStation && (
                        <Row className="mt-3">
                            <Col md={12}>
                                <Card className="selected-station-info">
                                    <Card.Header>
                                        <h6>Thông tin chi tiết: Trạm {selectedStation.station_id}</h6>
                                    </Card.Header>
                                    <Card.Body>
                                        <Row>
                                            <Col md={6}>
                                                <p><strong>Tên trạm:</strong> {selectedStation.name}</p>
                                                <p><strong>Vị trí:</strong> {selectedStation.latitude}, {selectedStation.longitude}</p>
                                                <p><strong>Trạng thái:</strong> {getStationStatusText(selectedStation.status)}</p>
                                            </Col>
                                            <Col md={6}>
                                                <p><strong>Mực nước hiện tại:</strong> {(selectedStation.last_measurement || 0).toFixed(3)}m</p>
                                                <p><strong>Cập nhật lần cuối:</strong> {new Date(selectedStation.last_updated).toLocaleString('vi-VN')}</p>
                                                <p><strong>Tổng số đo:</strong> {selectedStation.total_measurements}</p>
                                            </Col>
                                        </Row>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>
                    )}
                </Card.Body>
            </Card>
        </div>
    );
};

export default AdvancedStationMap; 