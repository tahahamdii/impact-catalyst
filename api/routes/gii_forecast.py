# api/routes/gii_forecast.py
from fastapi import APIRouter, Depends, HTTPException
from api.models.auth import oauth2_scheme, get_current_user
from api.services.gii import fetch_gii_data, forecast_gii

router = APIRouter()

@router.get("/gii_forecast")
async def get_gii_forecast(token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    gii_data = fetch_gii_data()  
    forecast_results = forecast_gii(gii_data)  
    
    return {"data": forecast_results}
