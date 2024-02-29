import request from '@/utils/request'

export function condition(data) {
  return request({
    url: '/stock/condition',
    method: 'post',
    data
  })
}

export function kline(data) {
  return request({
    url: '/stock/kline',
    method: 'post',
    data
  })
}

export function get_dhtz_stock_strategy_desc(data) {
  return request({
    url: '/shape/get_dhtz_stock_strategy_desc',
    method: 'post',
    data
  })
}

export function stock_saveopen(data) {
  return request({
    url: '/shape/stock_saveopen',
    method: 'post',
    data
  })
}
