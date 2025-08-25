"""
DỊCH VỤ XỬ LÝ DỮ LIỆU (DATA SERVICE) - Core service quản lý và xử lý dữ liệu thủy văn

Chức năng chính:
- Upload và validate dữ liệu từ file CSV/Excel
- Chuyển đổi và chuẩn hóa format dữ liệu
- Phát hiện và xử lý dữ liệu thiếu, ngoại lai
- Cung cấp interface thống nhất cho data access
- Cache dữ liệu trong memory để tăng hiệu năng

Hỗ trợ các định dạng dữ liệu:
- Time series hàng năm: [Year, Value] 
- Time series hàng tháng: [Year, Month, Value]
- Dữ liệu manual input từ frontend
"""

import pandas as pd
import numpy as np
from io import BytesIO
from fastapi import UploadFile, HTTPException
import logging
import re
from typing import Dict, Any, Union
from ..models.data_models import UploadManualPayload

class DataService:
    """
    DỊCH VỤ XỬ LÝ DỮ LIỆU TRUNG TÂM
    
    Đây là core service chứa logic xử lý dữ liệu chính của hệ thống.
    Thiết kế theo Singleton pattern để maintain state và cache data.
    
    Attributes:
        data: DataFrame chứa dữ liệu hiện tại đang được xử lý
        main_column: Tên của cột chứa dữ liệu chính (value column)
    """
    
    def __init__(self):
        """
        Khởi tạo DataService với state rỗng
        
        State sẽ được populate khi user upload dữ liệu hoặc
        service load data từ external sources
        """
        self.data: Union[pd.DataFrame, None] = None  # DataFrame chính chứa dữ liệu
        self.main_column: Union[str, None] = None    # Tên cột dữ liệu chính

    def convert_month(self, month_value: Any) -> Union[int, None]:
        """
        Chuyển đổi giá trị tháng từ nhiều định dạng khác nhau thành integer
        
        Xử lý các trường hợp:
        - String có chứa số: "Month 1", "Tháng 12" → extract số
        - String text: "Jan", "January" → trả None (sẽ handle riêng)
        - Số nguyên: 1, 2, 12 → convert trực tiếp
        - Invalid values → None để sau này dropna()
        
        Args:
            month_value: Giá trị tháng ở bất kỳ format nào
            
        Returns:
            int hoặc None: Số tháng (1-12) hoặc None nếu không parse được
        """
        try:
            if isinstance(month_value, str):
                # Tìm tất cả chữ số trong string
                digits = re.findall(r'\d+', month_value)
                if digits:
                    # Lấy số đầu tiên tìm được
                    return int(digits[0])
                else:
                    # Không có số nào → có thể là "Jan", "Feb" → cần xử lý riêng
                    return None
            else:
                # Giá trị không phải string → convert trực tiếp
                return int(month_value)
        except Exception:
            # Bất kỳ lỗi nào → trả None để handle gracefully
            return None

    def detect_main_data_column(self, df: pd.DataFrame) -> str:
        """
        Tự động phát hiện cột chứa dữ liệu chính (không phải Year/Month)
        
        Logic phát hiện:
        - Tìm các cột numeric trong DataFrame
        - Với 3 cột: phải có Year + Month + 1 cột data
        - Với 2 cột: phải có Year + 1 cột data  
        - Đảm bảo có ít nhất 1 cột số để phân tích
        
        Args:
            df: DataFrame cần phân tích
            
        Returns:
            str: Tên của cột chứa dữ liệu chính
            
        Raises:
            ValueError: Khi không tìm thấy cột số hoặc format không hợp lệ
        """
        # Tìm tất cả cột có kiểu dữ liệu số
        numeric_columns = df.select_dtypes(include=np.number).columns
        
        if len(numeric_columns) == 0:
            raise ValueError("Không tìm thấy cột số trong dữ liệu. Cần ít nhất 1 cột số để phân tích.")
        
        # Xử lý theo số cột trong DataFrame
        if len(df.columns) == 3:
            # Format: [Year, Month, Value] - time series hàng tháng
            if "Year" in df.columns and "Month" in df.columns:
                for col in df.columns:
                    if col not in ["Year", "Month"]:
                        return col
            else:
                raise ValueError("Dữ liệu 3 cột phải có định dạng: Year, Month, [Tên cột dữ liệu]")
                
        elif len(df.columns) == 2:
            if "Year" in df.columns:
                for col in df.columns:
                    if col != "Year":
                        return col
            else:
                raise ValueError("Phải có cột Year khi dữ liệu có 2 cột.")
        raise ValueError("Không tìm thấy cột dữ liệu phù hợp. Vui lòng kiểm tra lại dữ liệu.")

    def process_data(self, df: pd.DataFrame, main_column: str) -> pd.DataFrame:
        """
        Xử lý DF để nhất quán: Convert Month, expand no Month thành 12 rows/year, filter >0.
        - Fix: Thêm dropna cho Month nếu có (tránh NaN từ convert_month invalid).
        - Raise nếu DF empty sau process (edge case empty data).
        - Lý do: Trong thủy văn, Month NaN có thể từ data bẩn → drop để agg chính xác.
        """
        if "Month" in df.columns:
            df["Month"] = df["Month"].apply(self.convert_month)
            df = df.dropna(subset=["Month"])  # Drop rows với Month NaN
        else:
            if "Year" not in df.columns:
                raise ValueError("Dữ liệu phải chứa cột 'Year'")
            logging.info("Không có cột 'Month'. Tạo tự động 12 tháng cho mỗi năm với giá trị của năm đó.")
            new_rows = []
            for idx, row in df.iterrows():
                year = row["Year"]
                yearly_value = row[main_column]
                for m in range(1, 13):
                    new_rows.append({"Year": year, "Month": m, main_column: yearly_value})
            df = pd.DataFrame(new_rows)
        df = df[df[main_column] > 0]  # Loại bỏ giá trị không hợp lệ
        if df.empty:
            raise HTTPException(status_code=400, detail="Dữ liệu rỗng sau xử lý (có thể tất cả giá trị <=0 hoặc NaN)")
        return df

    async def upload_file(self, file: UploadFile) -> Dict:
        try:
            contents = await file.read()
            logging.info(f"Đã nhận file: {file.filename}")
            if file.filename.endswith('.csv'):
                df = pd.read_csv(BytesIO(contents), on_bad_lines='skip')
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(BytesIO(contents))
            else:
                raise HTTPException(status_code=400, detail="File type not supported")
            
            main_column = self.detect_main_data_column(df)
            df = self.process_data(df, main_column)
            
            self.data = df
            self.main_column = main_column
            return {"status": "success", "data": df.to_dict(orient="records")}
        except Exception as e:
            logging.error(f"Lỗi khi xử lý file: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def upload_manual(self, payload: UploadManualPayload) -> Dict:
        """
        Upload manual từ JSON payload.
        - Fix: Sau to_numeric, dropna main_column để loại NaN (từ coerce invalid values).
        - Lý do: Tránh agg NaN dẫn đến stats/analysis nan.
        """
        try:
            if not isinstance(payload.data, list):
                raise HTTPException(status_code=400, detail="Payload phải chứa trường 'data' dưới dạng danh sách")
            
            df = pd.DataFrame(payload.data)
            
            if "Year" not in df.columns:
                raise HTTPException(status_code=400, detail="Dữ liệu phải chứa cột 'Year'")
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
            
            main_column = self.detect_main_data_column(df)
            df[main_column] = pd.to_numeric(df[main_column], errors="coerce")
            
            df = df.dropna(subset=[main_column])  # Drop NaN in main_column
            
            df = self.process_data(df, main_column)
            
            self.data = df
            self.main_column = main_column
            
            return {"status": "success", "data": df.to_dict(orient="records")}
        except Exception as e:
            logging.error(f"Lỗi trong /upload_manual: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))