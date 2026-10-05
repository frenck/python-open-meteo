"""Models for the Open-Meteo weather forecast APIs."""

# pylint: disable=too-many-instance-attributes

import dataclasses
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from ._split import (
    _drop_suffixed,
    _split_members,
    _split_previous_days,
    _split_spread,
)
from .common import TimeFormat


class ForecastSection(StrEnum):
    """Enum to represent the forecast sections levels can be requested for."""

    CURRENT = "current"
    MINUTELY_15 = "minutely_15"
    HOURLY = "hourly"


class HourlyParameters(StrEnum):
    """Enum to represent the hourly parameters available.

    Every hourly parameter can be requested as a current condition as well.
    """

    # Density of the air at 2 meters above ground
    AIR_DENSITY_2M = "air_density_2m"

    # Surface albedo, the share of sunlight the surface reflects
    ALBEDO = "albedo"

    # Apparent (feels like) temperature at 2 meters above ground, combining
    # wind chill, humidity, and solar radiation
    APPARENT_TEMPERATURE = "apparent_temperature"

    # Height of the planetary boundary layer
    BOUNDARY_LAYER_HEIGHT = "boundary_layer_height"

    # Convective available potential energy
    CAPE = "cape"

    # Base and top height of clouds above ground
    CLOUD_BASE = "cloud_base"
    CLOUD_TOP = "cloud_top"

    # Total cloud cover as an area fraction
    CLOUD_COVER = "cloud_cover"

    # Cloud cover at 2 meters above ground, like fog, as an area fraction
    CLOUD_COVER_2M = "cloud_cover_2m"

    # High level clouds from 8 km altitude
    CLOUD_COVER_HIGH = "cloud_cover_high"

    # Low level clouds and fog up to 3 km altitude
    CLOUD_COVER_LOW = "cloud_cover_low"

    # Mid level clouds from 3 to 8 km altitude
    CLOUD_COVER_MID = "cloud_cover_mid"

    # Base and top height of convective clouds
    CONVECTIVE_CLOUD_BASE = "convective_cloud_base"
    CONVECTIVE_CLOUD_TOP = "convective_cloud_top"

    # Convective inhibition, the energy that prevents convection from starting
    CONVECTIVE_INHIBITION = "convective_inhibition"

    # Dew point temperature at 2 meters above ground
    DEW_POINT_2M = "dew_point_2m"

    # Diffuse solar radiation as average of the preceding hour
    DIFFUSE_RADIATION = "diffuse_radiation"

    # Direct solar radiation as average of the preceding hour on the horizontal
    # plane and the normal plane (perpendicular to the sun)
    DIRECT_NORMAL_IRRADIANCE = "direct_normal_irradiance"
    DIRECT_RADIATION = "direct_radiation"

    # Reference evapotranspiration of a well watered grass field (FAO-56)
    ET0_FAO_EVAPOTRANSPIRATION = "et0_fao_evapotranspiration"

    # Sum of evapotranspiration of the preceding hour from land surface and
    # plants
    EVAPOTRANSPIRATION = "evapotranspiration"

    # Altitude above sea level of the 0°C level
    FREEZING_LEVEL_HEIGHT = "freezing_level_height"

    # Probability of a specific type of precipitation or weather
    FREEZING_RAIN_PROBABILITY = "freezing_rain_probability"
    ICE_PELLETS_PROBABILITY = "ice_pellets_probability"
    RAIN_PROBABILITY = "rain_probability"
    SNOWFALL_PROBABILITY = "snowfall_probability"
    THUNDERSTORM_PROBABILITY = "thunderstorm_probability"

    # Growing degree days with a base of 0°C and a limit of 50°C
    GROWING_DEGREE_DAYS_BASE_0_LIMIT_50 = "growing_degree_days_base_0_limit_50"

    # Hail of the preceding hour
    HAIL = "hail"

    # Total solar radiation on a tilted panel, as average of the preceding hour;
    # use the tilt and azimuth parameters to describe the panel
    GLOBAL_TILTED_IRRADIANCE = "global_tilted_irradiance"

    # Whether it is day (1) or night (0) at the location
    IS_DAY = "is_day"

    # K index and lifted index, indicators of thunderstorm potential
    K_INDEX = "k_index"
    LIFTED_INDEX = "lifted_index"

    # Heat exchanged between the surface and the air, by evaporation
    # (latent) and by conduction (sensible)
    LATENT_HEAT_FLUX = "latent_heat_flux"
    SENSIBLE_HEAT_FLUX = "sensible_heat_flux"

    # Probability of leaf wetness
    LEAF_WETNESS_PROBABILITY = "leaf_wetness_probability"

    # Lightning density and lightning potential index
    LIGHTNING_DENSITY = "lightning_density"
    LIGHTNING_POTENTIAL = "lightning_potential"

    # Air density at 8 meters above ground
    MASS_DENSITY_8M = "mass_density_8m"

    # Ocean current velocity and direction
    OCEAN_CURRENT_DIRECTION = "ocean_current_direction"
    OCEAN_CURRENT_VELOCITY = "ocean_current_velocity"

    # Evapotranspiration as it would be with unlimited water
    POTENTIAL_EVAPOTRANSPIRATION = "potential_evapotranspiration"

    # Total precipitation (rain, showers, snow) sum of the preceding hour
    PRECIPITATION = "precipitation"

    # Probability of precipitation (rain, showers, snow) for the next hour
    PRECIPITATION_PROBABILITY = "precipitation_probability"

    # Type of precipitation, as a numeric code
    PRECIPITATION_TYPE = "precipitation_type"

    # Atmospheric air pressure reduced to sea level (hPa)
    PRESSURE_MSL = "pressure_msl"

    # Rain from large scale weather systems, and showers from convective
    # precipitation, as sum of the preceding hour
    RAIN = "rain"
    SHOWERS = "showers"

    # Relative humidity at 2 meters above ground
    RELATIVE_HUMIDITY_2M = "relative_humidity_2m"

    # Surface roughness length
    ROUGHNESS_LENGTH = "roughness_length"

    # Surface water runoff of the preceding hour
    RUNOFF = "runoff"

    # Sea ice thickness, sea surface temperature, and sea level height
    SEA_ICE_THICKNESS = "sea_ice_thickness"
    SEA_LEVEL_HEIGHT_MSL = "sea_level_height_msl"
    SEA_SURFACE_TEMPERATURE = "sea_surface_temperature"

    # Salinity of the sea water at the surface
    SEA_WATER_SALINITY = "sea_water_salinity"

    # Shortwave solar radiation as average of the preceding hour
    SHORTWAVE_RADIATION = "shortwave_radiation"

    # Shortwave solar radiation as it would be without clouds; only some
    # models have this, like the satellite models
    SHORTWAVE_RADIATION_CLEAR_SKY = "shortwave_radiation_clear_sky"

    # Shortwave solar radiation as it would be without clouds, at that moment
    SHORTWAVE_RADIATION_CLEAR_SKY_INSTANT = "shortwave_radiation_clear_sky_instant"

    # Snow depth on the ground, and the snow height
    SNOW_DEPTH = "snow_depth"
    SNOW_HEIGHT = "snow_height"

    # Snow depth on the ground as water equivalent
    SNOW_DEPTH_WATER_EQUIVALENT = "snow_depth_water_equivalent"

    # Snowfall amount of the preceding hour, in centimeters and as water
    # equivalent
    SNOWFALL = "snowfall"
    SNOWFALL_WATER_EQUIVALENT = "snowfall_water_equivalent"

    # Density of the snow cover
    SNOW_DENSITY = "snow_density"

    # Height of the snowfall level
    SNOWFALL_HEIGHT = "snowfall_height"

    # Average soil water content as volumetric mixing ratio, at fixed depths or
    # averaged over layers. Which depths are available depends on the weather
    # model.
    SOIL_MOISTURE_0_TO_1CM = "soil_moisture_0_to_1cm"
    SOIL_MOISTURE_0_TO_7CM = "soil_moisture_0_to_7cm"
    SOIL_MOISTURE_0_TO_10CM = "soil_moisture_0_to_10cm"
    SOIL_MOISTURE_0_TO_100CM = "soil_moisture_0_to_100cm"
    SOIL_MOISTURE_1_TO_3CM = "soil_moisture_1_to_3cm"
    SOIL_MOISTURE_3_TO_9CM = "soil_moisture_3_to_9cm"
    SOIL_MOISTURE_7_TO_28CM = "soil_moisture_7_to_28cm"
    SOIL_MOISTURE_9_TO_27CM = "soil_moisture_9_to_27cm"
    SOIL_MOISTURE_10_TO_35CM = "soil_moisture_10_to_35cm"
    SOIL_MOISTURE_10_TO_40CM = "soil_moisture_10_to_40cm"
    SOIL_MOISTURE_27_TO_81CM = "soil_moisture_27_to_81cm"
    SOIL_MOISTURE_28_TO_100CM = "soil_moisture_28_to_100cm"
    SOIL_MOISTURE_35_TO_100CM = "soil_moisture_35_to_100cm"
    SOIL_MOISTURE_40_TO_100CM = "soil_moisture_40_to_100cm"
    SOIL_MOISTURE_81_TO_243CM = "soil_moisture_81_to_243cm"
    SOIL_MOISTURE_100_TO_200CM = "soil_moisture_100_to_200cm"
    SOIL_MOISTURE_100_TO_255CM = "soil_moisture_100_to_255cm"
    SOIL_MOISTURE_100_TO_300CM = "soil_moisture_100_to_300cm"
    SOIL_MOISTURE_243_TO_729CM = "soil_moisture_243_to_729cm"
    SOIL_MOISTURE_729_TO_2187CM = "soil_moisture_729_to_2187cm"

    # Soil moisture index, averaged over layers, from 0 (wilting point) to 1
    # (field capacity) and beyond when the soil is saturated
    SOIL_MOISTURE_INDEX_0_TO_7CM = "soil_moisture_index_0_to_7cm"
    SOIL_MOISTURE_INDEX_0_TO_100CM = "soil_moisture_index_0_to_100cm"
    SOIL_MOISTURE_INDEX_7_TO_28CM = "soil_moisture_index_7_to_28cm"
    SOIL_MOISTURE_INDEX_28_TO_100CM = "soil_moisture_index_28_to_100cm"

    # Soil moisture index from 100 to 255 cm below ground, from 0 (wilting
    # point) to 1 (field capacity)
    SOIL_MOISTURE_INDEX_100_TO_255CM = "soil_moisture_index_100_to_255cm"

    # Temperature in the soil, at fixed depths or averaged over layers. 0 cm is
    # the surface temperature on land or water surface temperature on water.
    # Which depths are available depends on the weather model.
    SOIL_TEMPERATURE_0CM = "soil_temperature_0cm"
    SOIL_TEMPERATURE_6CM = "soil_temperature_6cm"
    SOIL_TEMPERATURE_18CM = "soil_temperature_18cm"
    SOIL_TEMPERATURE_54CM = "soil_temperature_54cm"
    SOIL_TEMPERATURE_162CM = "soil_temperature_162cm"
    SOIL_TEMPERATURE_486CM = "soil_temperature_486cm"
    SOIL_TEMPERATURE_1458CM = "soil_temperature_1458cm"
    SOIL_TEMPERATURE_0_TO_7CM = "soil_temperature_0_to_7cm"
    SOIL_TEMPERATURE_0_TO_10CM = "soil_temperature_0_to_10cm"
    SOIL_TEMPERATURE_0_TO_100CM = "soil_temperature_0_to_100cm"
    SOIL_TEMPERATURE_7_TO_28CM = "soil_temperature_7_to_28cm"
    SOIL_TEMPERATURE_10_TO_35CM = "soil_temperature_10_to_35cm"
    SOIL_TEMPERATURE_10_TO_40CM = "soil_temperature_10_to_40cm"
    SOIL_TEMPERATURE_28_TO_100CM = "soil_temperature_28_to_100cm"
    SOIL_TEMPERATURE_35_TO_100CM = "soil_temperature_35_to_100cm"
    SOIL_TEMPERATURE_40_TO_100CM = "soil_temperature_40_to_100cm"
    SOIL_TEMPERATURE_100_TO_200CM = "soil_temperature_100_to_200cm"
    SOIL_TEMPERATURE_100_TO_255CM = "soil_temperature_100_to_255cm"
    SOIL_TEMPERATURE_100_TO_300CM = "soil_temperature_100_to_300cm"

    # Sunshine duration of the preceding hour, in seconds
    SUNSHINE_DURATION = "sunshine_duration"

    # Atmospheric air pressure at the surface (hPa)
    SURFACE_PRESSURE = "surface_pressure"

    # Temperature of the land or water surface
    SURFACE_TEMPERATURE = "surface_temperature"

    # Air temperature at 2 meters above ground
    TEMPERATURE_2M = "temperature_2m"

    # Minimum and maximum air temperature at 2 meters above ground
    TEMPERATURE_2M_MAX = "temperature_2m_max"
    TEMPERATURE_2M_MIN = "temperature_2m_min"

    # Air temperature at 20 to 200 meters above ground
    TEMPERATURE_20M = "temperature_20m"
    TEMPERATURE_40M = "temperature_40m"
    TEMPERATURE_50M = "temperature_50m"
    TEMPERATURE_80M = "temperature_80m"
    TEMPERATURE_100M = "temperature_100m"
    TEMPERATURE_120M = "temperature_120m"
    TEMPERATURE_150M = "temperature_150m"
    TEMPERATURE_180M = "temperature_180m"
    TEMPERATURE_200M = "temperature_200m"

    # Solar radiation at the top of the atmosphere
    TERRESTRIAL_RADIATION = "terrestrial_radiation"

    # Total amount of water vapour in the entire air column
    TOTAL_COLUMN_INTEGRATED_WATER_VAPOUR = "total_column_integrated_water_vapour"

    # Total amount of water in a column of air, as vapour, liquid, and ice
    TOTAL_COLUMN_WATER = "total_column_water"

    # Maximum updraft speed
    UPDRAFT = "updraft"

    # UV index, with and without taking clouds into account
    UV_INDEX = "uv_index"
    UV_INDEX_CLEAR_SKY = "uv_index_clear_sky"

    # Vapour Pressure Deficit (VPD) in kilopascal (kPa). For high VPD (>1.6),
    # water transpiration of plants increases. For low VPD (<0.4),
    # transpiration decreases.
    VAPOUR_PRESSURE_DEFICIT = "vapour_pressure_deficit"

    # Visibility in meters
    VISIBILITY = "visibility"

    # Significant height, mean direction, mean period, and peak period of all
    # waves combined; only some models have these, like the seasonal models
    WAVE_DIRECTION = "wave_direction"
    WAVE_HEIGHT = "wave_height"
    WAVE_PEAK_PERIOD = "wave_peak_period"
    WAVE_PERIOD = "wave_period"

    # Weather condition as a WMO numeric weather code.
    WEATHER_CODE = "weather_code"

    # Wet bulb temperature at 2 meters above ground
    WET_BULB_TEMPERATURE_2M = "wet_bulb_temperature_2m"

    # Wind direction at 10 to 200 meters above ground
    WIND_DIRECTION_10M = "wind_direction_10m"
    WIND_DIRECTION_20M = "wind_direction_20m"
    WIND_DIRECTION_30M = "wind_direction_30m"
    WIND_DIRECTION_40M = "wind_direction_40m"
    WIND_DIRECTION_50M = "wind_direction_50m"
    WIND_DIRECTION_70M = "wind_direction_70m"
    WIND_DIRECTION_80M = "wind_direction_80m"
    WIND_DIRECTION_100M = "wind_direction_100m"
    WIND_DIRECTION_120M = "wind_direction_120m"
    WIND_DIRECTION_140M = "wind_direction_140m"
    WIND_DIRECTION_150M = "wind_direction_150m"
    WIND_DIRECTION_160M = "wind_direction_160m"
    WIND_DIRECTION_180M = "wind_direction_180m"
    WIND_DIRECTION_200M = "wind_direction_200m"

    # Gusts at 10 meters above ground as a maximum of the preceding hour
    WIND_GUSTS_10M = "wind_gusts_10m"

    # Wind speed at 10 to 200 meters above ground. Wind speed on 10 meters is
    # the standard level.
    WIND_SPEED_10M = "wind_speed_10m"
    WIND_SPEED_20M = "wind_speed_20m"
    WIND_SPEED_30M = "wind_speed_30m"
    WIND_SPEED_40M = "wind_speed_40m"
    WIND_SPEED_50M = "wind_speed_50m"
    WIND_SPEED_70M = "wind_speed_70m"
    WIND_SPEED_80M = "wind_speed_80m"
    WIND_SPEED_100M = "wind_speed_100m"
    WIND_SPEED_120M = "wind_speed_120m"
    WIND_SPEED_140M = "wind_speed_140m"
    WIND_SPEED_150M = "wind_speed_150m"
    WIND_SPEED_160M = "wind_speed_160m"
    WIND_SPEED_180M = "wind_speed_180m"
    WIND_SPEED_200M = "wind_speed_200m"

    # The same radiation variables as above, but as the instant value at the
    # given time instead of the average of the preceding hour
    DIFFUSE_RADIATION_INSTANT = "diffuse_radiation_instant"
    DIRECT_NORMAL_IRRADIANCE_INSTANT = "direct_normal_irradiance_instant"
    DIRECT_RADIATION_INSTANT = "direct_radiation_instant"
    GLOBAL_TILTED_IRRADIANCE_INSTANT = "global_tilted_irradiance_instant"
    SHORTWAVE_RADIATION_INSTANT = "shortwave_radiation_instant"
    TERRESTRIAL_RADIATION_INSTANT = "terrestrial_radiation_instant"


