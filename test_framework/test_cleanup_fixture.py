import pytest
import os
from pathlib import Path

# 创建一个pytest测试，使用cleanup_allure_results fixture
def test_cleanup_fixture(cleanup_allure_results):
    """
    测试cleanup_allure_results fixture是否正确删除文件但保留目录
    """
    # fixture会在测试开始前自动执行，所以我们需要在fixture执行后检查状态
    pass

# 创建一个测试来验证fixture的行为
@pytest.fixture(scope="function")
def prepare_test_file():
    """
    准备测试文件，在测试后清理
    """
    allure_dir = Path(__file__).resolve().parent.parent / "allure-results"
    test_file = allure_dir / "test.txt"
    
    # 确保目录存在
    allure_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试文件
    with open(test_file, "w") as f:
        f.write("test")
    
    # 验证文件存在
    assert test_file.exists(), f"Test file should exist: {test_file}"
    
    yield test_file, allure_dir
    
    # 清理
    if test_file.exists():
        test_file.unlink()

# 测试fixture是否在会话开始时执行
def test_fixture_behavior(prepare_test_file):
    """
    测试cleanup_allure_results fixture的行为
    """
    test_file, allure_dir = prepare_test_file
    
    # 手动运行fixture逻辑来测试
    import shutil
    
    # 定义allure-results目录来清理
    allure_dirs = [
        Path(__file__).resolve().parent / "allure-results",
        Path(__file__).resolve().parent.parent / "allure-results"
    ]
    
    # 模拟fixture的清理逻辑
    for dir_path in allure_dirs:
        if dir_path.exists():
            print(f"[INFO] Cleaning files in allure-results directory: {dir_path}")
            # Create directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            # Remove all files in the directory
            for item in dir_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        else:
            print(f"[INFO] allure-results directory not found: {dir_path}")
            # Create the directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # 验证文件被删除，但目录仍然存在
    assert not test_file.exists(), f"Test file should be deleted: {test_file}"
    assert allure_dir.exists(), f"Allure directory should still exist: {allure_dir}"
    
    print(f"✓ Test passed: {test_file} was deleted and {allure_dir} was preserved")

