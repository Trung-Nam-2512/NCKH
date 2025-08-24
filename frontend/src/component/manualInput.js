import React, { useState, useRef, useEffect } from "react";
import Handsontable from "react-handsontable";
import axios from "axios";
import "handsontable/dist/handsontable.full.css";
import styles from "../assets/manualInput.module.css";
import { useUnit } from "../context/unitContext";
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Config from "../config/config";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
// Component con để nhập năm và chọn kiểu nhập
const YearInput = ({ startYear, setStartYear, endYear, setEndYear, isYearly, setIsYearly, onGenerateTable }) => {

    return (
        <div className={styles.yearInputContainer}>
            <label className={styles.yearInputLabel}>
                Năm bắt đầu:
                <input
                    type="number"
                    className={styles.yearInput}
                    value={startYear}
                    onChange={(e) => setStartYear(e.target.value)}
                    placeholder="e.g 2000"
                />
            </label>
            <label className={styles.yearInputLabel}>
                Năm kết thúc:
                <input
                    type="number"
                    className={styles.yearInput}
                    value={endYear}
                    onChange={(e) => setEndYear(e.target.value)}
                    placeholder="e.g 2023"
                />
            </label>
            <label className={styles.yearInputLabel && 'year-label'}>
                Nhập theo năm:
                <input
                    type="checkbox"
                    className={styles.yearCheckbox}
                    checked={isYearly}
                    onChange={(e) => setIsYearly(e.target.checked)}
                />
            </label>
            <button onClick={onGenerateTable} className={styles.generateTableButton && 'generate-table-button'}>
                Tạo bảng dữ liệu
            </button>
        </div>
    );
};