class DailyParameters(StrEnum):
    """Enum to represent the daily parameters available."""

    # Maximum, mean, and minimum daily apparent temperature at 2 meters above
    # ground
    APPARENT_TEMPERATURE_MAX = "apparent_temperature_max"
    APPARENT_TEMPERATURE_MEAN = "apparent_temperature_mean"
    APPARENT_TEMPERATURE_MIN = "apparent_temperature_min"

    # Maximum, mean, and minimum convective available potential energy
    CAPE_MAX = "cape_max"
    CAPE_MEAN = "cape_mean"
    CAPE_MIN = "cape_min"

    # Maximum, mean, and minimum total cloud cover as an area fraction
    CLOUD_COVER_MAX = "cloud_cover_max"
    CLOUD_COVER_MEAN = "cloud_cover_mean"
    CLOUD_COVER_MIN = "cloud_cover_min"

    # Number of seconds of daylight per day
    DAYLIGHT_DURATION = "daylight_duration"

    # Maximum, mean, and minimum dew point temperature at 2 meters above ground
    DEW_POINT_2M_MAX = "dew_point_2m_max"
    DEW_POINT_2M_MEAN = "dew_point_2m_mean"
    DEW_POINT_2M_MIN = "dew_point_2m_min"

    # Daily sum of reference evapotranspiration of a well watered grass field
    ET0_FAO_EVAPOTRANSPIRATION = "et0_fao_evapotranspiration"
    ET0_FAO_EVAPOTRANSPIRATION_SUM = "et0_fao_evapotranspiration_sum"

    # Growing degree days with a base of 0°C and a limit of 50°C
    GROWING_DEGREE_DAYS_BASE_0_LIMIT_50 = "growing_degree_days_base_0_limit_50"

    # Mean probability of leaf wetness
    LEAF_WETNESS_PROBABILITY_MEAN = "leaf_wetness_probability_mean"

    # Moon phase as a fraction, and moon rise and set times
    MOON_PHASE = "moon_phase"
    MOONRISE = "moonrise"
    MOONSET = "moonset"

    # The number of hours with rain
    PRECIPITATION_HOURS = "precipitation_hours"

    # Maximum, mean, and minimum probability of precipitation for the day
    PRECIPITATION_PROBABILITY_MAX = "precipitation_probability_max"
    PRECIPITATION_PROBABILITY_MEAN = "precipitation_probability_mean"
    PRECIPITATION_PROBABILITY_MIN = "precipitation_probability_min"

    # Sum of daily precipitation, and the parts that fell as rain, showers, and
    # snow
    PRECIPITATION_SUM = "precipitation_sum"
    RAIN_SUM = "rain_sum"
    SHOWERS_SUM = "showers_sum"
    SNOWFALL_SUM = "snowfall_sum"
    SNOWFALL_WATER_EQUIVALENT_SUM = "snowfall_water_equivalent_sum"

    # Maximum and minimum snow depth of the day
    SNOW_DEPTH_MAX = "snow_depth_max"
    SNOW_DEPTH_MIN = "snow_depth_min"

    # Maximum, mean, and minimum air pressure reduced to sea level (hPa)
    PRESSURE_MSL_MAX = "pressure_msl_max"
    PRESSURE_MSL_MEAN = "pressure_msl_mean"
    PRESSURE_MSL_MIN = "pressure_msl_min"

    # Maximum, mean, and minimum relative humidity at 2 meters above ground
    RELATIVE_HUMIDITY_2M_MAX = "relative_humidity_2m_max"
    RELATIVE_HUMIDITY_2M_MEAN = "relative_humidity_2m_mean"
    RELATIVE_HUMIDITY_2M_MIN = "relative_humidity_2m_min"

    # The sum of solar radiation on a given day in Mega Joules
    SHORTWAVE_RADIATION_SUM = "shortwave_radiation_sum"

    # Maximum, mean, and minimum sea surface temperature, and mean snow depth
    SEA_SURFACE_TEMPERATURE_MAX = "sea_surface_temperature_max"
    SEA_SURFACE_TEMPERATURE_MEAN = "sea_surface_temperature_mean"
    SEA_SURFACE_TEMPERATURE_MIN = "sea_surface_temperature_min"
    SNOW_DEPTH_MEAN = "snow_depth_mean"

    # Mean soil moisture, and the soil moisture index, averaged over layers
    SOIL_MOISTURE_0_TO_7CM_MEAN = "soil_moisture_0_to_7cm_mean"
    SOIL_MOISTURE_0_TO_10CM_MEAN = "soil_moisture_0_to_10cm_mean"
    SOIL_MOISTURE_0_TO_100CM_MEAN = "soil_moisture_0_to_100cm_mean"
    SOIL_MOISTURE_7_TO_28CM_MEAN = "soil_moisture_7_to_28cm_mean"
    SOIL_MOISTURE_28_TO_100CM_MEAN = "soil_moisture_28_to_100cm_mean"
    SOIL_MOISTURE_INDEX_0_TO_7CM_MEAN = "soil_moisture_index_0_to_7cm_mean"
    SOIL_MOISTURE_INDEX_0_TO_100CM_MEAN = "soil_moisture_index_0_to_100cm_mean"
    SOIL_MOISTURE_INDEX_7_TO_28CM_MEAN = "soil_moisture_index_7_to_28cm_mean"
    SOIL_MOISTURE_INDEX_28_TO_100CM_MEAN = "soil_moisture_index_28_to_100cm_mean"
    SOIL_MOISTURE_INDEX_100_TO_255CM_MEAN = "soil_moisture_index_100_to_255cm_mean"

    # Mean soil moisture and temperature of the deep soil layer
    SOIL_MOISTURE_100_TO_255CM_MEAN = "soil_moisture_100_to_255cm_mean"
    SOIL_TEMPERATURE_100_TO_255CM_MEAN = "soil_temperature_100_to_255cm_mean"

    # Mean soil temperature, averaged over layers
    SOIL_TEMPERATURE_0_TO_7CM_MEAN = "soil_temperature_0_to_7cm_mean"
    SOIL_TEMPERATURE_0_TO_100CM_MEAN = "soil_temperature_0_to_100cm_mean"
    SOIL_TEMPERATURE_7_TO_28CM_MEAN = "soil_temperature_7_to_28cm_mean"
    SOIL_TEMPERATURE_28_TO_100CM_MEAN = "soil_temperature_28_to_100cm_mean"

    # Sun rise and set times
    SUNRISE = "sunrise"
    SUNSET = "sunset"

    # Number of seconds of sunshine per day
    SUNSHINE_DURATION = "sunshine_duration"

    # Maximum, mean, and minimum atmospheric air pressure at the surface (hPa)
    SURFACE_PRESSURE_MAX = "surface_pressure_max"
    SURFACE_PRESSURE_MEAN = "surface_pressure_mean"
    SURFACE_PRESSURE_MIN = "surface_pressure_min"

    # Maximum, mean, and minimum daily air temperature at 2 meters above ground
    TEMPERATURE_2M_MAX = "temperature_2m_max"
    TEMPERATURE_2M_MEAN = "temperature_2m_mean"
    TEMPERATURE_2M_MIN = "temperature_2m_min"

    # Maximum updraft speed
    UPDRAFT_MAX = "updraft_max"

    # Maximum UV index, with and without taking clouds into account
    UV_INDEX_CLEAR_SKY_MAX = "uv_index_clear_sky_max"
    UV_INDEX_MAX = "uv_index_max"

    # Maximum vapour pressure deficit
    VAPOUR_PRESSURE_DEFICIT_MAX = "vapour_pressure_deficit_max"

    # Maximum, mean, and minimum visibility
    VISIBILITY_MAX = "visibility_max"
    VISIBILITY_MEAN = "visibility_mean"
    VISIBILITY_MIN = "visibility_min"

    # The most severe weather condition on a given day
    WEATHER_CODE = "weather_code"

    # Maximum, mean, and minimum wet bulb temperature at 2 meters above ground
    WET_BULB_TEMPERATURE_2M_MAX = "wet_bulb_temperature_2m_max"
    WET_BULB_TEMPERATURE_2M_MEAN = "wet_bulb_temperature_2m_mean"
    WET_BULB_TEMPERATURE_2M_MIN = "wet_bulb_temperature_2m_min"

    # Dominant wind direction at 10, 100, and 200 meters above ground
    WIND_DIRECTION_10M_DOMINANT = "wind_direction_10m_dominant"
    WIND_DIRECTION_100M_DOMINANT = "wind_direction_100m_dominant"
    WIND_DIRECTION_200M_DOMINANT = "wind_direction_200m_dominant"

    # Maximum, mean, and minimum wind gusts on a day
    WIND_GUSTS_10M_MAX = "wind_gusts_10m_max"
    WIND_GUSTS_10M_MEAN = "wind_gusts_10m_mean"
    WIND_GUSTS_10M_MIN = "wind_gusts_10m_min"

    # Maximum, mean, and minimum wind speed on a day
    WIND_SPEED_10M_MAX = "wind_speed_10m_max"
    WIND_SPEED_10M_MEAN = "wind_speed_10m_mean"
    WIND_SPEED_10M_MIN = "wind_speed_10m_min"

    # Maximum, mean, and minimum wind speed at 100 and 200 meters above ground
    WIND_SPEED_100M_MAX = "wind_speed_100m_max"
    WIND_SPEED_100M_MEAN = "wind_speed_100m_mean"
    WIND_SPEED_100M_MIN = "wind_speed_100m_min"
    WIND_SPEED_200M_MAX = "wind_speed_200m_max"
    WIND_SPEED_200M_MEAN = "wind_speed_200m_mean"
    WIND_SPEED_200M_MIN = "wind_speed_200m_min"


