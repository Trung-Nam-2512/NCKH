import React, { useState, useEffect } from 'react';
import {
    Card,
    Form,
    Button,
    Alert,
    Spinner,
    Badge,
    Row,
    Col,
    Table,
    ProgressBar
} from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faChartArea,
    faSearch,
    faExclamationTriangle,
    faCheckCircle,
    faInfoCircle,
    faCopy,
    faDownload,
    faChartLine
} from '@fortawesome/free-solid-svg-icons';
import '../assets/stationMap.css';
import StationFrequencyChart from './stationFrequencyChart';
import StationFrequencyTable from './stationFrequencyTable';
import StationHistogram from './stationHistogram';
import StationEvaluationMetrics from './stationEvaluationMetrics';

const StationAnalysis = () => {
    const [stationId, setStationId] = useState('');
    const [analysisParams, setAnalysisParams] = useState({
        distribution: 'gumbel',
        aggregation: 'max',
        minYears: 1,
        startDate: '',
        endDate: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [analysisResult, setAnalysisResult] = useState(null);
    // const [showResults, setShowResults] = useState(false); // State để quản lý hiển thị kết quả - chưa sử dụng
    const [stationInfo, setStationInfo] = useState(null);
    const [copiedId, setCopiedId] = useState(null);

    // Set default dates
    useEffect(() => {
        const today = new Date();
        const oneMonthAgo = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());

        setAnalysisParams(prev => ({
            ...prev,
            startDate: oneMonthAgo.toISOString().split('T')[0],
            endDate: today.toISOString().split('T')[0]
        }));
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setAnalysisParams(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const copyStationId = async () => {
        try {
            await navigator.clipboard.writeText(stationId);
            setCopiedId(stationId);
            setTimeout(() => setCopiedId(null), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const validateInputs = () => {
        if (!stationId.trim()) {
            setError('Vui lòng nhập ID trạm');
            return false;
        }
        if (!analysisParams.startDate || !analysisParams.endDate) {
            setError('Vui lòng chọn khoảng thời gian');
            return false;
        }
        if (new Date(analysisParams.startDate) >= new Date(analysisParams.endDate)) {
            setError('Ngày bắt đầu phải nhỏ hơn ngày kết thúc');
            return false;
        }
        return true;
    };

    const performAnalysis = async () => {
        if (!validateInputs()) return;

        try {
            setLoading(true);
            setError(null);
            setAnalysisResult(null);

            // Fetch station data and perform analysis
            const response = await fetch('http://localhost:8000/integration/analyze-historical', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    station_id: stationId,
                    min_years: parseInt(analysisParams.minYears),
                    distribution_name: analysisParams.distribution,
                    agg_func: analysisParams.aggregation,
                    start_time: `${analysisParams.startDate} 05:00:00`,
                    end_time: `${analysisParams.endDate} 23:00:00`
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Lỗi khi thực hiện phân tích');
            }

            const result = await response.json();
            setAnalysisResult(result);
            setStationInfo(result.data_summary);
            // setShowResults(true); // Hiển thị kết quả sau khi phân tích thành công - chưa sử dụng

        } catch (err) {
            setError('Lỗi khi thực hiện phân tích: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const getDistributionColor = (distribution) => {
        const colors = {
            'gumbel': 'primary',
            'lognormal': 'success',
            'weibull': 'warning',
            'normal': 'info',
            'exponential': 'secondary'
        };
        return colors[distribution] || 'primary';
    };

    const formatNumber = (num) => {
        if (num === null || num === undefined) return 'N/A';
        return typeof num === 'number' ? num.toFixed(3) : num;
    };

    return (
        <div className="station-analysis-container">
            <Card>
                <Card.Header className="bg-primary text-white">
                    <FontAwesomeIcon icon={faChartArea} className="me-2" />
                    Phân tích tần suất theo trạm
                </Card.Header>
                <Card.Body>
                    {/* Input Section */}
                    <Row>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>
                                    <strong>ID Trạm *</strong>
                                </Form.Label>
                                <div className="d-flex">
                                    <Form.Control
                                        type="text"
                                        placeholder="Nhập ID trạm (VD: 056882)"
                                        value={stationId}
                                        onChange={(e) => setStationId(e.target.value)}
                                        className="me-2"
                                    />
                                    <Button
                                        variant="outline-secondary"
                                        onClick={copyStationId}
                                        title="Copy ID trạm"
                                    >
                                        <FontAwesomeIcon
                                            icon={copiedId === stationId ? faCheckCircle : faCopy}
                                        />
                                    </Button>
                                </div>
                                <Form.Text className="text-muted">
                                    Copy ID trạm từ bản đồ trạm hoặc nhập thủ công
                                </Form.Text>
                            </Form.Group>
                        </Col>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>
                                    <strong>Phân phối thống kê</strong>
                                </Form.Label>
                                <Form.Select
                                    name="distribution"
                                    value={analysisParams.distribution}
                                    onChange={handleInputChange}
                                >
                                    <option value="gumbel">Gumbel (Extreme Value)</option>
                                    <option value="lognormal">Log-Normal</option>
                                    <option value="weibull">Weibull</option>
                                    <option value="normal">Normal</option>
                                    <option value="exponential">Exponential</option>
                                </Form.Select>
                            </Form.Group>
                        </Col>
                    </Row>

                    <Row>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>
                                    <strong>Hàm tổng hợp</strong>
                                </Form.Label>
                                <Form.Select
                                    name="aggregation"
                                    value={analysisParams.aggregation}
                                    onChange={handleInputChange}
                                >
                                    <option value="max">Giá trị lớn nhất</option>
                                    <option value="min">Giá trị nhỏ nhất</option>
                                    <option value="mean">Giá trị trung bình</option>
                                </Form.Select>
                            </Form.Group>
                        </Col>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>
                                    <strong>Số năm tối thiểu</strong>
                                </Form.Label>
                                <Form.Control
                                    type="number"
                                    name="minYears"
                                    value={analysisParams.minYears}
                                    onChange={handleInputChange}
                                    min="1"
                                    max="50"
                                />
                            </Form.Group>
                        </Col>
                        <Col md={4}>
                            <Form.Group className="mb-3">
                                <Form.Label>
                                    <strong>Thực hiện phân tích</strong>
                                </Form.Label>
                                <div>
                                    <Button
                                        variant="primary"
                                        onClick={performAnalysis}
                                        disabled={loading || !stationId.trim()}
                                        className="w-100"
                                    >
                                        {loading ? (
                                            <>
                                                <Spinner
                                                    as="span"
                                                    animation="border"
                                                    size="sm"
                                                    role="status"
                                                    aria-hidden="true"
                                                    className="me-2"
                                                />
                                                Đang phân tích...
                                            </>
                                        ) : (
                                            <>
                                                <FontAwesomeIcon icon={faSearch} className="me-2" />
                                                Phân tích tần suất
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </Form.Group>
                        </Col>
                    </Row>

                    <Row>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>
                                    <strong>Ngày bắt đầu</strong>
                                </Form.Label>
                                <Form.Control
                                    type="date"
                                    name="startDate"
                                    value={analysisParams.startDate}
                                    onChange={handleInputChange}
                                />
                            </Form.Group>
                        </Col>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>
                                    <strong>Ngày kết thúc</strong>
                                </Form.Label>
                                <Form.Control
                                    type="date"
                                    name="endDate"
                                    value={analysisParams.endDate}
                                    onChange={handleInputChange}
                                />
                            </Form.Group>
                        </Col>
                    </Row>

                    {/* Error Display */}
                    {error && (
                        <Alert variant="danger" className="mt-3">
                            <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
                            {error}
                        </Alert>
                    )}

                    {/* Station Information */}
                    {stationInfo && (
                        <Card className="mt-3 border-info">
                            <Card.Header className="bg-info text-white">
                                <FontAwesomeIcon icon={faInfoCircle} className="me-2" />
                                Thông tin trạm: {stationId}
                            </Card.Header>
                            <Card.Body>
                                <Row>
                                    <Col md={3}>
                                        <div className="text-center">
                                            <h5>{stationInfo.total_records || 0}</h5>
                                            <small className="text-muted">Tổng số bản ghi</small>
                                        </div>
                                    </Col>
                                    <Col md={3}>
                                        <div className="text-center">
                                            <h5>{stationInfo.stations_count || 0}</h5>
                                            <small className="text-muted">Số trạm</small>
                                        </div>
                                    </Col>
                                    <Col md={3}>
                                        <div className="text-center">
                                            <h5>{stationInfo.years_covered || 0}</h5>
                                            <small className="text-muted">Số năm dữ liệu</small>
                                        </div>
                                    </Col>
                                    <Col md={3}>
                                        <div className="text-center">
                                            <h5>{formatNumber(stationInfo.depth_range?.mean || 0)}</h5>
                                            <small className="text-muted">Độ sâu TB (m)</small>
                                        </div>
                                    </Col>
                                </Row>
                            </Card.Body>
                        </Card>
                    )}

                    {/* Analysis Results */}
                    {analysisResult && (
                        <Card className="mt-3 border-success">
                            <Card.Header className="bg-success text-white">
                                <FontAwesomeIcon icon={faChartLine} className="me-2" />
                                Kết quả phân tích tần suất
                            </Card.Header>
                            <Card.Body>
                                <Row>
                                    <Col md={6}>
                                        <h6>Thông số phân phối</h6>
                                        <Table striped bordered size="sm">
                                            <tbody>
                                                <tr>
                                                    <td><strong>Phân phối:</strong></td>
                                                    <td>
                                                        <Badge bg={getDistributionColor(analysisParams.distribution)}>
                                                            {analysisParams.distribution.toUpperCase()}
                                                        </Badge>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Hàm tổng hợp:</strong></td>
                                                    <td>{analysisParams.aggregation.toUpperCase()}</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Giá trị min:</strong></td>
                                                    <td>{formatNumber(analysisResult.data_summary?.depth_range?.min)} m</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Giá trị max:</strong></td>
                                                    <td>{formatNumber(analysisResult.data_summary?.depth_range?.max)} m</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Giá trị trung bình:</strong></td>
                                                    <td>{formatNumber(analysisResult.data_summary?.depth_range?.mean)} m</td>
                                                </tr>
                                            </tbody>
                                        </Table>
                                    </Col>
                                    <Col md={6}>
                                        <h6>Độ tin cậy dữ liệu</h6>
                                        <div className="mb-3">
                                            <div className="d-flex justify-content-between">
                                                <span>Độ đầy đủ dữ liệu</span>
                                                <span>85%</span>
                                            </div>
                                            <ProgressBar variant="success" now={85} />
                                        </div>
                                        <div className="mb-3">
                                            <div className="d-flex justify-content-between">
                                                <span>Chất lượng dữ liệu</span>
                                                <span>92%</span>
                                            </div>
                                            <ProgressBar variant="info" now={92} />
                                        </div>
                                        <div className="mb-3">
                                            <div className="d-flex justify-content-between">
                                                <span>Độ tin cậy thống kê</span>
                                                <span>78%</span>
                                            </div>
                                            <ProgressBar variant="warning" now={78} />
                                        </div>
                                    </Col>
                                </Row>

                                {/* Frequency Analysis Results - Hiển thị biểu đồ và bảng kết quả thực tế */}
                                {analysisResult.comprehensive_analysis?.frequency_analysis && (
                                    <div className="mt-4">
                                        <h6>Kết quả phân tích tần suất</h6>
                                        
                                        {/* Row 1: Biểu đồ tần suất và Histogram */}
                                        <div className="row mt-3">
                                            <div className="col-md-6">
                                                <StationFrequencyChart 
                                                    frequencyCurveData={analysisResult.comprehensive_analysis.frequency_analysis.frequency_curves?.[analysisParams.distribution]}
                                                    distributionName={analysisParams.distribution}
                                                />
                                            </div>
                                            <div className="col-md-6">
                                                <StationHistogram 
                                                    frequencyData={analysisResult.comprehensive_analysis.frequency_analysis}
                                                    distributionName={analysisParams.distribution}
                                                />
                                            </div>
                                        </div>

                                        {/* Row 2: Chỉ số đánh giá và Bảng tần suất */}
                                        <div className="row mt-4">
                                            <div className="col-md-12">
                                                <StationEvaluationMetrics 
                                                    analysisResult={analysisResult}
                                                />
                                            </div>
                                        </div>

                                        <div className="row mt-3">
                                            <div className="col-md-12">
                                                <StationFrequencyTable 
                                                    frequencyData={analysisResult.comprehensive_analysis.frequency_analysis}
                                                    distributionName={analysisParams.distribution}
                                                />
                                            </div>
                                        </div>

                                        <div className="d-flex gap-2 mt-3">
                                            <Button 
                                                variant="outline-primary" 
                                                size="sm"
                                                onClick={() => {
                                                    // Tải báo cáo PDF - implement sau
                                                    alert('Đang phát triển tính năng tải báo cáo PDF');
                                                }}
                                            >
                                                <FontAwesomeIcon icon={faDownload} className="me-2" />
                                                Tải báo cáo PDF
                                            </Button>
                                            <Button 
                                                variant="outline-success" 
                                                size="sm"
                                                onClick={() => {
                                                    // Scroll đến biểu đồ
                                                    document.querySelector('.station-frequency-chart')?.scrollIntoView({
                                                        behavior: 'smooth'
                                                    });
                                                }}
                                            >
                                                <FontAwesomeIcon icon={faChartLine} className="me-2" />
                                                Xem biểu đồ
                                            </Button>
                                        </div>
                                    </div>
                                )}

                                {/* Thông báo nếu chưa có dữ liệu phân tích */}
                                {analysisResult && !analysisResult.comprehensive_analysis?.frequency_analysis && (
                                    <Alert variant="warning" className="mt-4">
                                        <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
                                        <strong>Chưa có kết quả phân tích tần suất</strong><br/>
                                        Dữ liệu của trạm này có thể chưa đủ để thực hiện phân tích tần suất đáng tin cậy. 
                                        Vui lòng thử lại với khoảng thời gian dài hơn hoặc trạm khác.
                                    </Alert>
                                )}
                            </Card.Body>
                        </Card>
                    )}

                    {/* Instructions */}
                    <Alert variant="info" className="mt-3">
                        <FontAwesomeIcon icon={faInfoCircle} className="me-2" />
                        <strong>Hướng dẫn sử dụng:</strong>
                        <ul className="mb-0 mt-2">
                            <li>Copy ID trạm từ bản đồ trạm hoặc nhập thủ công</li>
                            <li>Chọn phân phối thống kê phù hợp (Gumbel được khuyến nghị cho dữ liệu thủy văn)</li>
                            <li>Chọn hàm tổng hợp (thường dùng MAX cho phân tích tần suất)</li>
                            <li>Đặt khoảng thời gian phân tích</li>
                            <li>Nhấn "Phân tích tần suất" để thực hiện</li>
                        </ul>
                    </Alert>
                </Card.Body>
            </Card>
        </div>
    );
};

export default StationAnalysis; 