"""
验证脚本：检查所有修复是否生效
Verify Script: Check if all fixes are working
"""
import json
from pathlib import Path


def check_config_files():
    """检查配置文件是否正确 / Check if config files are correct"""
    print("\n" + "="*70)
    print("检查配置文件 / Checking Configuration Files")
    print("="*70)

    config_files = [
        "configs/report_config.json",
        "configs/report_config_with_testcases.json"
    ]

    for config_file in config_files:
        config_path = Path(__file__).parent / config_file
        if not config_path.exists():
            print(f"❌ 配置文件不存在 / Config file not found: {config_file}")
            continue

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 检查是否有测试用例映射配置
        # Check if there is test case mapping configuration
        if "测试用例 TestCases" in config.get("mappings", {}):
            tc_config = config["mappings"]["测试用例 TestCases"]

            # 检查必需的字段
            # Check required fields
            required_fields = ["type", "name_column", "result_column", "docstring_column", "result_mappings"]
            all_present = all(field in tc_config for field in required_fields)

            if all_present:
                print(f"✅ {config_file}: 测试用例映射配置完整 / Test case mapping config complete")
                print(f"   - name_column: {tc_config['name_column']}")
                print(f"   - result_column: {tc_config['result_column']}")
                print(f"   - docstring_column: {tc_config['docstring_column']}")
            else:
                print(f"❌ {config_file}: 测试用例映射配置不完整 / Test case mapping config incomplete")
                missing = [f for f in required_fields if f not in tc_config]
                print(f"   缺少字段 / Missing fields: {missing}")
        else:
            print(f"❌ {config_file}: 缺少测试用例映射配置 / Missing test case mapping config")

        # 检查测试详情是否使用中文名
        # Check if test details uses Chinese names
        if "测试详情 TestDetails" in config.get("mappings", {}):
            td_config = config["mappings"]["测试详情 TestDetails"]
            test_name_config = td_config.get("columns", {}).get("测试名称 / Test Name", {})

            if test_name_config.get("source") == "chinese_name":
                fallback = test_name_config.get("fallback", "N/A")
                print(f"✅ {config_file}: 测试详情使用中文名 / Test details uses Chinese names")
                print(f"   - source: {test_name_config.get('source')}")
                print(f"   - fallback: {fallback}")
            else:
                print(f"❌ {config_file}: 测试详情未使用中文名 / Test details doesn't use Chinese names")


def check_template():
    """检查Excel模板是否存在 / Check if Excel template exists"""
    print("\n" + "="*70)
    print("检查Excel模板 / Checking Excel Template")
    print("="*70)

    template_path = Path(__file__).parent / "templates" / "test_report_template.xlsx"

    if template_path.exists():
        print(f"✅ Excel模板存在 / Excel template exists: {template_path}")
        print(f"   文件大小 / File size: {template_path.stat().st_size / 1024:.2f} KB")
    else:
        print(f"❌ Excel模板不存在 / Excel template not found: {template_path}")
        print("   请运行: python scripts/create_template.py")
        print("   Please run: python scripts/create_template.py")


def check_codebase():
    """检查代码库是否包含正确的功能 / Check if codebase has correct features"""
    print("\n" + "="*70)
    print("检查代码库 / Checking Codebase")
    print("="*70)

    # 检查template_based_report.py是否包含所需方法
    # Check if template_based_report.py contains required methods
    report_file = Path(__file__).parent / "src" / "template_based_report.py"
    if report_file.exists():
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

        required_methods = [
            "_create_default_testcase_mapping_sheet",
            "_fill_testcase_mapping_sheet"
        ]

        for method in required_methods:
            if f"def {method}" in content:
                print(f"✅ {method} 方法存在 / method exists")
            else:
                print(f"❌ {method} 方法不存在 / method not found")

        # 检查是否支持fallback
        # Check if fallback is supported
        if "fallback = col_config.get('fallback')" in content:
            print("✅ 支持 fallback 字段 / Supports fallback field")
        else:
            print("❌ 不支持 fallback 字段 / Doesn't support fallback field")
    else:
        print(f"❌ 文件不存在 / File not found: {report_file}")

    # 检查conftest.py是否正确提取docstring
    # Check if conftest.py correctly extracts docstring
    conftest_file = Path(__file__).parent / "tests" / "conftest.py"
    if conftest_file.exists():
        with open(conftest_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "docstring = test_node.obj.__doc__.strip()" in content:
            print("✅ conftest.py 正确提取 docstring / conftest.py correctly extracts docstring")
        else:
            print("❌ conftest.py 未正确提取 docstring / conftest.py doesn't correctly extract docstring")
    else:
        print(f"❌ 文件不存在 / File not found: {conftest_file}")


def print_next_steps():
    """打印下一步操作 / Print next steps"""
    print("\n" + "="*70)
    print("下一步操作 / Next Steps")
    print("="*70)
    print("""
1. 运行测试 / Run tests:
   pytest tests/example_testcase_mapping.py -v

2. 查看生成的报告 / View generated report:
   打开 reports/test_report_YYYYMMDD_HHMMSS.xlsx
   Open reports/test_report_YYYYMMDD_HHMMSS.xlsx

3. 检查以下内容 / Check the following:
   - "测试详情 TestDetails"工作表的B列是否显示中文名
   - "测试用例 TestCases"工作表的D列和E列是否已填充
   - Check if column B in "测试详情 TestDetails" worksheet shows Chinese names
   - Check if columns D and E in "测试用例 TestCases" worksheet are filled

4. 如果有问题，查看文档 / If issues, check documentation:
   - 问题修复说明.md
   - 测试用例映射详细说明.md
    """)


def main():
    """主函数 / Main function"""
    print("\n" + "="*70)
    print("pytest-learn-multi-test-categories 功能验证 / pytest-learn-multi-test-categories Feature Verification")
    print("="*70)

    check_config_files()
    check_template()
    check_codebase()
    print_next_steps()

    print("\n" + "="*70)
    print("验证完成 / Verification Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
    main()
