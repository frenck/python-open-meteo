"""Asynchronous client for the Open-Meteo API."""
from __future__ import annotations

from datetime import date, datetime
from enum import auto
from typing import List, Optional

from pydantic import BaseModel, Field

from .util import StrEnum


class TemperatureUnit(StrEnum):
    """Enum to represent the temperature units available."""

    CELSIUS = auto()
    FAHRENHEIT = auto()


class WindSpeedUnit(StrEnum):
    """Enum to represent the wind speed units available."""

    KILOMETERS_PER_HOUR = "kmh"
    KNOTS = "kn"
    METERS_PER_SECOND = "ms"
    MILES_PER_HOUR = "mph"


class PrecipitationUnit(StrEnum):
    """Enum to represent the precipitation units available."""

    MILLIMETERS = "mm"
    INCHES = "in"


class TimeFormat(StrEnum):
    """Enum to represent the time formats available."""

    ISO_8601 = "iso8601"
    UNIXTIME = "unixtime"


class HourlyParameters(StrEnum):
    """Enum to represent the hourly parameters available."""

    # Air temperature at 2 meters above ground
    APPARENT_TEMPERATURE = "apparent_temperature"

    # Total cloud cover as an area fraction
    CLOUD_COVER = "cloudcover"

    # High level clouds from 8 km altitude
    CLOUD_COVER_HIGH = "cloudcover_high"

    # Low level clouds and fog up to 3 km altitude
    CLOUD_COVER_LOW = "cloudcover_low"

    # Mid level clouds from 3 to 8 km altitude
    CLOUD_COVER_MID = "cloudcover_mid"

    # Dew point temperature at 2 meters above ground
    DEW_POINT_2M = "dewpoint_2m"

    # Diffuse solar radiation as average of the preceding hour
    DIFFUSE_RADIATION = "diffuse_radiation"

    # Direct solar radiation as average of the preceding hour on the horizontal
    # plane and the normal plane (perpendicular to the sun)
    DIRECT_NORMAL_IRRADIANCE = "direct_normal_irradiance"
    DIRECT_RADIATION = "direct_radiation"

    # Sum of evapotranspration of the preceding hour
    # from lands urface and plants
    EVAPOTRANSPIRATION = "evapotranspiration"

    # Altitude above sea level of the 0°C level
    FREEZING_LEVEL_HEIGHT = "freezinglevel_height"

    # Total precipitation (rain, showers, snow) sum of the preceding hour
    PRECIPITATION = "precipitation"

    # Atmospheric air pressure reduced to sea level (hPa)
    PRESSURE_MSL = "pressure_msl"

    # Relative humidity at 2 meters above ground
    RELATIVE_HUMIDITY_2M = "relativehumidity_2m"

    # Shortwave solar radiation as average of the preceding hour
    SHORTWAVE_RADIATION = "shortwave_radiation"

    # Snow depth on the ground
    SNOW_DEPTH = "snow_depth"

    # Average soil water content as volumetric mixing ratio at 0-1, 1-3, 3-9,
    # 9-27 and 27-81 cm depths.
    SOIL_MOISTURE_0_1CM = "soil_moisture_0_1cm"
    SOIL_MOISTURE_1_3CM = "soil_moisture_1_3cm"
    SOIL_MOISTURE_27_81CM = "soil_moisture_27_81cm"
    SOIL_MOISTURE_3_9CM = "soil_moisture_3_9cm"
    SOIL_MOISTURE_9_27CM = "soil_moisture_9_27cm"

    # Temperature in the soil at 0, 6, 18 and 54 cm depths. 0 cm is the surface
    # temperature on land or water surface temperature on water.
    SOIL_TEMPERATURE_0CM = "soil_temperature_0cm"
    SOIL_TEMPERATURE_18CM = "soil_temperature_18cm"
    SOIL_TEMPERATURE_54CM = "soil_temperature_54cm"
    SOIL_TEMPERATURE_6CM = "soil_temperature_6cm"

    # Air temperature at 2 meters above ground
    TEMPERATURE_2M = "temperature_2m"

    # Vapor Pressure Deificit (VPD) in kilo pascal (kPa). For high VPD (>1.6),
    # water transpiration of plants increases. For low VPD (<0.4),
    # transpiration decreases.
    VAPOR_PRESSURE_DEFICIT = "vapor_pressure_deficit"

    # Weather condition as a WMO numeric weather code.
    WEATHER_CODE = "weathercode"

    # Wind direction at 10, 80, 120 or 180 meters above ground
    WIND_DIRECTION_10M = "winddirection_10m"
    WIND_DIRECTION_120M = "winddirection_120m"
    WIND_DIRECTION_180M = "winddirection_180m"
    WIND_DIRECTION_80M = "winddirection_80m"

    # Gusts at 10 meters above ground as a maximum of the preceding hour
    WIND_GUSTS_10M = "windgusts_10m"

    # Wind speed at 10, 80, 120 or 180 meters above ground.
    # Wind speed on 10 meters is the standard level.
    WIND_SPEED_10M = "windspeed_10m"
    WIND_SPEED_120M = "windspeed_120m"
    WIND_SPEED_180M = "windspeed_180m"
    WIND_SPEED_80M = "windspeed_80m"


