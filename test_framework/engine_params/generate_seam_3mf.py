"""
自动生成 Seam（接缝）参数的 3MF 文件

从模板 3MF 文件复制生成不同参数配置的测试文件。
注意：复制的 3MF 文件需要手动在 CrealityPrint 中打开并设置对应参数后重新保存。
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def _slug(s: str) -> str:
    """将参数值转换为文件名安全的字符串"""
    s = str(s)
    s = s.replace("%", "pct")
    s = s.replace(",", "_")
    s = s.replace("(", "_").replace(")", "")
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "value"


def _write_json(path: Path, data: dict) -> None:
    """写入 JSON 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    # 获取仓库根目录 (engine_params 目录)
    repo_root = Path(__file__).resolve().parent
    
    # 模板 3MF 文件路径
    template_3mf = repo_root / "data" / "models" / "template_model.3mf"
    if not template_3mf.exists():
        # 尝试 test_framework 目录下的模板
        template_3mf = repo_root.parent / "template_model.3mf"
    if not template_3mf.exists():
        print(f"[ERROR] Template 3MF not found: {template_3mf}")
        print("[INFO] Please ensure template_model.3mf exists in data/models/ or test_framework/")
        return 1
    
    print(f"[INFO] Using template: {template_3mf}")
    
    # JSON 和模型输出目录
    json_root = repo_root / "data" / "case_input" / "process" / "quality" / "seam"
    models_root = repo_root / "data" / "models" / "process" / "quality" / "seam"
    
    # Seam 参数配置
    # 参数名 -> 期望值列表
    params: dict[str, list[str | int | float]] = {
        # 接缝位置 (aligned/nearest/random/back)
        "seam_position": ["aligned", "nearest", "random"],
        
        # 接缝间隙 (0, 15%)
        "seam_gap": [0, 0.15],
        
        # 交错内墙接缝 (false/true)
        "staggered_inner_seams": [False, True],
        
        # 接缝斜坡类型 (none/linear/cubic)
        "seam_slope_type": ["none", "linear"],
        
        # 斜接流量比 (0.8, 1.0, 1.2)
        "scarf_joint_flow_ratio": [0.8, 1.0, 1.2],
    }
    
    total_files = 0
    created_files = 0
    
    for param, values in params.items():
        cases = []
        model_dir = models_root / param
        model_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[{param}] Generating {len(values)} test files...")
        
        for v in values:
            # 生成文件名
            slug = _slug(str(v))
            input_3mf = f"{param}_{slug}.3mf"
            dst = model_dir / input_3mf
            
            # 复制模板文件
            if not dst.exists():
                shutil.copy2(template_3mf, dst)
                print(f"  ✓ Created: {input_3mf}")
                created_files += 1
            else:
                print(f"  - Exists: {input_3mf}")
            
            total_files += 1
            
            # 构造 JSON case 条目
            case_data = {
                "project_name": f"{param}_{slug}",
                "input_3mf": input_3mf,
            }
            
            # 根据参数类型添加期望值字段
            if param == "seam_position":
                case_data["expected_seam_position"] = v
            elif param == "seam_gap":
                case_data["expected_seam_gap"] = float(v)
            elif param == "staggered_inner_seams":
                case_data["expected_staggered"] = bool(v)
            elif param == "seam_slope_type":
                case_data["expected_slope_type"] = v
            elif param == "scarf_joint_flow_ratio":
                case_data["expected_flow_ratio"] = float(v)
            
            cases.append(case_data)
        
        # 写入 JSON 配置文件
        json_file = json_root / f"{param}.json"
        _write_json(json_file, {"cases": cases})
        print(f"  ✓ JSON: {json_file.relative_to(repo_root)}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  - Total files: {total_files}")
    print(f"  - Created: {created_files}")
    print(f"  - Already existed: {total_files - created_files}")
    print(f"{'='*60}")
    
    if created_files > 0:
        print(f"\n⚠️  IMPORTANT: Next Steps")
        print(f"{'='*60}")
        print(f"The 3MF files have been created from the template, but you need to:")
        print(f"")
        print(f"1. Open each 3MF file in CrealityPrint")
        print(f"2. Go to Process → Quality → Seam")
        print(f"3. Set the corresponding parameter value:")
        print(f"   - seam_position_aligned.3mf → seam_position = aligned")
        print(f"   - seam_gap_0.3mf → seam_gap = 0")
        print(f"   - staggered_inner_seams_False.3mf → staggered_inner_seams = false")
        print(f"   - etc.")
        print(f"4. Save the project (File → Save)")
        print(f"")
        print(f"Directory: {models_root.relative_to(repo_root)}")
        print(f"{'='*60}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
