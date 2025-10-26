# Test Case Plan

*Note: This test case plan is based on the jobs-todo.csv file found in the docs/ai-reference directory.*

*This document is also available in [Chinese (中文)](test-case-plan-zh.md).*

This document outlines the test cases for the engine parameters validation framework. The tests are organized by parameter categories, based on the jobs-todo.csv file which contains a comprehensive list of parameters to be validated.

## 1. Quality Parameters

### 1.1 Layer Height Tests
- Test layer height parsing from G-code
- Validate layer height values match expected parameters (e.g., 0.24mm)
- Check layer height consistency across all layers
- Validation method: Analyze G-code based on `;LAYER_CHANGE` comments

### 1.2 Initial Layer Print Height Tests
- Test initial layer print height parsing from G-code
- Validate first layer height matches expected value (e.g., 0.28mm)
- Validation method: Analyze first `;LAYER_CHANGE` comment in G-code

### 1.3 Line Width Tests
- Test default line width (line_width) validation
  - Note: This is the default line width when other line width settings are set to 0
- Test initial layer line width validation
  - Validation method: Find first layer via `;LAYER_CHANGE`, calculate line width from "E X" extrusion values (rounded rectangle model)
  - Required parameters: Filament diameter, current layer height, extrusion length
- Test outer wall line width validation
  - Validation method: Find ";TYPE:OUTER WALL", calculate line width from "E X" extrusion values
  - Required parameters: Filament diameter, current layer height, extrusion length
- Test inner wall line width validation
  - Validation method: Find ";TYPE:INNER WALL", calculate line width from "E X" extrusion values
  - Required parameters: Filament diameter, current layer height, extrusion length
- Test top surface line width validation
  - Validation method: Find ";TYPE:Top surface", calculate line width from "E X" extrusion values
  - Required parameters: Filament diameter, current layer height, extrusion length
- Test sparse infill line width validation
  - Validation method: Find ";TYPE:Sparse infill", calculate line width from "E X" extrusion values
  - Required parameters: Filament diameter, current layer height, extrusion length
- Test internal solid infill line width validation
  - Validation method: Find ";TYPE:Internal solid infill", calculate line width from "E X" extrusion values
  - Required parameters: Filament diameter, current layer height, extrusion length
- Test support line width validation
  - Validation method: Find ";TYPE:Support", calculate line width from "E X" extrusion values
  - Required parameters: Filament diameter, current layer height, extrusion length

### 1.4 Seam Tests
- Test seam position (seam_position) validation
- Test staggered inner seams (staggered_inner_seams) validation
- Test seam gap (seam_gap) validation
- Test seam slope type (seam_slope_type) validation
- Test wipe speed validation with role-based wipe speed consideration
  - Special handling: If role_based_wipe_speed equals "1" in CONFIG_BLOCK, skip test and generate warning
  - If role_based_wipe_speed equals "0", find ";WIPE_START" and ";WIPE_END" for each layer, check "G1 V" commands, validate V/60 against expected values
- Test wipe on loops (wipe_on_loops) validation
- Test wipe before external loop (wipe_before_external_loop) validation

### 1.5 Precision Tests
- Test slice closing radius (slice_closing_radius) validation
- Test resolution (resolution) validation
- Test arc fitting (enable_arc_fitting) validation
- Test XY hole compensation (xy_hole_compensation) validation
- Test XY contour compensation (xy_contour_compensation) validation
- Test elephant foot compensation (elefant_foot_compensation) validation
  - Validation method: Use baseline cube G-code (without compensation) as reference, slice with expected compensation value, find first layer and all walls, compare contour shrinkage with expected value
- Test elephant foot compensation layers (elefant_foot_compensation_layers) validation
  - Special handling: Compensation has linear decreasing effect (e.g., elefant_foot_compensation=0.1mm affecting 5 layers results in [0.100, 0.080, 0.060, 0.040, 0.020] per layer)
- Test precise outer wall (precise_outer_wall) validation
- Test hole to polygon (hole_to_polygon) validation
- Test precise Z height (precise_z_height) validation

