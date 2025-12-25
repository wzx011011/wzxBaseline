"""
Filament parameter validation modules.

Submodules:
- advanced: 3 parameters (G-code, notes)
- cooling: 22 parameters (fan control, cooling)
- filament_basic: 19 parameters (basic info, properties)
- filament_temperature: 20 parameters (temperatures, bed temps)
- multimaterial: 14 parameters (toolchange, wipe tower)
- setting_overrides: 16 parameters (retraction overrides)

Total: 94 parameters
"""

# Import all submodules for backward compatibility
from .advanced import *
from .cooling import *
from .filament_basic import *
from .filament_temperature import *
from .multimaterial import *
from .setting_overrides import *
