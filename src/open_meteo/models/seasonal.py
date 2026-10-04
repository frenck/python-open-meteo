"""Models for the Open-Meteo seasonal forecast API."""

# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import TimeFormat
from .forecast import (
    DailyForecast,
    DailyForecastUnits,
    HourlyForecast,
    HourlyForecastUnits,
)


class SeasonalWeeklyParameters(StrEnum):
    """Enum to represent the weekly seasonal parameters available.

    Every variable is a statistic over the ensemble members, per period:
    _mean is the mean, and _anomaly the difference with the model climate
    (forecast minus model climatology). _anomaly_gtN and _anomaly_ltmN are
    the probability in percent that the anomaly is greater than N, or lower
    than minus N. _efi is the Extreme Forecast Index, from -1 to 1, for how
    unusual the forecast is compared to the model climate. _sot10 and _sot90
    are the Shift of Tails of the 10th and 90th percentile, for how extreme
    an event could become.
    """

    # Wind Speed (10 m)
    WIND_SPEED_10M_MEAN = "wind_speed_10m_mean"
    WIND_SPEED_10M_ANOMALY = "wind_speed_10m_anomaly"

    # Wind Speed (100 m)
    WIND_SPEED_100M_MEAN = "wind_speed_100m_mean"
    WIND_SPEED_100M_ANOMALY = "wind_speed_100m_anomaly"

    # Wind Direction (10 m)
    WIND_DIRECTION_10M_MEAN = "wind_direction_10m_mean"
    WIND_DIRECTION_10M_ANOMALY = "wind_direction_10m_anomaly"

    # Wind Direction (100 m)
    WIND_DIRECTION_100M_MEAN = "wind_direction_100m_mean"
    WIND_DIRECTION_100M_ANOMALY = "wind_direction_100m_anomaly"

    # Snow Depth
    SNOW_DEPTH_MEAN = "snow_depth_mean"
    SNOW_DEPTH_ANOMALY = "snow_depth_anomaly"

    # Snowfall
    SNOWFALL_MEAN = "snowfall_mean"
    SNOWFALL_ANOMALY = "snowfall_anomaly"

    #  Temperature (2 m)
    TEMPERATURE_2M_ANOMALY_GT0 = "temperature_2m_anomaly_gt0"
    TEMPERATURE_2M_ANOMALY_GT1 = "temperature_2m_anomaly_gt1"
    TEMPERATURE_2M_ANOMALY_GT2 = "temperature_2m_anomaly_gt2"
    TEMPERATURE_2M_ANOMALY_LTM1 = "temperature_2m_anomaly_ltm1"
    TEMPERATURE_2M_ANOMALY_LTM2 = "temperature_2m_anomaly_ltm2"
    TEMPERATURE_2M_SOT10 = "temperature_2m_sot10"
    TEMPERATURE_2M_SOT90 = "temperature_2m_sot90"
    TEMPERATURE_2M_EFI = "temperature_2m_efi"
    TEMPERATURE_2M_MEAN = "temperature_2m_mean"
    TEMPERATURE_2M_ANOMALY = "temperature_2m_anomaly"

    # Sealevel Pressure
    PRESSURE_MSL_ANOMALY_GT0 = "pressure_msl_anomaly_gt0"
    PRESSURE_MSL_MEAN = "pressure_msl_mean"
    PRESSURE_MSL_ANOMALY = "pressure_msl_anomaly"

    # Surface Temperature
    SURFACE_TEMPERATURE_ANOMALY_GT0 = "surface_temperature_anomaly_gt0"

    # Precipitation
    PRECIPITATION_ANOMALY_GT0 = "precipitation_anomaly_gt0"
    PRECIPITATION_ANOMALY_GT10 = "precipitation_anomaly_gt10"
    PRECIPITATION_ANOMALY_GT20 = "precipitation_anomaly_gt20"
    PRECIPITATION_EFI = "precipitation_efi"
    PRECIPITATION_SOT90 = "precipitation_sot90"
    PRECIPITATION_MEAN = "precipitation_mean"
    PRECIPITATION_ANOMALY = "precipitation_anomaly"

    # Showers
    SHOWERS_MEAN = "showers_mean"

    # Snow Density
    SNOW_DENSITY_MEAN = "snow_density_mean"
    SNOW_DENSITY_ANOMALY = "snow_density_anomaly"

    # Snow Depth (Water Equivalent)
    SNOW_DEPTH_WATER_EQUIVALENT_MEAN = "snow_depth_water_equivalent_mean"
    SNOW_DEPTH_WATER_EQUIVALENT_ANOMALY = "snow_depth_water_equivalent_anomaly"

    # Total Column Integrated Water Vapour
    TOTAL_COLUMN_INTEGRATED_WATER_VAPOUR_MEAN = (
        "total_column_integrated_water_vapour_mean"
    )
    TOTAL_COLUMN_INTEGRATED_WATER_VAPOUR_ANOMALY = (
        "total_column_integrated_water_vapour_anomaly"
    )

    # Dew Point (2 m)
    DEW_POINT_2M_MEAN = "dew_point_2m_mean"
    DEW_POINT_2M_ANOMALY = "dew_point_2m_anomaly"

    # Sea Surface Temperature
    SEA_SURFACE_TEMPERATURE_MEAN = "sea_surface_temperature_mean"
    SEA_SURFACE_TEMPERATURE_ANOMALY = "sea_surface_temperature_anomaly"

    # Eastward wind component (10 m)
    WIND_U_COMPONENT_10M_MEAN = "wind_u_component_10m_mean"
    WIND_U_COMPONENT_10M_ANOMALY = "wind_u_component_10m_anomaly"

    # Northward wind component (10 m)
    WIND_V_COMPONENT_10M_MEAN = "wind_v_component_10m_mean"
    WIND_V_COMPONENT_10M_ANOMALY = "wind_v_component_10m_anomaly"

    # Eastward wind component (100 m)
    WIND_U_COMPONENT_100M_MEAN = "wind_u_component_100m_mean"
    WIND_U_COMPONENT_100M_ANOMALY = "wind_u_component_100m_anomaly"

    # Northward wind component (100 m)
    WIND_V_COMPONENT_100M_MEAN = "wind_v_component_100m_mean"
    WIND_V_COMPONENT_100M_ANOMALY = "wind_v_component_100m_anomaly"

    # Snowfall Water Equivalent
    SNOWFALL_WATER_EQUIVALENT_MEAN = "snowfall_water_equivalent_mean"
    SNOWFALL_WATER_EQUIVALENT_ANOMALY = "snowfall_water_equivalent_anomaly"

    # Cloud Cover
    CLOUD_COVER_MEAN = "cloud_cover_mean"
    CLOUD_COVER_ANOMALY = "cloud_cover_anomaly"

    # Sunshine Duration
    SUNSHINE_DURATION_MEAN = "sunshine_duration_mean"
    SUNSHINE_DURATION_ANOMALY = "sunshine_duration_anomaly"

    # Soil Temperature (0-7 cm)
    SOIL_TEMPERATURE_0_TO_7CM_MEAN = "soil_temperature_0_to_7cm_mean"
    SOIL_TEMPERATURE_0_TO_7CM_ANOMALY = "soil_temperature_0_to_7cm_anomaly"

    # Temperature (2 m) Max 6h
    TEMPERATURE_MAX6H_2M_MEAN = "temperature_max6h_2m_mean"
    TEMPERATURE_MAX6H_2M_ANOMALY = "temperature_max6h_2m_anomaly"

    # Temperature (2 m) Min 6h
    TEMPERATURE_MIN6H_2M_MEAN = "temperature_min6h_2m_mean"
    TEMPERATURE_MIN6H_2M_ANOMALY = "temperature_min6h_2m_anomaly"


