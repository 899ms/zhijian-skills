#!/usr/bin/env python3
"""
Phase 5: 后台语言检测

扫描正文中的后台术语，确保证据已翻译成读者语言。
"""

import sys
import re
from pathlib import Path

# 后台术语清单
BACKEND_TERMS = [
    # 证据层级术语
    r'L[1-6]-\w+',
    r'证据层级',

    # 调研工具术语
    r'小红书评论',
    r'小红书笔记',
    r'公众号文章',
    r'公众号元数据',
    r'xhs-research',
    r'wxmp-cracker',

    # 后台流程术语
    r'根据调研',
    r'样本显示',
    r'数据来源',
    r'需求侧样本',
    r'线索',
    r'文章池',
    r'抓取结果',

    # 账本术语
    r'CLAIM_LEDGER',
    r'CASE_LIBRARY',
    r'BEHAVIOR_LEDGER',
    r'TRANSACTION_LEDGER',
]

def check_backend_language(book_md: Path) -> list:
    """检测后台语言"""

    if not book_md.exists():
        return [{"error": f"文件不存在: {book_md}"}]

    content = book_md.read_text(encoding="utf-8")
    lines = content.split('\n')

    issues = []

    for i, line in enumerate(lines, 1):
        for pattern in BACKEND_TERMS:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "line": i,
                    "term": match.group(),
                    "context": line.strip()[:80]
                })

    return issues

def main():
    if len(sys.argv) < 2:
        print("用法: python3 check-backend-language.py <book.md>")
        sys.exit(1)

    book_md = Path(sys.argv[1])
    issues = check_backend_language(book_md)

    if not issues:
        print("✅ 未检测到后台语言")
        sys.exit(0)

    print(f"⚠️  检测到 {len(issues)} 处后台语言：\n")

    for issue in issues:
        if "error" in issue:
            print(f"错误: {issue['error']}")
            continue

        print(f"第 {issue['line']} 行: {issue['term']}")
        print(f"  上下文: {issue['context']}")
        print()

    print("建议：将后台术语翻译成读者可理解的具体来源、场景或判断。")
    sys.exit(1)

if __name__ == "__main__":
    main()
