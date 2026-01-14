"""Filament parameters validation functions."""

# Basic information group
from .basic_information_check import (
    parse_filament_type,
    parse_filament_colour,
    parse_filament_diameter,
    parse_filament_density,
    parse_filament_vendor,
    parse_filament_cost,
    parse_default_filament_colour,
    parse_compatible_printers,
    parse_compatible_printers_condition,
    parse_compatible_prints,
    parse_compatible_prints_condition,
    parse_inherits,
    parse_start_filament_gcode,
    parse_end_filament_gcode,
    parse_compatible_machine,
    parse_compatible_machine_condition,
    parse_filament_notes,
    parse_pressure_advance,
    parse_filament_toolchange_delay,
)

# Chamber temperature group  
from .chamber_temperature_check import (
    parse_chamber_temperature,
    parse_activate_chamber_temp_control,
    parse_activate_chamber_layer,
)

# Print temperature group
from .print_temperature_check import (
    parse_nozzle_temperature_initial_layer,
    parse_nozzle_temperature,
    parse_material_flow_dependent_temperature,
    parse_material_flow_temp_graph,
)

# Bed temperature group
from .bed_temperature_check import (
    parse_cool_plate_temp_initial_layer,
    parse_cool_plate_temp,
    parse_eng_plate_temp_initial_layer,
    parse_eng_plate_temp,
    parse_hot_plate_temp_initial_layer,
    parse_hot_plate_temp,
    parse_textured_plate_temp_initial_layer,
    parse_textured_plate_temp,
    parse_customized_plate_temp_initial_layer,
    parse_customized_plate_temp,
    parse_epoxy_resin_plate_temp_initial_layer,
    parse_epoxy_resin_plate_temp,
)

# Volumetric speed group
from .volumetric_speed_check import (
    parse_filament_max_volumetric_speed,
)

__all__ = [
    # Basic information (19 parameters)
    "parse_filament_type",
    "parse_filament_colour", 
    "parse_filament_diameter",
    "parse_filament_density",
    "parse_filament_vendor",
    "parse_filament_cost",
    "parse_default_filament_colour",
    "parse_compatible_printers",
    "parse_compatible_printers_condition",
    "parse_compatible_prints",
    "parse_compatible_prints_condition",
    "parse_inherits",
    "parse_start_filament_gcode",
    "parse_end_filament_gcode",
    "parse_compatible_machine",
    "parse_compatible_machine_condition",
    "parse_filament_notes",
    "parse_pressure_advance",
    "parse_filament_toolchange_delay",
    
    # Chamber temperature (3 parameters)
    "parse_chamber_temperature",
    "parse_activate_chamber_temp_control",
    "parse_activate_chamber_layer",
    
    # Print temperature (4 parameters)
    "parse_nozzle_temperature_initial_layer",
    "parse_nozzle_temperature",
    "parse_material_flow_dependent_temperature",
    "parse_material_flow_temp_graph",
    
    # Bed temperature (12 parameters)
    "parse_cool_plate_temp_initial_layer",
    "parse_cool_plate_temp",
    "parse_eng_plate_temp_initial_layer",
    "parse_eng_plate_temp",
    "parse_hot_plate_temp_initial_layer",
    "parse_hot_plate_temp",
    "parse_textured_plate_temp_initial_layer",
    "parse_textured_plate_temp",
    "parse_customized_plate_temp_initial_layer",
    "parse_customized_plate_temp",
    "parse_epoxy_resin_plate_temp_initial_layer",
    "parse_epoxy_resin_plate_temp",
    
    # Volumetric speed (1 parameter)
    "parse_filament_max_volumetric_speed",
]