class PressureLevelVariable(StrEnum):
    """Enum to represent the variables available on pressure levels.

    Pressure levels are given in hPa, like 850 or 500. The lower the
    pressure, the higher up in the atmosphere: 1000 hPa is close to sea
    level, 500 hPa is about 5.6 km up.
    """

    # Cloud cover as an area fraction
    CLOUD_COVER = "cloud_cover"

    # Dew point temperature
    DEW_POINT = "dew_point"

    # Height above sea level of the pressure level
    GEOPOTENTIAL_HEIGHT = "geopotential_height"

    # Relative humidity
    RELATIVE_HUMIDITY = "relative_humidity"

    # Air temperature
    TEMPERATURE = "temperature"

    # Vertical wind speed; positive is upward
    VERTICAL_VELOCITY = "vertical_velocity"

    # Wind direction and speed
    WIND_DIRECTION = "wind_direction"
    WIND_SPEED = "wind_speed"

    # Wind speed from west to east (u) and from south to north (v);
    # negative is the other way around
    WIND_U_COMPONENT = "wind_u_component"
    WIND_V_COMPONENT = "wind_v_component"


# The API returns pressure level data as one variable per level, like
# temperature_850hPa
PRESSURE_LEVEL_KEY = re.compile(r"^(?P<variable>[a-z_]+)_(?P<level>\d+)hPa$")


# A plain set, as checking a string against a StrEnum only works from
# Python 3.12 on
PRESSURE_LEVEL_VARIABLES = {variable.value for variable in PressureLevelVariable}


def _split_pressure_levels(data: dict[Any, Any]) -> dict[Any, Any]:
    """Group the pressure level variables of a section by pressure level.

    temperature_850hPa and wind_speed_850hPa end up as the temperature and
    wind_speed of pressure_levels[850].
    """
    data = dict(data)
    levels: dict[int, dict[str, Any]] = {}
    for key in list(data):
        match = PRESSURE_LEVEL_KEY.match(key)
        if match is None or match["variable"] not in PRESSURE_LEVEL_VARIABLES:
            continue

        levels.setdefault(int(match["level"]), {})[match["variable"]] = data.pop(key)

    if levels:
        data["pressure_levels"] = levels

    return data


@dataclass
class PressureLevelForecast(DataClassORJSONMixin):
    """Hourly weather data on a single pressure level."""

    cloud_cover: list[int | None] | None = None
    dew_point: list[float | None] | None = None
    geopotential_height: list[float | None] | None = None
    relative_humidity: list[int | None] | None = None
    temperature: list[float | None] | None = None
    vertical_velocity: list[float | None] | None = None
    wind_direction: list[int | None] | None = None
    wind_speed: list[float | None] | None = None
    wind_u_component: list[float | None] | None = None
    wind_v_component: list[float | None] | None = None


@dataclass
class PressureLevelCurrent(DataClassORJSONMixin):
    """Current weather conditions on a single pressure level."""

    cloud_cover: int | None = None
    dew_point: float | None = None
    geopotential_height: float | None = None
    relative_humidity: int | None = None
    temperature: float | None = None
    vertical_velocity: float | None = None
    wind_direction: int | None = None
    wind_speed: float | None = None
    wind_u_component: float | None = None
    wind_v_component: float | None = None


