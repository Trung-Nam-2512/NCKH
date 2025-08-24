import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { useFileInfo } from "../context/fileInfoContext";
import { useUnit } from "../context/unitContext";
import Config from '../config/config';
import { Card, Table, Badge, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalendarAlt, faSpinner, faChartLine } from '@fortawesome/free-solid-svg-icons';
import '../assets/annualStatistics.css';

const AnnualStatistics = ({ fetch }) => {
    const [stats, setStats] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { fileInfo } = useFileInfo();
    const { nameColumn, unit } = useUnit();
    const headerTitle =
        fileInfo?.dataType && fileInfo.dataType !== "Unknown"
            ? fileInfo.dataType
            : nameColumn || "Unknown";

    const headerUnit =
        fileInfo?.unit && fileInfo.unit !== "Unknown"
            ? fileInfo.unit
            : unit || "Unknown";

    const fetchData = async () => {
        try {
            const response = await axios.get(`${Config.BASE_URL}/stats/annual`);
            setStats(response.data);
        } catch (error) {
            console.error("Error fetching annual statistics:", error);
            setError(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (fetch) {
            fetchData();
        }
    }, [fetch]);

    if (loading) return (
        <div className="text-center py-5">
            <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-3" />
            <p className="mt-3">Đang tải dữ liệu thống kê hàng năm...</p>
        </div>
    );

    if (error) return (
        <Alert variant="danger" className="text-center">
            <strong>Lỗi:</strong> {error.message}
        </Alert>
    );

    // Kiểm tra xem tất cả các năm có cùng giá trị min, max, mean không
    const allStatsAreSame = (stats) => {
        if (!stats || stats.length === 0) return false;

        const firstStat = stats[0]; // Lấy giá trị của năm đầu tiên
        return stats.every(stat =>
            stat.min === firstStat.min &&
            stat.max === firstStat.max &&
            stat.mean === firstStat.mean
        );
    };

    return (
        <div className="main-stats-year fade-in" style={{ marginBottom: '40px', marginTop: '50px' }}>
            <div className="text-center mb-4">
                <h2 className="modern-title">
                    <FontAwesomeIcon icon={faCalendarAlt} className="me-3" />
                    Thống kê hàng năm
                </h2>
                <p className="text-muted">Phân tích dữ liệu theo từng năm</p>
            </div>

            {allStatsAreSame(stats) ? (
                <Alert variant="warning" className="text-center">
                    <strong>Thông báo:</strong> Dữ liệu hàng năm không thay đổi
                </Alert>
            ) : (
                <Card className="modern-card">
                    <Card.Header className="text-center">
                        <h5 className="mb-0">
                            <FontAwesomeIcon icon={faChartLine} className="me-2" />
                            Bảng thống kê chi tiết
                        </h5>
                    </Card.Header>
                    <Card.Body className="p-0">
                        <div className="table-responsive">
                            <Table className="modern-table mb-0">
                                <thead>
                                    <tr>
                                        <th className="text-center">
                                            <Badge bg="primary">Năm</Badge>
                                        </th>
                                        <th className="text-center">
                                            <Badge bg="danger">Tối thiểu ({headerUnit})</Badge>
                                        </th>
                                        <th className="text-center">
                                            <Badge bg="success">Tối đa ({headerUnit})</Badge>
                                        </th>
                                        <th className="text-center">
                                            <Badge bg="info">Trung bình ({headerUnit})</Badge>
                                        </th>
                                        <th className="text-center">
                                            <Badge bg="warning" text="dark">Tổng ({headerUnit})</Badge>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.map((row, index) => {
                                        // Kiểm tra nếu min, max và mean bằng nhau (sử dụng epsilon nhỏ để so sánh số thực)
                                        const epsilon = 1e-6;
                                        const isSame =
                                            Math.abs((row.min || 0) - (row.max || 0)) < epsilon &&
                                            Math.abs((row.max || 0) - (row.mean || 0)) < epsilon;
                                        // Nếu bằng nhau thì gán sum = row.mean, ngược lại giữ nguyên row.sum
                                        const sumVal = isSame ? (row.mean || 0) : (row.sum || 0);

                                        return (
                                            <tr key={index} className="table-row-hover">
                                                <td className="text-center fw-bold">
                                                    <span className="year-badge">{row.Year}</span>
                                                </td>
                                                <td className="text-center min-cell">
                                                    {row.min ? row.min.toFixed(2) : 'N/A'}
                                                </td>
                                                <td className="text-center max-cell">
                                                    {row.max ? row.max.toFixed(2) : 'N/A'}
                                                </td>
                                                <td className="text-center mean-cell">
                                                    {row.mean ? row.mean.toFixed(2) : 'N/A'}
                                                </td>
                                                <td className="text-center sum-cell">
                                                    {sumVal ? sumVal.toFixed(2) : 'N/A'}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </Table>
                        </div>
                    </Card.Body>
                </Card>
            )}
        </div>
    );
};

export default AnnualStatistics;