// Component chính
function DataInputForm({ onUploadSuccess, checked }) {
    const [tableData, setTableData] = useState([]);
    const [startYear, setStartYear] = useState("");
    const [endYear, setEndYear] = useState("");
    const [isYearly, setIsYearly] = useState(false);
    const [warning, setWarning] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [columnNames, setColumnNames] = useState({
        year: "Year",
        month: "Month",
        rainfall: "Rainfall",
    });
    const { unit, setUnit, nameColumn, setNameColumn } = useUnit();
    const hotRef = useRef(null);





    const generateTableData = () => {
        const sYear = Number(startYear);
        const eYear = Number(endYear);
        setWarning("");

        if (isNaN(sYear) || isNaN(eYear)) {
            toast.error("Vui lòng nhập năm hợp lệ.", { position: "top-center", autoClose: 1400 });
            return;
        }
        const totalYears = eYear - sYear + 1;
        if (totalYears < 5) {
            toast.error("Số năm phải lớn hơn hoặc bằng 5.", { position: "top-center", autoClose: 1400 });
            return;
        }

        const newData = [];
        if (isYearly) {
            checked(true);
            for (let year = sYear; year <= eYear; year++) {
                newData.push([year, ""]);
            }
        } else {
            checked(false);
            for (let year = sYear; year <= eYear; year++) {
                for (let m = 1; m <= 12; m++) {
                    newData.push([year, `Tháng ${m}`, ""]);
                }
            }
        }
        setTableData(newData);
        setWarning("Nhập xong dữ liệu hãy bấm 'Tính toán'");
        toast.success("Tạo bảng thành công", { position: "top-center", autoClose: 1400 });
    };

    const handleSubmit = () => {
        setWarning("");

        if (!tableData.length) {
            toast.error("Chưa có dữ liệu. Vui lòng tạo bảng dữ liệu.", { position: "top-center", autoClose: 1400 });
            return;
        }

        const updatedData = hotRef.current.hotInstance.getData();

        if (!Array.isArray(updatedData)) {
            updatedData = Object.values(updatedData);
        }
        let transformedData = [];

        if (isYearly) {
            const incompleteRows = updatedData.filter((row) => row[1] === "" || row[1] === null);
            if (incompleteRows.length > 0) {
                toast.error("Vui lòng nhập đầy đủ giá trị Rainfall cho tất cả các năm.", { position: "top-center", autoClose: 1400 });
                return;
            }
            transformedData = updatedData.map((row) => ({
                [columnNames.year]: row[0],
                [columnNames.rainfall]: Number(row[1]),
            }));
        } else {
            const incompleteRows = updatedData.filter((row) => row[2] === "" || row[2] === null);
            if (incompleteRows.length > 0) {
                toast.error("Vui lòng nhập đầy đủ giá trị Rainfall cho tất cả các tháng.", { position: "top-center", autoClose: 1400 });
                return;
            }

            transformedData = updatedData.map((row) => {
                const monthStr = row[1].replace("Tháng ", "").trim();
                const month = parseInt(monthStr, 10);
                return {
                    [columnNames.year]: row[0],
                    [columnNames.month]: month,
                    [columnNames.rainfall]: Number(row[2]),
                };
            });
        }
        setNameColumn(columnNames.rainfall);
        // console.log("day la name column ", columnNames.rainfall);
        // Lưu dữ liệu vào localStorage chỉ khi người dùng ấn submit
        localStorage.setItem("tableData", JSON.stringify(transformedData));
        localStorage.setItem("startYear", startYear);
        localStorage.setItem("endYear", endYear);
        localStorage.setItem("isYearly", isYearly);
        const payload = {
            data: transformedData,
        };

        setIsLoading(true);

        axios
            .post(`${Config.BASE_URL}/data/upload_manual`, payload)
            .then((response) => {
                // console.log("Kết quả: ", response.data);
                if (onUploadSuccess) {
                    onUploadSuccess();
                }
                toast.success("Tính toán thành công", { position: "top-center", autoClose: 1400 });
            })
            .catch((error) => {
                console.error("Lỗi: ", error);
                toast.error("Lỗi khi gửi dữ liệu. Vui lòng kiểm tra lại.", { position: "top-center", autoClose: 1400 });
            })
            .finally(() => {
                setIsLoading(false);
            });
    };

    const handleColumnNameChange = (column, newName) => {
        setColumnNames((prevNames) => ({
            ...prevNames,
            [column]: newName,
        }));
    };

    return (
        <div className={styles.container && 'container-manual-input'} >
            <h2 className={styles.title}>Nhập Dữ Liệu Thủ Công</h2>
            <YearInput
                startYear={startYear}
                setStartYear={setStartYear}
                endYear={endYear}
                setEndYear={setEndYear}
                isYearly={isYearly}
                setIsYearly={setIsYearly}
                onGenerateTable={generateTableData}
            />
            {warning && <div className={styles.warning}>{warning}</div>}


            {/* Dropdown cho đơn vị */}
            <div className={styles.dropdownContainer} >
                {/* Dropdown chọn đơn vị */}
                <label className={styles.label} style={{ color: 'red' }}>Chọn đơn vị đo:</label>
                <select
                    className={styles.dropdownSelect}
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}

                >
                    <option value="mm">mm (millimeters)</option>
                    <option value="m³/s">m³/s  (cubic meters/second)</option>
                    <option value="°C">°C (Celsius)</option>
                    <option value="°F">°F (Fahrenheit)</option>
                    <option value="K">K (Kelvin)</option>
                    <option value="m/s">m/s (meters/second)</option>
                    <option value="km/h">km/h (kilometers/hour)</option>
                    <option value="mph">mph (miles/hour)</option>
                </select>



            </div>


            {tableData.length > 0 && (
                <div className={styles.handsontableContainer}>
                    <div className={styles.yearInputContainer}>
                        <label className={styles.yearInputLabel}>
                            Tên cột năm:
                            <input
                                type="text"
                                className={styles.customColumnNameInput}
                                value={columnNames.year}
                                readOnly="true"

                            />
                        </label>
                        {!isYearly && (
                            <label className={styles.yearInputLabel}>
                                Tên cột tháng:
                                <input
                                    type="text"
                                    className={styles.customColumnNameInput}
                                    value={columnNames.month}
                                    readOnly="true"

                                />
                            </label>
                        )}
                        <label className={styles.yearInputLabel}>
                            Tên cột Rainfall:
                            <input
                                type="text"
                                className={styles.customColumnNameInput}
                                value={columnNames.rainfall}
                                onChange={(e) => handleColumnNameChange("rainfall", e.target.value)}
                            />
                        </label>
                    </div>
                    <div className="handsontable-container">
                        <Handsontable
                            key={isYearly ? `yearly-${tableData.length}` : `monthly-${tableData.length}`}
                            ref={hotRef}
                            data={tableData}
                            colHeaders={
                                isYearly
                                    ? [columnNames.year, columnNames.rainfall]
                                    : [columnNames.year, columnNames.month, columnNames.rainfall]
                            }
                            rowHeaders={true}
                            columns={
                                isYearly
                                    ? [
                                        { data: 0, readOnly: true, className: "col-year" },
                                        { data: 1, className: "col-rainfall" },
                                    ]
                                    : [
                                        { data: 0, readOnly: true, className: "col-year" },
                                        { data: 1, readOnly: true, className: "col-month" },
                                        { data: 2, className: "col-rainfall" },
                                    ]
                            }
                            licenseKey="non-commercial-and-evaluation"
                            dragToScroll={true}
                            dragToFill={true}
                            autoFill={true}
                            colWidths={isYearly ? [200, 230] : [150, 150, 150]}
                        />

                        <button className={styles.submitButton} onClick={handleSubmit} disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <FontAwesomeIcon icon={faSpinner} className="loading-spinner me-2" />
                                    Đang tính toán...
                                </>
                            ) : (
                                'Tính Toán'
                            )}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default DataInputForm;