import { info, save, manual_info, audit_manual } from '@/api/audit'
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
  info({ commit }, data) {
    return new Promise((resolve, reject) => {
      info(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },

  save({ commit }, data) {
    return new Promise((resolve, reject) => {
      save(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },

  manual_info({ commit }, data) {
    return new Promise((resolve, reject) => {
      manual_info(data).then(response => {
        const { data } = response
        resolve(data)
      }).catch(error => {
        reject(error)
      })
    })
  },
  audit_manual({ commit }, data) {
    return new Promise((resolve, reject) => {
      audit_manual(data).then(response => {
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
  mutations,
  actions
}

