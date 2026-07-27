#!/usr/bin/env python3
"""
Phase 1.5: 证据可行性快速检查

在正式进入 Phase 2 调研前，用 5 分钟快速验证主题能否找到 L1-L4 证据。
避免调研完才发现找不到权威数据、真实案例。
"""

import sys
import re
from pathlib import Path

def check_feasibility(book_dir: Path) -> dict:
    """快速检查证据可行性"""

    brief_path = book_dir / "BOOK_BRIEF.md"
    if not brief_path.exists():
        return {"error": "BOOK_BRIEF.md 不存在"}

    brief_content = brief_path.read_text(encoding="utf-8")

    # 提取关键信息
    report = {
        "status": "feasible",
        "warnings": [],
        "recommendations": []
    }

    # 检查是否有明确的主题和读者，兼容当前 H1 + 独立读者文件模板。
    title_match = re.search(r"(?m)^#\s+(.+)$", brief_content)
    if not title_match or "待填写" in title_match.group(1):
        report["warnings"].append("缺少明确主题定义")

    reader_path = book_dir / "READER_PROFILE.md"
    reader_text = reader_path.read_text(encoding="utf-8") if reader_path.exists() else ""
    if not reader_text or "待填写" in reader_text:
        report["warnings"].append("缺少读者画像")

    # 检查是否有 content_profile
    profile_match = re.search(r"(?ms)^## Content Profile\s*\n+([^\n]+)", brief_content)
    if not profile_match or "待填写" in profile_match.group(1):
        report["warnings"].append("缺少 content_profile，无法判断证据门槛")

    # 建议快速验证步骤
    report["recommendations"] = [
        "用 web-access 搜索主题关键词，验证是否有权威报告、行业数据（L1-fact）",
        "用 xhs-research.py 搜索主题，验证是否有真实用户讨论（L2-demand）",
        "搜索「主题 + 招聘」「主题 + 活动」，验证是否有行为信号（L3-behavior）",
        "搜索「主题 + 定价」「主题 + 产品」，验证是否有交易信号（L4-transaction）"
    ]

    if len(report["warnings"]) > 2:
        report["status"] = "risky"

    return report

def main():
    if len(sys.argv) < 2:
        print("用法: python3 check-evidence-feasibility.py <book_dir>")
        sys.exit(1)

    book_dir = Path(sys.argv[1])
    result = check_feasibility(book_dir)

    # 输出报告
    report_path = book_dir / "evidence-feasibility-report.md"

    content = f"""# 证据可行性快速检查报告

**状态**: {result['status']}

## 警告

"""

    if result.get("warnings"):
        for w in result["warnings"]:
            content += f"- ⚠️ {w}\n"
    else:
        content += "- ✅ 无明显风险\n"

    content += "\n## 建议验证步骤\n\n"
    for r in result["recommendations"]:
        content += f"- [ ] {r}\n"

    content += """
## 下一步

如果上述验证步骤都能找到结果，可以进入 Phase 2 正式调研。
如果 L1-L4 中有 2 层以上找不到证据，建议重新评估主题可行性。
"""

    report_path.write_text(content, encoding="utf-8")
    print(f"✅ 报告已生成: {report_path}")
    print(f"状态: {result['status']}")

if __name__ == "__main__":
    main()
