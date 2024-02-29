import request from '@/utils/request'

export function info(data) {
  return request({
    url: '/shape/get_dhtz_open_symbol_data',
    method: 'post',
    data
  })
}

export function save(data) {
  return request({
    url: '/shape/audit',
    method: 'post',
    data
  })
}

export function manual_info(data) {
  return request({
    url: '/shape/audit_manual/get_dhtz_open_symbol_data',
    method: 'post',
    data
  })
}
export function audit_manual(data) {
  return request({
    url: '/shape/audit_manual',
    method: 'post',
    data
  })
}

