"""Asynchronous client for the Open-Meteo API."""

# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum, auto

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


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
    """Enum to represent the hourly parameters available.

    Every hourly parameter can be requested as a current condition as well.
    """

    # Apparent (feels like) temperature at 2 meters above ground, combining
    # wind chill, humidity, and solar radiation
    APPARENT_TEMPERATURE = "apparent_temperature"

    # Total cloud cover as an area fraction
    CLOUD_COVER = "cloud_cover"

    # High level clouds from 8 km altitude
    CLOUD_COVER_HIGH = "cloud_cover_high"

    # Low level clouds and fog up to 3 km altitude
    CLOUD_COVER_LOW = "cloud_cover_low"

    # Mid level clouds from 3 to 8 km altitude
    CLOUD_COVER_MID = "cloud_cover_mid"

    # Dew point temperature at 2 meters above ground
    DEW_POINT_2M = "dew_point_2m"

    # Diffuse solar radiation as average of the preceding hour
    DIFFUSE_RADIATION = "diffuse_radiation"

    # Direct solar radiation as average of the preceding hour on the horizontal
    # plane and the normal plane (perpendicular to the sun)
    DIRECT_NORMAL_IRRADIANCE = "direct_normal_irradiance"
    DIRECT_RADIATION = "direct_radiation"

    # Sum of evapotranspiration of the preceding hour from land surface and
    # plants
    EVAPOTRANSPIRATION = "evapotranspiration"

    # Altitude above sea level of the 0°C level
    FREEZING_LEVEL_HEIGHT = "freezing_level_height"

    # Whether it is day (1) or night (0) at the location
    IS_DAY = "is_day"

    # Total precipitation (rain, showers, snow) sum of the preceding hour
    PRECIPITATION = "precipitation"

    # Probability of precipitation (rain, showers, snow) for the next hour
    PRECIPITATION_PROBABILITY = "precipitation_probability"

    # Atmospheric air pressure reduced to sea level (hPa)
    PRESSURE_MSL = "pressure_msl"

    # Relative humidity at 2 meters above ground
    RELATIVE_HUMIDITY_2M = "relative_humidity_2m"

    # Shortwave solar radiation as average of the preceding hour
    SHORTWAVE_RADIATION = "shortwave_radiation"

    # Snow depth on the ground
    SNOW_DEPTH = "snow_depth"

    # Average soil water content as volumetric mixing ratio at 0-1, 1-3, 3-9,
    # 9-27 and 27-81 cm depths.
    SOIL_MOISTURE_0_TO_1CM = "soil_moisture_0_to_1cm"
    SOIL_MOISTURE_1_TO_3CM = "soil_moisture_1_to_3cm"
    SOIL_MOISTURE_27_TO_81CM = "soil_moisture_27_to_81cm"
    SOIL_MOISTURE_3_TO_9CM = "soil_moisture_3_to_9cm"
    SOIL_MOISTURE_9_TO_27CM = "soil_moisture_9_to_27cm"

    # Temperature in the soil at 0, 6, 18 and 54 cm depths. 0 cm is the surface
    # temperature on land or water surface temperature on water.
    SOIL_TEMPERATURE_0CM = "soil_temperature_0cm"
    SOIL_TEMPERATURE_18CM = "soil_temperature_18cm"
    SOIL_TEMPERATURE_54CM = "soil_temperature_54cm"
    SOIL_TEMPERATURE_6CM = "soil_temperature_6cm"

    # Air temperature at 2 meters above ground
    TEMPERATURE_2M = "temperature_2m"

    # UV index
    UV_INDEX = "uv_index"

    # Vapour Pressure Deficit (VPD) in kilopascal (kPa). For high VPD (>1.6),
    # water transpiration of plants increases. For low VPD (<0.4),
    # transpiration decreases.
    VAPOUR_PRESSURE_DEFICIT = "vapour_pressure_deficit"

    # Visibility in meters
    VISIBILITY = "visibility"

    # Weather condition as a WMO numeric weather code.
    WEATHER_CODE = "weather_code"

    # Wind direction at 10, 80, 120 or 180 meters above ground
    WIND_DIRECTION_10M = "wind_direction_10m"
    WIND_DIRECTION_120M = "wind_direction_120m"
    WIND_DIRECTION_180M = "wind_direction_180m"
    WIND_DIRECTION_80M = "wind_direction_80m"

    # Gusts at 10 meters above ground as a maximum of the preceding hour
    WIND_GUSTS_10M = "wind_gusts_10m"

    # Wind speed at 10, 80, 120 or 180 meters above ground.
    # Wind speed on 10 meters is the standard level.
    WIND_SPEED_10M = "wind_speed_10m"
    WIND_SPEED_120M = "wind_speed_120m"
    WIND_SPEED_180M = "wind_speed_180m"
    WIND_SPEED_80M = "wind_speed_80m"


