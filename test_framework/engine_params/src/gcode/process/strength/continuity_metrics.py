"""Retraction event metrics, independent of wipe segmentation and E mode."""

import re

from engine_params.src.gcode.process.quality.behavior import BehaviorGCode


def first_block_metrics(gcode_path, lines, start, end):
    behavior = BehaviorGCode(gcode_path)
    retracted = 0.0
    events, commands, positive, printing = 0, 0, 0, 0
    event_lines = []
    for move in behavior.moves:
        if move.line_no > end:
            break
        in_block = start < move.line_no <= end
        if move.e < -1e-9:
            if in_block:
                commands += 1
                if retracted <= 1e-4:
                    events += 1
                    event_lines.append(move.line_no)
            retracted -= move.e
        elif move.e > 1e-9:
            # The slicer splits one retract among pre-wipe, wipe segments and
            # post-wipe commands. End it only after the filament is restored.
            retracted = max(0.0, retracted - move.e)
            if in_block:
                positive += 1
                printing += move.is_extrusion
    block = lines[start:end]
    z_hops = 0
    for raw in block:
        body = raw.split(";", 1)[0].strip()
        if re.match(r"^G[01](?:\s|$)", body, re.I):
            axes = set(re.findall(r"\b([XYZE])(?=[-+.\d])", body.upper()))
            z_hops += {"X", "Y", "Z"} <= axes and "E" not in axes
    return {
        "block_lines": len(block), "retractions": events,
        "wipe_sections": sum(line.strip().upper() == ";WIPE_START" for line in block),
        "z_hop_travels": z_hops, "positive_extrusions": positive,
        "printing_moves": printing, "retraction_commands": commands,
    }, event_lines