@dataclass
class PressureLevelForecastUnits(DataClassORJSONMixin):
    """Hourly weather data units on a single pressure level."""

    cloud_cover: str | None = None
    dew_point: str | None = None
    geopotential_height: str | None = None
    relative_humidity: str | None = None
    temperature: str | None = None
    vertical_velocity: str | None = None
    wind_direction: str | None = None
    wind_speed: str | None = None
    wind_u_component: str | None = None
    wind_v_component: str | None = None


class HeightLevelVariable(StrEnum):
    """Enum to represent the variables available on height levels.

    Height levels are given in meters above ground, like 300 or 1000. Which
    heights have data depends on the weather model; UKMO, DMI, and KNMI have
    the most.
    """

    # Cloud cover as an area fraction
    CLOUD_COVER = "cloud_cover"

    # Dew point temperature
    DEW_POINT = "dew_point"

    # Relative humidity
    RELATIVE_HUMIDITY = "relative_humidity"

    # Air temperature
    TEMPERATURE = "temperature"

    # Vertical wind speed; positive is upward
    VERTICAL_VELOCITY = "vertical_velocity"

    # Wind direction and speed
    WIND_DIRECTION = "wind_direction"
    WIND_SPEED = "wind_speed"

    # Wind speed from west to east (u) and from south to north (v);
    # negative is the other way around
    WIND_U_COMPONENT = "wind_u_component"
    WIND_V_COMPONENT = "wind_v_component"


# The API returns height level data as one variable per height, like
# temperature_300m
HEIGHT_LEVEL_KEY = re.compile(r"^(?P<variable>[a-z_]+)_(?P<level>\d+)m$")

# A plain set, as checking a string against a StrEnum only works from
# Python 3.12 on
HEIGHT_LEVEL_VARIABLES = {variable.value for variable in HeightLevelVariable}


def _split_height_levels(data: dict[Any, Any], cls: type) -> dict[Any, Any]:
    """Group the height level variables of a section by height.

    temperature_300m and wind_speed_300m end up as the temperature and
    wind_speed of height_levels[300]. Heights that are a variable of their
    own, like temperature_2m or wind_speed_80m, stay where they are, as the
    API returns those as such too.
    """
    own_fields = {field.name for field in dataclasses.fields(cls)}

    data = dict(data)
    levels: dict[int, dict[str, Any]] = {}
    for key in list(data):
        match = HEIGHT_LEVEL_KEY.match(key)
        if (
            match is None
            or match["variable"] not in HEIGHT_LEVEL_VARIABLES
            or key in own_fields
        ):
            continue

        levels.setdefault(int(match["level"]), {})[match["variable"]] = data.pop(key)

    if levels:
        data["height_levels"] = levels

    return data


@dataclass
class HeightLevelForecast(DataClassORJSONMixin):
    """Hourly weather data at a single height above ground."""

    cloud_cover: list[int | None] | None = None
    dew_point: list[float | None] | None = None
    relative_humidity: list[int | None] | None = None
    temperature: list[float | None] | None = None
    vertical_velocity: list[float | None] | None = None
    wind_direction: list[int | None] | None = None
    wind_speed: list[float | None] | None = None
    wind_u_component: list[float | None] | None = None
    wind_v_component: list[float | None] | None = None


@dataclass
class HeightLevelCurrent(DataClassORJSONMixin):
    """Current weather conditions at a single height above ground."""

    cloud_cover: int | None = None
    dew_point: float | None = None
    relative_humidity: int | None = None
    temperature: float | None = None
    vertical_velocity: float | None = None
    wind_direction: int | None = None
    wind_speed: float | None = None
    wind_u_component: float | None = None
    wind_v_component: float | None = None


@dataclass
class HeightLevelForecastUnits(DataClassORJSONMixin):
    """Hourly weather data units at a single height above ground."""

    cloud_cover: str | None = None
    dew_point: str | None = None
    relative_humidity: str | None = None
    temperature: str | None = None
    vertical_velocity: str | None = None
    wind_direction: str | None = None
    wind_speed: str | None = None
    wind_u_component: str | None = None
    wind_v_component: str | None = None


@dataclass
class CurrentForecastBase(DataClassORJSONMixin):
    """Current weather conditions, of the forecast or of one of its groups.

    The groups, the previous model runs and the spread, have the same
    variables as the forecast, but no groups of their own.
    """

    time: datetime
    interval: int
    air_density_2m: float | None = None
    albedo: float | None = None
    apparent_temperature: float | None = None
    boundary_layer_height: float | None = None
    cape: float | None = None
    cloud_base: float | None = None
    cloud_cover: int | None = None
    cloud_cover_2m: int | None = None
    cloud_cover_high: int | None = None
    cloud_cover_low: int | None = None
    cloud_cover_mid: int | None = None
    cloud_top: float | None = None
    convective_cloud_base: float | None = None
    convective_cloud_top: float | None = None
    convective_inhibition: float | None = None
    dew_point_2m: float | None = None
    diffuse_radiation: float | None = None
    diffuse_radiation_instant: float | None = None
    direct_normal_irradiance: float | None = None
    direct_normal_irradiance_instant: float | None = None
    direct_radiation: float | None = None
    direct_radiation_instant: float | None = None
    et0_fao_evapotranspiration: float | None = None
    evapotranspiration: float | None = None
    freezing_level_height: float | None = None
    freezing_rain_probability: int | None = None
    global_tilted_irradiance: float | None = None
    global_tilted_irradiance_instant: float | None = None
    growing_degree_days_base_0_limit_50: float | None = None
    hail: float | None = None
    ice_pellets_probability: int | None = None
    is_day: bool | None = None
    k_index: float | None = None
    latent_heat_flux: float | None = None
    leaf_wetness_probability: int | None = None
    lifted_index: float | None = None
    lightning_density: float | None = None
    lightning_potential: float | None = None
    mass_density_8m: float | None = None
    ocean_current_direction: float | None = None
    ocean_current_velocity: float | None = None
    potential_evapotranspiration: float | None = None
    precipitation: float | None = None
    precipitation_probability: int | None = None
    precipitation_type: int | None = None
    pressure_msl: float | None = None
    rain: float | None = None
    rain_probability: int | None = None
    relative_humidity_2m: int | None = None
    roughness_length: float | None = None
    runoff: float | None = None
    sea_ice_thickness: float | None = None
    sea_level_height_msl: float | None = None
    sea_surface_temperature: float | None = None
    sea_water_salinity: float | None = None
    sensible_heat_flux: float | None = None
    shortwave_radiation: float | None = None
    shortwave_radiation_clear_sky: float | None = None
    shortwave_radiation_clear_sky_instant: float | None = None
    shortwave_radiation_instant: float | None = None
    showers: float | None = None
    snow_density: float | None = None
    snow_depth: float | None = None
    snow_depth_water_equivalent: float | None = None
    snow_height: float | None = None
    snowfall: float | None = None
    snowfall_height: float | None = None
    snowfall_probability: int | None = None
    snowfall_water_equivalent: float | None = None
    soil_moisture_0_to_100cm: float | None = None
    soil_moisture_0_to_10cm: float | None = None
    soil_moisture_0_to_1cm: float | None = None
    soil_moisture_0_to_7cm: float | None = None
    soil_moisture_100_to_200cm: float | None = None
    soil_moisture_100_to_255cm: float | None = None
    soil_moisture_100_to_300cm: float | None = None
    soil_moisture_10_to_35cm: float | None = None
    soil_moisture_10_to_40cm: float | None = None
    soil_moisture_1_to_3cm: float | None = None
    soil_moisture_243_to_729cm: float | None = None
    soil_moisture_27_to_81cm: float | None = None
    soil_moisture_28_to_100cm: float | None = None
    soil_moisture_35_to_100cm: float | None = None
    soil_moisture_3_to_9cm: float | None = None
    soil_moisture_40_to_100cm: float | None = None
    soil_moisture_729_to_2187cm: float | None = None
    soil_moisture_7_to_28cm: float | None = None
    soil_moisture_81_to_243cm: float | None = None
    soil_moisture_9_to_27cm: float | None = None
    soil_moisture_index_0_to_100cm: float | None = None
    soil_moisture_index_0_to_7cm: float | None = None
    soil_moisture_index_100_to_255cm: float | None = None
    soil_moisture_index_28_to_100cm: float | None = None
    soil_moisture_index_7_to_28cm: float | None = None
    soil_temperature_0_to_100cm: float | None = None
    soil_temperature_0_to_10cm: float | None = None
    soil_temperature_0_to_7cm: float | None = None
    soil_temperature_0cm: float | None = None
    soil_temperature_100_to_200cm: float | None = None
    soil_temperature_100_to_255cm: float | None = None
    soil_temperature_100_to_300cm: float | None = None
    soil_temperature_10_to_35cm: float | None = None
    soil_temperature_10_to_40cm: float | None = None
    soil_temperature_1458cm: float | None = None
    soil_temperature_162cm: float | None = None
    soil_temperature_18cm: float | None = None
    soil_temperature_28_to_100cm: float | None = None
    soil_temperature_35_to_100cm: float | None = None
    soil_temperature_40_to_100cm: float | None = None
    soil_temperature_486cm: float | None = None
    soil_temperature_54cm: float | None = None
    soil_temperature_6cm: float | None = None
    soil_temperature_7_to_28cm: float | None = None
    sunshine_duration: float | None = None
    surface_pressure: float | None = None
    surface_temperature: float | None = None
    temperature_100m: float | None = None
    temperature_120m: float | None = None
    temperature_150m: float | None = None
    temperature_180m: float | None = None
    temperature_200m: float | None = None
    temperature_20m: float | None = None
    temperature_2m: float | None = None
    temperature_2m_max: float | None = None
    temperature_2m_min: float | None = None
    temperature_40m: float | None = None
    temperature_50m: float | None = None
    temperature_80m: float | None = None
    terrestrial_radiation: float | None = None
    terrestrial_radiation_instant: float | None = None
    thunderstorm_probability: int | None = None
    total_column_integrated_water_vapour: float | None = None
    total_column_water: float | None = None
    updraft: float | None = None
    uv_index: float | None = None
    uv_index_clear_sky: float | None = None
    vapour_pressure_deficit: float | None = None
    visibility: float | None = None
    wave_direction: int | None = None
    wave_height: float | None = None
    wave_peak_period: float | None = None
    wave_period: float | None = None
    weather_code: int | None = None
    wet_bulb_temperature_2m: float | None = None
    wind_direction_100m: int | None = None
    wind_direction_10m: int | None = None
    wind_direction_120m: int | None = None
    wind_direction_140m: int | None = None
    wind_direction_150m: int | None = None
    wind_direction_160m: int | None = None
    wind_direction_180m: int | None = None
    wind_direction_200m: int | None = None
    wind_direction_20m: int | None = None
    wind_direction_30m: int | None = None
    wind_direction_40m: int | None = None
    wind_direction_50m: int | None = None
    wind_direction_70m: int | None = None
    wind_direction_80m: int | None = None
    wind_gusts_10m: float | None = None
    wind_speed_100m: float | None = None
    wind_speed_10m: float | None = None
    wind_speed_120m: float | None = None
    wind_speed_140m: float | None = None
    wind_speed_150m: float | None = None
    wind_speed_160m: float | None = None
    wind_speed_180m: float | None = None
    wind_speed_200m: float | None = None
    wind_speed_20m: float | None = None
    wind_speed_30m: float | None = None
    wind_speed_40m: float | None = None
    wind_speed_50m: float | None = None
    wind_speed_70m: float | None = None
    wind_speed_80m: float | None = None

    # Pressure level data, keyed by the pressure level in hPa
    pressure_levels: dict[int, PressureLevelCurrent] | None = None

    # Height level data, keyed by the height above ground in meters
    height_levels: dict[int, HeightLevelCurrent] | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the pressure and height levels."""
        return _split_height_levels(_split_pressure_levels(d), cls)


@dataclass
class CurrentForecast(CurrentForecastBase):
    """Current weather conditions."""

    # Only set for previous model runs, keyed by how many days before each
    # hour the forecast was made
    previous_days: dict[int, CurrentForecastBase] | None = None

    # Only set for ensemble mean models: the spread over the members
    spread: CurrentForecastBase | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group previous runs, the spread, and pressure and height levels."""
        return _split_height_levels(
            _split_pressure_levels(_split_spread(_split_previous_days(d))), cls
        )


