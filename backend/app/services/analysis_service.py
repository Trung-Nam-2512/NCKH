# Dịch vụ phân tích thống kê và đánh giá các mô hình phân phối xác suất
# Tính toán AIC, Chi-square, tần suất xuất hiện cho dữ liệu khí tượng thủy văn
import pandas as pd
import numpy as np
from scipy.stats import gumbel_r, genextreme, genpareto, expon, lognorm, logistic, gamma, chi2, pearson3
from fastapi import HTTPException
from starlette.responses import JSONResponse
from typing import Dict, Tuple, Callable, List, Any
from .data_service import DataService
from ..utils.helpers import extract_params, validate_agg_func
from datetime import datetime, timezone
import logging

class DistributionBase:
    """Lớp cơ sở chứa các hàm của mô hình phân phối xác suất"""
    def __init__(self, name: str, fit_func: Callable, ppf_func: Callable, cdf_func: Callable, pdf_func: Callable, logpdf_func: Callable):
        self.name = name           # Tên mô hình phân phối
        self.fit = fit_func        # Hàm ước lượng tham số
        self.ppf = ppf_func        # Hàm quantile (percent point function)
        self.cdf = cdf_func        # Hàm phân phối tích lũy
        self.pdf = pdf_func        # Hàm mật độ xác suất
        self.logpdf = logpdf_func  # Logarithm của hàm mật độ xác suất

# Từ điển các mô hình phân phối xác suất hỗ trợ trong hệ thống
# Bao gồm các mô hình phổ biến trong thủy văn học
distributions: Dict[str, DistributionBase] = {
    "gumbel": DistributionBase("Gumbel", gumbel_r.fit, gumbel_r.ppf, gumbel_r.cdf, gumbel_r.pdf, gumbel_r.logpdf),
    "genextreme": DistributionBase("Generalized Extreme Value", genextreme.fit, genextreme.ppf, genextreme.cdf, genextreme.pdf, genextreme.logpdf),
    "genpareto": DistributionBase("GPD", genpareto.fit, genpareto.ppf, genpareto.cdf, genpareto.pdf, genpareto.logpdf),
    "expon": DistributionBase("Exponential", expon.fit, expon.ppf, expon.cdf, expon.pdf, expon.logpdf),
    "lognorm": DistributionBase("Lognormal", lognorm.fit, lognorm.ppf, lognorm.cdf, lognorm.pdf, lognorm.logpdf),
    "logistic": DistributionBase("Logistic", logistic.fit, logistic.ppf, logistic.cdf, logistic.pdf, logistic.logpdf),
    "gamma": DistributionBase("Gamma", gamma.fit, gamma.ppf, gamma.cdf, gamma.pdf, gamma.logpdf),
    "pearson3": DistributionBase("Pearson3", pearson3.fit, pearson3.ppf, pearson3.cdf, pearson3.pdf, pearson3.logpdf),
    "frechet": DistributionBase("Frechet", genextreme.fit, genextreme.ppf, genextreme.cdf, genextreme.pdf, genextreme.logpdf),
}

