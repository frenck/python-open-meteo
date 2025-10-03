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
    # from lands surface and plants
    EVAPOTRANSPIRATION = "evapotranspiration"

    # Altitude above sea level of the 0°C level
    FREEZING_LEVEL_HEIGHT = "freezinglevel_height"

    # Total precipitation (rain, showers, snow) sum of the preceding hour
    PRECIPITATION = "precipitation"

    # Probability of precipitation (rain, showers, snow) for the next hour
    PRECIPITATION_PROBABILITY = "precipitation_probability"

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

    # UV index
    UV_INDEX = "uv_index"

    # Vapor Pressure Deificit (VPD) in kilo pascal (kPa). For high VPD (>1.6),
    # water transpiration of plants increases. For low VPD (<0.4),
    # transpiration decreases.
    VAPOR_PRESSURE_DEFICIT = "vapor_pressure_deficit"

    # Visibility
    VISIBILITY = "visibility"

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

    # Maximum probability of precipitation for the day
    PRECIPITATION_PROBABILITY_MAX = "precipitation_probability_max"
    PRECIPITATION_PROBABILITY_MEAN = "precipitation_probability_mean"
    PRECIPITATION_PROBABILITY_MIN = "precipitation_probability_min"

    # The sum of solar radiation on a given day in Mega Joules.
    SHORTWAVE_RADIATION_SUM = "shortwave_radiation_sum"

    # Sun rise and set times
    SUNRISE = "sunrise"
    SUNSET = "sunset"

    # Maximum and minimum daily air temperature at 2 meters above ground.
    TEMPERATURE_2M_MAX = "temperature_2m_max"
    TEMPERATURE_2M_MIN = "temperature_2m_min"

    # UV index
    UV_INDEX_MAX = "uv_index_max"
    UV_INDEX_CLEAR_SKY_MAX = "uv_index_clear_sky_max"

    # The most severe weather condition on a given day.
    WEATHER_CODE = "weathercode"

    # Dominant wind direction.
    WIND_DIRECTION_10M_DOMINANT = "winddirection_10m_dominant"

    # Maximum wind speed and gusts on a day
    WIND_GUSTS_10M_MAX = "windgusts_10m_max"
    WIND_SPEED_10M_MAX = "windspeed_10m_max"


@dataclass
class HourlyForecast(DataClassORJSONMixin):
    """Hourly weather data."""

    time: list[datetime]
    apparent_temperature: list[float] | None = field(default=None)
    cloud_cover_high: list[int] | None = field(
        default=None, metadata=field_options(alias="cloudcover_high")
    )
    cloud_cover_low: list[int] | None = field(
        default=None, metadata=field_options(alias="cloudcover_low")
    )
    cloud_cover_mid: list[int] | None = field(
        default=None, metadata=field_options(alias="cloudcover_mid")
    )
    cloud_cover: list[int] | None = field(
        default=None, metadata=field_options(alias="cloudcover")
    )
    dew_point_2m: list[float] | None = field(
        default=None, metadata=field_options(alias="dewpoint_2m")
    )
    diffuse_radiation: list[float] | None = field(default=None)
    direct_normal_irradiance: list[float] | None = field(default=None)
    direct_radiation: list[float] | None = field(default=None)
    evapotranspiration: list[float] | None = field(default=None)
    freezing_level_height: list[int] | None = field(
        default=None, metadata=field_options(alias="freezinglevel_height")
    )
    precipitation: list[float] | None = field(default=None)
    precipitation_probability: list[int] | None = field(default=None)
    pressure_msl: list[float] | None = field(default=None)
    relative_humidity_2m: list[int] | None = field(
        default=None, metadata=field_options(alias="relativehumidity_2m")
    )
    shortwave_radiation: list[float] | None = field(default=None)
    snow_depth: list[int] | None = field(default=None)
    soil_moisture_0_1cm: list[float] | None = field(default=None)
    soil_moisture_1_3cm: list[float] | None = field(default=None)
    soil_moisture_27_81cm: list[float] | None = field(default=None)
    soil_moisture_3_9cm: list[float] | None = field(default=None)
    soil_moisture_9_27cm: list[float] | None = field(default=None)
    soil_temperature_0cm: list[float] | None = field(default=None)
    soil_temperature_18cm: list[float] | None = field(default=None)
    soil_temperature_54cm: list[float] | None = field(default=None)
    soil_temperature_6cm: list[float] | None = field(default=None)
    temperature_2m: list[float] | None = field(default=None)
    uv_index: list[float] | None = field(default=None)
    vapor_pressure_deficit: list[float] | None = field(default=None)
    visibility: list[float] | None = field(default=None)
    weather_code: list[int] | None = field(
        default=None, metadata=field_options(alias="weathercode")
    )
    wind_direction_10m: list[int] | None = field(
        default=None, metadata=field_options(alias="winddirection_10m")
    )
    wind_direction_120m: list[int] | None = field(
        default=None, metadata=field_options(alias="winddirection_120m")
    )
    wind_direction_180m: list[int] | None = field(
        default=None, metadata=field_options(alias="winddirection_180m")
    )
    wind_direction_80m: list[int] | None = field(
        default=None, metadata=field_options(alias="winddirection_80m")
    )
    wind_gusts_10m: list[float] | None = field(
        default=None, metadata=field_options(alias="windgusts_10m")
    )
    wind_speed_10m: list[float] | None = field(
        default=None, metadata=field_options(alias="windspeed_10m")
    )
    wind_speed_120m: list[float] | None = field(
        default=None, metadata=field_options(alias="windspeed_120m")
    )
    wind_speed_180m: list[float] | None = field(
        default=None, metadata=field_options(alias="windspeed_180m")
    )
    wind_speed_80m: list[float] | None = field(
        default=None, metadata=field_options(alias="windspeed_80m")
    )


