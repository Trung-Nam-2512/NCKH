import axios from 'axios';
import React, { useEffect, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    BarController,
    LineElement,
    LineController,  // Import thêm LineController
    PointElement,
    Legend,
    Tooltip,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import { useFileInfo } from '../context/fileInfoContext';
import { useUnit } from '../context/unitContext';
import Config from '../config/config';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarController,
    BarElement,
    LineController,  // Đăng ký LineController
    LineElement,
    PointElement,
    Legend,
    Tooltip
);

const HistogramWithTheoreticalCurve = ({ endpoint, dataUpdated, fetch }) => {
    const [dataAPI, setDataAPI] = useState(null);
    const [isSmallScreen, setIsSmallScreen] = useState(window.innerWidth <= 768);
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

    useEffect(() => {
        const handleResize = () => {
            setIsSmallScreen(window.innerWidth <= 768);
        };

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);



    const fetchData = async () => {
        if (!fetch) return; // Chỉ fetch khi fetch === true

        try {
            const { data } = await axios.get(`${Config.BASE_URL}${endpoint}`);
            setDataAPI(data);
        } catch (error) {
            console.error('Error fetching data:', error.message);
        }
    };

    useEffect(() => {

        fetchData();
    }, [endpoint, dataUpdated, fetch]);


    if (!dataAPI || !dataAPI.histogram) {
        return (
            <div className="text-center py-5">
                <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-3" />
                <p className="mt-3">Đang tải biểu đồ tần số...</p>
            </div>
        );
    }

    // Giải nén dữ liệu từ backend
    const { histogram } = dataAPI;
    const { counts, bin_midpoints, expected_counts } = histogram;

    // Cấu hình dữ liệu cho biểu đồ: dùng bar chart cho empirical counts
    // và line chart cho expected counts từ mô hình đã fit
    const chartData = {
        labels: bin_midpoints.map(value => Number(value.toFixed(2))), // Làm tròn midpoint, // trung điểm các bin (đơn vị mm)
        datasets: [
            {
                type: 'bar',
                label: 'Empirical Counts',
                data: counts,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,

            },
            {
                type: 'line',
                label: `Expected Counts (${endpoint.charAt(0).toUpperCase() + endpoint.slice(1)})`,
                data: expected_counts,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                fill: false,
                tension: 0.4,
            },
        ],
    };

    const optionsHistogram = {
        maintainAspectRatio: isSmallScreen, // Quan trọng: Đặt thành false để chiều cao có thể tùy chỉnh
        height: 400,
        scales: {
            x: {
                title: {
                    display: true,
                    text: `${headerTitle} (${headerUnit})`,
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Count',


                },
                beginAtZero: true,
            },
        },
        plugins: {
            legend: {
                display: false,

            }
        },

    };

    return (
        <div style={{ padding: '0px', width: '100%', height: '100%' }} className='fix-histogram'>
            <Chart type="bar" data={chartData} options={optionsHistogram} />
        </div>
    );
};

export default HistogramWithTheoreticalCurve;
