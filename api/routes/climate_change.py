# api/routes/climate_change.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import pandas as pd
from datetime import timedelta
from api.models.auth import oauth2_scheme, get_current_user
from api.services.load_climate_data import get_climate_data 
import joblib
from sklearn.preprocessing import QuantileTransformer


router = APIRouter()

model_temp = joblib.load('models/xgboost_temp_model.pkl')
model_precip = joblib.load('models/xgboost_precip_model.pkl')
qt = QuantileTransformer(output_distribution='normal')

@router.get("/forecast_climate_change_prediction")
async def forecast(token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Retrieve climate data
    climate_change_df = get_climate_data()

    # Transform Precipitation
    climate_change_df['Transformed_Precipitation'] = qt.fit_transform(climate_change_df[['Precipitation']])

    # Generate dates for the next 10 days
    last_date = climate_change_df.index[-1]
    future_dates = [last_date + timedelta(days=i) for i in range(1, 11)]

    future_df = pd.DataFrame(index=future_dates)
    future_df['month'] = future_df.index.month
    future_df['dayofyear'] = future_df.index.dayofyear
    future_df['dayofmonth'] = future_df.index.day
    future_df['dayofweek'] = future_df.index.dayofweek

    # Add lag features
    for lag in range(1, 4):
        future_df[f'temp_lag_{lag}'] = climate_change_df['Temperature'].shift(lag).iloc[-1]
        future_df[f'precip_lag_{lag}'] = climate_change_df['Precipitation'].shift(lag).iloc[-1]

    future_df['temp_roll_mean'] = climate_change_df['Temperature'].rolling(window=7).mean().iloc[-1]
    future_df['precip_roll_mean'] = climate_change_df['Precipitation'].rolling(window=7).mean().iloc[-1]
    future_df['precip_diff'] = climate_change_df['Precipitation'].diff().iloc[-1]
    future_df['precip_pct_change'] = climate_change_df['Precipitation'].pct_change().iloc[-1]

    feature_names = model_temp.get_booster().feature_names
    future_df = future_df[feature_names]

    # Make predictions
    future_temp_predictions = model_temp.predict(future_df)
    future_precip_predictions = model_precip.predict(future_df)
    future_precip_predictions = qt.inverse_transform(future_precip_predictions.reshape(-1, 1)).flatten()

    # Prepare final output
    future_predictions_df = pd.DataFrame({
        'Date': future_dates,
        'Predicted_Temperature': future_temp_predictions,
        'Predicted_Precipitation': future_precip_predictions
    })

    future_predictions_df['Date'] = future_predictions_df['Date'].dt.strftime('%Y-%m-%d')
    return future_predictions_df.to_dict(orient="records")