@dataclass
class DailyForecast(DataClassORJSONMixin):
    """Daily weather data."""

    time: list[date]
    apparent_temperature_max: list[float] | None = field(default=None)
    apparent_temperature_min: list[float] | None = field(default=None)
    precipitation_hours: list[int] | None = field(default=None)
    precipitation_sum: list[float] | None = field(default=None)
    precipitation_probability_max: list[int] | None = field(default=None)
    precipitation_probability_mean: list[float] | None = field(default=None)
    precipitation_probability_min: list[float] | None = field(default=None)
    shortwave_radiation_sum: list[float] | None = field(default=None)
    sunrise: list[datetime] | None = field(default=None)
    sunset: list[datetime] | None = field(default=None)
    temperature_2m_max: list[float] | None = field(default=None)
    temperature_2m_min: list[float] | None = field(default=None)
    uv_index_max: list[float] | None = field(default=None)
    uv_index_clear_sky_max: list[float] | None = field(default=None)
    weathercode: list[int] | None = field(default=None)
    wind_direction_10m_dominant: list[int] | None = field(
        default=None, metadata=field_options(alias="winddirection_10m_dominant")
    )
    wind_gusts_10m_max: list[float] | None = field(
        default=None, metadata=field_options(alias="windgusts_10m_max")
    )
    wind_speed_10m_max: list[float] | None = field(
        default=None, metadata=field_options(alias="windspeed_10m_max")
    )


