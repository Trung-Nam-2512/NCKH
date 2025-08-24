import React, { useState } from 'react';
import { Container, Row, Col, Navbar, Nav, Card } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import {
  faUpload, faChartLine,
  faChartBar, faTable, faSlidersH, faFileAlt,
  faDatabase, faArrowDown, faArrowUp, faCaretDown,
  faBell, faUser, faSignInAlt, faSignOutAlt, faKey,
  faRightToBracket
} from '@fortawesome/free-solid-svg-icons';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
// Import các components con
import FileInput from './component/fileInput';
import DataInputForm from './component/manualInput';
import ChartSelector from './component/chartSelector';
import StatsDisplay from './component/descriptiveStats';
import QQPPPlot from './component/qqppPlot';
import QuantileSelector from './component/quantileSelector';
import FrequencyAnalysisTable from './component/frequencyAnalysis';
import FrequencyByModel from './component/frequencyByModel';
import AnnualStatistics from './component/annual';
import ModelSelector from './component/modelSelector';
import Sidebar from './component/sideBar';
import Analysis from './component/analysis';
import logo from './assets/assets'
import Footer from './component/footer';
import SampleDataGuide from './component/sampleDataGuid';
import { FileInfoProvider } from './context/fileInfoContext'
import Map from './component/map';
import StationMap from './component/stationMap';
import StationAnalysis from './component/stationAnalysis';
import TestQuantile from './component/testQuantile';
import AdvancedStationMap from './component/advancedStationMap';
import { UnitProvider } from './context/unitContext';
import './app.css';
import './assets/sidebar.css';

library.add(faUpload, faChartLine, faChartBar,
  faTable, faSlidersH, faFileAlt, faDatabase, faArrowDown, faArrowUp,
  faCaretDown, faBell, faUser, faSignInAlt, faSignOutAlt,
  faKey);

