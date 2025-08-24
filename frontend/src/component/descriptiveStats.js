import React, { useState, useEffect } from 'react';
import '../assets/descriptiveStats.css';
import axios from 'axios';
import Config from '../config/config';
import { Card, Badge } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartBar, faSpinner } from '@fortawesome/free-solid-svg-icons';

const StatsDisplay = ({ dataUpdated, fetch, checked }) => {
    const [overallStats, setOverallStats] = useState(null);
    const [loadingOverall, setLoadingOverall] = useState(false);
    const [errorOverall, setErrorOverall] = useState(null);

    const fetchOverallStats = async () => {
        setLoadingOverall(true);
        try {
            const response = await axios.get(`${Config.BASE_URL}/stats/monthly`);
            setOverallStats(response.data);
        } catch (error) {
            setErrorOverall(error.message);
        } finally {
            setLoadingOverall(false);
        }
    };

    useEffect(() => {
        if (fetch) {
            fetchOverallStats();
        }
    }, []);

    // Hàm kiểm tra xem tất cả các hàng có giống nhau không (chỉ xét các giá trị Min, Max, Mean, Std)
    const allStatsAreSame = (stats) => {
        if (!stats || stats.length === 0) return false;

        const firstStat = stats[0]; // Lấy giá trị đầu tiên để so sánh
        return stats.every(stat =>
            stat.min === firstStat.min &&
            stat.max === firstStat.max &&
            stat.mean === firstStat.mean &&
            stat.std === firstStat.std
        );
    };

    const getMonthName = (monthNumber) => {
        const months = [
            'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
            'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
        ];
        return months[monthNumber - 1] || `Tháng ${monthNumber}`;
    };

    return (
        <div className={`main-stats ${fetch ? 'p-20' : ''} fade-in`} style={{ marginTop: '30px' }}>
            {fetch && (
                <div className="text-center mb-5">
                    <h2 className="modern-title">
                        <FontAwesomeIcon icon={faChartBar} className="me-3" />
                        Thống kê mô tả theo tháng
                    </h2>
                    <p className="text-muted">Phân tích chi tiết dữ liệu theo từng tháng</p>
                </div>
            )}

            {loadingOverall ? (
                <div className="text-center py-5">
                    <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-3" />
                    <p className="mt-3">Đang nạp dữ liệu thống kê tổng hợp...</p>
                </div>
            ) : errorOverall ? (
                <div className="alert alert-danger text-center">
                    <strong>Lỗi:</strong> {errorOverall}
                </div>
            ) : overallStats && overallStats.length > 0 ? (
                allStatsAreSame(overallStats) ? (
                    <div className="alert alert-warning text-center">
                        <strong>Thông báo:</strong> Không có dữ liệu tháng (Dữ liệu các tháng giống nhau)
                    </div>
                ) : (
                    <div className="stats-grid-container">
                        {overallStats.map((stat, index) => (
                            <div key={index} className="stats-grid-item">
                                <Card className="modern-card h-100 stats-card">
                                    <Card.Header className="text-center">
                                        <Badge bg="primary" className="month-badge">
                                            {getMonthName(stat.Month)}
                                        </Badge>
                                    </Card.Header>
                                    <Card.Body className="text-center d-flex flex-column justify-content-center">
                                        <div className="stats-grid">
                                            <div className="stat-item">
                                                <div className="stat-label">Min</div>
                                                <div className="stat-value min-value">
                                                    {stat.min ? stat.min.toFixed(2) : 'N/A'}
                                                </div>
                                            </div>
                                            <div className="stat-item">
                                                <div className="stat-label">Max</div>
                                                <div className="stat-value max-value">
                                                    {stat.max ? stat.max.toFixed(2) : 'N/A'}
                                                </div>
                                            </div>
                                            <div className="stat-item">
                                                <div className="stat-label">Mean</div>
                                                <div className="stat-value mean-value">
                                                    {stat.mean ? stat.mean.toFixed(2) : 'N/A'}
                                                </div>
                                            </div>
                                            <div className="stat-item">
                                                <div className="stat-label">Std</div>
                                                <div className="stat-value std-value">
                                                    {stat.std ? stat.std.toFixed(2) : 'N/A'}
                                                </div>
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </div>
                        ))}
                    </div>
                )
            ) : (
                <div className="text-center py-5">
                    <div className="empty-state">
                        <FontAwesomeIcon icon={faChartBar} className="empty-icon" />
                        <p className="mt-3 text-muted">Chưa có dữ liệu để hiển thị</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StatsDisplay;
