"""
擦拭塔 GCode 行为测试用例

测试擦拭塔生成的 GCode 中的动作序列、路径逻辑等行为
覆盖 TC-WT-001 ~ TC-WT-027 测试用例
"""
from __future__ import annotations
from pathlib import Path
import pytest

from engine_params.src.gcode.process.filament.prime_tower_gcode_check import (
    parse_tc_wt_001,
)
from engine_params.src.gcode.process.filament.prime_tower_gcode_check_wt007 import (
    parse_tc_wt_007,
)


# ============================================================
# TC-WT-001: 打完模型去擦拭塔前的抬升逻辑
# ============================================================

@pytest.mark.engine_params
def test_tc_wt_001(
    slice_and_export: Path,
    expected_value: str,
) -> None:
    """
    TC-WT-001: 验证从模型到擦拭塔的抬升逻辑
    
    Bug覆盖: 10735, 11182, 11193, 11320, 13826
    校验级别: L1 (TYPE标记 + 基本序列验证)
    
    校验点:
    1. 打完模型后应先回抽
    2. 回抽后应抬升Z（高度符合配置）
    3. 抬升后空走到擦拭塔
    
    注: z_hop_type参数仅作记录，不做L2级别的GCode指令细节校验
        (关注是否抬升、抬升高度，不区分Normal/Slope等抬升方式的实现细节)
    
    测试用例配置示例:
    {
      "cases": [
        {
          "project_name": "tc_wt_001_normal_0.5mm",
          "input_3mf": "tc_wt_001_normal_0.5mm.3mf",
          "expected_value": {
            "z_hop": 0.5,
            "z_hop_type": "Normal Lift"
          }
        }
      ]
    }
    """
    gcode_path = slice_and_export
    assert gcode_path.exists(), f"GCode 文件不存在: {gcode_path}"
    
    ok, actual, details = parse_tc_wt_001(
        gcode_path,
        expected_value
    )
    
    # 打印详细信息
    print(f"\n=== TC-WT-001: 打完模型去擦拭塔前的抬升逻辑 ===")
    print(f"  GCode文件: {gcode_path.name}")
    print(f"  期望配置: {expected_value}")
    print(f"  找到转换点: {details.get('count', 0)} 个")
    
    if ok:
        print(f"  抬升高度: {details.get('z_hop')}mm")
        print(f"  抬升方式: {details.get('z_hop_type')}")
        print(f"  结果: [PASS]")
    else:
        print(f"  失败原因:")
        for failure in details.get('failures', []):
            print(f"    - {failure}")
        print(f"  结果: [FAIL]")
    
    print("=" * 60)
    
    assert ok, f"TC-WT-001 校验失败: {details}"


# ============================================================
# TC-WT-007: �س�����װ��������
# ============================================================

@pytest.mark.engine_params
def test_tc_wt_007(
    slice_and_export: Path,
    expected_value: str,
) -> None:
    '''
    TC-WT-007: ��֤��ͬ�Ĳ����͵Ļس�/װ����
    
    Bug����: 11460, 11462, 11463, 13303, 13309, 13379, 13534, 13537, 13555
    У�鼶��: L2 (������֤ + ����׷��)
    
    У���:
    1. ����ǰ�Ļس�ʹ��from_tool����
    2. ���Ϻ��װ��ʹ��to_tool����
    3. װ���� = �س��� + extra����
    
    ������������ʾ��:
    {
      "cases": [
        {
          "project_name": "tc_wt_007_pla_tpu",
          "input_3mf": "tc_wt_007_pla_tpu.3mf",
          "expected_value": {
            "tool_params": {
              "T0": {"retraction_length": 5.0, "extra": 0.0},
              "T1": {"retraction_length": 8.0, "extra": 0.5}
            },
            "from_tool": "T0",
            "to_tool": "T1",
            "check_points": ["before_change", "after_change"]
          }
        }
      ]
    }
    '''
    gcode_path = slice_and_export
    assert gcode_path.exists(), f'GCode �ļ�������: {gcode_path}'
    
    ok, actual, details = parse_tc_wt_007(
        gcode_path,
        expected_value
    )
    
    # ��ӡ��ϸ��Ϣ
    print(f'\n=== TC-WT-007: �س�����װ�������� ===')
    print(f'  GCode�ļ�: {gcode_path.name}')
    print(f'  ��������: {expected_value}')
    print(f'  ���ϵ�����: {details.get('tool_change_count', 0)} ��')
    print(f'  ������: {details.get('checked_count', 0)}')
    
    if ok:
        print(f'  换料方向: {details.get('from_tool')}  {details.get('to_tool')}')
        print(f'  结果: [PASS]')
    else:
        print(f'  失败原因:')
        for failure in details.get('failures', []):
            print(f'    - {failure}')
        print(f'  结果: [FAIL]')
    
    print('=' * 60)
    
    assert ok, f'TC-WT-007 У��ʧ��: {details}'