class SeasonalMonthlyParameters(StrEnum):
    """Enum to represent the monthly seasonal parameters available.

    Every variable is a statistic over the ensemble members, per period:
    _mean is the mean, and _anomaly the difference with the model climate
    (forecast minus model climatology). _anomaly_gtN and _anomaly_ltmN are
    the probability in percent that the anomaly is greater than N, or lower
    than minus N. _efi is the Extreme Forecast Index, from -1 to 1, for how
    unusual the forecast is compared to the model climate. _sot10 and _sot90
    are the Shift of Tails of the 10th and 90th percentile, for how extreme
    an event could become.
    """

    # Wind Gusts (10 m)
    WIND_GUSTS_10M_ANOMALY = "wind_gusts_10m_anomaly"

    # Wind Speed (10 m)
    WIND_SPEED_10M_MEAN = "wind_speed_10m_mean"
    WIND_SPEED_10M_ANOMALY = "wind_speed_10m_anomaly"

    # Albedo
    ALBEDO_MEAN = "albedo_mean"
    ALBEDO_ANOMALY = "albedo_anomaly"

    # Cloud Cover Low
    CLOUD_COVER_LOW_MEAN = "cloud_cover_low_mean"
    CLOUD_COVER_LOW_ANOMALY = "cloud_cover_low_anomaly"

    # Showers
    SHOWERS_MEAN = "showers_mean"
    SHOWERS_ANOMALY = "showers_anomaly"

    # Runoff
    RUNOFF_MEAN = "runoff_mean"
    RUNOFF_ANOMALY = "runoff_anomaly"

    # Snow Density
    SNOW_DENSITY_MEAN = "snow_density_mean"
    SNOW_DENSITY_ANOMALY = "snow_density_anomaly"

    # Snow Depth (Water Equivalent)
    SNOW_DEPTH_WATER_EQUIVALENT_MEAN = "snow_depth_water_equivalent_mean"
    SNOW_DEPTH_WATER_EQUIVALENT_ANOMALY = "snow_depth_water_equivalent_anomaly"

    # Total Column Integrated Water Vapour
    TOTAL_COLUMN_INTEGRATED_WATER_VAPOUR_MEAN = (
        "total_column_integrated_water_vapour_mean"
    )
    TOTAL_COLUMN_INTEGRATED_WATER_VAPOUR_ANOMALY = (
        "total_column_integrated_water_vapour_anomaly"
    )

    #  Temperature (2 m)
    TEMPERATURE_2M_MEAN = "temperature_2m_mean"
    TEMPERATURE_2M_ANOMALY = "temperature_2m_anomaly"

    # Dew Point (2 m)
    DEW_POINT_2M_MEAN = "dew_point_2m_mean"
    DEW_POINT_2M_ANOMALY = "dew_point_2m_anomaly"

    # Sealevel Pressure
    PRESSURE_MSL_MEAN = "pressure_msl_mean"
    PRESSURE_MSL_ANOMALY = "pressure_msl_anomaly"

    # Sea Surface Temperature
    SEA_SURFACE_TEMPERATURE_MEAN = "sea_surface_temperature_mean"
    SEA_SURFACE_TEMPERATURE_ANOMALY = "sea_surface_temperature_anomaly"

    # Eastward wind component (10 m)
    WIND_U_COMPONENT_10M_MEAN = "wind_u_component_10m_mean"
    WIND_U_COMPONENT_10M_ANOMALY = "wind_u_component_10m_anomaly"

    # Northward wind component (10 m)
    WIND_V_COMPONENT_10M_MEAN = "wind_v_component_10m_mean"
    WIND_V_COMPONENT_10M_ANOMALY = "wind_v_component_10m_anomaly"

    # Snowfall Water Equivalent
    SNOWFALL_WATER_EQUIVALENT_MEAN = "snowfall_water_equivalent_mean"
    SNOWFALL_WATER_EQUIVALENT_ANOMALY = "snowfall_water_equivalent_anomaly"

    # Precipitation
    PRECIPITATION_MEAN = "precipitation_mean"
    PRECIPITATION_ANOMALY = "precipitation_anomaly"

    # Shortwave Radiation
    SHORTWAVE_RADIATION_MEAN = "shortwave_radiation_mean"
    SHORTWAVE_RADIATION_ANOMALY = "shortwave_radiation_anomaly"

    # Longwave Radiation
    LONGWAVE_RADIATION_MEAN = "longwave_radiation_mean"
    LONGWAVE_RADIATION_ANOMALY = "longwave_radiation_anomaly"

    # Cloud Cover
    CLOUD_COVER_MEAN = "cloud_cover_mean"
    CLOUD_COVER_ANOMALY = "cloud_cover_anomaly"

    # Sunshine Duration
    SUNSHINE_DURATION_MEAN = "sunshine_duration_mean"
    SUNSHINE_DURATION_ANOMALY = "sunshine_duration_anomaly"

    # Soil Temperature (0-7 cm)
    SOIL_TEMPERATURE_0_TO_7CM_MEAN = "soil_temperature_0_to_7cm_mean"
    SOIL_TEMPERATURE_0_TO_7CM_ANOMALY = "soil_temperature_0_to_7cm_anomaly"

    # Soil Temperature (7-28 cm)
    SOIL_TEMPERATURE_7_TO_28CM_MEAN = "soil_temperature_7_to_28cm_mean"
    SOIL_TEMPERATURE_7_TO_28CM_ANOMALY = "soil_temperature_7_to_28cm_anomaly"

    # Soil Temperature (28-100 cm)
    SOIL_TEMPERATURE_28_TO_100CM_MEAN = "soil_temperature_28_to_100cm_mean"
    SOIL_TEMPERATURE_28_TO_100CM_ANOMALY = "soil_temperature_28_to_100cm_anomaly"

    # Soil Temperature (100-255 cm)
    SOIL_TEMPERATURE_100_TO_255CM_MEAN = "soil_temperature_100_to_255cm_mean"
    SOIL_TEMPERATURE_100_TO_255CM_ANOMALY = "soil_temperature_100_to_255cm_anomaly"

    # Soil Moisture (0-7 cm)
    SOIL_MOISTURE_0_TO_7CM_MEAN = "soil_moisture_0_to_7cm_mean"
    SOIL_MOISTURE_0_TO_7CM_ANOMALY = "soil_moisture_0_to_7cm_anomaly"

    # Soil Moisture (7-28 cm)
    SOIL_MOISTURE_7_TO_28CM_MEAN = "soil_moisture_7_to_28cm_mean"
    SOIL_MOISTURE_7_TO_28CM_ANOMALY = "soil_moisture_7_to_28cm_anomaly"

    # Soil Moisture (28-100 cm)
    SOIL_MOISTURE_28_TO_100CM_MEAN = "soil_moisture_28_to_100cm_mean"
    SOIL_MOISTURE_28_TO_100CM_ANOMALY = "soil_moisture_28_to_100cm_anomaly"

    # Soil Moisture (100-255 cm)
    SOIL_MOISTURE_100_TO_255CM_MEAN = "soil_moisture_100_to_255cm_mean"
    SOIL_MOISTURE_100_TO_255CM_ANOMALY = "soil_moisture_100_to_255cm_anomaly"

    # Temperature (2 m) Max 24h
    TEMPERATURE_MAX24H_2M_MEAN = "temperature_max24h_2m_mean"
    TEMPERATURE_MAX24H_2M_ANOMALY = "temperature_max24h_2m_anomaly"

    # Temperature (2 m) Min 24h
    TEMPERATURE_MIN24H_2M_MEAN = "temperature_min24h_2m_mean"
    TEMPERATURE_MIN24H_2M_ANOMALY = "temperature_min24h_2m_anomaly"

    # Sea Ice Cover
    SEA_ICE_COVER_MEAN = "sea_ice_cover_mean"
    SEA_ICE_COVER_ANOMALY = "sea_ice_cover_anomaly"

    # Latent Heat Flux
    LATENT_HEAT_FLUX_MEAN = "latent_heat_flux_mean"
    LATENT_HEAT_FLUX_ANOMALY = "latent_heat_flux_anomaly"

    # Sensible Heat Flux
    SENSIBLE_HEAT_FLUX_MEAN = "sensible_heat_flux_mean"
    SENSIBLE_HEAT_FLUX_ANOMALY = "sensible_heat_flux_anomaly"

    # Evapotranspiration
    EVAPOTRANSPIRATION_MEAN = "evapotranspiration_mean"
    EVAPOTRANSPIRATION_ANOMALY = "evapotranspiration_anomaly"

    # Snowfall
    SNOWFALL_MEAN = "snowfall_mean"
    SNOWFALL_ANOMALY = "snowfall_anomaly"

    # Snow Depth
    SNOW_DEPTH_MEAN = "snow_depth_mean"
    SNOW_DEPTH_ANOMALY = "snow_depth_anomaly"