const App = () => {
  const [data, setData] = useState(null);
  const [dataUpdate, setDataUpdate] = useState(false);
  const [fetch, setFetch] = useState(false);
  const [checkInput, setCheckInput] = useState(true);
  const [activeSection, setActiveSection] = useState('tai-len-file');

  const handleFileDataReceived = (receivedData) => {
    setData(receivedData);
    setFetch(true);
  };

  const handleDataUpdate = () => {
    setDataUpdate((prev) => !prev);
  };

  const handleSectionChange = (section) => {
    setActiveSection(section);
  };
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Thêm state để quản lý trạng thái sidebar

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleCloseSideBar = () => {
    setIsSidebarOpen(false);
  }

  const handleOverlayClick = () => {
    setIsSidebarOpen(false);
  };
  return (
    <FileInfoProvider>
      <UnitProvider>
        <Container fluid className="app-container p-0">
          <Navbar variant="dark" expand="xxl" className="app-navbar fixed-top">
            <Container fluid>
              <Navbar.Toggle aria-controls="basic-navbar-nav" onClick={toggleSidebar} />
              <Navbar.Collapse id="basic-navbar-nav" className="justify-content-center d-flex">
                <Navbar.Brand href="#home" className="app-logo">
                  <img
                    src={logo}
                    alt="Logo"
                    height="70"
                    className="d-inline-block align-top app-logo-image"
                  />
                  <span >PHẦN MỀM PHÂN TÍCH TẦN SUẤT DỮ LIỆU KHÍ TƯỢNG THỦY VĂN</span>
                </Navbar.Brand>
                <Nav className="ms-auto app-nav-links">
                  {/* Nút thông báo */}
                  <Nav.Link href="#notifications" className="app-notification-link">
                    <FontAwesomeIcon icon={faBell} />
                  </Nav.Link>

                  {/* Nút đăng nhập */}
                  <Nav.Link href="#login" className="app-login-link">
                    <FontAwesomeIcon icon={faRightToBracket} /> Đăng nhập
                  </Nav.Link>

                  {/* Nút người dùng */}
                  <Nav.Link href="#user" className="app-user-link">
                    <FontAwesomeIcon icon={faUser} />
                  </Nav.Link>



                </Nav>
              </Navbar.Collapse>
            </Container>
          </Navbar>


          <Row className="app-content">
            {/* Overlay for mobile sidebar */}
            <div
              className={`sidebar-overlay ${isSidebarOpen ? 'active' : ''}`}
              onClick={handleOverlayClick}
            ></div>

            {/* Sidebar */}
            <Col xs={12} md={2} className={`app-sidebar ${isSidebarOpen ? 'open' : ''}`}>
              <Sidebar onSectionChange={handleSectionChange} activeSection={activeSection} handleCloseSideBar={handleCloseSideBar} />
            </Col>

            {/* Main Content */}
            <Col xs={10} className={`app-main-content fix-flex ${isSidebarOpen ? 'sidebar-open' : ''}`}>
              {/* Tải lên file */}
              {activeSection === 'tai-len-file' && (
                <Card className='section-card'>

                  <Card.Body>
                    <Row className="row-input">
                      <Col md={6} style={{ marginTop: '70px' }}>
                        <FileInput setData={handleFileDataReceived} onDataUpdate={handleDataUpdate} />

                      </Col>
                      <Col md={6} className='mt-3'>
                        <SampleDataGuide />
                      </Col>
                    </Row>



                  </Card.Body>
                </Card>
              )}





              {/* Nhập Dữ liệu */}
              {activeSection === 'nhap-du-lieu' && (
                <Card className='section-card'>

                  <Card.Body>
                    <Row className="row-input">

                      <Col md={12}>
                        <DataInputForm onUploadSuccess={() => setFetch(true)} checked={setCheckInput} />
                      </Col>

                    </Row>
                  </Card.Body>
                </Card>
              )}

              {/* Xem Thống Kê */}
              {activeSection === 'xem-thong-ke' && (
                <Card className='section-card'>

                  <Card.Body>
                    <Row className='row-stats' >
                      {!fetch && <h2 style={{ textAlign: 'center', marginTop: '50px' }}>Nhập dữ liệu để xem thống kê...</h2>}

                      <Col md={12} className='stats-year mb-4'>
                        <AnnualStatistics key={dataUpdate} dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                      <Col md={12} className='stats-month'>
                        <StatsDisplay key={dataUpdate} dataUpdated={dataUpdate} fetch={fetch} checked={checkInput} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}
              {/* Dữ liệu API */}
              {activeSection === 'du-lieu-api' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='row-stats' >
                      <Col md={12} className='stats-year'>
                        <Map key={dataUpdate} dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}

              {/* Bản đồ trạm */}
              {activeSection === 'ban-do-tram' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='row-stats' >
                      <Col md={12} className='stats-year'>
                        <StationMap />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}

              {/* Bản đồ nâng cao */}
              {activeSection === 'ban-do-nang-cao' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='row-stats' >
                      <Col md={12} className='stats-year'>
                        <AdvancedStationMap />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}

              {/* Phân tích theo trạm */}
              {activeSection === 'phan-tich-tram' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='row-stats' >
                      <Col md={12} className='stats-year'>
                        <StationAnalysis />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}

              {/* Theo dõi realtime */}
              {activeSection === 'theo-doi-realtime' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='row-stats' >
                      <Col md={12} className='stats-year'>
                        <StationMap />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}

              {/* Kết Quả (Bao gồm cả Chọn Mô Hình) */}
              {activeSection === 'ket-qua' && (
                <Card className='section-card'>
                  <Card.Body>
                    {/* Chọn Mô Hình */}
                    <Row className='row-select-model'>
                      <Col md={12}>

                        <ModelSelector />
                      </Col>
                    </Row>
                    {/*Biểu đồ */}
                    {/* row-cols-1: Khi màn hình nhỏ (xs, sm) thì mỗi hàng sẽ chỉ có 1 cột (chiếm toàn bộ chiều rộng). */}
                    <Row className='row-chart'>
                      <Col md={6} xs={12} >
                        <ChartSelector key={dataUpdate} dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                      <Col md={6} xs={12} >
                        <QuantileSelector dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}
              {/* Biểu đồ QQ-PP */}
              {activeSection === 'bieu-do-qqpp' && (
                <Card className='section-card'>

                  <Card.Body>
                    <Row className='pp-qq-chart'>
                      <Col md={12}>
                        <QQPPPlot dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}
              {/* Chỉ số phân tích */}
              {activeSection === 'chi-so-phan-tich' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='analyst-model'>
                      <Col md={12}>
                        <h2 style={{ textAlign: 'center', marginTop: '100px', marginBottom: '0px', marginRight: '80px', color: 'blue' }}>Chỉ số phân phối xác suất</h2>

                        <Analysis dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}
              {/* Kết quả mô hình */}
              {activeSection === 'ket-qua-mo-hinh' && (
                <Card className='section-card'>

                  <Card.Body>
                    <Row className='row-result'>
                      <Col md={12}>
                        <FrequencyByModel key={dataUpdate} dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}
              {/* Phân tích dòng chảy */}
              {activeSection === 'phan-tich-dong-chay' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='row-result2'>
                      <Col md={12}>
                        <FrequencyAnalysisTable key={dataUpdate} dataUpdated={dataUpdate} fetch={fetch} checked={checkInput} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}

              {/* Test Quantile */}
              {activeSection === 'test-quantile' && (
                <Card className='section-card'>
                  <Card.Body>
                    <Row className='row-result2'>
                      <Col md={12}>
                        <TestQuantile endpoint="/analysis/histogram" dataUpdated={dataUpdate} fetch={fetch} />
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}
            </Col>
          </Row>
          <Footer />
          <ToastContainer />
        </Container>
      </UnitProvider>

    </FileInfoProvider>

  );
};

export default App;