### 1.6 Ironing Type Tests
- Test ironing type (ironing_type) validation
  - Validation method: Check for ";TYPE:IRONING" in G-code to confirm ironing is enabled
  - TODO: Can ironing type be reverse-engineered from G-code movement instructions?

### 1.7 Wall Generator Tests
- Test wall generator (wall_generator) validation

### 1.8 Walls and Surfaces Tests
- Test wall sequence (wall_sequence) validation
  - Validation method: Check order of ";TYPE INNER WALL" and ";TYPE OUTER WALL" for each layer
  - Special considerations: 
    1. Don't start counting from first layer (it has fixed inner/outer order)
    2. Currently using cube model for validation
    3. Three G-code styles exist:
       a. inner wall/outer wall (default)
       b. outer wall/inner wall
       c. inner-outer-inner wall
- Test infill first (is_infill_first) validation
  - Validation method: Check if Sparse infill and Internal solid infill types appear before Inner wall and Outer wall types
- Test wall direction (wall_direction) validation
  - Validation method: Find contour points, use directed area calculation to determine cw/ccw direction
- Test top solid infill flow ratio (top_solid_infill_flow_ratio) validation
- Test bottom solid infill flow ratio (bottom_solod_infill_flow_ratio) validation
- Test only one wall top (only_one_wall_top) validation
  - Validation method: Find top surface via ";TYPE:Top surface", check if only one outer wall exists
  - Special marker: Look for "; printing object" and "EXCLUDE_OBJECT_START NAME=立方体_id_0_copy_0"
- Test minimum width top surface (min_width_top_surface) validation
- Test only one wall first layer (only_one_wall_first_layer) validation
  - Validation method: Find first layer walls, count wall layers
  - Counting rule: Wall layer count determined by whether start and end points of contour are within tolerance
- Test reduce crossing wall (reduce_crossing_wall) validation
- Test small area infill compensation (small_aera_infill_compensation) validation

### 1.9 Bridging Tests
- Test bridge flow (bridge_flow) validation
- Test internal bridge flow (internal_bridge_flow) validation
- Test bridge density (bridge_density) validation
- Test thick bridges (thick_bridges) validation
- Test thick internal bridges (thick_internal_bridges) validation
- Test don't filter internal bridges (dont_filter_internal_bridges) validation
- Test counterbore hole bridging (counterbore_hole_bridging) validation

### 1.10 Overhangs Tests
- Test detect overhang wall (detect_overhang_wall) validation
- Test make overhang printable (make_overhang_printable) validation
- Test extra perimeters on overhangs (extra_perimeters_on_overhangs) validation
- Test overhang reverse (overhang_reverse) validation
- Test overhang optimization (overhang_optimization) validation

## 2. Strength Parameters

### 2.1 Walls Tests
- Test wall loops (wall_loops) validation
  - Validation method: Count ";TYPE INNER WALL" and ";TYPE OUTER WALL" instructions
  - Special considerations:
    1. First layer wall print speed may differ from other layers
    2. Non-first layers may have different inner/outer wall speeds
- Test alternate extra wall (alternate_extra_wall) validation
- Test detect thin wall (detect_thin_wall) validation

### 2.2 Top/Bottom Shells Tests
- Test top surface pattern (top_surface_pattern) validation
- Test top shell layers (top_shell_layers) validation
  - Validation method: Count occurrences of Top Surface, Internal solid infill, and Internal Bridge extrusion types
  - Special considerations:
    1. Internal Bridge type may not exist if no sparse infill
    2. Currently using fixed models with these three types and single top surface
    3. Logic is intertwined with top shell thickness parameter
    4. TODO: Why doesn't sparse infill exist when layer count < 10?
- Test top shell thickness (top_shell_thickness) validation
- Test bottom surface pattern (bottom_surface_pattern) validation
- Test bottom shell layers (bottom_shell_layers) validation
  - Validation method: Find Bottom Surface, count Internal solid infill layers upward until Sparse infill type appears, record total Bottom Surface + Internal solid infill layers