@dataclass
class WeeklySeasonal(DataClassORJSONMixin):
    """Weekly seasonal data, with the date each week starts."""

    time: list[date]
    cloud_cover_anomaly: list[float | None] | None = None
    cloud_cover_mean: list[float | None] | None = None
    dew_point_2m_anomaly: list[float | None] | None = None
    dew_point_2m_mean: list[float | None] | None = None
    precipitation_anomaly: list[float | None] | None = None
    precipitation_anomaly_gt0: list[float | None] | None = None
    precipitation_anomaly_gt10: list[float | None] | None = None
    precipitation_anomaly_gt20: list[float | None] | None = None
    precipitation_efi: list[float | None] | None = None
    precipitation_mean: list[float | None] | None = None
    precipitation_sot90: list[float | None] | None = None
    pressure_msl_anomaly: list[float | None] | None = None
    pressure_msl_anomaly_gt0: list[float | None] | None = None
    pressure_msl_mean: list[float | None] | None = None
    sea_surface_temperature_anomaly: list[float | None] | None = None
    sea_surface_temperature_mean: list[float | None] | None = None
    showers_mean: list[float | None] | None = None
    snow_density_anomaly: list[float | None] | None = None
    snow_density_mean: list[float | None] | None = None
    snow_depth_anomaly: list[float | None] | None = None
    snow_depth_mean: list[float | None] | None = None
    snow_depth_water_equivalent_anomaly: list[float | None] | None = None
    snow_depth_water_equivalent_mean: list[float | None] | None = None
    snowfall_anomaly: list[float | None] | None = None
    snowfall_mean: list[float | None] | None = None
    snowfall_water_equivalent_anomaly: list[float | None] | None = None
    snowfall_water_equivalent_mean: list[float | None] | None = None
    soil_temperature_0_to_7cm_anomaly: list[float | None] | None = None
    soil_temperature_0_to_7cm_mean: list[float | None] | None = None
    sunshine_duration_anomaly: list[float | None] | None = None
    sunshine_duration_mean: list[float | None] | None = None
    surface_temperature_anomaly_gt0: list[float | None] | None = None
    temperature_2m_anomaly: list[float | None] | None = None
    temperature_2m_anomaly_gt0: list[float | None] | None = None
    temperature_2m_anomaly_gt1: list[float | None] | None = None
    temperature_2m_anomaly_gt2: list[float | None] | None = None
    temperature_2m_anomaly_ltm1: list[float | None] | None = None
    temperature_2m_anomaly_ltm2: list[float | None] | None = None
    temperature_2m_efi: list[float | None] | None = None
    temperature_2m_mean: list[float | None] | None = None
    temperature_2m_sot10: list[float | None] | None = None
    temperature_2m_sot90: list[float | None] | None = None
    temperature_max6h_2m_anomaly: list[float | None] | None = None
    temperature_max6h_2m_mean: list[float | None] | None = None
    temperature_min6h_2m_anomaly: list[float | None] | None = None
    temperature_min6h_2m_mean: list[float | None] | None = None
    total_column_integrated_water_vapour_anomaly: list[float | None] | None = None
    total_column_integrated_water_vapour_mean: list[float | None] | None = None
    wind_direction_100m_anomaly: list[float | None] | None = None
    wind_direction_100m_mean: list[float | None] | None = None
    wind_direction_10m_anomaly: list[float | None] | None = None
    wind_direction_10m_mean: list[float | None] | None = None
    wind_speed_100m_anomaly: list[float | None] | None = None
    wind_speed_100m_mean: list[float | None] | None = None
    wind_speed_10m_anomaly: list[float | None] | None = None
    wind_speed_10m_mean: list[float | None] | None = None
    wind_u_component_100m_anomaly: list[float | None] | None = None
    wind_u_component_100m_mean: list[float | None] | None = None
    wind_u_component_10m_anomaly: list[float | None] | None = None
    wind_u_component_10m_mean: list[float | None] | None = None
    wind_v_component_100m_anomaly: list[float | None] | None = None
    wind_v_component_100m_mean: list[float | None] | None = None
    wind_v_component_10m_anomaly: list[float | None] | None = None
    wind_v_component_10m_mean: list[float | None] | None = None


