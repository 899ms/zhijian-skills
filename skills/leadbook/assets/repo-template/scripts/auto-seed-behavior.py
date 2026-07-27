#!/usr/bin/env python3
"""
Phase 2: 行为层自动推导

从 BOOK_BRIEF.md 自动提取行业、角色、痛点关键词，生成 BEHAVIOR_SEED_PLAN.md。
"""

import sys
import re
from pathlib import Path

def extract_keywords(brief_path: Path) -> dict:
    """从 BOOK_BRIEF.md 提取关键词"""

    if not brief_path.exists():
        return {"error": "BOOK_BRIEF.md 不存在"}

    content = brief_path.read_text(encoding="utf-8")

    keywords = {
        "industry": [],
        "roles": [],
        "pain_points": []
    }

    # 从标题与正文提取常见行业词；不依赖某一种固定标题模板。
    industry_patterns = [
        r'AI', r'人工智能', r'企业', r'中小企业', r'个人IP', r'内容',
        r'营销', r'运营', r'产品', r'技术', r'商业'
    ]
    for pattern in industry_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            keywords["industry"].append(pattern)

    # 提取角色关键词
    role_patterns = [
        r'创始人', r'CEO', r'产品经理', r'运营', r'市场',
        r'个人', r'自由职业', r'超级个体', r'企业主'
    ]
    for pattern in role_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            keywords["roles"].append(pattern)

    # 提取痛点关键词
    pain_patterns = [
        r'不知道', r'困惑', r'难以', r'缺少', r'没有',
        r'如何', r'怎么', r'瓶颈', r'挑战'
    ]
    for pattern in pain_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            keywords["pain_points"].append(pattern)

    return keywords

def generate_seed_plan(book_dir: Path):
    """生成 BEHAVIOR_SEED_PLAN.md"""

    brief_path = book_dir / "BOOK_BRIEF.md"
    keywords = extract_keywords(brief_path)

    if "error" in keywords:
        print(f"错误: {keywords['error']}")
        return

    seed_plan_path = book_dir / "BEHAVIOR_SEED_PLAN.md"

    content = """# 行为层采集计划

## 招聘关键词候选

"""

    if keywords["industry"] or keywords["roles"]:
        roles = keywords["roles"][:2] or ["负责人"]
        for industry in keywords["industry"][:3]:
            for role in roles:
                content += f"- [ ] {industry} + {role} + 招聘\n"
    else:
        content += "- [ ] （请根据主题手动补充）\n"

    content += "\n## 活动关键词候选\n\n"

    if keywords["industry"]:
        for industry in keywords["industry"][:3]:
            content += f"- [ ] {industry} + 峰会\n"
            content += f"- [ ] {industry} + 沙龙\n"
    else:
        content += "- [ ] （请根据主题手动补充）\n"

    content += "\n## 产品/项目关键词候选\n\n"

    if keywords["industry"]:
        for industry in keywords["industry"][:3]:
            content += f"- [ ] {industry} + 产品\n"
            content += f"- [ ] {industry} + 解决方案\n"
    else:
        content += "- [ ] （请根据主题手动补充）\n"

    content += """
## 使用说明

1. 删除不相关的候选关键词
2. 补充更精准的行业/角色/产品词
3. 用这些关键词搜索招聘网站、活动平台、公司官网
4. 把找到的行为信号记录到 BEHAVIOR_LEDGER.md
"""

    seed_plan_path.write_text(content, encoding="utf-8")
    print(f"✅ 已生成: {seed_plan_path}")
    print(f"提取到: {len(keywords['industry'])} 个行业词, {len(keywords['roles'])} 个角色词")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 auto-seed-behavior.py <book_dir>")
        sys.exit(1)

    book_dir = Path(sys.argv[1])
    generate_seed_plan(book_dir)

if __name__ == "__main__":
    main()
