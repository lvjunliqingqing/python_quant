import request from '@/utils/request'

export function condition_list(data) {
  return request({
    url: '/stock/condition_list',
    method: 'get',
    data
  })
}

export function dynamic_from_list(data) {
  return request({
    url: '/stock/dynamic_form_list',
    method: 'get',
    data
  })
}

export function all_strategy(data) {
  return request({
    url: '/shape/get_dhtz_strategy_desc',
    method: 'get',
    data
  })
}

export function strategy_by_symbol(data) {
  return request({
    url: '/shape/get_dhtz_strategy_desc_by_symbol',
    method: 'post',
    data
  })
}