@dataclass
class CurrentForecastUnitsBase(DataClassORJSONMixin):
    """Current weather conditions units, of the forecast or of its spread."""

    time: TimeFormat | None = None
    interval: str | None = None
    air_density_2m: str | None = None
    albedo: str | None = None
    apparent_temperature: str | None = None
    boundary_layer_height: str | None = None
    cape: str | None = None
    cloud_base: str | None = None
    cloud_cover: str | None = None
    cloud_cover_2m: str | None = None
    cloud_cover_high: str | None = None
    cloud_cover_low: str | None = None
    cloud_cover_mid: str | None = None
    cloud_top: str | None = None
    convective_cloud_base: str | None = None
    convective_cloud_top: str | None = None
    convective_inhibition: str | None = None
    dew_point_2m: str | None = None
    diffuse_radiation: str | None = None
    diffuse_radiation_instant: str | None = None
    direct_normal_irradiance: str | None = None
    direct_normal_irradiance_instant: str | None = None
    direct_radiation: str | None = None
    direct_radiation_instant: str | None = None
    et0_fao_evapotranspiration: str | None = None
    evapotranspiration: str | None = None
    freezing_level_height: str | None = None
    freezing_rain_probability: str | None = None
    global_tilted_irradiance: str | None = None
    global_tilted_irradiance_instant: str | None = None
    growing_degree_days_base_0_limit_50: str | None = None
    hail: str | None = None
    ice_pellets_probability: str | None = None
    is_day: str | None = None
    k_index: str | None = None
    latent_heat_flux: str | None = None
    leaf_wetness_probability: str | None = None
    lifted_index: str | None = None
    lightning_density: str | None = None
    lightning_potential: str | None = None
    mass_density_8m: str | None = None
    ocean_current_direction: str | None = None
    ocean_current_velocity: str | None = None
    potential_evapotranspiration: str | None = None
    precipitation: str | None = None
    precipitation_probability: str | None = None
    precipitation_type: str | None = None
    pressure_msl: str | None = None
    rain: str | None = None
    rain_probability: str | None = None
    relative_humidity_2m: str | None = None
    roughness_length: str | None = None
    runoff: str | None = None
    sea_ice_thickness: str | None = None
    sea_level_height_msl: str | None = None
    sea_surface_temperature: str | None = None
    sea_water_salinity: str | None = None
    sensible_heat_flux: str | None = None
    shortwave_radiation: str | None = None
    shortwave_radiation_clear_sky: str | None = None
    shortwave_radiation_clear_sky_instant: str | None = None
    shortwave_radiation_instant: str | None = None
    showers: str | None = None
    snow_density: str | None = None
    snow_depth: str | None = None
    snow_depth_water_equivalent: str | None = None
    snow_height: str | None = None
    snowfall: str | None = None
    snowfall_height: str | None = None
    snowfall_probability: str | None = None
    snowfall_water_equivalent: str | None = None
    soil_moisture_0_to_100cm: str | None = None
    soil_moisture_0_to_10cm: str | None = None
    soil_moisture_0_to_1cm: str | None = None
    soil_moisture_0_to_7cm: str | None = None
    soil_moisture_100_to_200cm: str | None = None
    soil_moisture_100_to_255cm: str | None = None
    soil_moisture_100_to_300cm: str | None = None
    soil_moisture_10_to_35cm: str | None = None
    soil_moisture_10_to_40cm: str | None = None
    soil_moisture_1_to_3cm: str | None = None
    soil_moisture_243_to_729cm: str | None = None
    soil_moisture_27_to_81cm: str | None = None
    soil_moisture_28_to_100cm: str | None = None
    soil_moisture_35_to_100cm: str | None = None
    soil_moisture_3_to_9cm: str | None = None
    soil_moisture_40_to_100cm: str | None = None
    soil_moisture_729_to_2187cm: str | None = None
    soil_moisture_7_to_28cm: str | None = None
    soil_moisture_81_to_243cm: str | None = None
    soil_moisture_9_to_27cm: str | None = None
    soil_moisture_index_0_to_100cm: str | None = None
    soil_moisture_index_0_to_7cm: str | None = None
    soil_moisture_index_100_to_255cm: str | None = None
    soil_moisture_index_28_to_100cm: str | None = None
    soil_moisture_index_7_to_28cm: str | None = None
    soil_temperature_0_to_100cm: str | None = None
    soil_temperature_0_to_10cm: str | None = None
    soil_temperature_0_to_7cm: str | None = None
    soil_temperature_0cm: str | None = None
    soil_temperature_100_to_200cm: str | None = None
    soil_temperature_100_to_255cm: str | None = None
    soil_temperature_100_to_300cm: str | None = None
    soil_temperature_10_to_35cm: str | None = None
    soil_temperature_10_to_40cm: str | None = None
    soil_temperature_1458cm: str | None = None
    soil_temperature_162cm: str | None = None
    soil_temperature_18cm: str | None = None
    soil_temperature_28_to_100cm: str | None = None
    soil_temperature_35_to_100cm: str | None = None
    soil_temperature_40_to_100cm: str | None = None
    soil_temperature_486cm: str | None = None
    soil_temperature_54cm: str | None = None
    soil_temperature_6cm: str | None = None
    soil_temperature_7_to_28cm: str | None = None
    sunshine_duration: str | None = None
    surface_pressure: str | None = None
    surface_temperature: str | None = None
    temperature_100m: str | None = None
    temperature_120m: str | None = None
    temperature_150m: str | None = None
    temperature_180m: str | None = None
    temperature_200m: str | None = None
    temperature_20m: str | None = None
    temperature_2m: str | None = None
    temperature_2m_max: str | None = None
    temperature_2m_min: str | None = None
    temperature_40m: str | None = None
    temperature_50m: str | None = None
    temperature_80m: str | None = None
    terrestrial_radiation: str | None = None
    terrestrial_radiation_instant: str | None = None
    thunderstorm_probability: str | None = None
    total_column_integrated_water_vapour: str | None = None
    total_column_water: str | None = None
    updraft: str | None = None
    uv_index: str | None = None
    uv_index_clear_sky: str | None = None
    vapour_pressure_deficit: str | None = None
    visibility: str | None = None
    wave_direction: str | None = None
    wave_height: str | None = None
    wave_peak_period: str | None = None
    wave_period: str | None = None
    weather_code: str | None = None
    wet_bulb_temperature_2m: str | None = None
    wind_direction_100m: str | None = None
    wind_direction_10m: str | None = None
    wind_direction_120m: str | None = None
    wind_direction_140m: str | None = None
    wind_direction_150m: str | None = None
    wind_direction_160m: str | None = None
    wind_direction_180m: str | None = None
    wind_direction_200m: str | None = None
    wind_direction_20m: str | None = None
    wind_direction_30m: str | None = None
    wind_direction_40m: str | None = None
    wind_direction_50m: str | None = None
    wind_direction_70m: str | None = None
    wind_direction_80m: str | None = None
    wind_gusts_10m: str | None = None
    wind_speed_100m: str | None = None
    wind_speed_10m: str | None = None
    wind_speed_120m: str | None = None
    wind_speed_140m: str | None = None
    wind_speed_150m: str | None = None
    wind_speed_160m: str | None = None
    wind_speed_180m: str | None = None
    wind_speed_200m: str | None = None
    wind_speed_20m: str | None = None
    wind_speed_30m: str | None = None
    wind_speed_40m: str | None = None
    wind_speed_50m: str | None = None
    wind_speed_70m: str | None = None
    wind_speed_80m: str | None = None

    # Pressure level units, keyed by the pressure level in hPa
    pressure_levels: dict[int, PressureLevelForecastUnits] | None = None

    # Height level units, keyed by the height above ground in meters
    height_levels: dict[int, HeightLevelForecastUnits] | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the pressure and height levels."""
        return _split_height_levels(_split_pressure_levels(d), cls)


@dataclass
class CurrentForecastUnits(CurrentForecastUnitsBase):
    """Current weather conditions units."""

    # Only set for ensemble mean models: the units of the spread
    spread: CurrentForecastUnitsBase | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the levels and spread, and drop previous run units."""
        return _split_height_levels(
            _split_pressure_levels(_split_spread(_drop_suffixed(d))), cls
        )


