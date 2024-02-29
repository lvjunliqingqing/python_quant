
import { condition_list, dynamic_from_list, all_strategy, strategy_by_symbol } from '@/api/common'
import { getToken, setToken, removeToken } from '@/utils/auth'

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
  condition_list({ commit }, data) {
    return new Promise((resolve, reject) => {
      condition_list(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },

  dynamic_from_list({ commit }, data) {
    return new Promise((resolve, reject) => {
      dynamic_from_list(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },

  all_strategy({ commit }, data) {
    return new Promise((resolve, reject) => {
      all_strategy(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },

  strategy_by_symbol({ commit }, data) {
    return new Promise((resolve, reject) => {
      strategy_by_symbol(data).then(response => {
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