@dataclass
class HourlyForecastUnits(DataClassORJSONMixin):
    """Hourly weather data units."""

    apparent_temperature: str | None = field(default=None)
    cloud_cover_high: str | None = field(
        default=None, metadata=field_options(alias="cloudcover_high")
    )
    cloud_cover_low: str | None = field(
        default=None, metadata=field_options(alias="cloudcover_low")
    )
    cloud_cover_mid: str | None = field(
        default=None, metadata=field_options(alias="cloudcover_mid")
    )
    cloud_cover: str | None = field(
        default=None, metadata=field_options(alias="cloudcover")
    )
    dew_point_2m: str | None = field(
        default=None, metadata=field_options(alias="dewpoint_2m")
    )
    diffuse_radiation: str | None = field(default=None)
    direct_normal_irradiance: str | None = field(default=None)
    direct_radiation: str | None = field(default=None)
    evapotranspiration: str | None = field(default=None)
    freezing_level_height: str | None = field(
        default=None, metadata=field_options(alias="freezinglevel_height")
    )
    precipitation: str | None = field(default=None)
    precipitation_probability: str | None = field(default=None)
    pressure_msl: str | None = field(default=None)
    relative_humidity_2m: str | None = field(
        default=None, metadata=field_options(alias="relativehumidity_2m")
    )
    shortwave_radiation: str | None = field(default=None)
    snow_depth: str | None = field(default=None)
    soil_moisture_0_1cm: str | None = field(default=None)
    soil_moisture_1_3cm: str | None = field(default=None)
    soil_moisture_27_81cm: str | None = field(default=None)
    soil_moisture_3_9cm: str | None = field(default=None)
    soil_moisture_9_27cm: str | None = field(default=None)
    soil_temperature_0cm: str | None = field(default=None)
    soil_temperature_18cm: str | None = field(default=None)
    soil_temperature_54cm: str | None = field(default=None)
    soil_temperature_6cm: str | None = field(default=None)
    temperature_2m: str | None = field(default=None)
    time: TimeFormat | None = field(default=None)
    vapor_pressure_deficit: str | None = field(default=None)
    visibility: str | None = field(default=None)
    uv_index: str | None = field(default=None)
    weather_code: str | None = field(
        default=None, metadata=field_options(alias="weathercode")
    )
    wind_direction_10m: str | None = field(
        default=None, metadata=field_options(alias="winddirection_10m")
    )
    wind_direction_120m: str | None = field(
        default=None, metadata=field_options(alias="winddirection_120m")
    )
    wind_direction_180m: str | None = field(
        default=None, metadata=field_options(alias="winddirection_180m")
    )
    wind_direction_80m: str | None = field(
        default=None, metadata=field_options(alias="winddirection_80m")
    )
    wind_gusts_10m: str | None = field(
        default=None, metadata=field_options(alias="windgusts_10m")
    )
    wind_speed_10m: str | None = field(
        default=None, metadata=field_options(alias="windspeed_10m")
    )
    wind_speed_120m: str | None = field(
        default=None, metadata=field_options(alias="windspeed_120m")
    )
    wind_speed_180m: str | None = field(
        default=None, metadata=field_options(alias="windspeed_180m")
    )
    wind_speed_80m: str | None = field(
        default=None, metadata=field_options(alias="windspeed_80m")
    )


@dataclass
class CurrentWeather(DataClassORJSONMixin):
    """Current weather data."""

    time: datetime
    temperature: float
    wind_speed: float = field(metadata=field_options(alias="windspeed"))
    wind_direction: int = field(metadata=field_options(alias="winddirection"))
    weather_code: int = field(metadata=field_options(alias="weathercode"))


@dataclass
class DailyForecastUnits(DataClassORJSONMixin):
    """Daily weather data units."""

    apparent_temperature_max: str | None = field(default=None)
    apparent_temperature_min: str | None = field(default=None)
    precipitation_hours: str | None = field(default=None)
    precipitation_sum: str | None = field(default=None)
    precipitation_probability_max: str | None = field(default=None)
    precipitation_probability_mean: str | None = field(default=None)
    precipitation_probability_min: str | None = field(default=None)
    shortwave_radiation_sum: str | None = field(default=None)
    sunrise: TimeFormat | None = field(default=None)
    sunset: TimeFormat | None = field(default=None)
    temperature_2m_max: str | None = field(default=None)
    temperature_2m_min: str | None = field(default=None)
    time: TimeFormat | None = field(default=None)
    uv_index_max: str | None = field(default=None)
    uv_index_clear_sky_max: str | None = field(default=None)
    weather_code: str | None = field(
        default=None, metadata=field_options(alias="weathercode")
    )
    wind_direction_10m_dominant: str | None = field(
        default=None,
        metadata=field_options(alias="winddirection_10m_dominant"),
    )
    wind_gusts_10m_max: str | None = field(
        default=None, metadata=field_options(alias="windgusts_10m_max")
    )
    wind_speed_10m_max: str | None = field(
        default=None, metadata=field_options(alias="windspeed_10m_max")
    )


@dataclass
class Forecast(DataClassORJSONMixin):
    """Weather forecast."""

    elevation: float
    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    latitude: float
    longitude: float
    utc_offset_seconds: int
    current_weather: CurrentWeather | None = field(default=None)
    daily_units: DailyForecastUnits | None = field(default=None)
    daily: DailyForecast | None = field(default=None)
    hourly_units: HourlyForecastUnits | None = field(default=None)
    hourly: HourlyForecast | None = field(default=None)


class AirQualityParameters(StrEnum):
    """Enum to represent the hourly air quality parameters available."""

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
    EUROPEAN_AQI_SULPHUR_DIOXID = "european_aqi_sulphur_dioxide"

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
    european_aqi: int | None = None
    us_aqi: int | None = None
    pm2_5: float | None = None
    pm10: float | None = None
    carbon_monoxide: float | None = None
    nitrogen_dioxide: float | None = None
    sulphur_dioxide: float | None = None
    ozone: float | None = None
    aerosol_optical_depth: float | None = None
    dust: float | None = None
    uv_index: float | None = None
    uv_index_clear_sky: float | None = None
    ammonia: float | None = None
    alder_pollen: float | None = None
    birch_pollen: float | None = None
    grass_pollen: float | None = None
    mugwort_pollen: float | None = None
    olive_pollen: float | None = None
    ragweed_pollen: float | None = None


