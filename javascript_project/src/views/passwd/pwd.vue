<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="12" :offset="6" class="content">

        <el-card class="box-card">
          <div slot="header" class="clearfix">
            <span>修改密码</span>
          </div>

          <el-form ref="form" :model="form" label-width="100px" :rules="rules">
            <el-form-item label="旧密码" prop="oldpasswd">
              <el-col :span="8">
                <el-input v-model="form.oldpasswd" type="password" />
              </el-col>
            </el-form-item>
            <el-form-item label="新密码" prop="newpasswd">
              <el-col :span="8">
                <el-input v-model="form.newpasswd" type="password" />
              </el-col>
            </el-form-item>
            <el-form-item label="确认新密码" prop="newpasswd1">
              <el-col :span="8">
                <el-input v-model="form.newpasswd1" type="password" />
              </el-col>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="onSubmit('form')">保存</el-button>
            </el-form-item>
          </el-form>

        </el-card>

      </el-col>
    </el-row>
  </div>
</template>

<script>

export default {
  components: {
  },
  data() {
    return {
      form: {
        oldpasswd: '',
        newpasswd: '',
        newpasswd1: ''
      },
      rules: {
        oldpasswd: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 12, message: '长度在 6 到 12 个字符', trigger: 'blur' }
        ],
        newpasswd: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 12, message: '长度在 6 到 12 个字符', trigger: 'blur' }
        ],
        newpasswd1: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 12, message: '长度在 6 到 12 个字符', trigger: 'blur' }
        ]

      }
    }
  },
  computed: {
  },
  methods: {
    onSubmit(formName) {
      this.$refs[formName].validate((valid) => {
        console.log(valid)
        if (valid) {
          this.$store.dispatch('user/changePwd', this.form).then((data) => {
            this.$message({
              message: '修改成功',
              type: 'success'
            })
            this.form = {}
          })
        }
      })
    }
  }
}
</script>

<style scoped>
.content{
    margin-top: 2rem;
}
</style>
