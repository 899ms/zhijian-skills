# Leadbook Profiles

一本 leadbook 有两条独立选择：

- `content_profile`：决定这本书的结构任务。
- `voice_profile`：决定这本书像哪类专家写出来。
- `voice_anchor`：用一个或几个典型名人作为压缩提示词，帮助 Agent 进入思考姿态。

不要用一种 profile 解决所有问题。书型解决“装什么”，文风解决“谁在说”。

名人锚点只用于压缩思考姿态，不用于逐字仿写。不要复制某个名人的原文句式、口头禅和可识别表达；要抽取他的判断方式、结构偏好和解释节奏。

## Content Profiles

### whitepaper

适合：

- 企业 AI 落地白皮书
- AI 时代个人 IP 打造白皮书
- Agent Skill 白皮书

结构：

1. 趋势背景
2. 核心问题
3. 方法框架
4. 场景拆解
5. 路线图
6. 自测表

质量标准：事实和趋势判断要有来源，观点要克制，不能写成宣传册。

### playbook

适合：

- 内容获客系统手册
- 私域信任与成交手册
- 从专业能力到可售卖产品

结构：

1. 问题诊断
2. 操作步骤
3. 模板示例
4. 常见错误
5. 检查清单

质量标准：每章必须有可执行动作，不能只讲认知。

### methodology-book

适合：

- 超级个体商业操作系统
- OPC 商业系统
- 一个人公司的增长飞轮

结构：

1. 核心主张
2. 概念定义
3. 系统模型
4. 案例演示
5. 能力地图
6. 迁移路径

质量标准：模型要清楚，概念要能被读者复述，不能堆术语。

### business-report

适合：

- 行业观察报告
- 平台变化报告
- 趋势研判报告

结构：

1. 研究问题
2. 事实证据
3. 趋势判断
4. 机会地图
5. 行动建议

质量标准：事实、判断、推论必须分开写。

### course-manual

适合：

- 公开课程讲义
- 训练营教材
- 工作坊手册

结构：

1. 模块目标
2. 讲解正文
3. 练习任务
4. 交付标准
5. 作业检查

质量标准：教材可以有练习和作业，但不能把正文写成销售页。

## Book-Feel Density Rules

- `whitepaper`、`methodology-book`、`business-report`：正文优先承担开场、论证、模型、案例、边界和收束，不默认把模板、自测、填写题放进每一章主结构。
- `playbook`：可以有更强的动作密度，但仍要让章节推进一个更大的判断，不能把全书压成重复 SOP。
- `course-manual`：最适合高密度练习、自测和检查标准，但也要有完整学习路径，不只是作业表。
- 一本书允许章节不等长、不等形。均质模板有利于交付，不利于书感。
- 如果读者记住的是模板，而不是作者判断，这本书的 profile 还没有真正落地。

## Voice Profiles

### strategy-consultant

像一个给创始人做战略诊断的人写。句子短，判断直接，先给结论，再说明依据和取舍。

适合：白皮书、商业报告、战略型方法论书。

名人锚点：

- Peter Drucker：先定义问题，再判断管理动作。
- Clayton Christensen：用清晰分类解释为什么旧做法会失效。

Agent 代入提示：像 Drucker 在给创始人写一份克制但锋利的诊断备忘录；像 Christensen 在把混乱市场拆成可判断的类别。

写法要求：

- 多用“我的判断是”“这里真正要分清的是”“这个问题不能只看表层动作”。
- 每章至少有一个取舍判断：读者应该做什么、放弃什么、为什么。
- 少写热词，多写约束、边界、成本、次序。

禁区：不能写成咨询公司 PPT 口吻，不能堆“战略、组织、生态、闭环”。

### operator-playbook

像一线操盘者写的手册。重视步骤、错误、检查清单和可执行动作。

适合：playbook、课程手册、操作型短书。

名人锚点：

- Alex Hormozi：把 offer、结果承诺、交付边界拆到可购买。
- Ramit Sethi：把建议写成脚本、模板和可执行动作。

Agent 代入提示：像 Hormozi 在拆一个能卖的 offer，但去掉强销售腔；像 Ramit 在给读者一套可以直接照着填的脚本。

写法要求：

- 每章都要落到“怎么做”“做到什么程度算合格”“常见失败点”。
- 案例写具体动作，避免只写理念。
- 多用“先做 A，再做 B”“做到这一步就停”“不要急着进入下一步”。

禁区：不能把复杂问题简化成鸡血口号，不能只给原则不给样例。

### research-analyst

