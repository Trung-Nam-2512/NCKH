import React, { useState } from 'react';
import axios from 'axios';
import { useFileInfo, parseFileName } from '../context/fileInfoContext';
import { toast } from 'react-toastify';
import Config from '../config/config';
import { Card, Button, Alert, ProgressBar } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUpload, faFileAlt, faSpinner, faCheckCircle, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons';
import '../assets/fileInput.css';

const FileInput = ({ setData, onDataUpdate }) => {
    const [file, setFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploadSuccess, setUploadSuccess] = useState(null);
    const { updateFileInfo } = useFileInfo();

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        setFile(selectedFile);
        setUploadSuccess(null);
        setUploadProgress(0);
    };

    const handleUpload = async () => {
        if (!file) {
            toast.warning("Vui lòng chọn file!", { position: 'top-center', autoClose: 2000 });
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        setIsUploading(true);
        setUploadProgress(0);

        // Simulate upload progress
        const progressInterval = setInterval(() => {
            setUploadProgress(prev => {
                if (prev >= 90) {
                    clearInterval(progressInterval);
                    return 90;
                }
                return prev + 10;
            });
        }, 200);

        try {
            const response = await axios.post(`${Config.BASE_URL}/data/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            clearInterval(progressInterval);
            setUploadProgress(100);

            onDataUpdate();
            setData(response.data);
            setUploadSuccess(true);

            const fileName = file.name;
            const fileInfo = parseFileName(fileName);

            toast.success("Tải file thành công!", {
                position: 'top-center',
                autoClose: 2000,
                icon: <FontAwesomeIcon icon={faCheckCircle} />
            });

            updateFileInfo(fileInfo);
        } catch (error) {
            clearInterval(progressInterval);
            setUploadProgress(0);

            toast.error("Lỗi khi tải file!", {
                position: 'top-center',
                autoClose: 3000,
                icon: <FontAwesomeIcon icon={faExclamationTriangle} />
            });

            setUploadSuccess(false);
            updateFileInfo({
                dataType: "Unknown",
                unit: "Unknown",
                fileExtension: "",
                isValid: false,
            });
        } finally {
            setIsUploading(false);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');

        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            setFile(droppedFile);
            setUploadSuccess(null);
            setUploadProgress(0);
        }
    };

    return (
        <div className="file-input-container fade-in">
            <Card className="modern-card upload-card">
                <Card.Header className="text-center">
                    <h3 className="mb-0">
                        <FontAwesomeIcon icon={faUpload} className="me-2" />
                        Tải lên File
                    </h3>
                    <p className="text-muted mb-0">Hỗ trợ file CSV và Excel</p>
                </Card.Header>
                <Card.Body>
                    <div
                        className="file-drop-zone"
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <div className="drop-zone-content">
                            <FontAwesomeIcon icon={faFileAlt} className="drop-zone-icon" />
                            <p className="drop-zone-text">
                                {file ? file.name : "Kéo thả file vào đây hoặc click để chọn"}
                            </p>
                            <input
                                type="file"
                                onChange={handleFileChange}
                                className="file-input"
                                accept=".csv,.xlsx,.xls"
                            />
                            <Button
                                variant="outline-primary"
                                className="select-file-btn"
                                onClick={() => document.querySelector('.file-input').click()}
                            >
                                Chọn File
                            </Button>
                        </div>
                    </div>

                    {file && (
                        <div className="file-info mt-3">
                            <div className="file-details">
                                <FontAwesomeIcon icon={faFileAlt} className="me-2" />
                                <span className="file-name">{file.name}</span>
                                <span className="file-size">
                                    ({(file.size / 1024).toFixed(2)} KB)
                                </span>
                            </div>
                        </div>
                    )}

                    {isUploading && (
                        <div className="upload-progress mt-3">
                            <div className="progress-header">
                                <FontAwesomeIcon icon={faSpinner} className="spinning me-2" />
                                <span>Đang tải lên...</span>
                            </div>
                            <ProgressBar
                                now={uploadProgress}
                                variant="success"
                                className="progress-bar-custom"
                                label={`${uploadProgress}%`}
                            />
                        </div>
                    )}

                    <Button
                        onClick={handleUpload}
                        className="upload-btn modern-btn w-100 mt-3"
                        disabled={isUploading || !file}
                        size="lg"
                    >
                        {isUploading ? (
                            <>
                                <FontAwesomeIcon icon={faSpinner} className="spinning me-2" />
                                Đang tải lên...
                            </>
                        ) : (
                            <>
                                <FontAwesomeIcon icon={faUpload} className="me-2" />
                                Tải lên
                            </>
                        )}
                    </Button>

                    {uploadSuccess !== null && (
                        <Alert
                            variant={uploadSuccess ? 'success' : 'danger'}
                            className="mt-3 upload-alert"
                        >
                            <FontAwesomeIcon
                                icon={uploadSuccess ? faCheckCircle : faExclamationTriangle}
                                className="me-2"
                            />
                            {uploadSuccess ? 'Tải file thành công!' : 'Có lỗi xảy ra khi tải file!'}
                        </Alert>
                    )}
                </Card.Body>
            </Card>
        </div>
    );
};

export default FileInput;