class DailyParameters(StrEnum):
    """Enum to represent the daily parameters available."""

    # Maximum and minimum daily apparent temperature at 2 meters above ground.
    APPARENT_TEMPERATURE_MAX = "apparent_temperature_max"
    APPARENT_TEMPERATURE_MIN = "apparent_temperature_min"

    # Mean total cloud cover as an area fraction
    CLOUD_COVER_MEAN = "cloud_cover_mean"

    # Mean dew point temperature at 2 meters above ground
    DEW_POINT_2M_MEAN = "dew_point_2m_mean"

    # The number of hours with rain
    PRECIPITATION_HOURS = "precipitation_hours"

    # Sum of daily precipitation
    PRECIPITATION_SUM = "precipitation_sum"

    # Maximum, mean, and minimum probability of precipitation for the day
    PRECIPITATION_PROBABILITY_MAX = "precipitation_probability_max"
    PRECIPITATION_PROBABILITY_MEAN = "precipitation_probability_mean"
    PRECIPITATION_PROBABILITY_MIN = "precipitation_probability_min"

    # Mean atmospheric air pressure reduced to sea level (hPa)
    PRESSURE_MSL_MEAN = "pressure_msl_mean"

    # Mean relative humidity at 2 meters above ground
    RELATIVE_HUMIDITY_2M_MEAN = "relative_humidity_2m_mean"

    # The sum of solar radiation on a given day in Mega Joules
    SHORTWAVE_RADIATION_SUM = "shortwave_radiation_sum"

    # Sun rise and set times
    SUNRISE = "sunrise"
    SUNSET = "sunset"

    # Maximum and minimum daily air temperature at 2 meters above ground
    TEMPERATURE_2M_MAX = "temperature_2m_max"
    TEMPERATURE_2M_MIN = "temperature_2m_min"

    # Maximum UV index, with and without taking clouds into account
    UV_INDEX_MAX = "uv_index_max"
    UV_INDEX_CLEAR_SKY_MAX = "uv_index_clear_sky_max"

    # The most severe weather condition on a given day
    WEATHER_CODE = "weather_code"

    # Dominant wind direction
    WIND_DIRECTION_10M_DOMINANT = "wind_direction_10m_dominant"

    # Maximum wind speed and gusts on a day
    WIND_GUSTS_10M_MAX = "wind_gusts_10m_max"
    WIND_SPEED_10M_MAX = "wind_speed_10m_max"


@dataclass
class CurrentForecast(DataClassORJSONMixin):
    """Current weather conditions."""

    time: datetime
    interval: int
    apparent_temperature: float | None = None
    cloud_cover: int | None = None
    cloud_cover_high: int | None = None
    cloud_cover_low: int | None = None
    cloud_cover_mid: int | None = None
    dew_point_2m: float | None = None
    diffuse_radiation: float | None = None
    direct_normal_irradiance: float | None = None
    direct_radiation: float | None = None
    evapotranspiration: float | None = None
    freezing_level_height: float | None = None
    is_day: bool | None = None
    precipitation: float | None = None
    precipitation_probability: int | None = None
    pressure_msl: float | None = None
    relative_humidity_2m: int | None = None
    shortwave_radiation: float | None = None
    snow_depth: float | None = None
    soil_moisture_0_to_1cm: float | None = None
    soil_moisture_1_to_3cm: float | None = None
    soil_moisture_27_to_81cm: float | None = None
    soil_moisture_3_to_9cm: float | None = None
    soil_moisture_9_to_27cm: float | None = None
    soil_temperature_0cm: float | None = None
    soil_temperature_18cm: float | None = None
    soil_temperature_54cm: float | None = None
    soil_temperature_6cm: float | None = None
    temperature_2m: float | None = None
    uv_index: float | None = None
    vapour_pressure_deficit: float | None = None
    visibility: float | None = None
    weather_code: int | None = None
    wind_direction_10m: int | None = None
    wind_direction_120m: int | None = None
    wind_direction_180m: int | None = None
    wind_direction_80m: int | None = None
    wind_gusts_10m: float | None = None
    wind_speed_10m: float | None = None
    wind_speed_120m: float | None = None
    wind_speed_180m: float | None = None
    wind_speed_80m: float | None = None