@dataclass
class HourlyForecastBase(DataClassORJSONMixin):
    """Hourly weather data, of the forecast or of one of its groups.

    The groups, the ensemble members, the previous model runs, and the
    spread, have the same variables as the forecast, but no groups of their
    own; only a member can have a spread.
    """

    time: list[datetime]
    air_density_2m: list[float | None] | None = None
    albedo: list[float | None] | None = None
    apparent_temperature: list[float | None] | None = None
    boundary_layer_height: list[float | None] | None = None
    cape: list[float | None] | None = None
    cloud_base: list[float | None] | None = None
    cloud_cover: list[int | None] | None = None
    cloud_cover_2m: list[int | None] | None = None
    cloud_cover_high: list[int | None] | None = None
    cloud_cover_low: list[int | None] | None = None
    cloud_cover_mid: list[int | None] | None = None
    cloud_top: list[float | None] | None = None
    convective_cloud_base: list[float | None] | None = None
    convective_cloud_top: list[float | None] | None = None
    convective_inhibition: list[float | None] | None = None
    dew_point_2m: list[float | None] | None = None
    diffuse_radiation: list[float | None] | None = None
    diffuse_radiation_instant: list[float | None] | None = None
    direct_normal_irradiance: list[float | None] | None = None
    direct_normal_irradiance_instant: list[float | None] | None = None
    direct_radiation: list[float | None] | None = None
    direct_radiation_instant: list[float | None] | None = None
    et0_fao_evapotranspiration: list[float | None] | None = None
    evapotranspiration: list[float | None] | None = None
    freezing_level_height: list[float | None] | None = None
    freezing_rain_probability: list[int | None] | None = None
    global_tilted_irradiance: list[float | None] | None = None
    global_tilted_irradiance_instant: list[float | None] | None = None
    growing_degree_days_base_0_limit_50: list[float | None] | None = None
    hail: list[float | None] | None = None
    ice_pellets_probability: list[int | None] | None = None
    is_day: list[bool | None] | None = None
    k_index: list[float | None] | None = None
    latent_heat_flux: list[float | None] | None = None
    leaf_wetness_probability: list[int | None] | None = None
    lifted_index: list[float | None] | None = None
    lightning_density: list[float | None] | None = None
    lightning_potential: list[float | None] | None = None
    mass_density_8m: list[float | None] | None = None
    ocean_current_direction: list[float | None] | None = None
    ocean_current_velocity: list[float | None] | None = None
    potential_evapotranspiration: list[float | None] | None = None
    precipitation: list[float | None] | None = None
    precipitation_probability: list[int | None] | None = None
    precipitation_type: list[int | None] | None = None
    pressure_msl: list[float | None] | None = None
    rain: list[float | None] | None = None
    rain_probability: list[int | None] | None = None
    relative_humidity_2m: list[int | None] | None = None
    roughness_length: list[float | None] | None = None
    runoff: list[float | None] | None = None
    sea_ice_thickness: list[float | None] | None = None
    sea_level_height_msl: list[float | None] | None = None
    sea_surface_temperature: list[float | None] | None = None
    sea_water_salinity: list[float | None] | None = None
    sensible_heat_flux: list[float | None] | None = None
    shortwave_radiation: list[float | None] | None = None
    shortwave_radiation_clear_sky: list[float | None] | None = None
    shortwave_radiation_clear_sky_instant: list[float | None] | None = None
    shortwave_radiation_instant: list[float | None] | None = None
    showers: list[float | None] | None = None
    snow_density: list[float | None] | None = None
    snow_depth: list[float | None] | None = None
    snow_depth_water_equivalent: list[float | None] | None = None
    snow_height: list[float | None] | None = None
    snowfall: list[float | None] | None = None
    snowfall_height: list[float | None] | None = None
    snowfall_probability: list[int | None] | None = None
    snowfall_water_equivalent: list[float | None] | None = None
    soil_moisture_0_to_100cm: list[float | None] | None = None
    soil_moisture_0_to_10cm: list[float | None] | None = None
    soil_moisture_0_to_1cm: list[float | None] | None = None
    soil_moisture_0_to_7cm: list[float | None] | None = None
    soil_moisture_100_to_200cm: list[float | None] | None = None
    soil_moisture_100_to_255cm: list[float | None] | None = None
    soil_moisture_100_to_300cm: list[float | None] | None = None
    soil_moisture_10_to_35cm: list[float | None] | None = None
    soil_moisture_10_to_40cm: list[float | None] | None = None
    soil_moisture_1_to_3cm: list[float | None] | None = None
    soil_moisture_243_to_729cm: list[float | None] | None = None
    soil_moisture_27_to_81cm: list[float | None] | None = None
    soil_moisture_28_to_100cm: list[float | None] | None = None
    soil_moisture_35_to_100cm: list[float | None] | None = None
    soil_moisture_3_to_9cm: list[float | None] | None = None
    soil_moisture_40_to_100cm: list[float | None] | None = None
    soil_moisture_729_to_2187cm: list[float | None] | None = None
    soil_moisture_7_to_28cm: list[float | None] | None = None
    soil_moisture_81_to_243cm: list[float | None] | None = None
    soil_moisture_9_to_27cm: list[float | None] | None = None
    soil_moisture_index_0_to_100cm: list[float | None] | None = None
    soil_moisture_index_0_to_7cm: list[float | None] | None = None
    soil_moisture_index_100_to_255cm: list[float | None] | None = None
    soil_moisture_index_28_to_100cm: list[float | None] | None = None
    soil_moisture_index_7_to_28cm: list[float | None] | None = None
    soil_temperature_0_to_100cm: list[float | None] | None = None
    soil_temperature_0_to_10cm: list[float | None] | None = None
    soil_temperature_0_to_7cm: list[float | None] | None = None
    soil_temperature_0cm: list[float | None] | None = None
    soil_temperature_100_to_200cm: list[float | None] | None = None
    soil_temperature_100_to_255cm: list[float | None] | None = None
    soil_temperature_100_to_300cm: list[float | None] | None = None
    soil_temperature_10_to_35cm: list[float | None] | None = None
    soil_temperature_10_to_40cm: list[float | None] | None = None
    soil_temperature_1458cm: list[float | None] | None = None
    soil_temperature_162cm: list[float | None] | None = None
    soil_temperature_18cm: list[float | None] | None = None
    soil_temperature_28_to_100cm: list[float | None] | None = None
    soil_temperature_35_to_100cm: list[float | None] | None = None
    soil_temperature_40_to_100cm: list[float | None] | None = None
    soil_temperature_486cm: list[float | None] | None = None
    soil_temperature_54cm: list[float | None] | None = None
    soil_temperature_6cm: list[float | None] | None = None
    soil_temperature_7_to_28cm: list[float | None] | None = None
    sunshine_duration: list[float | None] | None = None
    surface_pressure: list[float | None] | None = None
    surface_temperature: list[float | None] | None = None
    temperature_100m: list[float | None] | None = None
    temperature_120m: list[float | None] | None = None
    temperature_150m: list[float | None] | None = None
    temperature_180m: list[float | None] | None = None
    temperature_200m: list[float | None] | None = None
    temperature_20m: list[float | None] | None = None
    temperature_2m: list[float | None] | None = None
    temperature_2m_max: list[float | None] | None = None
    temperature_2m_min: list[float | None] | None = None
    temperature_40m: list[float | None] | None = None
    temperature_50m: list[float | None] | None = None
    temperature_80m: list[float | None] | None = None
    terrestrial_radiation: list[float | None] | None = None
    terrestrial_radiation_instant: list[float | None] | None = None
    thunderstorm_probability: list[int | None] | None = None
    total_column_integrated_water_vapour: list[float | None] | None = None
    total_column_water: list[float | None] | None = None
    updraft: list[float | None] | None = None
    uv_index: list[float | None] | None = None
    uv_index_clear_sky: list[float | None] | None = None
    vapour_pressure_deficit: list[float | None] | None = None
    visibility: list[float | None] | None = None
    wave_direction: list[int | None] | None = None
    wave_height: list[float | None] | None = None
    wave_peak_period: list[float | None] | None = None
    wave_period: list[float | None] | None = None
    weather_code: list[int | None] | None = None
    wet_bulb_temperature_2m: list[float | None] | None = None
    wind_direction_100m: list[int | None] | None = None
    wind_direction_10m: list[int | None] | None = None
    wind_direction_120m: list[int | None] | None = None
    wind_direction_140m: list[int | None] | None = None
    wind_direction_150m: list[int | None] | None = None
    wind_direction_160m: list[int | None] | None = None
    wind_direction_180m: list[int | None] | None = None
    wind_direction_200m: list[int | None] | None = None
    wind_direction_20m: list[int | None] | None = None
    wind_direction_30m: list[int | None] | None = None
    wind_direction_40m: list[int | None] | None = None
    wind_direction_50m: list[int | None] | None = None
    wind_direction_70m: list[int | None] | None = None
    wind_direction_80m: list[int | None] | None = None
    wind_gusts_10m: list[float | None] | None = None
    wind_speed_100m: list[float | None] | None = None
    wind_speed_10m: list[float | None] | None = None
    wind_speed_120m: list[float | None] | None = None
    wind_speed_140m: list[float | None] | None = None
    wind_speed_150m: list[float | None] | None = None
    wind_speed_160m: list[float | None] | None = None
    wind_speed_180m: list[float | None] | None = None
    wind_speed_200m: list[float | None] | None = None
    wind_speed_20m: list[float | None] | None = None
    wind_speed_30m: list[float | None] | None = None
    wind_speed_40m: list[float | None] | None = None
    wind_speed_50m: list[float | None] | None = None
    wind_speed_70m: list[float | None] | None = None
    wind_speed_80m: list[float | None] | None = None

    # Pressure level data, keyed by the pressure level in hPa
    pressure_levels: dict[int, PressureLevelForecast] | None = None

    # Height level data, keyed by the height above ground in meters
    height_levels: dict[int, HeightLevelForecast] | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the pressure and height levels."""
        return _split_height_levels(_split_pressure_levels(d), cls)


@dataclass
class HourlyForecastMember(HourlyForecastBase):
    """Hourly weather data of a single ensemble member."""

    # Only set for ensemble mean models: the spread of this member
    spread: HourlyForecastBase | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the spread, and the pressure and height levels."""
        return _split_height_levels(_split_pressure_levels(_split_spread(d)), cls)


