import assert from 'node:assert/strict';
import test from 'node:test';

import {
  compareSaveStates,
  normalizeSaveState,
  normalizeVerificationState,
} from '../scripts/wechat-opencli.mjs';

test('normalizes missing OpenCLI arrays instead of throwing during verification', () => {
  const state = normalizeVerificationState({ ok: true, url: 'https://mp.weixin.qq.com/' });

  assert.deepEqual(state.failedUrls, []);
  assert.deepEqual(state.pendingImages, []);
  assert.deepEqual(state.history, []);
});

test('confirms a draft with appmsgid and saved banner when history is unavailable', () => {
  const state = normalizeSaveState({
    url: 'https://mp.weixin.qq.com/cgi-bin/appmsg?appmsgid=42',
    saved: true,
  });

  assert.deepEqual(state.history, []);
  assert.equal(state.appmsgid, '42');
  assert.equal(state.confirmed, true);
  assert.deepEqual(state.evidence, {
    appmsgid: true,
    savedBanner: true,
    history: false,
  });
});

test('does not claim save success from an existing appmsgid alone', () => {
  const state = normalizeSaveState({
    url: 'https://mp.weixin.qq.com/cgi-bin/appmsg?appmsgid=42',
  });

  assert.equal(state.confirmed, false);
});

test('requires a new save signal when editing an existing draft', () => {
  const before = {
    url: 'https://mp.weixin.qq.com/cgi-bin/appmsg?appmsgid=42',
    saved: true,
    history: ['07-18 09:00 手动保存'],
  };
  const unchanged = compareSaveStates(before, before);
  const updated = compareSaveStates(before, {
    ...before,
    history: ['07-18 09:10 手动保存'],
  });

  assert.equal(unchanged.confirmed, false);
  assert.equal(updated.confirmed, true);
  assert.equal(updated.transition.historyChanged, true);
});
