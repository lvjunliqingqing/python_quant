const getters = {
  sidebar: state => state.app.sidebar,
  device: state => state.app.device,
  token: state => state.user.token,
  avatar: state => state.user.avatar,
  name: state => state.user.name,
  account: state => state.user.account,
  passwdDig: state => state.app.passwdDig,
  account_list: state => state.user.account_list
}
export default getters
