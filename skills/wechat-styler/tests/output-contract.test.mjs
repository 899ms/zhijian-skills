import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

test('renders the shared content root and metadata for downstream publishers', () => {
  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'wechat-output-contract-'));
  const input = path.join(workDir, 'article.md');
  const output = path.join(workDir, 'article.html');
  fs.writeFileSync(input, '---\ntitle: 合同测试\nsummary: 摘要测试\n---\n\n# 正文标题\n\n正文。\n');

  const result = spawnSync(process.execPath, [
    path.join(skillRoot, 'scripts/convert.mjs'), input, '--output', output,
  ], { encoding: 'utf8' });

  assert.equal(result.status, 0, result.stderr || result.stdout);
  const html = fs.readFileSync(output, 'utf8');
  assert.match(html, /data-wechat-root="article"/);
  assert.match(html, /<meta name="description" content="摘要测试">/);
  fs.rmSync(workDir, { recursive: true, force: true });
});

test('passes the generated path to the opener without shell interpretation', () => {
  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'wechat-output-safety-'));
  const input = path.join(workDir, 'article.md');
  const output = path.join(workDir, 'article.html"; touch INJECTED; #');
  fs.writeFileSync(input, '# 正文\n');

  const result = spawnSync(process.execPath, [
    path.join(skillRoot, 'scripts/convert.mjs'), input, '--output', output,
  ], { cwd: workDir, encoding: 'utf8' });

  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.equal(fs.existsSync(path.join(workDir, 'INJECTED')), false);
  assert.equal(fs.existsSync(output), true);
  fs.rmSync(workDir, { recursive: true, force: true });
});

test('zhijian theme keeps action and trust semantics visually distinct', () => {
  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'wechat-zhijian-theme-'));
  const input = path.join(workDir, 'article.md');
  const output = path.join(workDir, 'article.html');
  fs.writeFileSync(input, [
    '## 章节标题',
    '',
    '### 结构标题',
    '',
    '正文包含 **普通加粗** 和 [资料链接](https://example.com)。',
    '',
    '- 列表正文',
    '',
    '> 一段用于交代上下文或证据的普通引用。',
    '',
    '![图注测试](https://example.com/image.png)',
    '',
  ].join('\n'));

  const result = spawnSync(process.execPath, [
    path.join(skillRoot, 'scripts/convert.mjs'), input,
    '--theme', 'zhijian',
    '--output', output,
  ], { encoding: 'utf8' });

  assert.equal(result.status, 0, result.stderr || result.stdout);
  const html = fs.readFileSync(output, 'utf8');
  assert.match(html, /font-size:15px;font-weight:450[^>]+line-height:1\.68/);
  assert.match(html, /<h2[^>]+font-family:'TsangerJinKai02'[^>]+font-size:22px;font-weight:500[^>]+border-left:4px solid #B85235/);
  assert.match(html, /<h3[^>]+font-family:'TsangerJinKai02'[^>]+font-size:18px;font-weight:600[^>]+color:#1B365D/);
  assert.match(html, /<ul[^>]+font-size:15px;font-weight:450/);
  assert.match(html, /<strong style="color:#A04A2E;font-weight:600/);
  assert.match(html, /<a href="https:\/\/example\.com"[^>]+color:#1B365D/);
  assert.match(html, /<section data-wechat-block="quote" style="background-color:#EEF2F7;padding:13px 16px 14px[^>]+border-radius:4px;">/);
  assert.match(html, /<p[^>]*><span style="display:inline-block[^>]+font-size:21px[^>]+color:#1B365D[^>]*>“<\/span>/);
  assert.doesNotMatch(html, /display:block[^>]+>“<\/span>/);
  assert.doesNotMatch(html, /background-color:#EEF2F7;border-left:/);
  assert.match(html, /<section style="text-align:center;margin:0;background-color:#F5F4ED;">\s*<img[^>]+alt="图注测试"/);
  assert.match(html, /<p style="font-family:'Source Han Sans CN'[^\"]*font-size:13px[^\"]*line-height:1\.4;text-align:center;margin:0 12px 22px/);
  assert.doesNotMatch(html, /text-align:center;margin:0 0 8px;background-color:#F5F4ED/);
  fs.rmSync(workDir, { recursive: true, force: true });
});
