import assert from 'node:assert/strict';
import test from 'node:test';

import { analyzeContentDensity } from '../scripts/content-density-audit.mjs';

test('balanced Chinese article paragraphs pass density audit', () => {
  const markdown = [
    '这次培训没有从模型排行榜讲起，而是从一堆真实材料开始。',
    '一个真实项目包含很多文件、持续修改和不断变化的状态。',
    '所以问题已经从会不会提问，变成怎样让 Agent 进入完整工作现场。',
    'Agent 活在工作空间里。',
    '在授权范围内，它可以搜索文件、比较版本、整理材料，并把结果写回项目目录。',
    '这让过去由人完成的附件挑选和上下文收集，开始可以交给 Agent。',
    '工具决定它能做什么，状态决定它知不知道做到哪了。',
    '循环让它不断检查结果并向目标靠近。',
    '当然，能干活不代表一定能把活干对。',
    '人仍然要保留目标、业务判断和最终验收责任。',
  ].join('\n\n');

  assert.equal(analyzeContentDensity(markdown).status, 'pass');
});

test('wall-of-text paragraphs fail density audit', () => {
  const dense = '这是一段同时包含背景、机制、案例、边界和行动建议的正文，'.repeat(9);
  const markdown = Array.from({ length: 12 }, () => dense).join('\n\n');
  const report = analyzeContentDensity(markdown);

  assert.equal(report.status, 'fail');
  assert.ok(report.maxConsecutiveGe100 >= 3);
});

test('a long run of ultrashort paragraphs requests semantic review without automatic failure', () => {
  const markdown = [
    '问题来了。',
    '怎么办？',
    '继续看。',
    '这很重要。',
    '再往下。',
    '还没结束。',
    '注意这里。',
    '记住这一点。',
  ].join('\n\n');
  const report = analyzeContentDensity(markdown);

  assert.equal(report.status, 'pass');
  assert.equal(report.maxConsecutiveLe20, 8);
  assert.ok(report.warnings.some(warning => warning.includes('人工检查')));
});

test('component bodies and image lines do not count as prose paragraphs', () => {
  const markdown = [
    '正文判断完整成立。',
    '',
    ':::compare',
    '**方案 A** | 标题 | 描述',
    '方案 B | 标题 | 描述',
    ':::',
    '',
    '![示意图](https://example.com/a.png)',
    '',
    '正文继续推进。',
  ].join('\n');
  const report = analyzeContentDensity(markdown);

  assert.equal(report.paragraphCount, 2);
});
