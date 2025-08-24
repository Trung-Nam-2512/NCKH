import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { useFileInfo } from '../context/fileInfoContext';
import { useUnit } from '../context/unitContext';
import Config from '../config/config';
import * as d3 from 'd3';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

// Hàm chuyển đổi xác suất vượt (theo phần trăm) sang reduced variate
const toReducedVariate = (pPercent) => {
    const np = 1 - pPercent / 100; // xác suất không vượt
    return -Math.log(-Math.log(np));
};

const PlotlyFrequencyChart = ({ endpoint, dataUpdated }) => {
    const [chartData, setChartData] = useState({
        theoretical_curve: [],
        empirical_points: []
    });

    const { fileInfo } = useFileInfo();
    const { nameColumn, unit } = useUnit();
    const headerTitle =
        fileInfo?.dataType && fileInfo.dataType !== 'Unknown'
            ? fileInfo.dataType
            : nameColumn || 'Unknown';
    const headerUnit =
        fileInfo?.unit && fileInfo.unit !== 'Unknown'
            ? fileInfo.unit
            : unit || 'Unknown';
    // Giá trị mặc định cho màn hình lớn
    const defaultWidth = 600;
    const defaultHeight = 550;

    const [chartSize, setChartSize] = useState({
        width: window.innerWidth > 768 ? defaultWidth : null,
        height: window.innerWidth > 768 ? defaultHeight : null,
        autosize: window.innerWidth <= 768
    });

    useEffect(() => {
        const handleResize = () => {
            setChartSize({
                width: window.innerWidth > 768 ? defaultWidth : null,
                height: window.innerWidth > 768 ? defaultHeight : null,
                autosize: window.innerWidth <= 768
            });
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);
    useEffect(() => {
        if (!endpoint) return;
        const controller = new AbortController();
        const signal = controller.signal;
        const fetchData = async () => {
            try {
                const response = await fetch(`${Config.BASE_URL}/${endpoint}`, { signal });
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                setChartData(data);
            } catch (error) {
                if (error.name === 'AbortError') console.log('Fetch aborted');
                else console.error('Error fetching data:', error);
            }
        };
        if (dataUpdated !== null) {
            fetchData();
        }
        return () => {
            controller.abort();
        };
    }, [endpoint, dataUpdated]);

    if (!chartData || !chartData.theoretical_curve || !chartData.empirical_points) {
        return (
            <div className="text-center py-5">
                <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-3" />
                <p className="mt-3">Đang tải biểu đồ...</p>
            </div>
        );
    }



    const originalTicks = [0.01, 0.1, 1, 10, 50, 90, 99];

    const tickPositions = originalTicks.map(x => toReducedVariate(x));

    // Tính phạm vi trục x từ dữ liệu
    const minX = d3.min(chartData.theoretical_curve, d => d.P_percent);
    const maxX = d3.max(chartData.theoretical_curve, d => d.P_percent);
    const xRange = [
        toReducedVariate(minX),
        toReducedVariate(maxX)
    ];

    // Tính phạm vi trục y dựa trên toàn bộ dữ liệu
    const allYValues = [
        ...chartData.theoretical_curve.map(pt => pt.Q),
        ...chartData.empirical_points.map(pt => pt.Q)
    ];
    const maxY = Math.max(...allYValues);
    const dynamicMaxY = Math.ceil(maxY * 1.1);
    const StartdynamicMaxY = Math.ceil(maxY / 10);
    // Tạo mảng tick tự động từ StartdynamicMaxY đến dynamicMaxY với 5 tick (hoặc số bạn mong muốn)
    let yTicks = d3.ticks(StartdynamicMaxY, dynamicMaxY, 5);
    // Loại bỏ tick đầu tiên (nếu nó bằng StartdynamicMaxY)
    if (yTicks[0] === StartdynamicMaxY) {
        yTicks.shift();
    }
    const theoreticalData = {
        x: chartData.theoretical_curve.map(pt => pt.P_percent), // dùng giá trị gốc
        y: chartData.theoretical_curve.map(pt => pt.Q),
        type: 'scatter',
        mode: 'lines',
        name: 'Phân bố Gumbel',
        line: { color: 'blue', width: 2, shape: 'spline', smoothing: 0.5 }
    };

    const empiricalData = {
        x: chartData.empirical_points.map(pt => pt.P_percent), // dùng giá trị gốc
        y: chartData.empirical_points.map(pt => pt.Q),
        type: 'scatter',
        mode: 'markers',
        name: 'Điểm kinh nghiệm',
        marker: { color: 'orange', size: 6 }
    };

    const layout = {
        // title: { text: 'Đường Tần Suất (Gumbel Probability Plot)', font: { size: 16, color: 'black' } },
        width: chartSize.autosize ? null : chartSize.width,
        height: chartSize.autosize ? null : chartSize.height,
        autosize: chartSize.autosize, // Chỉ auto khi màn hình nhỏ
        xaxis: {
            type: 'log',
            tickvals: [0.01, 0.1, 1, 10, 50, 99],  // các giá trị  muốn hiển thị
            ticktext: ['0.01', '0.1', '1', '10', '50', '99'],  // nhãn tương ứng
            title: { text: 'Xác suất vượt (%)', font: { size: 12 } },
            tickfont: { size: 10 },
            showgrid: true,
            gridcolor: '#E5E5E5',
            gridwidth: 1,
            zeroline: false,
            showline: true,
            linecolor: 'black',
            linewidth: 2
        },
        yaxis: {
            title: { text: `${headerTitle} (${headerUnit})`, font: { size: 12 } },
            range: [0, dynamicMaxY],
            tickfont: { size: 10 },
            showgrid: true,
            gridcolor: '#E5E5E5',
            gridwidth: 1,
            zeroline: false,
            showline: false
        },
        margin: { l: 50, r: 30, t: 50, b: 60 },
        hovermode: 'closest',
        showlegend: true,
        legend: {
            x: 0.5,
            y: -0.2,
            xanchor: 'center',
            yanchor: 'top',
            orientation: 'h',
            bgcolor: 'rgba(255,255,255,0.7)',
            bordercolor: '#E2E2E2',
            borderwidth: 1
        },
        shapes: [
            {
                type: 'line',
                xref: 'x',
                yref: 'paper',
                x0: 0.01,
                x1: 0.01,
                y0: 0,
                y1: 1,
                line: { color: 'red', width: 2, dash: 'dash' }
            },
            {
                type: 'line',
                xref: 'x',
                yref: 'paper',
                x0: 0.1,
                x1: 0.1,
                y0: 0,
                y1: 1,
                line: { color: 'green', width: 2, dash: 'dash' }
            },
            {
                type: 'line',
                xref: 'x',
                yref: 'paper',
                x0: 1,
                x1: 1,
                y0: 0,
                y1: 1,
                line: { color: 'blue', width: 2, dash: 'dash' }
            }
        ]
    }








    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: 'duong-tan-suat',
            height: 550,
            width: 600,
            scale: 2
        }
    };

    return (
        <Plot
            data={[theoreticalData, empiricalData]}
            layout={layout}
            config={config}
            style={{ width: '100%', height: '100%' }}
        />
    );
}
export default PlotlyFrequencyChart;
