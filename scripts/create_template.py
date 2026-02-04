"""
Excel模板生成脚本 / Excel Template Generator Script

运行此脚本生成默认的Excel报告模板
Run this script to generate default Excel report template
"""
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.common.template_based_report import TemplateBasedReportGenerator


def main():
    """生成Excel模板 / Generate Excel template"""
    config_path = project_root / "configs" / "report_config.json"

    print("="*70)
    print("Excel模板生成器 / Excel Template Generator")
    print("="*70)

    # 创建生成器实例 / Create generator instance
    generator = TemplateBasedReportGenerator(config_path)

    # 检查模板是否存在 / Check if template exists
    if generator.template_path.exists():
        print(f"\n✓ 模板已存在: {generator.template_path}")
        choice = input("是否重新生成？(y/n): ").strip().lower()
        if choice != 'y':
            print("操作取消 / Operation cancelled")
            return

    # 创建模板 / Create template
    print(f"\n正在生成模板: {generator.template_path}")
    generator._create_default_template()

    print(f"\n✓ 模板生成成功！/ Template generated successfully!")
    print(f"  模板路径 / Template Path: {generator.template_path}")
    print(f"  配置文件 / Config File: {config_path}")
    print(f"\n提示 / Tip:")
    print(f"  - 可以直接编辑Excel模板来自定义样式和布局")
    print(f"  - 通过修改 report_config.json 来调整数据映射")
    print(f"  - 模板文件路径: {generator.template_path}")
    print("="*70)


if __name__ == "__main__":
    main()