@dataclass
class WeeklySeasonalUnits(DataClassORJSONMixin):
    """Weekly seasonal data units."""

    time: TimeFormat | None = None
    cloud_cover_anomaly: str | None = None
    cloud_cover_mean: str | None = None
    dew_point_2m_anomaly: str | None = None
    dew_point_2m_mean: str | None = None
    precipitation_anomaly: str | None = None
    precipitation_anomaly_gt0: str | None = None
    precipitation_anomaly_gt10: str | None = None
    precipitation_anomaly_gt20: str | None = None
    precipitation_efi: str | None = None
    precipitation_mean: str | None = None
    precipitation_sot90: str | None = None
    pressure_msl_anomaly: str | None = None
    pressure_msl_anomaly_gt0: str | None = None
    pressure_msl_mean: str | None = None
    sea_surface_temperature_anomaly: str | None = None
    sea_surface_temperature_mean: str | None = None
    showers_mean: str | None = None
    snow_density_anomaly: str | None = None
    snow_density_mean: str | None = None
    snow_depth_anomaly: str | None = None
    snow_depth_mean: str | None = None
    snow_depth_water_equivalent_anomaly: str | None = None
    snow_depth_water_equivalent_mean: str | None = None
    snowfall_anomaly: str | None = None
    snowfall_mean: str | None = None
    snowfall_water_equivalent_anomaly: str | None = None
    snowfall_water_equivalent_mean: str | None = None
    soil_temperature_0_to_7cm_anomaly: str | None = None
    soil_temperature_0_to_7cm_mean: str | None = None
    sunshine_duration_anomaly: str | None = None
    sunshine_duration_mean: str | None = None
    surface_temperature_anomaly_gt0: str | None = None
    temperature_2m_anomaly: str | None = None
    temperature_2m_anomaly_gt0: str | None = None
    temperature_2m_anomaly_gt1: str | None = None
    temperature_2m_anomaly_gt2: str | None = None
    temperature_2m_anomaly_ltm1: str | None = None
    temperature_2m_anomaly_ltm2: str | None = None
    temperature_2m_efi: str | None = None
    temperature_2m_mean: str | None = None
    temperature_2m_sot10: str | None = None
    temperature_2m_sot90: str | None = None
    temperature_max6h_2m_anomaly: str | None = None
    temperature_max6h_2m_mean: str | None = None
    temperature_min6h_2m_anomaly: str | None = None
    temperature_min6h_2m_mean: str | None = None
    total_column_integrated_water_vapour_anomaly: str | None = None
    total_column_integrated_water_vapour_mean: str | None = None
    wind_direction_100m_anomaly: str | None = None
    wind_direction_100m_mean: str | None = None
    wind_direction_10m_anomaly: str | None = None
    wind_direction_10m_mean: str | None = None
    wind_speed_100m_anomaly: str | None = None
    wind_speed_100m_mean: str | None = None
    wind_speed_10m_anomaly: str | None = None
    wind_speed_10m_mean: str | None = None
    wind_u_component_100m_anomaly: str | None = None
    wind_u_component_100m_mean: str | None = None
    wind_u_component_10m_anomaly: str | None = None
    wind_u_component_10m_mean: str | None = None
    wind_v_component_100m_anomaly: str | None = None
    wind_v_component_100m_mean: str | None = None
    wind_v_component_10m_anomaly: str | None = None
    wind_v_component_10m_mean: str | None = None


