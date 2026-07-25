export const WECHAT_IMAGE_HOSTS = Object.freeze([
  'mmbiz.qpic.cn',
  'mmbiz.qlogo.cn',
  'wx.qlogo.cn',
]);

export function isWeChatHostedImageUrl(value) {
  if (typeof value !== 'string' || value.length === 0) return false;
  try {
    return WECHAT_IMAGE_HOSTS.includes(new URL(value).hostname.toLowerCase());
  } catch {
    return false;
  }
}