@dataclass
class CurrentForecastUnits(DataClassORJSONMixin):
    """Current weather conditions units."""

    time: TimeFormat | None = None
    interval: str | None = None
    apparent_temperature: str | None = None
    cloud_cover: str | None = None
    cloud_cover_high: str | None = None
    cloud_cover_low: str | None = None
    cloud_cover_mid: str | None = None
    dew_point_2m: str | None = None
    diffuse_radiation: str | None = None
    direct_normal_irradiance: str | None = None
    direct_radiation: str | None = None
    evapotranspiration: str | None = None
    freezing_level_height: str | None = None
    is_day: str | None = None
    precipitation: str | None = None
    precipitation_probability: str | None = None
    pressure_msl: str | None = None
    relative_humidity_2m: str | None = None
    shortwave_radiation: str | None = None
    snow_depth: str | None = None
    soil_moisture_0_to_1cm: str | None = None
    soil_moisture_1_to_3cm: str | None = None
    soil_moisture_27_to_81cm: str | None = None
    soil_moisture_3_to_9cm: str | None = None
    soil_moisture_9_to_27cm: str | None = None
    soil_temperature_0cm: str | None = None
    soil_temperature_18cm: str | None = None
    soil_temperature_54cm: str | None = None
    soil_temperature_6cm: str | None = None
    temperature_2m: str | None = None
    uv_index: str | None = None
    vapour_pressure_deficit: str | None = None
    visibility: str | None = None
    weather_code: str | None = None
    wind_direction_10m: str | None = None
    wind_direction_120m: str | None = None
    wind_direction_180m: str | None = None
    wind_direction_80m: str | None = None
    wind_gusts_10m: str | None = None
    wind_speed_10m: str | None = None
    wind_speed_120m: str | None = None
    wind_speed_180m: str | None = None
    wind_speed_80m: str | None = None


@dataclass
class HourlyForecast(DataClassORJSONMixin):
    """Hourly weather data."""

    time: list[datetime]
    apparent_temperature: list[float | None] | None = None
    cloud_cover: list[int | None] | None = None
    cloud_cover_high: list[int | None] | None = None
    cloud_cover_low: list[int | None] | None = None
    cloud_cover_mid: list[int | None] | None = None
    dew_point_2m: list[float | None] | None = None
    diffuse_radiation: list[float | None] | None = None
    direct_normal_irradiance: list[float | None] | None = None
    direct_radiation: list[float | None] | None = None
    evapotranspiration: list[float | None] | None = None
    freezing_level_height: list[float | None] | None = None
    is_day: list[bool | None] | None = None
    precipitation: list[float | None] | None = None
    precipitation_probability: list[int | None] | None = None
    pressure_msl: list[float | None] | None = None
    relative_humidity_2m: list[int | None] | None = None
    shortwave_radiation: list[float | None] | None = None
    snow_depth: list[float | None] | None = None
    soil_moisture_0_to_1cm: list[float | None] | None = None
    soil_moisture_1_to_3cm: list[float | None] | None = None
    soil_moisture_27_to_81cm: list[float | None] | None = None
    soil_moisture_3_to_9cm: list[float | None] | None = None
    soil_moisture_9_to_27cm: list[float | None] | None = None
    soil_temperature_0cm: list[float | None] | None = None
    soil_temperature_18cm: list[float | None] | None = None
    soil_temperature_54cm: list[float | None] | None = None
    soil_temperature_6cm: list[float | None] | None = None
    temperature_2m: list[float | None] | None = None
    uv_index: list[float | None] | None = None
    vapour_pressure_deficit: list[float | None] | None = None
    visibility: list[float | None] | None = None
    weather_code: list[int | None] | None = None
    wind_direction_10m: list[int | None] | None = None
    wind_direction_120m: list[int | None] | None = None
    wind_direction_180m: list[int | None] | None = None
    wind_direction_80m: list[int | None] | None = None
    wind_gusts_10m: list[float | None] | None = None
    wind_speed_10m: list[float | None] | None = None
    wind_speed_120m: list[float | None] | None = None
    wind_speed_180m: list[float | None] | None = None
    wind_speed_80m: list[float | None] | None = None