- Test bottom shell thickness (bottom_shell_thickness) validation
- Test top bottom infill wall overlap (top_bottom_infill_wall_overlap) validation

### 2.3 Fill Tests
- Test sparse infill density (sparse_infill_density) validation
- Test AI infill (ai_infill) validation
- Test sparse infill pattern (sparse_infill_pattern) validation
- Test infill anchor (infill_anchor) validation
- Test infill anchor max (infill_anchor_max) validation
- Test internal solid infill pattern (internal_solid_infill_pattern) validation
- Test gap fill target (gap_fill_target) validation
- Test filter out gap fill (filter_out_gap_fill) validation
- Test infill wall overlap (infill_wall_overlap) validation
- Test external infill margin (external_infill_margin) validation

### 2.4 Advance Tests
- Test infill direction (infill_direction) validation
- Test solid infill direction (solid_infill_direction) validation
- Test rotate solid infill direction (rotate_solid_infill_direction) validation
- Test bridge angle (bridge_angle) validation
- Test minimum sparse infill area (minimum_sparse_infill_aera) validation
- Test infill combination (infill_combination) validation
- Test detect narrow internal solid infill (detect_narrow_internal_solid_infill) validation
- Test ensure vertical shell thickness (ensure_vertical_shell_thickness) validation

## 3. Special Mode Tests

### 3.1 Others Tests
- Test print sequence (print_sequence) validation
  - Validation method: Check layer data structure continuity
  - If data structure is not continuously increasing, it's per-object print mode
  - If continuous, it's per-layer print mode

## 4. Test Structure

Each test follows this structure:
1. Load 3MF model file with specific parameters
2. Slice and export G-code using the engine
3. Parse the generated G-code
4. Validate parameters against expected values

Test fixtures handle:
- Model loading
- Slicing and G-code generation
- Cleanup of temporary files

## 5. Test Data

Test data is organized in the `data/models` directory, with subdirectories for each parameter category:
- `quality/` - Models for quality parameter tests
- `strength/` - Models for strength parameter tests

Each model file is named to indicate the specific parameter being tested:
- Format: `{parameter_name}_{value}.{extension}`
- Examples: `layer_height_0.24mm.3mf`, `ironing_type_cube.3mf`

## 6. Test Execution

Tests are executed using pytest with the `engine_params` marker:
```
python -m pytest -m engine_params --slicer-exe="path/to/slicer/executable"
```

Additional command-line options:
- `--clean-gcode` - Automatically clean up generated G-code files
- `-v` - Verbose output for detailed test information

## 7. Expected Outcomes

Each test validates that:
- The slicer correctly interprets the input parameters
- The generated G-code contains the expected parameter values
- The parameter values fall within acceptable tolerance ranges
- Edge cases and boundary conditions are handled properly

## 8. Test Categories

Tests are categorized using pytest markers:
- `@pytest.mark.engine_params` - Main marker for all engine parameter tests
- Sub-markers for specific categories:
  - `quality` - Quality parameter tests
  - `strength` - Strength parameter tests
  - Parameter-specific markers (e.g., `layer_height`, `infill`)

## 9. Validation Methods

Based on the jobs-todo.csv file, validation methods include:
- 3MF slicing and G-code analysis
- Parsing G-code comments like `;LAYER_CHANGE`, `;TYPE:*`, `;WIPE_START`, `;WIPE_END`
- Calculating line widths from extrusion values using rounded rectangle models
- Checking for specific G-code commands
- Comparing layer structures and sequences
- Analyzing geometric properties
- Checking data structure continuity for print sequence detection

## 10. Special Considerations

- All parameters should have a CONFIG_BLOCK in the G-code
- Some parameters require special handling (e.g., role_based_wipe_speed)
- First layer behavior may differ from other layers
- Some tests may require specific model geometries (e.g., rounded rectangle for line width calculations)
- Warning messages should be generated for incompatible test configurations
- Some parameters have complex interactions with others (e.g., top shell layers and top shell thickness)
- Special validation rules exist for certain parameters (e.g., elephant foot compensation layers have linear decreasing effect)