@dataclass
class MonthlySeasonal(DataClassORJSONMixin):
    """Monthly seasonal data, with the date each month starts."""

    time: list[date]
    albedo_anomaly: list[float | None] | None = None
    albedo_mean: list[float | None] | None = None
    cloud_cover_anomaly: list[float | None] | None = None
    cloud_cover_low_anomaly: list[float | None] | None = None
    cloud_cover_low_mean: list[float | None] | None = None
    cloud_cover_mean: list[float | None] | None = None
    dew_point_2m_anomaly: list[float | None] | None = None
    dew_point_2m_mean: list[float | None] | None = None
    evapotranspiration_anomaly: list[float | None] | None = None
    evapotranspiration_mean: list[float | None] | None = None
    latent_heat_flux_anomaly: list[float | None] | None = None
    latent_heat_flux_mean: list[float | None] | None = None
    longwave_radiation_anomaly: list[float | None] | None = None
    longwave_radiation_mean: list[float | None] | None = None
    precipitation_anomaly: list[float | None] | None = None
    precipitation_mean: list[float | None] | None = None
    pressure_msl_anomaly: list[float | None] | None = None
    pressure_msl_mean: list[float | None] | None = None
    runoff_anomaly: list[float | None] | None = None
    runoff_mean: list[float | None] | None = None
    sea_ice_cover_anomaly: list[float | None] | None = None
    sea_ice_cover_mean: list[float | None] | None = None
    sea_surface_temperature_anomaly: list[float | None] | None = None
    sea_surface_temperature_mean: list[float | None] | None = None
    sensible_heat_flux_anomaly: list[float | None] | None = None
    sensible_heat_flux_mean: list[float | None] | None = None
    shortwave_radiation_anomaly: list[float | None] | None = None
    shortwave_radiation_mean: list[float | None] | None = None
    showers_anomaly: list[float | None] | None = None
    showers_mean: list[float | None] | None = None
    snow_density_anomaly: list[float | None] | None = None
    snow_density_mean: list[float | None] | None = None
    snow_depth_anomaly: list[float | None] | None = None
    snow_depth_mean: list[float | None] | None = None
    snow_depth_water_equivalent_anomaly: list[float | None] | None = None
    snow_depth_water_equivalent_mean: list[float | None] | None = None
    snowfall_anomaly: list[float | None] | None = None
    snowfall_mean: list[float | None] | None = None
    snowfall_water_equivalent_anomaly: list[float | None] | None = None
    snowfall_water_equivalent_mean: list[float | None] | None = None
    soil_moisture_0_to_7cm_anomaly: list[float | None] | None = None
    soil_moisture_0_to_7cm_mean: list[float | None] | None = None
    soil_moisture_100_to_255cm_anomaly: list[float | None] | None = None
    soil_moisture_100_to_255cm_mean: list[float | None] | None = None
    soil_moisture_28_to_100cm_anomaly: list[float | None] | None = None
    soil_moisture_28_to_100cm_mean: list[float | None] | None = None
    soil_moisture_7_to_28cm_anomaly: list[float | None] | None = None
    soil_moisture_7_to_28cm_mean: list[float | None] | None = None
    soil_temperature_0_to_7cm_anomaly: list[float | None] | None = None
    soil_temperature_0_to_7cm_mean: list[float | None] | None = None
    soil_temperature_100_to_255cm_anomaly: list[float | None] | None = None
    soil_temperature_100_to_255cm_mean: list[float | None] | None = None
    soil_temperature_28_to_100cm_anomaly: list[float | None] | None = None
    soil_temperature_28_to_100cm_mean: list[float | None] | None = None
    soil_temperature_7_to_28cm_anomaly: list[float | None] | None = None
    soil_temperature_7_to_28cm_mean: list[float | None] | None = None
    sunshine_duration_anomaly: list[float | None] | None = None
    sunshine_duration_mean: list[float | None] | None = None
    temperature_2m_anomaly: list[float | None] | None = None
    temperature_2m_mean: list[float | None] | None = None
    temperature_max24h_2m_anomaly: list[float | None] | None = None
    temperature_max24h_2m_mean: list[float | None] | None = None
    temperature_min24h_2m_anomaly: list[float | None] | None = None
    temperature_min24h_2m_mean: list[float | None] | None = None
    total_column_integrated_water_vapour_anomaly: list[float | None] | None = None
    total_column_integrated_water_vapour_mean: list[float | None] | None = None
    wind_gusts_10m_anomaly: list[float | None] | None = None
    wind_speed_10m_anomaly: list[float | None] | None = None
    wind_speed_10m_mean: list[float | None] | None = None
    wind_u_component_10m_anomaly: list[float | None] | None = None
    wind_u_component_10m_mean: list[float | None] | None = None
    wind_v_component_10m_anomaly: list[float | None] | None = None
    wind_v_component_10m_mean: list[float | None] | None = None