class DailyParameters(StrEnum):
    """Enum to represent the daily parameters available."""

    # Maximum and minimum daily air temperature at 2 meters above ground.
    APPARENT_TEMPERATURE_MAX = "apparent_temperature_max"
    APPARENT_TEMPERATURE_MIN = "apparent_temperature_min"

    # The number of hours with rain,
    PRECIPITATION_HOURS = "precipitation_hours"

    # Sum of daily precipitation.
    PRECIPITATION_SUM = "precipitation_sum"

    # The sum of solar radiation on a given day in Mega Joules.
    SHORTWAVE_RADIATION_SUM = "shortwave_radiation_sum"

    # Sun rise and set times
    SUNRISE = "sunrise"
    SUNSET = "sunset"

    # Maximum and minimum daily air temperature at 2 meters above ground.
    TEMPERATURE_2M_MAX = "temperature_2m_max"
    TEMPERATURE_2M_MIN = "temperature_2m_min"

    # The most severe weather condition on a given day.
    WEATHER_CODE = "weathercode"

    # Dominant wind direction.
    WIND_DIRECTION_10M_DOMINANT = "winddirection_10m_dominant"

    # Maximum wind speed and gusts on a day
    WIND_GUSTS_10M_MAX = "windgusts_10m_max"
    WIND_SPEED_10M_MAX = "windspeed_10m_max"


class HourlyForecast(BaseModel):
    """Hourly weather data."""

    apparent_temperature: Optional[List[float]]
    cloudcover_high: Optional[List[int]]
    cloudcover_low: Optional[List[int]]
    cloudcover_mid: Optional[List[int]]
    cloudcover: Optional[List[int]]
    dewpoint_2m: Optional[List[float]]
    diffuse_radiation: Optional[List[float]]
    direct_normal_irradiance: Optional[List[float]]
    direct_radiation: Optional[List[float]]
    evapotranspiration: Optional[List[float]]
    freezinglevel_height: Optional[List[int]]
    precipitation: Optional[List[float]]
    pressure_msl: Optional[List[float]]
    relativehumidity_2m: Optional[List[int]]
    shortwave_radiation: Optional[List[float]]
    snow_depth: Optional[List[int]]
    soil_moisture_0_1cm: Optional[List[float]]
    soil_moisture_1_3cm: Optional[List[float]]
    soil_moisture_27_81cm: Optional[List[float]]
    soil_moisture_3_9cm: Optional[List[float]]
    soil_moisture_9_27cm: Optional[List[float]]
    soil_temperature_0cm: Optional[List[float]]
    soil_temperature_18cm: Optional[List[float]]
    soil_temperature_54cm: Optional[List[float]]
    soil_temperature_6cm: Optional[List[float]]
    temperature_2m: Optional[List[float]]
    time: List[datetime]
    vapor_pressure_deficit: Optional[List[float]]
    weathercode: Optional[List[int]]
    winddirection_10m: Optional[List[int]]
    winddirection_120m: Optional[List[int]]
    winddirection_180m: Optional[List[int]]
    winddirection_80m: Optional[List[int]]
    windgusts_10m: Optional[List[float]]
    windspeed_10m: Optional[List[float]]
    windspeed_120m: Optional[List[float]]
    windspeed_180m: Optional[List[float]]
    windspeed_80m: Optional[List[float]]


