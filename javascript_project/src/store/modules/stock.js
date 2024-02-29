import { condition, kline, get_dhtz_stock_strategy_desc, stock_saveopen } from '@/api/stock'
import { getToken, setToken, removeToken } from '@/utils/auth'
import { resetRouter } from '@/router'

const getDefaultState = () => {
  return {
    token: getToken(),
    name: '',
    avatar: ''
  }
}

const state = getDefaultState()

const mutations = {
  RESET_STATE: (state) => {
    Object.assign(state, getDefaultState())
  }
}

const actions = {
  // user login
  condition({ commit }, data) {
    return new Promise((resolve, reject) => {
      condition(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },
  kline({ commit }, data) {
    return new Promise((resolve, reject) => {
      kline(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },
  get_dhtz_stock_strategy_desc({ commit }, data) {
    return new Promise((resolve, reject) => {
      get_dhtz_stock_strategy_desc(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },
  stock_saveopen({ commit }, data) {
    return new Promise((resolve, reject) => {
      stock_saveopen(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}