@dataclass
class HourlyForecast(HourlyForecastBase):
    """Hourly weather data."""

    # Only set for ensemble data, keyed by member number
    members: dict[int, HourlyForecastMember] | None = None

    # Only set for previous model runs, keyed by how many days before each
    # hour the forecast was made
    previous_days: dict[int, HourlyForecastBase] | None = None

    # Only set for ensemble mean models: the spread over the members
    spread: HourlyForecastBase | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group previous runs, members, spread, and pressure and height levels.

        The order follows the API: a member can have a spread, like
        temperature_2m_spread_member01, and both can be on a pressure level,
        like temperature_850hPa_spread. Each group then splits its own.
        """
        return _split_height_levels(
            _split_pressure_levels(
                _split_spread(_split_members(_split_previous_days(d)))
            ),
            cls,
        )


@dataclass
class HourlyForecastUnitsBase(DataClassORJSONMixin):
    """Hourly weather data units, of the forecast or of its spread."""

    time: TimeFormat | None = None
    air_density_2m: str | None = None
    albedo: str | None = None
    apparent_temperature: str | None = None
    boundary_layer_height: str | None = None
    cape: str | None = None
    cloud_base: str | None = None
    cloud_cover: str | None = None
    cloud_cover_2m: str | None = None
    cloud_cover_high: str | None = None
    cloud_cover_low: str | None = None
    cloud_cover_mid: str | None = None
    cloud_top: str | None = None
    convective_cloud_base: str | None = None
    convective_cloud_top: str | None = None
    convective_inhibition: str | None = None
    dew_point_2m: str | None = None
    diffuse_radiation: str | None = None
    diffuse_radiation_instant: str | None = None
    direct_normal_irradiance: str | None = None
    direct_normal_irradiance_instant: str | None = None
    direct_radiation: str | None = None
    direct_radiation_instant: str | None = None
    et0_fao_evapotranspiration: str | None = None
    evapotranspiration: str | None = None
    freezing_level_height: str | None = None
    freezing_rain_probability: str | None = None
    global_tilted_irradiance: str | None = None
    global_tilted_irradiance_instant: str | None = None
    growing_degree_days_base_0_limit_50: str | None = None
    hail: str | None = None
    ice_pellets_probability: str | None = None
    is_day: str | None = None
    k_index: str | None = None
    latent_heat_flux: str | None = None
    leaf_wetness_probability: str | None = None
    lifted_index: str | None = None
    lightning_density: str | None = None
    lightning_potential: str | None = None
    mass_density_8m: str | None = None
    ocean_current_direction: str | None = None
    ocean_current_velocity: str | None = None
    potential_evapotranspiration: str | None = None
    precipitation: str | None = None
    precipitation_probability: str | None = None
    precipitation_type: str | None = None
    pressure_msl: str | None = None
    rain: str | None = None
    rain_probability: str | None = None
    relative_humidity_2m: str | None = None
    roughness_length: str | None = None
    runoff: str | None = None
    sea_ice_thickness: str | None = None
    sea_level_height_msl: str | None = None
    sea_surface_temperature: str | None = None
    sea_water_salinity: str | None = None
    sensible_heat_flux: str | None = None
    shortwave_radiation: str | None = None
    shortwave_radiation_clear_sky: str | None = None
    shortwave_radiation_clear_sky_instant: str | None = None
    shortwave_radiation_instant: str | None = None
    showers: str | None = None
    snow_density: str | None = None
    snow_depth: str | None = None
    snow_depth_water_equivalent: str | None = None
    snow_height: str | None = None
    snowfall: str | None = None
    snowfall_height: str | None = None
    snowfall_probability: str | None = None
    snowfall_water_equivalent: str | None = None
    soil_moisture_0_to_100cm: str | None = None
    soil_moisture_0_to_10cm: str | None = None
    soil_moisture_0_to_1cm: str | None = None
    soil_moisture_0_to_7cm: str | None = None
    soil_moisture_100_to_200cm: str | None = None
    soil_moisture_100_to_255cm: str | None = None
    soil_moisture_100_to_300cm: str | None = None
    soil_moisture_10_to_35cm: str | None = None
    soil_moisture_10_to_40cm: str | None = None
    soil_moisture_1_to_3cm: str | None = None
    soil_moisture_243_to_729cm: str | None = None
    soil_moisture_27_to_81cm: str | None = None
    soil_moisture_28_to_100cm: str | None = None
    soil_moisture_35_to_100cm: str | None = None
    soil_moisture_3_to_9cm: str | None = None
    soil_moisture_40_to_100cm: str | None = None
    soil_moisture_729_to_2187cm: str | None = None
    soil_moisture_7_to_28cm: str | None = None
    soil_moisture_81_to_243cm: str | None = None
    soil_moisture_9_to_27cm: str | None = None
    soil_moisture_index_0_to_100cm: str | None = None
    soil_moisture_index_0_to_7cm: str | None = None
    soil_moisture_index_100_to_255cm: str | None = None
    soil_moisture_index_28_to_100cm: str | None = None
    soil_moisture_index_7_to_28cm: str | None = None
    soil_temperature_0_to_100cm: str | None = None
    soil_temperature_0_to_10cm: str | None = None
    soil_temperature_0_to_7cm: str | None = None
    soil_temperature_0cm: str | None = None
    soil_temperature_100_to_200cm: str | None = None
    soil_temperature_100_to_255cm: str | None = None
    soil_temperature_100_to_300cm: str | None = None
    soil_temperature_10_to_35cm: str | None = None
    soil_temperature_10_to_40cm: str | None = None
    soil_temperature_1458cm: str | None = None
    soil_temperature_162cm: str | None = None
    soil_temperature_18cm: str | None = None
    soil_temperature_28_to_100cm: str | None = None
    soil_temperature_35_to_100cm: str | None = None
    soil_temperature_40_to_100cm: str | None = None
    soil_temperature_486cm: str | None = None
    soil_temperature_54cm: str | None = None
    soil_temperature_6cm: str | None = None
    soil_temperature_7_to_28cm: str | None = None
    sunshine_duration: str | None = None
    surface_pressure: str | None = None
    surface_temperature: str | None = None
    temperature_100m: str | None = None
    temperature_120m: str | None = None
    temperature_150m: str | None = None
    temperature_180m: str | None = None
    temperature_200m: str | None = None
    temperature_20m: str | None = None
    temperature_2m: str | None = None
    temperature_2m_max: str | None = None
    temperature_2m_min: str | None = None
    temperature_40m: str | None = None
    temperature_50m: str | None = None
    temperature_80m: str | None = None
    terrestrial_radiation: str | None = None
    terrestrial_radiation_instant: str | None = None
    thunderstorm_probability: str | None = None
    total_column_integrated_water_vapour: str | None = None
    total_column_water: str | None = None
    updraft: str | None = None
    uv_index: str | None = None
    uv_index_clear_sky: str | None = None
    vapour_pressure_deficit: str | None = None
    visibility: str | None = None
    wave_direction: str | None = None
    wave_height: str | None = None
    wave_peak_period: str | None = None
    wave_period: str | None = None
    weather_code: str | None = None
    wet_bulb_temperature_2m: str | None = None
    wind_direction_100m: str | None = None
    wind_direction_10m: str | None = None
    wind_direction_120m: str | None = None
    wind_direction_140m: str | None = None
    wind_direction_150m: str | None = None
    wind_direction_160m: str | None = None
    wind_direction_180m: str | None = None
    wind_direction_200m: str | None = None
    wind_direction_20m: str | None = None
    wind_direction_30m: str | None = None
    wind_direction_40m: str | None = None
    wind_direction_50m: str | None = None
    wind_direction_70m: str | None = None
    wind_direction_80m: str | None = None
    wind_gusts_10m: str | None = None
    wind_speed_100m: str | None = None
    wind_speed_10m: str | None = None
    wind_speed_120m: str | None = None
    wind_speed_140m: str | None = None
    wind_speed_150m: str | None = None
    wind_speed_160m: str | None = None
    wind_speed_180m: str | None = None
    wind_speed_200m: str | None = None
    wind_speed_20m: str | None = None
    wind_speed_30m: str | None = None
    wind_speed_40m: str | None = None
    wind_speed_50m: str | None = None
    wind_speed_70m: str | None = None
    wind_speed_80m: str | None = None

    # Pressure level units, keyed by the pressure level in hPa
    pressure_levels: dict[int, PressureLevelForecastUnits] | None = None

    # Height level units, keyed by the height above ground in meters
    height_levels: dict[int, HeightLevelForecastUnits] | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the pressure and height levels."""
        return _split_height_levels(_split_pressure_levels(d), cls)


