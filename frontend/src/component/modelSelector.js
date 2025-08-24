import React, { useContext } from 'react';
import { ModelContext } from '../context/selectedModelContext'; // Import ModelContext

const ModelSelector = () => {
    const { selectedModel, handleModelChange, selectedValue, handleValueChange } = useContext(ModelContext);

    // Mảng các mô hình dưới dạng đối tượng: { display: hiển thị, value: giá trị thực }
    const models = [
        { display: 'Chọn mô hình', value: '' },
        { display: 'Gumbel', value: 'gumbel' },
        { display: 'Lognormal', value: 'lognorm' },
        { display: 'Gamma', value: 'gamma' },
        { display: 'Logistic', value: 'logistic' },
        { display: 'Exponential', value: 'expon' },
        { display: 'Generalized Extreme Value', value: 'genextreme' },
        { display: 'Generalized Pareto', value: 'genpareto' },
        { display: 'Pearson3', value: 'pearson3' },
        { display: 'Frechet', value: 'frechet' }
    ];

    const values = [
        { display: 'Chọn giá trị', value: '' },
        { display: 'Min', value: 'min' },
        { display: 'Max', value: 'max' },
        { display: 'Mean', value: 'mean' },
        { display: 'Sum', value: 'sum' }
    ];

    return (
        <div className="col-md-10 container-select-option" style={{ padding: '50px 0', margin: '0 auto' }}>
            <label htmlFor="modelSelect" style={{ fontWeight: 'bold', marginRight: '10px', fontSize: '24px', marginLeft: '100px' }}>
                Chọn mô hình:
            </label>
            <select id="modelSelect" value={selectedModel} onChange={(e) => handleModelChange(e.target.value)}>
                {models.map((model) => (
                    <option key={model.value} value={model.value}>
                        {model.display}
                    </option>
                ))}
            </select>
            <label htmlFor="valueSelect" style={{ fontWeight: 'bold', marginRight: '10px', fontSize: '24px', marginLeft: '100px' }}>
                Chọn giá trị:
            </label>
            <select id="valueSelect" value={selectedValue} onChange={(e) => handleValueChange(e.target.value)}>
                {values.map((item) => (
                    <option key={item.value} value={item.value}>
                        {item.display}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default ModelSelector;
