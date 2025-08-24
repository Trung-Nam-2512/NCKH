// import dotenv from 'dotenv';
// dotenv.config();

const Config = {
    // BASE_URL: 'https://tstv.baonamdts.com/api',
    BASE_URL: 'http://localhost:8000',
    BASE_PROXY: 'https://my-worker.trungnampyag.workers.dev',
    // Mapbox Access Token - Tự động lấy từ .env hoặc sử dụng token thực tế
    MAPBOX_ACCESS_TOKEN: process.env.MAPBOX_ACCESS_TOKEN || 'pk.eyJ1IjoibmFta2lzaTI1MTIiLCJhIjoiY21jeGVqeGduMGRhdTJsb2V2N2MweXc1ciJ9.naZfpBG6ZynTLBC6fQDFRg'
}
export default Config;