@dataclass
class HourlyForecastUnits(HourlyForecastUnitsBase):
    """Hourly weather data units."""

    # Only set for ensemble mean models: the units of the spread
    spread: HourlyForecastUnitsBase | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the levels and spread, and drop member and run units."""
        return _split_height_levels(
            _split_pressure_levels(_split_spread(_drop_suffixed(d))), cls
        )


@dataclass
class Minutely15Forecast(HourlyForecast):
    """15-minutely weather data.

    Every hourly variable is available. Only some weather models have native
    15-minutely data, for others the data is interpolated from hourly values.
    """


@dataclass
class Minutely15ForecastUnits(HourlyForecastUnits):
    """15-minutely weather data units."""


@dataclass
class DailyForecastBase(DataClassORJSONMixin):
    """Daily weather data, of the forecast or of a single ensemble member."""

    time: list[date]
    apparent_temperature_max: list[float | None] | None = None
    apparent_temperature_mean: list[float | None] | None = None
    apparent_temperature_min: list[float | None] | None = None
    cape_max: list[float | None] | None = None
    cape_mean: list[float | None] | None = None
    cape_min: list[float | None] | None = None
    cloud_cover_max: list[int | None] | None = None
    cloud_cover_mean: list[int | None] | None = None
    cloud_cover_min: list[int | None] | None = None
    daylight_duration: list[float | None] | None = None
    dew_point_2m_max: list[float | None] | None = None
    dew_point_2m_mean: list[float | None] | None = None
    dew_point_2m_min: list[float | None] | None = None
    et0_fao_evapotranspiration: list[float | None] | None = None
    et0_fao_evapotranspiration_sum: list[float | None] | None = None
    growing_degree_days_base_0_limit_50: list[float | None] | None = None
    leaf_wetness_probability_mean: list[float | None] | None = None
    moon_phase: list[float | None] | None = None
    moonrise: list[datetime | None] | None = None
    moonset: list[datetime | None] | None = None
    precipitation_hours: list[float | None] | None = None
    precipitation_probability_max: list[int | None] | None = None
    precipitation_probability_mean: list[float | None] | None = None
    precipitation_probability_min: list[float | None] | None = None
    precipitation_sum: list[float | None] | None = None
    pressure_msl_max: list[float | None] | None = None
    pressure_msl_mean: list[float | None] | None = None
    pressure_msl_min: list[float | None] | None = None
    rain_sum: list[float | None] | None = None
    relative_humidity_2m_max: list[int | None] | None = None
    relative_humidity_2m_mean: list[int | None] | None = None
    relative_humidity_2m_min: list[int | None] | None = None
    sea_surface_temperature_max: list[float | None] | None = None
    sea_surface_temperature_mean: list[float | None] | None = None
    sea_surface_temperature_min: list[float | None] | None = None
    shortwave_radiation_sum: list[float | None] | None = None
    showers_sum: list[float | None] | None = None
    snow_depth_max: list[float | None] | None = None
    snow_depth_mean: list[float | None] | None = None
    snow_depth_min: list[float | None] | None = None
    snowfall_sum: list[float | None] | None = None
    snowfall_water_equivalent_sum: list[float | None] | None = None
    soil_moisture_0_to_100cm_mean: list[float | None] | None = None
    soil_moisture_0_to_10cm_mean: list[float | None] | None = None
    soil_moisture_0_to_7cm_mean: list[float | None] | None = None
    soil_moisture_100_to_255cm_mean: list[float | None] | None = None
    soil_moisture_28_to_100cm_mean: list[float | None] | None = None
    soil_moisture_7_to_28cm_mean: list[float | None] | None = None
    soil_moisture_index_0_to_100cm_mean: list[float | None] | None = None
    soil_moisture_index_0_to_7cm_mean: list[float | None] | None = None
    soil_moisture_index_100_to_255cm_mean: list[float | None] | None = None
    soil_moisture_index_28_to_100cm_mean: list[float | None] | None = None
    soil_moisture_index_7_to_28cm_mean: list[float | None] | None = None
    soil_temperature_0_to_100cm_mean: list[float | None] | None = None
    soil_temperature_0_to_7cm_mean: list[float | None] | None = None
    soil_temperature_100_to_255cm_mean: list[float | None] | None = None
    soil_temperature_28_to_100cm_mean: list[float | None] | None = None
    soil_temperature_7_to_28cm_mean: list[float | None] | None = None
    sunrise: list[datetime | None] | None = None
    sunset: list[datetime | None] | None = None
    sunshine_duration: list[float | None] | None = None
    surface_pressure_max: list[float | None] | None = None
    surface_pressure_mean: list[float | None] | None = None
    surface_pressure_min: list[float | None] | None = None
    temperature_2m_max: list[float | None] | None = None
    temperature_2m_mean: list[float | None] | None = None
    temperature_2m_min: list[float | None] | None = None
    updraft_max: list[float | None] | None = None
    uv_index_clear_sky_max: list[float | None] | None = None
    uv_index_max: list[float | None] | None = None
    vapour_pressure_deficit_max: list[float | None] | None = None
    visibility_max: list[float | None] | None = None
    visibility_mean: list[float | None] | None = None
    visibility_min: list[float | None] | None = None
    weather_code: list[int | None] | None = None
    wet_bulb_temperature_2m_max: list[float | None] | None = None
    wet_bulb_temperature_2m_mean: list[float | None] | None = None
    wet_bulb_temperature_2m_min: list[float | None] | None = None
    wind_direction_100m_dominant: list[int | None] | None = None
    wind_direction_10m_dominant: list[int | None] | None = None
    wind_direction_200m_dominant: list[int | None] | None = None
    wind_gusts_10m_max: list[float | None] | None = None
    wind_gusts_10m_mean: list[float | None] | None = None
    wind_gusts_10m_min: list[float | None] | None = None
    wind_speed_100m_max: list[float | None] | None = None
    wind_speed_100m_mean: list[float | None] | None = None
    wind_speed_100m_min: list[float | None] | None = None
    wind_speed_10m_max: list[float | None] | None = None
    wind_speed_10m_mean: list[float | None] | None = None
    wind_speed_10m_min: list[float | None] | None = None
    wind_speed_200m_max: list[float | None] | None = None
    wind_speed_200m_mean: list[float | None] | None = None
    wind_speed_200m_min: list[float | None] | None = None


@dataclass
class DailyForecast(DailyForecastBase):
    """Daily weather data."""

    # Only set for ensemble data, keyed by member number
    members: dict[int, DailyForecastBase] | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the ensemble members by member number."""
        return _split_members(d)


@dataclass
class DailyForecastUnits(DataClassORJSONMixin):
    """Daily weather data units."""

    time: TimeFormat | None = None
    apparent_temperature_max: str | None = None
    apparent_temperature_mean: str | None = None
    apparent_temperature_min: str | None = None
    cape_max: str | None = None
    cape_mean: str | None = None
    cape_min: str | None = None
    cloud_cover_max: str | None = None
    cloud_cover_mean: str | None = None
    cloud_cover_min: str | None = None
    daylight_duration: str | None = None
    dew_point_2m_max: str | None = None
    dew_point_2m_mean: str | None = None
    dew_point_2m_min: str | None = None
    et0_fao_evapotranspiration: str | None = None
    et0_fao_evapotranspiration_sum: str | None = None
    growing_degree_days_base_0_limit_50: str | None = None
    leaf_wetness_probability_mean: str | None = None
    moon_phase: str | None = None
    moonrise: TimeFormat | None = None
    moonset: TimeFormat | None = None
    precipitation_hours: str | None = None
    precipitation_probability_max: str | None = None
    precipitation_probability_mean: str | None = None
    precipitation_probability_min: str | None = None
    precipitation_sum: str | None = None
    pressure_msl_max: str | None = None
    pressure_msl_mean: str | None = None
    pressure_msl_min: str | None = None
    rain_sum: str | None = None
    relative_humidity_2m_max: str | None = None
    relative_humidity_2m_mean: str | None = None
    relative_humidity_2m_min: str | None = None
    sea_surface_temperature_max: str | None = None
    sea_surface_temperature_mean: str | None = None
    sea_surface_temperature_min: str | None = None
    shortwave_radiation_sum: str | None = None
    showers_sum: str | None = None
    snow_depth_max: str | None = None
    snow_depth_mean: str | None = None
    snow_depth_min: str | None = None
    snowfall_sum: str | None = None
    snowfall_water_equivalent_sum: str | None = None
    soil_moisture_0_to_100cm_mean: str | None = None
    soil_moisture_0_to_10cm_mean: str | None = None
    soil_moisture_0_to_7cm_mean: str | None = None
    soil_moisture_100_to_255cm_mean: str | None = None
    soil_moisture_28_to_100cm_mean: str | None = None
    soil_moisture_7_to_28cm_mean: str | None = None
    soil_moisture_index_0_to_100cm_mean: str | None = None
    soil_moisture_index_0_to_7cm_mean: str | None = None
    soil_moisture_index_100_to_255cm_mean: str | None = None
    soil_moisture_index_28_to_100cm_mean: str | None = None
    soil_moisture_index_7_to_28cm_mean: str | None = None
    soil_temperature_0_to_100cm_mean: str | None = None
    soil_temperature_0_to_7cm_mean: str | None = None
    soil_temperature_100_to_255cm_mean: str | None = None
    soil_temperature_28_to_100cm_mean: str | None = None
    soil_temperature_7_to_28cm_mean: str | None = None
    sunrise: TimeFormat | None = None
    sunset: TimeFormat | None = None
    sunshine_duration: str | None = None
    surface_pressure_max: str | None = None
    surface_pressure_mean: str | None = None
    surface_pressure_min: str | None = None
    temperature_2m_max: str | None = None
    temperature_2m_mean: str | None = None
    temperature_2m_min: str | None = None
    updraft_max: str | None = None
    uv_index_clear_sky_max: str | None = None
    uv_index_max: str | None = None
    vapour_pressure_deficit_max: str | None = None
    visibility_max: str | None = None
    visibility_mean: str | None = None
    visibility_min: str | None = None
    weather_code: str | None = None
    wet_bulb_temperature_2m_max: str | None = None
    wet_bulb_temperature_2m_mean: str | None = None
    wet_bulb_temperature_2m_min: str | None = None
    wind_direction_100m_dominant: str | None = None
    wind_direction_10m_dominant: str | None = None
    wind_direction_200m_dominant: str | None = None
    wind_gusts_10m_max: str | None = None
    wind_gusts_10m_mean: str | None = None
    wind_gusts_10m_min: str | None = None
    wind_speed_100m_max: str | None = None
    wind_speed_100m_mean: str | None = None
    wind_speed_100m_min: str | None = None
    wind_speed_10m_max: str | None = None
    wind_speed_10m_mean: str | None = None
    wind_speed_10m_min: str | None = None
    wind_speed_200m_max: str | None = None
    wind_speed_200m_mean: str | None = None
    wind_speed_200m_min: str | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Drop the units of ensemble members and previous runs."""
        return _drop_suffixed(d)


@dataclass
class ForecastBase(DataClassORJSONMixin):
    """Weather forecast, of all models together or of a single model."""

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
    minutely_15_units: Minutely15ForecastUnits | None = None
    minutely_15: Minutely15Forecast | None = None


@dataclass
class Forecast(ForecastBase):
    """Weather forecast."""

    # Only set when multiple models were requested, keyed by the model name
    models: dict[str, ForecastBase] | None = None
