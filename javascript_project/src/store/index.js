import Vue from 'vue'
import Vuex from 'vuex'
import getters from './getters'
import app from './modules/app'
import settings from './modules/settings'
import user from './modules/user'
import stock from './modules/stock'
import shape from './modules/shape'
import audit from './modules/audit'
import common from './modules/common'

Vue.use(Vuex)

const store = new Vuex.Store({
  modules: {
    app,
    settings,
    user,
    stock,
    common,
    shape,
    audit
  },
  getters
})

export default store
