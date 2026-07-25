import assert from 'node:assert/strict';
import test from 'node:test';

import { generateCoverAnimation } from '../scripts/generate-cover-animation.mjs';

const theme = {
  background_color: '#F5F4ED',
  accent_color: '#B85235',
  accent_secondary: '#1B365D',
  text_color: '#141413',
  tertiary_color: '#6B6A64',
};

test('typewriter renders comma-separated cover tags', () => {
  const svg = generateCoverAnimation(theme, {
    template: 'typewriter',
    title: '十万卡，开始干活了',
    subtitle: '单日峰值50万个作业',
    tags: '曙光8000,十万卡AI超集群,WAIC 2026',
  });

  assert.match(svg, /<tspan leaf="">曙光8000 · 十万卡AI超集群 · WAIC 2026<\/tspan>/);
  assert.match(svg, /y="178"[^>]+fill="#1B365D"/);
});

test('typewriter shrinks long titles and subtitles into the safe width', () => {
  const svg = generateCoverAnimation(theme, {
    template: 'typewriter',
    title: '这是一个明显超过默认安全长度但仍然需要完整显示的打字机标题',
    subtitle: '这是一条同样很长并且需要自动缩小字号避免越过画布左右边界的副标题',
  });

  const title = svg.match(/<text x="([\d.]+)" y="65"[^>]+font-size="([\d.]+)"/);
  const subtitle = svg.match(/<text x="([\d.]+)" y="140"[^>]+font-size="([\d.]+)"/);

  assert.ok(title, 'title text should be rendered');
  assert.ok(subtitle, 'subtitle text should be rendered');
  assert.ok(Number(title[1]) >= 40, `title starts outside safe area: ${title[1]}`);
  assert.ok(Number(subtitle[1]) >= 32, `subtitle starts outside safe area: ${subtitle[1]}`);
  assert.ok(Number(title[2]) < 48, `title font was not reduced: ${title[2]}`);
  assert.ok(Number(subtitle[2]) < 26, `subtitle font was not reduced: ${subtitle[2]}`);
});

test('typewriter keeps valid SVG geometry when optional subtitle and tags are absent', () => {
  const svg = generateCoverAnimation(theme, {
    template: 'typewriter',
    title: '只有标题',
  });

  assert.doesNotMatch(svg, /NaN|dur="0s"/);
});

test('typewriter uses a monospace stack for mixed Chinese and English subtitles', () => {
  const svg = generateCoverAnimation({
    ...theme,
    code_font: "'SF Mono','JetBrains Mono',Menlo,monospace",
    font_family_cn: "'Source Han Serif SC','Songti SC',serif",
  }, {
    template: 'typewriter',
    title: 'AI写完，还不能交付',
    subtitle: '从 Markdown 到 Word 和 PDF',
  });

  const subtitleStart = svg.match(/<text x="[\d.]+" y="140"[^>]+font-family="([^"]+)"/);
  assert.ok(subtitleStart, 'subtitle text should be rendered');
  assert.equal(subtitleStart[1], "'SF Mono','JetBrains Mono',Menlo,monospace");
});