@dataclass
class HourlyForecastUnits(DataClassORJSONMixin):
    """Hourly weather data units."""

    time: TimeFormat | None = None
    apparent_temperature: str | None = None
    cloud_cover: str | None = None
    cloud_cover_high: str | None = None
    cloud_cover_low: str | None = None
    cloud_cover_mid: str | None = None
    dew_point_2m: str | None = None
    diffuse_radiation: str | None = None
    direct_normal_irradiance: str | None = None
    direct_radiation: str | None = None
    evapotranspiration: str | None = None
    freezing_level_height: str | None = None
    is_day: str | None = None
    precipitation: str | None = None
    precipitation_probability: str | None = None
    pressure_msl: str | None = None
    relative_humidity_2m: str | None = None
    shortwave_radiation: str | None = None
    snow_depth: str | None = None
    soil_moisture_0_to_1cm: str | None = None
    soil_moisture_1_to_3cm: str | None = None
    soil_moisture_27_to_81cm: str | None = None
    soil_moisture_3_to_9cm: str | None = None
    soil_moisture_9_to_27cm: str | None = None
    soil_temperature_0cm: str | None = None
    soil_temperature_18cm: str | None = None
    soil_temperature_54cm: str | None = None
    soil_temperature_6cm: str | None = None
    temperature_2m: str | None = None
    uv_index: str | None = None
    vapour_pressure_deficit: str | None = None
    visibility: str | None = None
    weather_code: str | None = None
    wind_direction_10m: str | None = None
    wind_direction_120m: str | None = None
    wind_direction_180m: str | None = None
    wind_direction_80m: str | None = None
    wind_gusts_10m: str | None = None
    wind_speed_10m: str | None = None
    wind_speed_120m: str | None = None
    wind_speed_180m: str | None = None
    wind_speed_80m: str | None = None


@dataclass
class DailyForecast(DataClassORJSONMixin):
    """Daily weather data."""

    time: list[date]
    apparent_temperature_max: list[float | None] | None = None
    apparent_temperature_min: list[float | None] | None = None
    cloud_cover_mean: list[int | None] | None = None
    dew_point_2m_mean: list[float | None] | None = None
    precipitation_hours: list[float | None] | None = None
    precipitation_sum: list[float | None] | None = None
    precipitation_probability_max: list[int | None] | None = None
    precipitation_probability_mean: list[float | None] | None = None
    precipitation_probability_min: list[float | None] | None = None
    pressure_msl_mean: list[float | None] | None = None
    relative_humidity_2m_mean: list[int | None] | None = None
    shortwave_radiation_sum: list[float | None] | None = None
    sunrise: list[datetime | None] | None = None
    sunset: list[datetime | None] | None = None
    temperature_2m_max: list[float | None] | None = None
    temperature_2m_min: list[float | None] | None = None
    uv_index_max: list[float | None] | None = None
    uv_index_clear_sky_max: list[float | None] | None = None
    weather_code: list[int | None] | None = None
    wind_direction_10m_dominant: list[int | None] | None = None
    wind_gusts_10m_max: list[float | None] | None = None
    wind_speed_10m_max: list[float | None] | None = None


