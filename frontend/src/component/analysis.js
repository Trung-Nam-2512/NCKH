import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import Config from '../config/config';
import { ModelContext } from '../context/selectedModelContext';
import { Card, Row, Col, Badge, Alert, ProgressBar } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartBar, faSpinner, faCheckCircle, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons';
import '../assets/analysis.css';

function Analysis({ dataUpdated, fetch }) {
    const [analysis, setAnalysis] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { selectedValue } = useContext(ModelContext);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios
                .get(`${Config.BASE_URL}/analysis/distribution?agg_func=${selectedValue}`);
            setAnalysis(response.data);
        } catch (err) {
            console.error("Error fetching distribution analysis: ", err);
            if (err.response && err.response.status === 404) {
                setAnalysis({});
            } else {
                setError(err);
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (dataUpdated != null && fetch && selectedValue !== 'null') {
            fetchData();
        }
    }, [dataUpdated, fetch, selectedValue]);

    if (loading) {
        return (
            <div className="text-center py-5">
                <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-3" />
                <p className="mt-3">Chờ nạp dữ liệu phân tích...</p>
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="danger" className="text-center">
                <FontAwesomeIcon icon={faExclamationTriangle} className="me-2" />
                <strong>Lỗi:</strong> {error.message}
            </Alert>
        );
    }

    const getDistributionColor = (modelName) => {
        const colors = {
            'gumbel': 'primary',
            'genextreme': 'success',
            'genpareto': 'warning',
            'expon': 'info',
            'lognorm': 'secondary',
            'logistic': 'dark',
            'gamma': 'danger',
            'pearson3': 'light',
            'frechet': 'primary'
        };
        return colors[modelName] || 'primary';
    };

    const getQualityScore = (aic, pValue) => {
        if (!aic || !pValue) return { score: 0, label: 'Không đủ dữ liệu', color: 'secondary' };

        // Tính điểm dựa trên AIC và p-value
        let score = 0;
        if (aic < 10) score += 40;
        else if (aic < 20) score += 30;
        else if (aic < 30) score += 20;
        else score += 10;

        if (pValue > 0.05) score += 60;
        else if (pValue > 0.01) score += 40;
        else if (pValue > 0.001) score += 20;
        else score += 10;

        if (score >= 80) return { score, label: 'Tuyệt vời', color: 'success' };
        if (score >= 60) return { score, label: 'Tốt', color: 'info' };
        if (score >= 40) return { score, label: 'Trung bình', color: 'warning' };
        return { score, label: 'Kém', color: 'danger' };
    };

    return (
        <div className="analysis fade-in" style={{ marginTop: '50px' }}>
            <div className="text-center mb-4">
                <h2 className="modern-title">
                    <FontAwesomeIcon icon={faChartBar} className="me-3" />
                    Chỉ số phân phối xác suất
                </h2>
                <p className="text-muted">Phân tích chất lượng mô hình phân phối</p>
            </div>

            {analysis && Object.keys(analysis).length > 0 ? (
                <Row className="g-4">
                    {Object.keys(analysis).map((model) => {
                        const modelData = analysis[model];
                        const quality = getQualityScore(modelData.AIC, modelData.p_value);

                        return (
                            <Col key={model} xs={12} md={6} lg={4}>
                                <Card className="modern-card analysis-card h-100">
                                    <Card.Header className="text-center">
                                        <Badge bg={getDistributionColor(model)} className="model-badge">
                                            {model.toUpperCase()} Distribution
                                        </Badge>
                                    </Card.Header>
                                    <Card.Body>
                                        <div className="analysis-metrics">
                                            <div className="metric-item">
                                                <div className="metric-label">
                                                    <FontAwesomeIcon icon={faCheckCircle} className="me-2" />
                                                    AIC Score
                                                </div>
                                                <div className="metric-value aic-value">
                                                    {modelData.AIC ? modelData.AIC.toFixed(2) : 'N/A'}
                                                </div>
                                            </div>

                                            <div className="metric-item">
                                                <div className="metric-label">Chi-Square</div>
                                                <div className="metric-value chi-value">
                                                    {modelData.ChiSquare ? modelData.ChiSquare.toFixed(2) : 'N/A'}
                                                </div>
                                            </div>

                                            <div className="metric-item">
                                                <div className="metric-label">p-value</div>
                                                <div className="metric-value pvalue-value">
                                                    {modelData.p_value ? modelData.p_value.toFixed(4) : 'N/A'}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="quality-assessment mt-3">
                                            <div className="quality-header">
                                                <span>Chất lượng mô hình:</span>
                                                <Badge bg={quality.color} className="quality-badge">
                                                    {quality.label}
                                                </Badge>
                                            </div>
                                            <ProgressBar
                                                now={quality.score}
                                                variant={quality.color}
                                                className="quality-progress"
                                                label={`${quality.score}%`}
                                            />
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        );
                    })}
                </Row>
            ) : (
                <div className="text-center py-5">
                    <div className="empty-state">
                        <FontAwesomeIcon icon={faChartBar} className="empty-icon" />
                        <p className="mt-3 text-muted">Chờ nạp dữ liệu để phân tích...</p>
                    </div>
                </div>
            )}

            <div className="parameters-section mt-5">
                <div className="text-center mb-4">
                    <h3 className="modern-subtitle">
                        <FontAwesomeIcon icon={faChartBar} className="me-2" />
                        Giá trị tham số của phân phối xác suất
                    </h3>
                </div>

                <Row className="g-4">
                    {analysis && Object.keys(analysis).length > 0 ? (
                        Object.keys(analysis).map((model) => (
                            analysis[model].params && (
                                <Col key={model} xs={12} md={6} lg={4}>
                                    <Card className="modern-card parameter-card h-100">
                                        <Card.Header className="text-center">
                                            <h5 className="mb-0">
                                                <Badge bg={getDistributionColor(model)}>
                                                    {model.toUpperCase()} Parameters
                                                </Badge>
                                            </h5>
                                        </Card.Header>
                                        <Card.Body>
                                            <div className="parameter-grid">
                                                <div className="param-item">
                                                    <div className="param-label">Shape</div>
                                                    <div className="param-value">
                                                        {analysis[model].params.shape === null
                                                            ? 'None'
                                                            : analysis[model].params.shape ? analysis[model].params.shape.toFixed(3) : 'N/A'}
                                                    </div>
                                                </div>
                                                <div className="param-item">
                                                    <div className="param-label">Loc</div>
                                                    <div className="param-value">
                                                        {analysis[model].params.loc ? analysis[model].params.loc.toFixed(3) : 'N/A'}
                                                    </div>
                                                </div>
                                                <div className="param-item">
                                                    <div className="param-label">Scale</div>
                                                    <div className="param-value">
                                                        {analysis[model].params.scale ? analysis[model].params.scale.toFixed(3) : 'N/A'}
                                                    </div>
                                                </div>
                                            </div>
                                        </Card.Body>
                                    </Card>
                                </Col>
                            )
                        ))
                    ) : (
                        <div className="text-center py-5">
                            <div className="empty-state">
                                <FontAwesomeIcon icon={faChartBar} className="empty-icon" />
                                <p className="mt-3 text-muted">Chờ nạp dữ liệu để xem tham số...</p>
                            </div>
                        </div>
                    )}
                </Row>
            </div>
        </div>
    );
}

export default Analysis;