@dataclass
class MonthlySeasonalUnits(DataClassORJSONMixin):
    """Monthly seasonal data units."""

    time: TimeFormat | None = None
    albedo_anomaly: str | None = None
    albedo_mean: str | None = None
    cloud_cover_anomaly: str | None = None
    cloud_cover_low_anomaly: str | None = None
    cloud_cover_low_mean: str | None = None
    cloud_cover_mean: str | None = None
    dew_point_2m_anomaly: str | None = None
    dew_point_2m_mean: str | None = None
    evapotranspiration_anomaly: str | None = None
    evapotranspiration_mean: str | None = None
    latent_heat_flux_anomaly: str | None = None
    latent_heat_flux_mean: str | None = None
    longwave_radiation_anomaly: str | None = None
    longwave_radiation_mean: str | None = None
    precipitation_anomaly: str | None = None
    precipitation_mean: str | None = None
    pressure_msl_anomaly: str | None = None
    pressure_msl_mean: str | None = None
    runoff_anomaly: str | None = None
    runoff_mean: str | None = None
    sea_ice_cover_anomaly: str | None = None
    sea_ice_cover_mean: str | None = None
    sea_surface_temperature_anomaly: str | None = None
    sea_surface_temperature_mean: str | None = None
    sensible_heat_flux_anomaly: str | None = None
    sensible_heat_flux_mean: str | None = None
    shortwave_radiation_anomaly: str | None = None
    shortwave_radiation_mean: str | None = None
    showers_anomaly: str | None = None
    showers_mean: str | None = None
    snow_density_anomaly: str | None = None
    snow_density_mean: str | None = None
    snow_depth_anomaly: str | None = None
    snow_depth_mean: str | None = None
    snow_depth_water_equivalent_anomaly: str | None = None
    snow_depth_water_equivalent_mean: str | None = None
    snowfall_anomaly: str | None = None
    snowfall_mean: str | None = None
    snowfall_water_equivalent_anomaly: str | None = None
    snowfall_water_equivalent_mean: str | None = None
    soil_moisture_0_to_7cm_anomaly: str | None = None
    soil_moisture_0_to_7cm_mean: str | None = None
    soil_moisture_100_to_255cm_anomaly: str | None = None
    soil_moisture_100_to_255cm_mean: str | None = None
    soil_moisture_28_to_100cm_anomaly: str | None = None
    soil_moisture_28_to_100cm_mean: str | None = None
    soil_moisture_7_to_28cm_anomaly: str | None = None
    soil_moisture_7_to_28cm_mean: str | None = None
    soil_temperature_0_to_7cm_anomaly: str | None = None
    soil_temperature_0_to_7cm_mean: str | None = None
    soil_temperature_100_to_255cm_anomaly: str | None = None
    soil_temperature_100_to_255cm_mean: str | None = None
    soil_temperature_28_to_100cm_anomaly: str | None = None
    soil_temperature_28_to_100cm_mean: str | None = None
    soil_temperature_7_to_28cm_anomaly: str | None = None
    soil_temperature_7_to_28cm_mean: str | None = None
    sunshine_duration_anomaly: str | None = None
    sunshine_duration_mean: str | None = None
    temperature_2m_anomaly: str | None = None
    temperature_2m_mean: str | None = None
    temperature_max24h_2m_anomaly: str | None = None
    temperature_max24h_2m_mean: str | None = None
    temperature_min24h_2m_anomaly: str | None = None
    temperature_min24h_2m_mean: str | None = None
    total_column_integrated_water_vapour_anomaly: str | None = None
    total_column_integrated_water_vapour_mean: str | None = None
    wind_gusts_10m_anomaly: str | None = None
    wind_speed_10m_anomaly: str | None = None
    wind_speed_10m_mean: str | None = None
    wind_u_component_10m_anomaly: str | None = None
    wind_u_component_10m_mean: str | None = None
    wind_v_component_10m_anomaly: str | None = None
    wind_v_component_10m_mean: str | None = None


@dataclass
class Seasonal(DataClassORJSONMixin):
    """Seasonal forecast."""

    elevation: float
    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    latitude: float
    longitude: float
    timezone: str
    timezone_abbreviation: str
    utc_offset_seconds: int

    # The hourly data has a resolution of 6 hours; it and the daily data
    # have the ensemble members, the weekly and monthly data are statistics
    hourly_units: HourlyForecastUnits | None = None
    hourly: HourlyForecast | None = None
    daily_units: DailyForecastUnits | None = None
    daily: DailyForecast | None = None
    weekly_units: WeeklySeasonalUnits | None = None
    weekly: WeeklySeasonal | None = None
    monthly_units: MonthlySeasonalUnits | None = None
    monthly: MonthlySeasonal | None = None

    # Only set when multiple models were requested, keyed by the model name
    models: dict[str, Seasonal] | None = None
