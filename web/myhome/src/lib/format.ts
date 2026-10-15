const money = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  maximumFractionDigits: 0,
})

export function formatMoney(n: number) {
  return money.format(n || 0)
}