@dataclass
class DailyForecastUnits(DataClassORJSONMixin):
    """Daily weather data units."""

    time: TimeFormat | None = None
    apparent_temperature_max: str | None = None
    apparent_temperature_min: str | None = None
    cloud_cover_mean: str | None = None
    dew_point_2m_mean: str | None = None
    precipitation_hours: str | None = None
    precipitation_sum: str | None = None
    precipitation_probability_max: str | None = None
    precipitation_probability_mean: str | None = None
    precipitation_probability_min: str | None = None
    pressure_msl_mean: str | None = None
    relative_humidity_2m_mean: str | None = None
    shortwave_radiation_sum: str | None = None
    sunrise: TimeFormat | None = None
    sunset: TimeFormat | None = None
    temperature_2m_max: str | None = None
    temperature_2m_min: str | None = None
    uv_index_max: str | None = None
    uv_index_clear_sky_max: str | None = None
    weather_code: str | None = None
    wind_direction_10m_dominant: str | None = None
    wind_gusts_10m_max: str | None = None
    wind_speed_10m_max: str | None = None


@dataclass
class Forecast(DataClassORJSONMixin):
    """Weather forecast."""

    elevation: float
    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    latitude: float
    longitude: float
    timezone: str
    timezone_abbreviation: str
    utc_offset_seconds: int
    current_units: CurrentForecastUnits | None = None
    current: CurrentForecast | None = None
    daily_units: DailyForecastUnits | None = None
    daily: DailyForecast | None = None
    hourly_units: HourlyForecastUnits | None = None
    hourly: HourlyForecast | None = None


class AirQualityParameters(StrEnum):
    """Enum to represent the air quality parameters available.

    These can be requested both as current conditions and hourly.
    """

    # Particulate matter with diameter smaller than 10 µm (PM10) and smaller
    # than 2.5 µm (PM2.5) close to surface (10 meter above ground).
    PM10 = "pm10"
    PM2_5 = "pm2_5"

    # Atmospheric gases close to surface (10 meter above ground)
    CARBON_MONOXIDE = "carbon_monoxide"
    NITROGEN_DIOXIDE = "nitrogen_dioxide"
    SULPHUR_DIOXIDE = "sulphur_dioxide"
    OZONE = "ozone"

    # CO2 close to surface (10 meter above ground)
    CARBON_DIOXIDE = "carbon_dioxide"

    # Ammonia concentration. Only available for Europe
    AMMONIA = "ammonia"

    # Aerosol optical depth at 550 nm of the entire atmosphere to indicate haze
    AEROSOL_OPTICAL_DEPTH = "aerosol_optical_depth"

    # Methane close to surface (10 meter above ground)
    METHANE = "methane"

    # Saharan dust particles close to surface level (10 meter above ground)
    DUST = "dust"

    # UV index considering clouds and clear sky
    UV_INDEX = "uv_index"
    UV_INDEX_CLEAR_SKY = "uv_index_clear_sky"

    # Pollen for various plants. Only available in Europe as provided by
    # CAMS European Air Quality forecast.
    ALDER_POLLEN = "alder_pollen"
    BIRCH_POLLEN = "birch_pollen"
    GRASS_POLLEN = "grass_pollen"
    MUGWORT_POLLEN = "mugwort_pollen"
    OLIVE_POLLEN = "olive_pollen"
    RAGWEED_POLLEN = "ragweed_pollen"

    # European Air Quality Index (AQI) calculated for different particulate
    # matter and gases individually. The consolidated european_aqi returns
    # the maximum of all individual indices. Ranges from 0-20 (good), 20-40
    # (fair), 40-60 (moderate), 60-80 (poor), 80-100 (very poor) and exceeds
    # 100 for extremely poor conditions.
    EUROPEAN_AQI = "european_aqi"
    EUROPEAN_AQI_PM2_5 = "european_aqi_pm2_5"
    EUROPEAN_AQI_PM10 = "european_aqi_pm10"
    EUROPEAN_AQI_NITROGEN_DIOXIDE = "european_aqi_nitrogen_dioxide"
    EUROPEAN_AQI_OZONE = "european_aqi_ozone"
    EUROPEAN_AQI_SULPHUR_DIOXIDE = "european_aqi_sulphur_dioxide"

    # United States Air Quality Index (AQI) calculated for different particulate
    # matter and gases individually. The consolidated us_aqi returns the maximum
    # of all individual indices. Ranges from 0-50 (good), 51-100 (moderate),
    # 101-150 (unhealthy for sensitive groups), 151-200 (unhealthy), 201-300
    # (very unhealthy) and 301-500 (hazardous).
    US_AQI = "us_aqi"
    US_AQI_PM2_5 = "us_aqi_pm2_5"
    US_AQI_PM10 = "us_aqi_pm10"
    US_AQI_NITROGEN_DIOXIDE = "us_aqi_nitrogen_dioxide"
    US_AQI_OZONE = "us_aqi_ozone"
    US_AQI_SULPHUR_DIOXIDE = "us_aqi_sulphur_dioxide"
    US_AQI_CARBON_MONOXIDE = "us_aqi_carbon_monoxide"


