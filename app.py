from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
import io

app = FastAPI()

# Mount frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    # Redirect root to our index.html
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url='/static/index.html')

@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # ---------------------------------------------------------
        # Dynamic Data Intelligence Core (Similar to our pipeline)
        # ---------------------------------------------------------
        # Try to find a datetime column and a value column automatically
        time_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                time_col = col
                break
                
        val_col = None
        for col in df.select_dtypes(include=[np.number]).columns:
            if 'mw' in col.lower() or 'kw' in col.lower() or 'usage' in col.lower() or 'power' in col.lower() or 'consumption' in col.lower():
                val_col = col
                break

        if not time_col or not val_col:
            # Fallback if no specific names found
            time_col = df.columns[0]
            val_col = df.select_dtypes(include=[np.number]).columns[0]
            
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
        df = df.dropna(subset=[time_col, val_col])
        
        # Sort chronologically
        df = df.sort_values(by=time_col)
        
        total_rows = len(df)
        
        # 1. Seasonal Trends (Monthly Average)
        df['month'] = df[time_col].dt.month
        monthly_avg = df.groupby('month')[val_col].mean().reindex(range(1,13), fill_value=0).round(2)
        
        seasonal_data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'values': monthly_avg.tolist()
        }
        
        # 2. Peaks Calculation
        peaks = df.nlargest(10, val_col)
        peaks_data = {
            'labels': peaks[time_col].dt.strftime('%m-%d %H:00').tolist(),
            'values': peaks[val_col].round(2).tolist()
        }
        
        # 3. Dynamic Insights Generation
        mean_val = df[val_col].mean()
        max_val = df[val_col].max()
        peak_ratio = max_val / mean_val if mean_val else 0
        
        insights = []
        if peak_ratio > 2.0:
            insights.append({
                "title": "High Volatility Detected",
                "desc": f"Your peak usage is {peak_ratio:.1f}x higher than your average load. Immediate load-shifting programs (e.g. Battery Storage) are highly recommended to avoid surge pricing."
            })
        else:
            insights.append({
                "title": "Stable Baseline Load",
                "desc": "The consumption curve is relatively flat. Your highest priority should be auditing 'always-on' baseline legacy equipment (HVAC, server rooms) for baseline efficiency gains."
            })
            
        summer_avg = df[df['month'].isin([6,7,8])][val_col].mean()
        winter_avg = df[df['month'].isin([12,1,2])][val_col].mean()
        
        if summer_avg > winter_avg * 1.2:
            insights.append({
                "title": "Summer Cooling Penalty",
                "desc": "The data shows a massive summer AC heating penalty. Upgrading HVAC insulation and implementing a Time-of-Use schedule in Q3 will yield high ROI."
            })
        elif winter_avg > summer_avg * 1.2:
            insights.append({
                "title": "Winter Heating Driven",
                "desc": "Significant winter peaking observed. Transitioning to modern Heat Pumps from resistive heating will slash winter operational costs."
            })
        
        return JSONResponse(content={
            "total_rows": total_rows,
            "total_peaks": len(peaks),
            "seasonal_data": seasonal_data,
            "peaks_data": peaks_data,
            "insights": insights
        })
        
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
