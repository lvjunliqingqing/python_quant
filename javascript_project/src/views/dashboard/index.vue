<template>
  <div class="dashboard-container">
    <div class="dashboard-text">name: {{ name }}</div>

  </div>

</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'Dashboard',
  computed: {
    ...mapGetters([
      'name',
      'passwdDig'
    ])
  },
  watch: {
    passwdDig: {
      handler(newName, oldName) {
        console.log(newName, oldName)
      },
      deep: true,
      immediate: true
    }
  },
  data() {
    return {
      form: {

      }
    }
  },
  methods: {
    onSubmit() {

    }
  }
}

</script>

<style lang="scss" scoped>
.dashboard {
  &-container {
    margin: 30px;
  }
  &-text {
    font-size: 30px;
    line-height: 46px;
  }
}
</style>
