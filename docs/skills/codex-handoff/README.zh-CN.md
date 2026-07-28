# Codex Handoff

把历史过大、响应变慢的 Codex task 换到一个全新的用户可见 task 中继续，不复制完整对话。

[English](./README.md) · [唯一源码](https://github.com/zjp1997720/zhijian-skills/tree/main/skills/codex-handoff)

## 安装

```bash
npx skills add zjp1997720/zhijian-skills \
  --skill codex-handoff --agent codex --global --copy --yes
```

显式调用：

```text
$codex-handoff 在新 task 中继续完成发布验证。
```

## 运行要求

- 支持创建用户可见 task 的 Codex Desktop。
- 工作依赖项目文件时，当前项目必须能被 Codex 正确识别。
- 必须由用户显式调用。创建新 task 会改变应用状态，因此默认关闭自动触发。

## 它会做什么

一个长期运行的 Codex task 会不断积累历史。即使系统已经压缩上下文，后续每轮模型调用仍可能处理大量旧内容。`codex-handoff` 把它视为一次上下文换舱：

- 只提取当前目标、已验证状态、关键决策、权威产物、失败记录、剩余工作、脆弱状态和建议 Skills；
- 生成紧凑的交接 Prompt，不复制聊天记录；
- 在当前项目中创建一个全新的用户可见 Codex task；
- 用户没有明确要求时，不改变模型和推理强度；
- 新 task 立即执行下一步，老 task 停止继续工作。

老 task 保持原样，继续承担历史档案作用。新 task 不再为完整旧对话支付每轮上下文成本。

## 工作方式

```text
历史过大的老 task
  → 核对工作区和当前项目规则
  → 把必要状态压缩成指针优先的 Prompt
  → 识别 Codex 当前项目
  → 创建并命名一个全新 task
  → 在新 task 中立即执行下一步
  → 老 task 原样保留为历史
```

交接 Prompt 优先引用计划、文件、Issue、提交、Diff 和 URL，不重复粘贴内容。密钥、凭证、无关个人信息、超长状态输出和重复推理不会进入新 task。

## 使用示例

```text
$codex-handoff 这个 task 已经很慢了，在新 task 中从第一个失败的发布检查继续。
```

```text
$codex-handoff 把这个超长对话换到新 task，只继续剩余的文档工作。
```

```text
$codex-handoff 新 task 只继续完成测试、PR 和发布验证。
```

## 安全边界与限制

- 不复制完整历史，不派内部子代理，不迁移其他 task 的 Git checkout，也不生成交接文件。
- 普通的“继续做”不会触发本 Skill。
- 遵守项目规则和 Codex 环境策略；如果新环境会遗漏关键未提交状态，会在创建前停止并说明风险。
- worktree 尚在排队时只报告“已排队”，不会误报为已经运行。
- 临时目录和机器本地路径会被标注为脆弱状态。
- 缺少 Codex task 工具时直接停止，不用其他方式伪造成功。

## 开发与验证

```bash
python3 -m unittest discover -s skills/codex-handoff/tests -v
```

安装包包含显式触发正例、负例、近邻样例和输出契约评测。

## 许可证

[MIT](../../../LICENSE)
