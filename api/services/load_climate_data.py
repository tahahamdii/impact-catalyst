import requests
import pandas as pd

nasa_url = "https://power.larc.nasa.gov/api/projection/daily/point?start=20200101&end=20241105&latitude=27.7103&longitude=85.3222&community=ag&parameters=PRECTOTCORR%2CT2M&format=json&user=utkarsha&header=true&time-standard=utc&model=ensemble&scenario=ssp126"

def get_climate_data():
    response = requests.get(nasa_url)
    if response.status_code == 200:
        data = response.json()
        parameters = data['properties']['parameter']
        dates = list(parameters['PRECTOTCORR'].keys())

        precipitation = [parameters['PRECTOTCORR'][date] for date in dates]
        temperature = [parameters['T2M'][date] for date in dates]
        
        climate_change_df = pd.DataFrame({
            'Date': dates,
            'Precipitation': precipitation,
            'Temperature': temperature
        })
        climate_change_df['Date'] = pd.to_datetime(climate_change_df['Date'])
        climate_change_df.set_index('Date', inplace=True)
        return climate_change_df
    else:
        raise Exception("Failed to retrieve data from NASA API.")
