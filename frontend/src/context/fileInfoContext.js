// fileInfoContext.js
import React, { createContext, useState, useContext } from 'react';

const FileInfoContext = createContext();

// Provider context
export function FileInfoProvider({ children }) {
    const [fileInfo, setFileInfo] = useState({
        dataType: "Unknown",
        unit: "Unknown",
        fileExtension: "",
        isValid: false,
    });

    const updateFileInfo = (newFileInfo) => {
        setFileInfo(newFileInfo);
    };

    return (
        <FileInfoContext.Provider value={{ fileInfo, updateFileInfo }}>
            {children}
        </FileInfoContext.Provider>
    );
}
// Custom hook để lấy giá trị từ context
export function useFileInfo() {
    return useContext(FileInfoContext);
}
// FileInfoContext.js

export function parseFileName(fileName) {
    const parts = fileName.split("_"); // Tách chuỗi theo dấu "_"
    const fileExtension = fileName.split(".").pop().toLowerCase();
    if (parts.length < 2) {
        // Tên file không theo quy ước
        return {
            dataType: "Unknown",
            unit: "Unknown",
            fileExtension: fileExtension,
            isValid: false,
        };
    }

    let dataType = parts[0];
    let unit = parts[1];
    //Xử lý thêm nếu có nhiều _

    // Xóa các kí tự số và phần mở rộng của file, ví dụ : Rainfall_mm_2023.csv
    if (isNaN(parts[parts.length - 1])) { // Không phải là số thì là đơn vị
        unit = parts[parts.length - 1].split('.')[0]
    }

    return {
        dataType: dataType,
        unit: unit,
        fileExtension: fileExtension,
        isValid: true,
    };
}
