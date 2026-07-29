from engine_params.scripts.design_quality_l1_models import mark_process_overrides


def test_mark_process_overrides_preserves_slots_and_registers_dependencies():
    settings = {
        "different_settings_to_system": ["ironing_flow", "filament_flow_ratio", ""],
    }

    mark_process_overrides(settings, ["ironing_flow", "ironing_type", "top_shell_layers"])

    assert settings["different_settings_to_system"] == [
        "ironing_flow;ironing_type;top_shell_layers",
        "filament_flow_ratio",
        "",
    ]


def test_mark_process_overrides_initializes_missing_slots():
    settings = {}

    mark_process_overrides(settings, ["wall_generator", "wall_loops"])

    assert settings["different_settings_to_system"] == [
        "wall_generator;wall_loops",
        "",
        "",
    ]
