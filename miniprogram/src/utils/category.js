/**
 * 资源类别 → 样式类名后缀。
 *
 * 为什么不用中文类名：uni-app 编译 WXSS 时会把中文选择器转义成 `.cat-\53e4\9547`，
 * 而微信开发者工具的 WXSS 解析器不支持这种反斜杠转义，会直接报
 * "unexpected `\`" 导致页面白屏。所以统一用英文后缀。
 */
const CATEGORY_SUFFIX = {
  古镇: 'town',
  果园: 'orchard',
  村落: 'village',
  景区: 'scenic'
}

export function categoryClass(category) {
  return 'cat-' + (CATEGORY_SUFFIX[category] || 'default')
}