class DailyForecast(BaseModel):
    """Daily weather data."""

    apparent_temperature_max: Optional[List[float]]
    apparent_temperature_min: Optional[List[float]]
    precipitation_hours: Optional[List[int]]
    precipitation_sum: Optional[List[float]]
    shortwave_radiation_sum: Optional[List[float]]
    sunrise: Optional[List[datetime]]
    sunset: Optional[List[datetime]]
    temperature_2m_max: Optional[List[float]]
    temperature_2m_min: Optional[List[float]]
    time: List[date]
    weathercode: Optional[List[int]]
    winddirection_10m_dominant: Optional[List[int]]
    windgusts_10m_max: Optional[List[float]]
    windspeed_10m_max: Optional[List[float]]


class HourlyForecastUnits(BaseModel):
    """Hourly weather data units."""

    apparent_temperature: Optional[str]
    cloudcover_high: Optional[str]
    cloudcover_low: Optional[str]
    cloudcover_mid: Optional[str]
    cloudcover: Optional[str]
    dewpoint_2m: Optional[str]
    diffuse_radiation: Optional[str]
    direct_normal_irradiance: Optional[str]
    direct_radiation: Optional[str]
    evapotranspiration: Optional[str]
    freezinglevel_height: Optional[str]
    precipitation: Optional[str]
    pressure_msl: Optional[str]
    relativehumidity_2m: Optional[str]
    shortwave_radiation: Optional[str]
    snow_depth: Optional[str]
    soil_moisture_0_1cm: Optional[str]
    soil_moisture_1_3cm: Optional[str]
    soil_moisture_27_81cm: Optional[str]
    soil_moisture_3_9cm: Optional[str]
    soil_moisture_9_27cm: Optional[str]
    soil_temperature_0cm: Optional[str]
    soil_temperature_18cm: Optional[str]
    soil_temperature_54cm: Optional[str]
    soil_temperature_6cm: Optional[str]
    temperature_2m: Optional[str]
    time: Optional[TimeFormat]
    vapor_pressure_deficit: Optional[str]
    weathercode: Optional[str]
    winddirection_10m: Optional[str]
    winddirection_120m: Optional[str]
    winddirection_180m: Optional[str]
    winddirection_80m: Optional[str]
    windgusts_10m: Optional[str]
    windspeed_10m: Optional[str]
    windspeed_120m: Optional[str]
    windspeed_180m: Optional[str]
    windspeed_80m: Optional[str]


class CurrentWeather(BaseModel):
    """Current weather data."""

    time: str
    windspeed: float
    winddirection: int
    temperature: float
    weathercode: int


class DailyForecastUnits(BaseModel):
    """Daily weather data units."""

    apparent_temperature_max: Optional[str]
    apparent_temperature_min: Optional[str]
    precipitation_hours: Optional[str]
    precipitation_sum: Optional[str]
    shortwave_radiation_sum: Optional[str]
    sunrise: Optional[TimeFormat]
    sunset: Optional[TimeFormat]
    temperature_2m_max: Optional[str]
    temperature_2m_min: Optional[str]
    time: Optional[TimeFormat]
    weathercode: Optional[str]
    winddirection_10m_dominant: Optional[str]
    windgusts_10m_max: Optional[str]
    windspeed_10m_max: Optional[str]


class Forecast(BaseModel):
    """Weather forecast."""

    current_weather: Optional[CurrentWeather]
    daily_units: Optional[DailyForecastUnits]
    daily: Optional[DailyForecast]
    elevation: float
    generationtime_ms: float
    hourly_units: Optional[HourlyForecastUnits]
    hourly: Optional[HourlyForecast]
    latitude: float
    longitude: float
    utc_offset_seconds: int


class GeocodingResult(BaseModel):
    """Geocoding result item."""

    geo_id: int = Field(..., alias="id")
    admin1_id: Optional[int]
    admin1: Optional[str]
    admin2_id: Optional[int]
    admin2: Optional[str]
    admin3_id: Optional[int]
    admin3: Optional[str]
    admin4_id: Optional[int]
    admin4: Optional[str]
    country_code: str
    country_id: int
    country: str
    elevation: float
    feature_code: str
    latitude: float
    longitude: float
    name: str
    population: Optional[int] = None
    postcodes: Optional[List[str]] = None
    ranking: Optional[float] = None
    timezone: str


class Geocoding(BaseModel):
    """Geocoding search result."""

    results: Optional[List[GeocodingResult]]
    generationtime_ms: float
