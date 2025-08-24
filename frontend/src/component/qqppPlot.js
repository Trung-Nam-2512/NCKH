import React, { useState, useEffect, useContext } from 'react';
import Plot from 'react-plotly.js';
import axios from "axios";
import { ModelContext } from '../context/selectedModelContext';
import { useFileInfo } from '../context/fileInfoContext';
import { useUnit } from '../context/unitContext';
import Config from '../config/config';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
const QQPPPlot = ({ dataUpdated, fetch }) => {
    const [qqData, setQQData] = useState([]);
    const [ppData, setPPData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");



    const { selectedModel, selectedValue } = useContext(ModelContext);
    const { fileInfo } = useFileInfo();
    const { unit } = useUnit();
    const headerUnit =
        fileInfo?.unit && fileInfo.unit !== "Unknown"
            ? fileInfo.unit
            : unit || "Unknown";
    useEffect(() => {
        if (selectedModel === 'null') return; // Không fetch 

        const fetchData = async () => {
            setLoading(true);
            try {
                const { data } = await axios.get(`${Config.BASE_URL}/analysis/qq_pp/${selectedModel}?agg_func=${selectedValue}`);
                setQQData(data.qq);
                setPPData(data.pp);
                setError("");
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selectedModel, dataUpdated, fetch]);

    // Prepare dữ liệu cho QQ plot:
    const qq_x = qqData.map(item => item.theoretical);
    const qq_y = qqData.map(item => item.sample);

    // Prepare dữ liệu cho PP plot:
    const pp_x = ppData.map(item => item.theoretical);
    const pp_y = ppData.map(item => item.empirical);

    return (
        <div style={{ padding: "50px" }}>
            {selectedModel === 'null' ? <h2 style={{ textAlign: 'center', marginTop: '30px', marginBottom: '0px' }}>Chọn mô hình để xem biểu đồ ...</h2> : null}
            {loading ? (
                <div className="text-center py-5">
                    <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-3" />
                    <p className="mt-3">Đang tải biểu đồ QQ/PP...</p>
                </div>
            ) : error ? (
                <div>Lỗi: {error}</div>
            ) : selectedModel !== 'null' ? (
                <div className='fix-flex' style={{ display: "flex", flexDirection: "row", gap: "10px" }}>
                    {/* QQ Plot */}
                    <div style={{ flex: 1, border: "1px solid #ccc", borderRadius: "8px", padding: "10px" }}>
                        <h2 style={{ textAlign: 'center', marginTop: '30px', marginBottom: '0px', marginRight: '90px', color: 'blue' }}>Biểu đồ QQ Plot</h2>
                        <Plot
                            data={[
                                {
                                    x: qq_x,
                                    y: qq_y,
                                    mode: 'markers',
                                    type: 'scatter',
                                    marker: { color: 'blue' },
                                    name: `QQ Plot Data (${headerUnit})`,


                                },
                                {
                                    x: [Math.min(...qq_x), Math.max(...qq_x)],
                                    y: [Math.min(...qq_y), Math.max(...qq_y)],  // dùng qq_y Thay vì dùng qq_x
                                    mode: 'lines',
                                    type: 'scatter',
                                    line: { dash: 'dash', color: 'red' },
                                    name: 'Reference line'
                                }
                            ]}
                            layout={{
                                title: {
                                    font: { size: 20 },
                                    x: 0.5,
                                    xanchor: 'center'
                                },

                                xaxis: {
                                    title: "Theoretical Quantiles",
                                    showgrid: true,
                                    zeroline: false,
                                    linecolor: '#636363',
                                    linewidth: 2,
                                    mirror: true,
                                },
                                yaxis: {
                                    title: "Sample Quantiles",
                                    showgrid: true,
                                    zeroline: false,
                                    linecolor: '#636363',
                                    linewidth: 2,
                                    mirror: true
                                },
                                margin: { t: 50, r: 30, b: 50, l: 50 },
                                legend: {
                                    font: { size: 10 }  // Điều chỉnh kích thước font cho toàn bộ legend
                                },
                                paper_bgcolor: "#fff",
                                plot_bgcolor: "#f9f9f9"
                            }}
                            style={{ width: "100%", height: "400px" }}
                            config={{ responsive: true }}
                        />
                    </div>

                    {/* PP Plot */}
                    <div style={{ flex: 1, border: "1px solid #ccc", borderRadius: "8px", padding: "10px" }}>
                        <h2 style={{ textAlign: 'center', marginTop: '30px', marginBottom: '0px', marginRight: '90px', color: 'green' }}>Biểu đồ PP Plot</h2>
                        <Plot
                            data={[
                                {
                                    x: pp_x,
                                    y: pp_y,
                                    mode: 'markers',
                                    type: 'scatter',
                                    marker: { color: 'green' },
                                    name: 'PP Plot Data (%)'
                                },
                                {
                                    x: [0, 1],
                                    y: [0, 1],
                                    mode: 'lines',
                                    type: 'scatter',
                                    line: { dash: 'dash', color: 'red' },
                                    name: 'Reference line'
                                }
                            ]}
                            layout={{
                                title: "PP Plot",
                                xaxis: {
                                    title: "Theoretical CDF",
                                    showgrid: true,
                                    zeroline: false,
                                    linecolor: '#636363',
                                    linewidth: 2,
                                    mirror: true
                                },
                                yaxis: {
                                    title: "Empirical CDF",
                                    showgrid: true,
                                    zeroline: false,
                                    linecolor: '#636363',
                                    linewidth: 2,
                                    mirror: true
                                },
                                margin: { t: 50, r: 30, b: 50, l: 50 },
                                legend: {
                                    font: { size: 10 }  // Điều chỉnh kích thước font cho toàn bộ legend
                                },
                                paper_bgcolor: "#fff",
                                plot_bgcolor: "#f9f9f9"
                            }}
                            style={{ width: "100%", height: "400px" }}

                            config={{ responsive: true }}

                        />
                    </div>
                </div>
            ) : null}
            <hr />
        </div>
    );
};

export default QQPPPlot;