@dataclass
class CurrentAirQuality(DataClassORJSONMixin):
    """Current air quality data."""

    time: datetime
    interval: int
    pm10: float | None = None
    pm2_5: float | None = None
    carbon_monoxide: float | None = None
    nitrogen_dioxide: float | None = None
    sulphur_dioxide: float | None = None
    ozone: float | None = None
    carbon_dioxide: float | None = None
    ammonia: float | None = None
    aerosol_optical_depth: float | None = None
    methane: float | None = None
    dust: float | None = None
    uv_index: float | None = None
    uv_index_clear_sky: float | None = None
    alder_pollen: float | None = None
    birch_pollen: float | None = None
    grass_pollen: float | None = None
    mugwort_pollen: float | None = None
    olive_pollen: float | None = None
    ragweed_pollen: float | None = None
    european_aqi: int | None = None
    european_aqi_pm2_5: int | None = None
    european_aqi_pm10: int | None = None
    european_aqi_nitrogen_dioxide: int | None = None
    european_aqi_ozone: int | None = None
    european_aqi_sulphur_dioxide: int | None = None
    us_aqi: int | None = None
    us_aqi_pm2_5: int | None = None
    us_aqi_pm10: int | None = None
    us_aqi_nitrogen_dioxide: int | None = None
    us_aqi_ozone: int | None = None
    us_aqi_sulphur_dioxide: int | None = None
    us_aqi_carbon_monoxide: int | None = None


@dataclass
class CurrentAirQualityUnits(DataClassORJSONMixin):
    """Current air quality data units."""

    time: str
    interval: str
    pm10: str | None = None
    pm2_5: str | None = None
    carbon_monoxide: str | None = None
    nitrogen_dioxide: str | None = None
    sulphur_dioxide: str | None = None
    ozone: str | None = None
    carbon_dioxide: str | None = None
    ammonia: str | None = None
    aerosol_optical_depth: str | None = None
    methane: str | None = None
    dust: str | None = None
    uv_index: str | None = None
    uv_index_clear_sky: str | None = None
    alder_pollen: str | None = None
    birch_pollen: str | None = None
    grass_pollen: str | None = None
    mugwort_pollen: str | None = None
    olive_pollen: str | None = None
    ragweed_pollen: str | None = None
    european_aqi: str | None = None
    european_aqi_pm2_5: str | None = None
    european_aqi_pm10: str | None = None
    european_aqi_nitrogen_dioxide: str | None = None
    european_aqi_ozone: str | None = None
    european_aqi_sulphur_dioxide: str | None = None
    us_aqi: str | None = None
    us_aqi_pm2_5: str | None = None
    us_aqi_pm10: str | None = None
    us_aqi_nitrogen_dioxide: str | None = None
    us_aqi_ozone: str | None = None
    us_aqi_sulphur_dioxide: str | None = None
    us_aqi_carbon_monoxide: str | None = None