class AnalysisService:
    """Dịch vụ chính để thực hiện các phân tích thống kê và tần suất"""
    def __init__(self, data_service: DataService):
        self.data_service = data_service  # Dịch vụ quản lý dữ liệu

    def get_distribution_analysis(self, agg_func: str= 'max'):
        """
        Phân tích đánh giá các mô hình phân phối xác suất trên dữ liệu
        Tính toán các chỉ số: AIC, Chi-square, p-value, đánh giá chất lượng dữ liệu
        
        Cải tiến chủ yếu:
        - Sử dụng CDF chính xác thay vì xấp xỉ PDF cho dữ liệu liên tục
        - Tính bậc tự do (df) chuẩn cho kiểm định tính phù hợp
        - Xử lý an toàn các trường hợp dữ liệu nhỏ và cảnh báo người dùng
        - Đánh giá chất lượng dữ liệu dựa trên số năm quan trắc
        """
        # Lấy dữ liệu và kiểm tra tính hợp lệ
        df = self.data_service.data
        main_column = self.data_service.main_column
        if df is None:
            raise HTTPException(status_code=404, detail="Dữ liệu chưa được tải")
        validate_agg_func(agg_func)
        # Tổng hợp dữ liệu theo năm (lấy giá trị cực đại hoặc tổng)
        aggregated = df.groupby('Year')[main_column].agg(agg_func).values

        # Kiểm tra dữ liệu đủ để phân tích phân phối
        n = len(aggregated)  # Số năm quan trắc
        if n < 3:
            raise HTTPException(
                status_code=400, 
                detail=f"Không đủ dữ liệu để phân tích phân phối xác suất. Cần ít nhất 3 năm dữ liệu, hiện tại chỉ có {n} năm. "
                       f"Phân tích phân phối yêu cầu đủ điểm dữ liệu để ước lượng tham số và kiểm định độ phù hợp."
            )
        
        # Tính số lượng khoảng (bins) dựa trên công thức Sturges
        sturges_bins = int(np.ceil(1 + np.log2(n + 1))) if n > 0 else 5
        num_bins = max(5, sturges_bins)  # Tối thiểu 5 khoảng

        # Đánh giá chất lượng dữ liệu dựa trên độ dài chuỗi thời gian
        data_quality_grade = "excellent"
        uncertainty_level = "low"
        
        if n < 10:
            data_quality_grade = "poor"      # Kém
            uncertainty_level = "very high"  # Độ không chắc chắn rất cao
            logging.warning(f"⚠️ Chuỗi thời gian rất ngắn ({n} năm) - kết quả có độ không chắc chắn rất cao")
        elif n < 20:
            data_quality_grade = "fair"       # Khá 
            uncertainty_level = "high"       # Độ không chắc chắn cao
            logging.warning(f"⚠️ Chuỗi thời gian ngắn ({n} năm) - kết quả có độ không chắc chắn cao")
        elif n < 30:
            data_quality_grade = "good"       # Tốt
            uncertainty_level = "moderate"   # Độ không chắc chắn vừa phải
            logging.info(f"ℹ️ Chuỗi thời gian vừa phải ({n} năm) - chấp nhận được cho phân tích sơ bộ")
        else:
            logging.info(f"✅ Chuỗi thời gian tốt ({n} năm) - đáng tin cậy cho phân tích tần suất")

        # Phân tích từng mô hình phân phối
        analysis = {}
        for name, dist in distributions.items():
            try:
                # Ước lượng tham số của mô hình
                params = dist.fit(aggregated)
                extracted = extract_params(params)
                
                # Tính log-likelihood và AIC
                loglik = np.sum(dist.logpdf(aggregated, *params))
                aic = 2 * len(params) - 2 * loglik  # Akaike Information Criterion
                
                # Tạo histogram và tính tần số mong đợi
                bins = np.histogram_bin_edges(aggregated, bins=num_bins)
                observed_freq, _ = np.histogram(aggregated, bins=bins)
                expected_freq = n * (dist.cdf(bins[1:], *params) - dist.cdf(bins[:-1], *params))
                expected_freq = np.where(expected_freq <= 0, 1e-10, expected_freq)  # Tránh chia cho 0
                
                # Tính Chi-square và p-value
                chi_square = np.sum((observed_freq - expected_freq) ** 2 / expected_freq)
                df_chi = len(observed_freq) - 1 - len(params)  # Bậc tự do
                p_value = 1 - chi2.cdf(chi_square, df_chi) if df_chi > 0 else None
                
                # Cảnh báo khi mẫu nhỏ hoặc bậc tự do thấp
                if n < 30 or df_chi <= 0:
                    logging.warning(f"Mẫu nhỏ hoặc bậc tự do thấp cho mô hình {name}: n={n}, df={df_chi}. Cần thêm dữ liệu để ước lượng đáng tin cậy.")
                
                analysis[name] = {
                    "params": extracted,
                    "AIC": aic,
                    "ChiSquare": chi_square,
                    "p_value": p_value,
                    "data_quality_grade": data_quality_grade,
                    "uncertainty_level": uncertainty_level,
                    "sample_size": n
                }
            except Exception as e:
                logging.error(f"❌ Thất bại khi ước lượng mô hình phân phối {name}: {e}")
                analysis[name] = {
                    "params": {},
                    "AIC": float('inf'),
                    "ChiSquare": float('inf'),
                    "p_value": None,
                    "data_quality_grade": data_quality_grade,
                    "uncertainty_level": uncertainty_level,
                    "sample_size": n,
                    "error": str(e)
                }
        return analysis  # Trả về kết quả phân tích tất cả các mô hình

    def get_quantile_data(self, distribution_name: str, agg_func: str= 'max'):
        validate_agg_func(agg_func)
        if distribution_name not in distributions:
            raise HTTPException(status_code=404, detail=f"Mô hình {distribution_name} không được hỗ trợ.")
        
        df = self.data_service.data
        main_column = self.data_service.main_column

        if df is None:
            raise HTTPException(status_code=404, detail="Dữ liệu chưa được tải")
        
        df_max = df.groupby('Year', as_index=False)[main_column].agg(agg_func)
        qmax_values = df_max[main_column].tolist()
        years = df_max['Year'].tolist()
        N = len(qmax_values)
        
        counts, bin_edges = np.histogram(qmax_values, bins="auto")
        
        bin_midpoints = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
        
        dist = distributions[distribution_name]
        
        params = dist.fit(qmax_values)
        
        expected_counts = []
        for i in range(len(bin_edges)-1):
            a = bin_edges[i]
            b = bin_edges[i+1]
            expected_count = N * (dist.cdf(b, *params) - dist.cdf(a, *params))
            expected_counts.append(expected_count)
        
        # Tính toán đường cong lý thuyết cho kỳ tái hiện
        # p_values: xác suất vượt quá (exceedance probability) từ 1% đến 99%
        p_values = np.linspace(0.01, 0.99, num=100)
        # Q_theoretical: giá trị lưu lượng tương ứng với từng xác suất
        # Sử dụng ppf (percent point function) với xác suất không vượt quá = 1 - p_values
        # Đây là phương pháp chuẩn quốc tế (WMO-168, ASCE) cho phân tích tần suất
        Q_theoretical = dist.ppf(1 - p_values, *params)
        
        return {
            "years": years,
            "qmax_values": qmax_values,
            "histogram": {
                "counts": counts.tolist(),
                "bin_edges": bin_edges.tolist(),
                "bin_midpoints": bin_midpoints,
                "expected_counts": expected_counts
            },
            "theoretical_curve": {
                "p_values": p_values.tolist(),
                "Q_values": Q_theoretical.tolist()
            }
        }

    def compute_frequency_curve(self, distribution_name: str, agg_func: str= 'max'):
        validate_agg_func(agg_func)
        if distribution_name not in distributions:
            raise HTTPException(status_code=404, detail=f"Mô hình {distribution_name} không được hỗ trợ.")
        
        df = self.data_service.data
        main_column = self.data_service.main_column
        
        if df is None:
            return {"theoretical_curve": [], "empirical_points": []}
        
        Qmax = df.groupby('Year')[main_column].agg(agg_func).values
        
        if Qmax.size == 0:
            return {"theoretical_curve": [], "empirical_points": []}

        dist = distributions[distribution_name]
        params = dist.fit(Qmax)
        
        # Tạo lưới xác suất với phân bố logarit từ 0.01% đến 99.9%
        # Điều này đảm bảo độ phân giải cao ở các kỳ tái hiện lớn (hiếm)
        p_percent_fixed = np.logspace(np.log10(0.01), np.log10(99.9), num=200)
        p_values = p_percent_fixed / 100.0  # Chuyển từ % sang xác suất thập phân
        
        # Tính giá trị lưu lượng theo đường cong tần suất lý thuyết
        # Phương pháp PPF chuẩn quốc tế: Q = F^(-1)(1-P) với P là xác suất vượt quá
        Q_theoretical = dist.ppf(1 - p_values, *params)
        
        # Tính xác suất thực nghiệm bằng công thức Weibull plotting position
        Q_sorted = sorted(Qmax, reverse=True)  # Sắp xếp giảm dần (lớn nhất trước)
        n = len(Q_sorted)  # Số năm quan trắc
        m = np.arange(1, n + 1)  # Thứ hạng từ 1 đến n
        # Công thức Weibull: P = m/(n+1) - được WMO khuyến nghị cho thủy văn
        p_empirical = m / (n + 1)  # Xác suất vượt quá thực nghiệm
        p_percent_empirical = p_empirical * 100  # Chuyển sang %

        theoretical_curve = sorted(
            [{"P_percent": p, "Q": q} for p, q in zip(p_percent_fixed, Q_theoretical)],
            key=lambda item: item["P_percent"]
        )
        empirical_points = [{"P_percent": p, "Q": q} for p, q in zip(p_percent_empirical, Q_sorted)]

        return {"theoretical_curve": theoretical_curve, "empirical_points": empirical_points}

    def compute_qq_pp(self, distribution_name: str, agg_func: str= 'max'):
        validate_agg_func(agg_func)
        if distribution_name not in distributions:
            raise HTTPException(status_code=400, detail=f"Mô hình {distribution_name} không được hỗ trợ.")
        
        df = self.data_service.data
        main_column = self.data_service.main_column
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dữ liệu chưa được tải")
        
        Qmax = df.groupby('Year')[main_column].agg(agg_func).values
        
        if Qmax.size == 0:
            return {"qq": [], "pp": []}
        
        dist = distributions[distribution_name]
        
        params = dist.fit(Qmax)
        
        sorted_Q = np.sort(Qmax)
        n = len(sorted_Q)
        
        qq_data = []
        pp_data = []
        for i in range(n):
            p_empirical = (i + 1) / (n + 1)
            theoretical_quantile = dist.ppf(p_empirical, *params)
            empirical_cdf = p_empirical
            theoretical_cdf = dist.cdf(sorted_Q[i], *params)
            qq_data.append({
                "p_empirical": p_empirical,
                "sample": sorted_Q[i],
                "theoretical": theoretical_quantile
            })
            pp_data.append({
                "empirical": empirical_cdf,
                "theoretical": theoretical_cdf
            })
        
        return {"qq": qq_data, "pp": pp_data}

    def get_frequency_analysis(self):
        df = self.data_service.data
        main_column = self.data_service.main_column
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dữ liệu chưa được tải")
        
        agg_df = df.groupby('Year', as_index=False).agg({main_column: 'max'})
        
        # Kiểm tra dữ liệu đủ để phân tích tần suất
        n = len(agg_df)
        if n < 2:
            raise HTTPException(
                status_code=400, 
                detail=f"Không đủ dữ liệu để phân tích tần suất. Cần ít nhất 2 năm dữ liệu, hiện tại chỉ có {n} năm. "
                       f"Phân tích tần suất yêu cầu nhiều điểm dữ liệu để ước tính xác suất xuất hiện đáng tin cậy."
            )
        
        # Cảnh báo nếu dữ liệu ít
        if n < 10:
            logging.warning(f"⚠️ Dữ liệu ít ({n} năm) - kết quả phân tích tần suất có độ không chắc chắn cao. Khuyến nghị có ít nhất 10-30 năm dữ liệu.")
        
        agg_df["Thời gian"] = agg_df["Year"].astype(str) + "-" + (agg_df["Year"] + 1).astype(str)
        
        agg_df['Thứ hạng'] = agg_df[main_column].rank(ascending=False, method='min').astype(int)
        
        # Tính tần suất sử dụng công thức Weibull plotting position
        agg_df["Tần suất P(%)"] = (agg_df['Thứ hạng'] / (n + 1)) * 100
        
        agg_df = agg_df.sort_values("Year").reset_index(drop=True)
        agg_df["Thứ tự"] = agg_df.index + 1
        
        agg_df = agg_df.rename(columns={main_column: "Chỉ số"})
        
        output_df = agg_df[["Thứ tự", "Thời gian", "Chỉ số", "Tần suất P(%)", "Thứ hạng"]]
        
        output_df.loc[:, "Tần suất P(%)"] = output_df["Tần suất P(%)"].round(2)
        output_df.loc[:, "Chỉ số"] = output_df["Chỉ số"].round(2)

        return output_df.to_dict(orient="records")

    def get_frequency_by_model(self, distribution_name: str, agg_func: str= 'max'):
        validate_agg_func(agg_func)
        if distribution_name not in distributions:
            raise HTTPException(status_code=400, detail=f"Mô hình {distribution_name} không được hỗ trợ.")
        
        df = self.data_service.data
        main_column = self.data_service.main_column
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dữ liệu chưa được tải")
        
        Qmax = df.groupby('Year')[main_column].agg(agg_func).values
        
        if Qmax.size == 0:
            return {}
        
        dist = distributions[distribution_name]
        
        params = dist.fit(Qmax)
        
        # Các kỳ tái hiện tiêu chuẩn được sử dụng trong thiết kế công trình thủy lợi
        # Từ 0.01% (T=10000 năm) đến 99.99% (T=1.0001 năm)
        fixed_p_percent = np.array([
            0.01, 0.10, 0.20, 0.33, 0.50, 1.00, 1.50, 2.00, 3.00, 5.00, 10.00,
            20.00, 25.00, 30.00, 40.00, 50.00, 60.00, 70.00, 75.00, 80.00,
            85.00, 90.00, 95.00, 97.00, 99.00, 99.90, 99.99
        ])
        p_values = fixed_p_percent / 100.0  # Chuyển % thành xác suất
        
        # Tính lưu lượng thiết kế theo phương pháp PPF chuẩn quốc tế
        # Q_T = F^(-1)(1-1/T) với T là kỳ tái hiện (năm)
        Q_theoretical = dist.ppf(1 - p_values, *params)
        
        # Tính kỳ tái hiện tương ứng: T = 1/P (năm)
        T_theoretical = 100 / fixed_p_percent
        
        theoretical_curve = [
            {
                "Thứ tự": i,
                "Tần suất P(%)": f"{p:.2f}",
                "Lưu lượng dòng chảy Q m³/s": f"{q:.2f}",
                "Thời gian lặp lại (năm)": f"{T:.3f}"
            }
            for i, (p, q, T) in enumerate(zip(fixed_p_percent, Q_theoretical, T_theoretical), start=1)
        ]
        
        Q_sorted_desc = sorted(Qmax, reverse=True)
        n = len(Q_sorted_desc)
        
        ranks = np.arange(1, n + 1)
        
        p_empirical = ranks / (n + 1)
        p_percent_empirical = p_empirical * 100
        
        T_empirical = (n + 1) / ranks
        
        empirical_points = [
            {
                "Thứ tự": i,
                "Tần suất P(%)": f"{p:.2f}",
                "Lưu lượng dòng chảy Q m³/s": f"{q:.2f}",
                "Thời gian lặp lại (năm)": f"{T:.3f}"
            }
            for i, (p, q, T) in enumerate(zip(p_percent_empirical, Q_sorted_desc, T_empirical), start=1)
        ]
        
        
        return {
            "theoretical_curve": theoretical_curve,
            "empirical_points": empirical_points,
        }