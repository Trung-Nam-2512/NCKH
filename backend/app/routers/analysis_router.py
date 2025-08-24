from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, HTTPException, Form
from ..dependencies import get_analysis_service, get_data_service
from ..services.analysis_service import AnalysisService
from ..services.data_service import DataService
import pandas as pd
import io

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/distribution")
def get_distribution_analysis(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.get_distribution_analysis(agg_func)

@router.get("/quantile_data/{model}")
def call_get_quantile_data(model: str = Path(...), agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.get_quantile_data(model, agg_func)

@router.get("/frequency_curve_gumbel")
def get_frequency_curve_gumbel(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("gumbel", agg_func)

@router.get("/frequency_curve_lognorm")
def get_frequency_curve_lognorm(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("lognorm", agg_func)

@router.get("/frequency_curve_gamma")
def get_frequency_curve_gamma(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("gamma", agg_func)

@router.get("/frequency_curve_logistic")
def get_frequency_curve_logistic(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("logistic", agg_func)

@router.get("/frequency_curve_exponential")
def get_frequency_curve_exponential(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("expon", agg_func)

@router.get("/frequency_curve_gpd")
def get_frequency_curve_gpd(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("genpareto", agg_func)

@router.get("/frequency_curve_frechet")
def get_frequency_curve_frechet(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("frechet", agg_func)

@router.get("/frequency_curve_pearson3")
def get_frequency_curve_pearson3(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("pearson3", agg_func)

@router.get("/frequency_curve_genextreme")
def get_frequency_curve_genextreme(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("genextreme", agg_func)

@router.get("/qq_pp/{model}")
def get_qq_pp_plot_data(model: str = Path(...), agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_qq_pp(model, agg_func)

@router.get("/frequency")
def get_frequency_analysis(analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.get_frequency_analysis()

@router.get("/frequency_by_model")
def get_frequency_by_model(distribution_name: str = Query(...), agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.get_frequency_by_model(distribution_name, agg_func)

@router.get("/histogram")
def get_histogram_analysis(distribution_name: str = Query('gumbel'), agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    """
    Lấy dữ liệu histogram và đường cong lý thuyết để vẽ biểu đồ tần số
    """
    return analysis_service.get_quantile_data(distribution_name, agg_func)

@router.post("/analyze-file")
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    distribution_name: str = Form("gumbel"),
    agg_func: str = Form("max"),
    data_service: DataService = Depends(get_data_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Upload CSV file and perform frequency analysis
    """
    try:
        # Read the uploaded file
        content = await file.read()
        
        # Parse CSV
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Validate data format
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Load data into service
        data_service.data = df
        if 'Q' in df.columns:
            data_service.main_column = 'Q'
        elif 'depth' in df.columns:
            data_service.main_column = 'depth'
        else:
            # Use the last numeric column
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                raise HTTPException(status_code=400, detail="No numeric data found in file")
            data_service.main_column = numeric_cols[-1]
        
        # Perform analysis
        result = analysis_service.get_distribution_analysis(agg_func)
        
        return {
            "status": "success",
            "message": "File analyzed successfully",
            "data_info": {
                "rows": len(df),
                "columns": list(df.columns),
                "main_column": data_service.main_column
            },
            "analysis": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")