@dataclass
class HourlyAirQuality(DataClassORJSONMixin):
    """Hourly air quality data."""

    time: list[datetime]
    pm10: list[float | None] | None = None
    pm2_5: list[float | None] | None = None
    carbon_monoxide: list[float | None] | None = None
    nitrogen_dioxide: list[float | None] | None = None
    sulphur_dioxide: list[float | None] | None = None
    ozone: list[float | None] | None = None
    carbon_dioxide: list[float | None] | None = None
    ammonia: list[float | None] | None = None
    aerosol_optical_depth: list[float | None] | None = None
    methane: list[float | None] | None = None
    dust: list[float | None] | None = None
    uv_index: list[float | None] | None = None
    uv_index_clear_sky: list[float | None] | None = None
    alder_pollen: list[float | None] | None = None
    birch_pollen: list[float | None] | None = None
    grass_pollen: list[float | None] | None = None
    mugwort_pollen: list[float | None] | None = None
    olive_pollen: list[float | None] | None = None
    ragweed_pollen: list[float | None] | None = None
    european_aqi: list[int | None] | None = None
    european_aqi_pm2_5: list[int | None] | None = None
    european_aqi_pm10: list[int | None] | None = None
    european_aqi_nitrogen_dioxide: list[int | None] | None = None
    european_aqi_ozone: list[int | None] | None = None
    european_aqi_sulphur_dioxide: list[int | None] | None = None
    us_aqi: list[int | None] | None = None
    us_aqi_pm2_5: list[int | None] | None = None
    us_aqi_pm10: list[int | None] | None = None
    us_aqi_nitrogen_dioxide: list[int | None] | None = None
    us_aqi_ozone: list[int | None] | None = None
    us_aqi_sulphur_dioxide: list[int | None] | None = None
    us_aqi_carbon_monoxide: list[int | None] | None = None


@dataclass
class HourlyAirQualityUnits(DataClassORJSONMixin):
    """Hourly air quality data units."""

    time: str
    pm10: str | None = None
    pm2_5: str | None = None
    carbon_monoxide: str | None = None
    nitrogen_dioxide: str | None = None
    sulphur_dioxide: str | None = None
    ozone: str | None = None
    carbon_dioxide: str | None = None
    ammonia: str | None = None
    aerosol_optical_depth: str | None = None
    methane: str | None = None
    dust: str | None = None
    uv_index: str | None = None
    uv_index_clear_sky: str | None = None
    alder_pollen: str | None = None
    birch_pollen: str | None = None
    grass_pollen: str | None = None
    mugwort_pollen: str | None = None
    olive_pollen: str | None = None
    ragweed_pollen: str | None = None
    european_aqi: str | None = None
    european_aqi_pm2_5: str | None = None
    european_aqi_pm10: str | None = None
    european_aqi_nitrogen_dioxide: str | None = None
    european_aqi_ozone: str | None = None
    european_aqi_sulphur_dioxide: str | None = None
    us_aqi: str | None = None
    us_aqi_pm2_5: str | None = None
    us_aqi_pm10: str | None = None
    us_aqi_nitrogen_dioxide: str | None = None
    us_aqi_ozone: str | None = None
    us_aqi_sulphur_dioxide: str | None = None
    us_aqi_carbon_monoxide: str | None = None


@dataclass
class AirQuality(DataClassORJSONMixin):
    """Air quality forecast."""

    elevation: float
    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    latitude: float
    longitude: float
    timezone: str
    timezone_abbreviation: str
    utc_offset_seconds: int
    current_units: CurrentAirQualityUnits | None = None
    current: CurrentAirQuality | None = None
    hourly_units: HourlyAirQualityUnits | None = None
    hourly: HourlyAirQuality | None = None


@dataclass
class GeocodingResult(DataClassORJSONMixin):
    """Geocoding result item."""

    geo_id: int = field(metadata=field_options(alias="id"))
    feature_code: str
    latitude: float
    longitude: float
    name: str
    timezone: str

    # Not every location has these, Antarctica or some islands for example
    country_code: str | None = None
    country_id: int | None = None
    country: str | None = None
    elevation: float | None = None

    admin1_id: int | None = None
    admin1: str | None = None
    admin2_id: int | None = None
    admin2: str | None = None
    admin3_id: int | None = None
    admin3: str | None = None
    admin4_id: int | None = None
    admin4: str | None = None
    population: int | None = None
    postcodes: list[str] | None = None
    ranking: float | None = None


@dataclass
class Geocoding(DataClassORJSONMixin):
    """Geocoding search result."""

    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    results: list[GeocodingResult] | None = None


@dataclass
class Elevation(DataClassORJSONMixin):
    """Elevation lookup result."""

    elevation: list[float]
