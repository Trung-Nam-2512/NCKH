// ChartSelector.jsx
import React, { useContext } from 'react'; // Đã loại bỏ useState vì sử dụng props từ parent
// import ChartRender from './chartRender';
// import FrequencyByModel from './frequencyByModel' // Không sử dụng trong component này
import ChartRender from './chartRender';
import { ModelContext } from '../context/selectedModelContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

const ChartSelector = ({ fetch, dataUpdated }) => {
    // const [selectedModel, setSelectedModel] = useState('gumbel');
    // const [dataUpdate, setDataUpdate] = useState(false); // Đã sử dụng props từ parent
    // const handleDataUpdate = () => { // Đã sử dụng props từ parent
    //     setDataUpdate((prev) => !prev)
    // }

    // const distributionName = selectedModel;
    const { selectedModel, selectedValue } = useContext(ModelContext);

    // Xác định endpoint dựa trên lựa chọn của người dùng
    let endpoint;
    // console.log("day la value ", selectedValue);

    switch (selectedModel) {
        case 'gumbel':
            endpoint = `analysis/frequency_curve_gumbel?agg_func=${selectedValue}`;
            break;
        case 'lognorm':
            endpoint = `analysis/frequency_curve_lognorm?agg_func=${selectedValue}`;
            break;
        case 'gamma':
            endpoint = `analysis/frequency_curve_gamma?agg_func=${selectedValue}`;
            break;
        case 'logistic':
            endpoint = `analysis/frequency_curve_logistic?agg_func=${selectedValue}`;
            break;
        case 'expon':
            endpoint = `analysis/frequency_curve_exponential?agg_func=${selectedValue}`;
            break;
        case 'genextreme':
            endpoint = `analysis/frequency_curve_genextreme?agg_func=${selectedValue}`;
            break;
        case 'genpareto':
            endpoint = `analysis/frequency_curve_gpd?agg_func=${selectedValue}`;
            break;
        case 'frechet':
            endpoint = `analysis/frequency_curve_frechet?agg_func=${selectedValue}`;
            break;
        case 'pearson3':
            endpoint = `analysis/frequency_curve_pearson3?agg_func=${selectedValue}`;
            break;
        default:
            endpoint = 'null';
    }
    if (selectedModel === 'null' || selectedValue === 'null') {
        return (
            <div className="text-center py-5" style={{ marginTop: '100px' }}>
                <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-3" />
                <p className="mt-3">Đang tải biểu đồ...</p>
            </div>
        );
    }

    return (
        <div className="mt-4 container-chart1">

            <div >
                <div >
                    <h2 style={{ alignItems: 'center', textAlign: 'center', marginBottom: '30px', fontWeight: 'bold', color: 'blue' }}>Biểu đồ tần suất</h2>

                    {fetch ? (
                        <ChartRender endpoint={endpoint} dataUpdated={dataUpdated} />
                    ) : (
                        <div style={{ textAlign: 'center', marginTop: '250px', fontWeight: 'bold' }}>Cung cấp dữ liệu để xem kết quả . . .</div>
                    )}
                </div>

            </div>

        </div>
    );
};

export default ChartSelector;
