"""Models for the Open-Meteo air quality API."""

# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


class AirQualityDomain(StrEnum):
    """Enum to represent the air quality model domains available."""

    # Combine both domains automatically (the API default)
    AUTO = "auto"

    # CAMS European air quality forecast, about 11 km resolution
    CAMS_EUROPE = "cams_europe"

    # CAMS global atmospheric composition forecast, about 45 km resolution
    CAMS_GLOBAL = "cams_global"


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

    # Whether it is day (1) or night (0) at the location
    IS_DAY = "is_day"

    # Additional gases close to surface (10 meter above ground)
    FORMALDEHYDE = "formaldehyde"
    GLYOXAL = "glyoxal"
    NITROGEN_MONOXIDE = "nitrogen_monoxide"
    PEROXYACYL_NITRATES = "peroxyacyl_nitrates"

    # Sea salt aerosol close to surface (10 meter above ground)
    SEA_SALT_AEROSOL = "sea_salt_aerosol"

    # Additional compounds and aerosols close to surface (10 meter above
    # ground). Only available for Europe.
    NON_METHANE_VOLATILE_ORGANIC_COMPOUNDS = "non_methane_volatile_organic_compounds"
    PM10_WILDFIRES = "pm10_wildfires"
    PM2_5_TOTAL_ORGANIC_MATTER = "pm2_5_total_organic_matter"
    RESIDENTIAL_ELEMENTARY_CARBON = "residential_elementary_carbon"
    SECONDARY_INORGANIC_AEROSOL = "secondary_inorganic_aerosol"
    TOTAL_ELEMENTARY_CARBON = "total_elementary_carbon"

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
    is_day: bool | None = None
    formaldehyde: float | None = None
    glyoxal: float | None = None
    nitrogen_monoxide: float | None = None
    peroxyacyl_nitrates: float | None = None
    sea_salt_aerosol: float | None = None
    non_methane_volatile_organic_compounds: float | None = None
    pm10_wildfires: float | None = None
    pm2_5_total_organic_matter: float | None = None
    residential_elementary_carbon: float | None = None
    secondary_inorganic_aerosol: float | None = None
    total_elementary_carbon: float | None = None
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
    is_day: str | None = None
    formaldehyde: str | None = None
    glyoxal: str | None = None
    nitrogen_monoxide: str | None = None
    peroxyacyl_nitrates: str | None = None
    sea_salt_aerosol: str | None = None
    non_methane_volatile_organic_compounds: str | None = None
    pm10_wildfires: str | None = None
    pm2_5_total_organic_matter: str | None = None
    residential_elementary_carbon: str | None = None
    secondary_inorganic_aerosol: str | None = None
    total_elementary_carbon: str | None = None
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
    is_day: list[bool | None] | None = None
    formaldehyde: list[float | None] | None = None
    glyoxal: list[float | None] | None = None
    nitrogen_monoxide: list[float | None] | None = None
    peroxyacyl_nitrates: list[float | None] | None = None
    sea_salt_aerosol: list[float | None] | None = None
    non_methane_volatile_organic_compounds: list[float | None] | None = None
    pm10_wildfires: list[float | None] | None = None
    pm2_5_total_organic_matter: list[float | None] | None = None
    residential_elementary_carbon: list[float | None] | None = None
    secondary_inorganic_aerosol: list[float | None] | None = None
    total_elementary_carbon: list[float | None] | None = None
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
    is_day: str | None = None
    formaldehyde: str | None = None
    glyoxal: str | None = None
    nitrogen_monoxide: str | None = None
    peroxyacyl_nitrates: str | None = None
    sea_salt_aerosol: str | None = None
    non_methane_volatile_organic_compounds: str | None = None
    pm10_wildfires: str | None = None
    pm2_5_total_organic_matter: str | None = None
    residential_elementary_carbon: str | None = None
    secondary_inorganic_aerosol: str | None = None
    total_elementary_carbon: str | None = None
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
