"""
演示脚本：展示如何使用pytest-viu-design框架
Demo Script: How to use the pytest-viu-design framework
"""
import os
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """运行命令并显示结果 / Run command and show results"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"命令 / Command: {cmd}")
    print(f"{'-'*70}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print("错误 / Error:", result.stderr)
    return result.returncode == 0


def main():
    """主函数 / Main function"""
    project_root = Path(__file__).parent

    print("\n" + "="*70)
    print("Pytest-VIU-Design 框架演示 / Pytest-VIU-Design Framework Demo")
    print("="*70)

    # 步骤1：检查依赖 / Step 1: Check dependencies
    print(f"\n当前目录 / Current directory: {project_root}")
    print("\n步骤1：检查Python环境 / Step 1: Check Python environment")
    run_command("python --version", "检查Python版本 / Check Python version")
    run_command("pytest --version", "检查Pytest版本 / Check Pytest version")

    # 步骤2：生成Excel模板 / Step 2: Generate Excel template
    print("\n\n步骤2：生成Excel模板 / Step 2: Generate Excel Template")
    success = run_command(
        f'cd "{project_root}" && python scripts/create_template.py',
        "生成测试报告模板 / Generate test report template"
    )

    if not success:
        print("\n❌ 模板生成失败！/ Template generation failed!")
        return

    template_path = project_root / "templates" / "test_report_template.xlsx"
    if template_path.exists():
        print(f"\n✅ 模板已生成 / Template generated: {template_path}")
    else:
        print(f"\n❌ 模板文件不存在 / Template file not found: {template_path}")

    # 步骤3：运行示例测试 / Step 3: Run example tests
    print("\n\n步骤3：运行示例测试 / Step 3: Run Example Tests")
    print("\n说明 / Explanation:")
    print("- 测试文件 / Test file: tests/example_testcase_mapping.py")
    print("- 包含示例 / Contains: Flash, Interface, Function, Performance tests")
    print("- 使用中文名映射 / Uses: Chinese name mapping\n")

    success = run_command(
        f'cd "{project_root}" && pytest tests/example_testcase_mapping.py -v',
        "运行示例测试 / Run example tests"
    )

    # 步骤4：查看生成的报告 / Step 4: View generated reports
    print("\n\n步骤4：查看生成的报告 / Step 4: View Generated Reports")
    reports_dir = project_root / "reports"

    if reports_dir.exists():
        reports = list(reports_dir.glob("test_report_*.xlsx"))
        reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if reports:
            latest_report = reports[0]
            print(f"\n✅ 最新报告 / Latest report: {latest_report.name}")
            print(f"   路径 / Path: {latest_report}")
            print(f"   大小 / Size: {latest_report.stat().st_size / 1024:.2f} KB")
            print(f"\n所有报告 / All reports ({len(reports)}):")
            for i, report in enumerate(reports[:5], 1):
                print(f"   {i}. {report.name}")
        else:
            print("\n❌ 没有找到报告文件 / No report files found")
    else:
        print("\n❌ 报告目录不存在 / Reports directory does not exist")

    # 步骤5：显示使用说明 / Step 5: Show usage instructions
    print("\n\n步骤5：如何使用 / Step 5: How to Use")
    print("\n创建你自己的测试 / Create your own tests:")
    print("""
# 1. 在tests/目录下创建测试文件
# 1. Create test file in tests/ directory

import pytest

# Flash测试 / Flash test
@pytest.mark.flash
@pytest.mark.chinese_name("我的测试")
def test_my_flash():
    \"\"\"我的测试\"\"\"
    assert True

# Interface测试 / Interface test
@pytest.mark.interface
def test_api_login():
    \"\"\"API登录测试\"\"\"
    assert True

# 2. 在Excel模板的"测试用例 TestCases"工作表中填入中文名
# 2. Fill in Chinese names in "测试用例 TestCases" sheet of Excel template

# 3. 运行测试
# 3. Run tests
# pytest tests/your_test_file.py -v

# 4. 查看报告
# 4. View reports
# 报告在 reports/test_report_YYYYMMDD_HHMMSS.xlsx
    """)

    print("\n\n测试依赖规则 / Test Dependency Rules:")
    print("  Flash → Interface → Function → Performance")
    print("  上一个阶段的测试全部通过后，下一个阶段的测试才会运行")
    print("  Tests in the next phase run only after all tests in the previous phase pass")

    print("\n\n" + "="*70)
    print("演示完成！/ Demo Complete!")
    print("="*70)
    print("\n下一步 / Next Steps:")
    print("1. 打开 templates/test_report_template.xlsx 编辑模板")
    print("2. 创建你的测试文件 tests/your_tests.py")
    print("3. 运行 pytest tests/your_tests.py -v")
    print("4. 查看 reports/ 目录下的Excel报告")
    print("\n详细文档 / Detailed docs:")
    print("- 快速开始 / Quick Start: 快速开始.md")
    print("- 使用指南 / Usage Guide: 使用指南.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