像研究员写的判断报告。事实、推论、作者判断要分开，语气克制。

适合：business-report、whitepaper、趋势研判。

名人锚点：

- Mary Meeker：用趋势、数据和图表组织长判断。
- Ben Thompson：用清晰模型解释技术、平台和商业结构。

Agent 代入提示：像 Mary Meeker 写趋势报告，像 Ben Thompson 写商业结构分析；证据先行，结论克制。

写法要求：

- 每个关键判断说明证据层级和不确定性。
- 多用“公开资料显示”“更稳妥的说法是”“目前只能判断到这个程度”。
- 图表优先服务证据结构，而不是装饰页面。

禁区：不能用需求侧样本直接推出行业结论，不能伪精确。

### product-architect

像产品架构师写方法论。重视模块、接口、流程、输入输出和复用。

适合：方法论书、系统搭建手册、工具产品化主题。

名人锚点：

- Jeff Bezos：从客户倒推，写成 working-backwards memo。
- Marty Cagan：把产品能力拆成用户问题、方案、验证和交付系统。

Agent 代入提示：像 Bezos 写内部备忘录，先问客户要什么结果；像 Marty Cagan 拆产品系统，讲清输入、输出、验证和边界。

写法要求：

- 把概念拆成模块和关系，让读者知道每个部件解决什么问题。
- 多写“输入是什么、输出是什么、失败信号是什么”。
- 每章最好有一张结构图、流程图或决策图。

禁区：不能让模型变成术语堆叠，不能只画架构不解释使用场景。

### austrian-economics

像奥派经济学视角的商业作者。重视主观价值、企业家判断、市场过程和激励结构。

适合：商业方法论、个人商业系统、定价、产品化、创业判断。

名人锚点：

- Friedrich Hayek：重视分散知识、市场信号和自发秩序。
- Ludwig von Mises：重视人的行动、主观价值和交换。
- Israel Kirzner：重视企业家发现机会的过程。

Agent 代入提示：像 Hayek 在解释市场如何传递信息，像 Mises 在追问行动背后的主观价值，像 Kirzner 在看企业家如何发现机会。

写法要求：

- 先问“谁在什么处境下愿意付出什么代价”。
- 解释行动背后的激励、机会成本和市场信号。
- 区分个人偏好、可交易价值和可验证需求。

禁区：不能写成经济学术语课，不能用理论压过读者的具体处境。

### teacher-coach

像有经验的老师写给行动者。亲近、清楚、有引导，但不讨好。

适合：课程手册、入门指南、认知迁移型短书。

名人锚点：

- Richard Feynman：用简单语言解释复杂问题，先找到学生真正不懂的地方。
- Sal Khan：把学习路径拆成小台阶，让读者持续获得掌控感。

Agent 代入提示：像 Feynman 在白板前把概念讲到孩子也能复述；像 Sal Khan 把复杂技能拆成连续小练习。

写法要求：

- 先承认读者卡点，再给清晰路径。
- 每章有小练习、自测问题或反思问题。
- 用例子降低理解成本，但保持判断锋利。

禁区：不能写成安慰文，不能用“相信自己”替代方法。

## Selection Rules

| 任务 | 推荐 content_profile | 推荐 voice_profile | 推荐 voice_anchor |
|---|---|---|---|
| 从专业能力到可售卖产品 | playbook | operator-playbook / product-architect | Hormozi + Ramit / Bezos + Cagan |
| 超级个体商业操作系统 | methodology-book | product-architect / austrian-economics | Bezos + Cagan / Hayek + Mises + Kirzner |
| AI 时代个人 IP 打造白皮书 | whitepaper | strategy-consultant / research-analyst | Drucker + Christensen / Meeker + Thompson |
| 内容获客系统手册 | playbook | operator-playbook / teacher-coach | Hormozi + Ramit / Feynman + Khan |
| 中小企业 AI 落地白皮书 | whitepaper | strategy-consultant / product-architect | Drucker + Christensen / Bezos + Cagan |

## Voice Contract

写正文前必须在 `BOOK_BRIEF.md` 写明：

- 这本书选择哪个 `voice_profile`。
- 这本书选择哪个 `voice_anchor`，以及它只借用哪种思考姿态。
- 作者为什么有资格这样说。
- 读者会从这个声音里获得什么。
- 这个声音不做什么。

每章至少有 1 处作者判断，形式可以是：

- “我的判断是……”
- “真正值得警惕的是……”
- “如果只能做一个动作，先做……”
- “这个方法成立的前提是……”

如果一章读完像资料汇编，说明 voice_profile 没有落地。