@dataclass
class HourlyAirQuality(DataClassORJSONMixin):
    """Current air quality data."""

    time: list[datetime]
    european_aqi: list[int | None] | None = None
    us_aqi: list[int | None] | None = None
    pm2_5: list[float | None] | None = None
    pm10: list[float | None] | None = None
    carbon_monoxide: list[float | None] | None = None
    nitrogen_dioxide: list[float | None] | None = None
    sulphur_dioxide: list[float | None] | None = None
    ozone: list[float | None] | None = None
    aerosol_optical_depth: list[float | None] | None = None
    dust: list[float | None] | None = None
    uv_index: list[float | None] | None = None
    uv_index_clear_sky: list[float | None] | None = None
    ammonia: list[float | None] | None = None
    alder_pollen: list[float | None] | None = None
    birch_pollen: list[float | None] | None = None
    grass_pollen: list[float | None] | None = None
    mugwort_pollen: list[float | None] | None = None
    olive_pollen: list[float | None] | None = None
    ragweed_pollen: list[float | None] | None = None


@dataclass
class CurrentAirQualityUnits(DataClassORJSONMixin):
    """Current air quality data."""

    time: str
    interval: str
    european_aqi: str | None = None
    us_aqi: str | None = None
    pm2_5: str | None = None
    pm10: str | None = None
    carbon_monoxide: str | None = None
    nitrogen_dioxide: str | None = None
    sulphur_dioxide: str | None = None
    ozone: str | None = None
    aerosol_optical_depth: str | None = None
    dust: str | None = None
    uv_index: str | None = None
    uv_index_clear_sky: str | None = None
    ammonia: str | None = None
    alder_pollen: str | None = None
    birch_pollen: str | None = None
    grass_pollen: str | None = None
    mugwort_pollen: str | None = None
    olive_pollen: str | None = None
    ragweed_pollen: str | None = None


@dataclass
class HourlyAirQualityUnits(DataClassORJSONMixin):
    """Hourly air quality data."""

    time: str
    european_aqi: str | None = None
    us_aqi: str | None = None
    pm2_5: str | None = None
    pm10: str | None = None
    carbon_monoxide: str | None = None
    nitrogen_dioxide: str | None = None
    sulphur_dioxide: str | None = None
    ozone: str | None = None
    aerosol_optical_depth: str | None = None
    dust: str | None = None
    uv_index: str | None = None
    uv_index_clear_sky: str | None = None
    ammonia: str | None = None
    alder_pollen: str | None = None
    birch_pollen: str | None = None
    grass_pollen: str | None = None
    mugwort_pollen: str | None = None
    olive_pollen: str | None = None
    ragweed_pollen: str | None = None


@dataclass
class AirQuality(DataClassORJSONMixin):
    """Air Quality forecast."""

    elevation: float
    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    latitude: float
    longitude: float
    utc_offset_seconds: int
    current_units: CurrentAirQualityUnits | None = field(default=None)
    current: CurrentAirQuality | None = field(default=None)
    hourly_units: HourlyAirQualityUnits | None = field(default=None)
    hourly: HourlyAirQuality | None = field(default=None)


@dataclass
class GeocodingResult(DataClassORJSONMixin):
    """Geocoding result item."""

    geo_id: int = field(metadata=field_options(alias="id"))
    country_code: str
    country_id: int
    country: str
    elevation: float
    feature_code: str
    latitude: float
    longitude: float
    name: str
    timezone: str
    admin1_id: int | None = field(default=None)
    admin1: str | None = field(default=None)
    admin2_id: int | None = field(default=None)
    admin2: str | None = field(default=None)
    admin3_id: int | None = field(default=None)
    admin3: str | None = field(default=None)
    admin4_id: int | None = field(default=None)
    admin4: str | None = field(default=None)
    population: int | None = field(default=None)
    postcodes: list[str] | None = field(default=None)
    ranking: float | None = field(default=None)


@dataclass
class Geocoding(DataClassORJSONMixin):
    """Geocoding search result."""

    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    results: list[GeocodingResult] | None = field(default=None)
