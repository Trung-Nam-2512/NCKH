// ModelContext.js
import React, { createContext, useState } from 'react';

// Tạo Context
export const ModelContext = createContext();

// Provider để cung cấp Context cho các component con
export const ModelProvider = ({ children }) => {
    const [selectedModel, setSelectedModel] = useState('null'); // Giá trị mặc định là 'gumbel'
    const [selectedValue, setSelectedValue] = useState('null');
    // Các hàm xử lý thay đổi giá trị
    const handleValueChange = (value) => {
        setSelectedValue(value);
    }
    const handleModelChange = (model) => {
        setSelectedModel(model);
    };

    return (
        <ModelContext.Provider value={{ selectedModel, handleModelChange, selectedValue, handleValueChange }}>
            {children}
        </ModelContext.Provider>
    );
};
