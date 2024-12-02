# api/gii.py
import pandas as pd
from prophet import Prophet

gii_url = "https://data.humdata.org/dataset/5a1ea18e-9177-4e37-b91f-5631961bdb6c/resource/4539296c-289c-48a2-b0dc-3fc8dcad1b77/download/gii_gender_inequality_index_value.csv"

def fetch_gii_data():
    return pd.read_csv(gii_url)

def forecast_gii(nepal_data):
    nepal_data = nepal_data[nepal_data["country"] == "Nepal"]
    nepal_data = nepal_data.groupby("year")["value"].mean()

    nepal_data_prophet = pd.DataFrame({
        'ds': pd.to_datetime(nepal_data.index.astype(str)),  
        'y': nepal_data.values  
    })

    model = Prophet()
    model.fit(nepal_data_prophet)

    future = model.make_future_dataframe(periods=8, freq="AS")  
    forecast = model.predict(future)

    actual_data = nepal_data_prophet.copy()
    actual_data['type'] = 'Actual'
    forecast_data = forecast[['ds', 'yhat']].copy()
    forecast_data.rename(columns={'yhat': 'y'}, inplace=True)
    forecast_data['type'] = 'Forecast'

    combined_data = pd.concat([actual_data, forecast_data])
    
    return combined_data.to_dict(orient='records')
