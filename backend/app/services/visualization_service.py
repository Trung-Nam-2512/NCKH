"""
Visualization Service - Generate frequency analysis charts and plots
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats
import io
import base64
from typing import Dict, List, Any, Optional
import logging
from .data_service import DataService
from .analysis_service import AnalysisService, distributions

# Configure matplotlib for non-interactive backend
import matplotlib
matplotlib.use('Agg')

plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

class VisualizationService:
    """Service để tạo các biểu đồ phân tích tần suất chuyên nghiệp"""
    
    def __init__(self, data_service: DataService, analysis_service: AnalysisService):
        self.data_service = data_service
        self.analysis_service = analysis_service
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        try:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logging.error(f"Error converting figure to base64: {e}")
            plt.close(fig)
            return ""
    
    def create_frequency_curve_plot(self, distribution_name: str, agg_func: str = 'max') -> Dict[str, Any]:
        """Tạo biểu đồ đường cong tần suất cho phân phối cụ thể"""
        
        try:
            # Lấy data đường cong từ analysis service
            freq_data = self.analysis_service.compute_frequency_curve(distribution_name, agg_func)
            
            if not freq_data.get('theoretical_curve') or not freq_data.get('empirical_points'):
                return {"error": "Không có dữ liệu để vẽ biểu đồ"}
            
            # Tạo figure
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Vẽ đường cong lý thuyết
            theoretical = freq_data['theoretical_curve']
            theo_x = [point['P_percent'] for point in theoretical]
            theo_y = [point['Q'] for point in theoretical]
            
            ax.semilogx(theo_x, theo_y, 'b-', linewidth=2, 
                       label=f'Đường cong lý thuyết ({distribution_name.capitalize()})')
            
            # Vẽ điểm thực nghiệm
            empirical = freq_data['empirical_points']
            emp_x = [point['P_percent'] for point in empirical]
            emp_y = [point['Q'] for point in empirical]
            
            ax.semilogx(emp_x, emp_y, 'ro', markersize=8, 
                       label='Điểm thực nghiệm')
            
            # Định dạng biểu đồ
            ax.set_xlabel('Tần suất vượt quá (%)')
            ax.set_ylabel(f'Lưu lượng (m³/s) - {agg_func.upper()}')
            ax.set_title(f'Đường cong tần suất - Phân phối {distribution_name.capitalize()}')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Thêm các đường thẳng đứng cho các chu kỳ quan trọng
            return_periods = [2, 5, 10, 25, 50, 100]
            colors = ['green', 'orange', 'red', 'purple', 'brown', 'black']
            
            for i, T in enumerate(return_periods):
                p_percent = 100 / T
                if p_percent >= min(theo_x) and p_percent <= max(theo_x):
                    ax.axvline(x=p_percent, color=colors[i % len(colors)], 
                              linestyle='--', alpha=0.7, linewidth=1)
                    ax.text(p_percent, max(theo_y) * 0.95, f'T={T}năm', 
                           rotation=90, ha='right', va='top', fontsize=9)
            
            plt.tight_layout()
            
            return {
                "plot_base64": self._fig_to_base64(fig),
                "distribution": distribution_name,
                "data_points": len(empirical),
                "curve_points": len(theoretical)
            }
            
        except Exception as e:
            logging.error(f"Error creating frequency curve plot: {e}")
            return {"error": str(e)}
    
    def create_qq_pp_plots(self, distribution_name: str, agg_func: str = 'max') -> Dict[str, Any]:
        """Tạo QQ và PP plots để kiểm tra độ phù hợp của phân phối"""
        
        try:
            qq_pp_data = self.analysis_service.compute_qq_pp(distribution_name, agg_func)
            
            if not qq_pp_data.get('qq') or not qq_pp_data.get('pp'):
                return {"error": "Không có dữ liệu cho QQ/PP plots"}
            
            # Tạo subplot
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            # QQ Plot
            qq_data = qq_pp_data['qq']
            theoretical_q = [point['theoretical'] for point in qq_data]
            sample_q = [point['sample'] for point in qq_data]
            
            ax1.scatter(theoretical_q, sample_q, alpha=0.7, s=50, color='blue')
            
            # Đường 45 độ cho QQ plot
            min_val = min(min(theoretical_q), min(sample_q))
            max_val = max(max(theoretical_q), max(sample_q))
            ax1.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, alpha=0.8)
            
            ax1.set_xlabel(f'Quantile lý thuyết ({distribution_name})')
            ax1.set_ylabel('Quantile mẫu')
            ax1.set_title('Q-Q Plot')
            ax1.grid(True, alpha=0.3)
            
            # PP Plot
            pp_data = qq_pp_data['pp']
            theoretical_p = [point['theoretical'] for point in pp_data]
            empirical_p = [point['empirical'] for point in pp_data]
            
            ax2.scatter(theoretical_p, empirical_p, alpha=0.7, s=50, color='green')
            
            # Đường 45 độ cho PP plot
            ax2.plot([0, 1], [0, 1], 'r--', linewidth=2, alpha=0.8)
            
            ax2.set_xlabel(f'Xác suất lý thuyết ({distribution_name})')
            ax2.set_ylabel('Xác suất thực nghiệm')
            ax2.set_title('P-P Plot')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            return {
                "plot_base64": self._fig_to_base64(fig),
                "distribution": distribution_name,
                "qq_points": len(qq_data),
                "pp_points": len(pp_data)
            }
            
        except Exception as e:
            logging.error(f"Error creating QQ/PP plots: {e}")
            return {"error": str(e)}
    
    def create_distribution_comparison_plot(self, agg_func: str = 'max') -> Dict[str, Any]:
        """So sánh các phân phối khác nhau trên cùng một biểu đồ"""
        
        try:
            # Lấy data cho tất cả phân phối
            distribution_analysis = self.analysis_service.get_distribution_analysis(agg_func)
            
            # Tạo figure
            fig, ax = plt.subplots(figsize=(14, 10))
            
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive']
            plotted_distributions = []
            
            for i, (dist_name, analysis_result) in enumerate(distribution_analysis.items()):
                if analysis_result.get('AIC') == float('inf'):
                    continue  # Skip failed distributions
                    
                try:
                    freq_data = self.analysis_service.compute_frequency_curve(dist_name, agg_func)
                    
                    if freq_data.get('theoretical_curve'):
                        theoretical = freq_data['theoretical_curve']
                        x_vals = [point['P_percent'] for point in theoretical]
                        y_vals = [point['Q'] for point in theoretical]
                        
                        color = colors[i % len(colors)]
                        aic_value = analysis_result['AIC']
                        
                        ax.semilogx(x_vals, y_vals, color=color, linewidth=2, 
                                   label=f'{dist_name.capitalize()} (AIC={aic_value:.1f})')
                        plotted_distributions.append(dist_name)
                        
                except Exception as e:
                    logging.warning(f"Skip distribution {dist_name}: {e}")
                    continue
            
            # Vẽ điểm thực nghiệm một lần
            if plotted_distributions:
                first_dist = plotted_distributions[0]
                freq_data = self.analysis_service.compute_frequency_curve(first_dist, agg_func)
                empirical = freq_data.get('empirical_points', [])
                
                if empirical:
                    emp_x = [point['P_percent'] for point in empirical]
                    emp_y = [point['Q'] for point in empirical]
                    ax.semilogx(emp_x, emp_y, 'ko', markersize=6, 
                               label='Dữ liệu thực nghiệm')
            
            # Định dạng
            ax.set_xlabel('Tần suất vượt quá (%)')
            ax.set_ylabel(f'Lưu lượng (m³/s) - {agg_func.upper()}')
            ax.set_title('So sánh các phân phối xác suất')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best', fontsize=9)
            
            plt.tight_layout()
            
            return {
                "plot_base64": self._fig_to_base64(fig),
                "plotted_distributions": plotted_distributions,
                "total_distributions": len(plotted_distributions)
            }
            
        except Exception as e:
            logging.error(f"Error creating distribution comparison plot: {e}")
            return {"error": str(e)}
    
    def create_histogram_with_fitted_distributions(self, agg_func: str = 'max', top_n: int = 3) -> Dict[str, Any]:
        """Tạo histogram với các phân phối fitted overlay"""
        
        try:
            df = self.data_service.data
            main_column = self.data_service.main_column
            
            if df is None:
                return {"error": "Không có dữ liệu"}
            
            # Lấy dữ liệu tổng hợp
            aggregated = df.groupby('Year')[main_column].agg(agg_func).values
            
            # Lấy phân tích phân phối
            distribution_analysis = self.analysis_service.get_distribution_analysis(agg_func)
            
            # Sắp xếp theo AIC để lấy top distributions
            valid_dists = [(name, result) for name, result in distribution_analysis.items() 
                          if result.get('AIC', float('inf')) != float('inf')]
            valid_dists.sort(key=lambda x: x[1]['AIC'])
            top_distributions = valid_dists[:top_n]
            
            # Tạo figure
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Vẽ histogram
            n_bins = min(len(aggregated) // 2, 15)  # Adaptive number of bins
            counts, bins, patches = ax.hist(aggregated, bins=n_bins, density=True, alpha=0.7, 
                                           color='lightblue', edgecolor='black', 
                                           label='Histogram dữ liệu')
            
            # Vẽ các phân phối fitted
            x_range = np.linspace(aggregated.min(), aggregated.max(), 200)
            colors = ['red', 'green', 'orange', 'purple', 'brown']
            
            for i, (dist_name, analysis_result) in enumerate(top_distributions):
                try:
                    dist = distributions[dist_name]
                    params = dist.fit(aggregated)
                    pdf_values = dist.pdf(x_range, *params)
                    
                    aic_value = analysis_result['AIC']
                    p_value = analysis_result.get('p_value')
                    p_text = f", p={p_value:.3f}" if p_value is not None else ""
                    
                    ax.plot(x_range, pdf_values, color=colors[i % len(colors)], 
                           linewidth=2, label=f'{dist_name.capitalize()} (AIC={aic_value:.1f}{p_text})')
                    
                except Exception as e:
                    logging.warning(f"Error plotting {dist_name}: {e}")
                    continue
            
            # Định dạng
            ax.set_xlabel(f'{main_column} ({agg_func.upper()})')
            ax.set_ylabel('Mật độ xác suất')
            ax.set_title(f'Histogram và các phân phối fitted - {len(aggregated)} năm dữ liệu')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            plt.tight_layout()
            
            return {
                "plot_base64": self._fig_to_base64(fig),
                "data_years": len(aggregated),
                "fitted_distributions": [dist[0] for dist in top_distributions],
                "best_distribution": top_distributions[0][0] if top_distributions else None
            }
            
        except Exception as e:
            logging.error(f"Error creating histogram plot: {e}")
            return {"error": str(e)}
    
    def create_return_period_table_plot(self, distribution_name: str, agg_func: str = 'max') -> Dict[str, Any]:
        """Tạo bảng chu kỳ lặp lại dạng biểu đồ"""
        
        try:
            # Lấy data từ analysis service
            freq_by_model = self.analysis_service.get_frequency_by_model(distribution_name, agg_func)
            
            if not freq_by_model.get('theoretical_curve'):
                return {"error": "Không có dữ liệu cho bảng chu kỳ lặp lại"}
            
            # Prepare data for table
            theoretical_data = freq_by_model['theoretical_curve']
            
            # Chọn các chu kỳ quan trọng
            important_periods = [2, 5, 10, 25, 50, 100]
            table_data = []
            
            for period in important_periods:
                freq_percent = 100 / period
                # Tìm điểm gần nhất
                closest_point = min(theoretical_data, 
                                  key=lambda x: abs(float(x['Tần suất P(%)']) - freq_percent))
                
                table_data.append({
                    'Chu kỳ lặp lại (năm)': period,
                    'Tần suất (%)': f"{freq_percent:.2f}",
                    'Lưu lượng (m³/s)': closest_point['Lưu lượng dòng chảy Q m³/s']
                })
            
            # Tạo figure cho bảng
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis('tight')
            ax.axis('off')
            
            # Tạo bảng
            df_table = pd.DataFrame(table_data)
            table = ax.table(cellText=df_table.values,
                           colLabels=df_table.columns,
                           cellLoc='center',
                           loc='center',
                           colWidths=[0.3, 0.3, 0.4])
            
            # Định dạng bảng
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 1.5)
            
            # Tô màu header
            for i in range(len(df_table.columns)):
                table[(0, i)].set_facecolor('#4472C4')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            # Tô màu xen kẽ cho các dòng
            for i in range(1, len(table_data) + 1):
                if i % 2 == 0:
                    for j in range(len(df_table.columns)):
                        table[(i, j)].set_facecolor('#F2F2F2')
            
            ax.set_title(f'Bảng chu kỳ lặp lại - Phân phối {distribution_name.capitalize()}', 
                        pad=20, fontsize=14, weight='bold')
            
            plt.tight_layout()
            
            return {
                "plot_base64": self._fig_to_base64(fig),
                "distribution": distribution_name,
                "table_data": table_data,
                "return_periods": important_periods
            }
            
        except Exception as e:
            logging.error(f"Error creating return period table: {e}")
            return {"error": str(e)}
    
    def generate_comprehensive_report_plots(self, agg_func: str = 'max') -> Dict[str, Any]:
        """Tạo tất cả biểu đồ cho báo cáo toàn diện"""
        
        try:
            # Lấy phân phối tốt nhất
            distribution_analysis = self.analysis_service.get_distribution_analysis(agg_func)
            best_dist = min(distribution_analysis.items(), key=lambda x: x[1].get('AIC', float('inf')))
            best_distribution_name = best_dist[0]
            
            plots = {}
            
            # 1. Frequency curve cho phân phối tốt nhất
            plots['frequency_curve'] = self.create_frequency_curve_plot(best_distribution_name, agg_func)
            
            # 2. QQ/PP plots cho phân phối tốt nhất
            plots['qq_pp_plots'] = self.create_qq_pp_plots(best_distribution_name, agg_func)
            
            # 3. So sánh các phân phối
            plots['distribution_comparison'] = self.create_distribution_comparison_plot(agg_func)
            
            # 4. Histogram với fitted distributions
            plots['histogram_fitted'] = self.create_histogram_with_fitted_distributions(agg_func)
            
            # 5. Bảng chu kỳ lặp lại
            plots['return_period_table'] = self.create_return_period_table_plot(best_distribution_name, agg_func)
            
            # Metadata
            plots['metadata'] = {
                'best_distribution': best_distribution_name,
                'best_aic': best_dist[1]['AIC'],
                'analysis_type': agg_func,
                'data_years': len(self.data_service.data.groupby('Year')) if self.data_service.data is not None else 0,
                'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return plots
            
        except Exception as e:
            logging.error(f"Error generating comprehensive plots: {e}")
            return {"error": str(e)}