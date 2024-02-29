import request from '@/utils/request'

export function info(data) {
  return request({
    url: '/shape/info',
    method: 'post',
    data
  })
}

export function saveopen(data) {
  return request({
    url: '/shape/saveopen',
    method: 'post',
    data
  })
}

export function save(data) {
  return request({
    url: '/shape/new_shape',
    method: 'post',
    data
  })
}

