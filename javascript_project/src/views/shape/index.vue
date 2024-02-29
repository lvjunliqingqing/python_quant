<template>
  <div class="app-container">

    <el-row style="margin-bottom:1rem;">

      <el-date-picker
        v-model="trade_day"
        align="right"
        type="date"
        placeholder="选择日期"
        format="yyyy-MM-dd"
        value-format="yyyy-MM-dd"
        :picker-options="pickerOptions"
        @change="changePicker"
      />
      <el-button type="primary" size="medium" style="margin-left:1rem" @click="newShape=true">新形态</el-button>
      <el-button type="success" size="medium" style="margin-left:1rem" @click="addClick('multiple')">加入交易</el-button>
    </el-row>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="55"
      />
      <el-table-column
        v-for=" col in column"
        :key="col.key"
        :prop="col.key"
        :label="col.name"
        :sortable="col.sort"
        align="center"
      />
      <el-table-column
        fixed="right"
        label="操作"
        width="100"
      >
        <template slot-scope="scope">
          <el-button type="text" size="small" @click="addClick(scope.row, scope.$index)">加入交易</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top:1rem;float:right"
      background
      layout="prev, pager, next"
      :hide-on-single-page="singlePage"
      :page-size="10"
      :total="total"
      @current-change="currentChange"
    />

    <el-dialog
      title="新形态"
      :visible.sync="newShape"
      width="50%"
    >

      <el-form ref="form" :model="form" label-width="100px">
        <el-form-item label="交易日期">
          <el-col :span="8">
            <el-date-picker
              v-model="form.trade_day"
              type="date"
              placeholder="选择日期"
              format="yyyy 年 MM 月 dd 日"
              value-format="yyyy-MM-dd"
              style="width: 100%;"
            />
          </el-col>
        </el-form-item>
        <el-form-item label="标的物代码">
          <el-col :span="8">
            <el-input v-model="form.symbol" />
          </el-col>
        </el-form-item>
        <el-form-item label="方向">
          <el-select v-model="form.direction" placeholder="选择方向">
            <el-option label="多" value="LONG" />
            <el-option label="空" value="SHORT" />
            <el-option label="多&空" value="NET" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="onSubmit">添加</el-button>
          <el-button @click="newShape=false">取消</el-button>
        </el-form-item>
      </el-form>

    </el-dialog>

    <el-dialog
      :visible.sync="addDialog"
      @close="diglogClose"
    >
      <el-row :gutter="20">
        <div style="padding-left:2rem;margin-bottom:1rem">{{ this.dynamicValidateForm.symbol }}</div>
      </el-row>
      <el-form
        ref="dynamicValidateForm"
        :model="dynamicValidateForm"
        label-width="100px"
        label-position="right"
        :rules="rules"
        class="demo-dynamic"
      >
        <el-row :gutter="22">
          <el-col :span="9">
            <el-form-item
              label="策略名称"
              prop="strategy_name"
            >
              <el-select
                v-model="dynamicValidateForm.strategy_name"
                label="策略名称"
                class="select"
                placeholder="策略名称"
                @change="strategyChange"
              >
                <el-option
                  v-for="item in strategy_name_options"
                  :key="item.strategy_class_name"
                  :label="item.strategy_name + item.strategy_desc +'('+ item.strategy_class_name +')'"
                  :value="item.strategy_class_name"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              label="方向"
              prop="direction"
            >
              <el-select
                v-model="dynamicValidateForm.direction"
                label="方向"
                class="select"
                placeholder="方向"
                @change="directionChange"
              >
                <el-option
                  v-for="item in direction_options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              label="账户"
              prop="account_list"
            >
              <el-select
                v-model="dynamicValidateForm.account_list"
                label="账户"
                multiple
                class="select"
                placeholder="账户"
                @change="accountChange"
              >
                <template v-for="item in account_list.list">
                  <el-option
                    v-if="item.account_type == 'futures'"
                    :key="item.account_id"
                    :label="item.account_id + '-'+item.commpany"
                    :value="item.account_id"
                  />
                </template>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col v-if=" this.args_map[dynamicValidateForm.strategy_name]" :span="12" style="border-left:1px solid #eee;padding-left:2rem">
            <el-form-item
              v-for="(row, index) in this.args_map[dynamicValidateForm.strategy_name]"
              :key="index"
              label-width="auto"
              :label="row.name"
              :prop="index"
            >
              <el-input v-model="dynamicValidateForm.strategy_args[index].value" style="margin-bottom:1rem"	type="number" :placeholder="row.name" @input="inpuChange($event)" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="addDialog = false">取 消</el-button>
        <el-button :loading="loading" type="primary" @click="submitForm('dynamicValidateForm')">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.select {
  margin-bottom: 0;
}

</style>

<script>
import { mapGetters } from 'vuex'
import { clipPointsByRect } from 'echarts/lib/util/graphic'

export default {
  computed: {
    ...mapGetters([
      'sidebar',
      'avatar',
      'account_list',
      'name',
      'passwdDig'
    ])
  },
  data() {
    return {
      trade_day: '',
      form: {
        trade_day: '',
        symbol: '',
        direction: ''
      },
      default_trade_day: '',
      args_map: {},
      args_map_default: {},
      newShape: false,

      pickerOptions: {
        disabledDate(time) {
          return time.getTime() > Date.now()
        },
        shortcuts: [{
          text: '今天',
          onClick(picker) {
            picker.$emit('pick', new Date())
          }
        }, {
          text: '昨天',
          onClick(picker) {
            const date = new Date()
            date.setTime(date.getTime() - 3600 * 1000 * 24)
            picker.$emit('pick', date)
          }
        }, {
          text: '一周前',
          onClick(picker) {
            const date = new Date()
            date.setTime(date.getTime() - 3600 * 1000 * 24 * 7)
            picker.$emit('pick', date)
          }
        }]
      },

      dynamicValidateForm: {
        'strategy_name': 'a11_full_auto_twodays_half'
      },
      link_table: {

      },
      column: [
        { 'name': '收盘日期', 'key': 'trade_date' },
        { 'name': '股票代码', 'key': 'symbol' },
        { 'name': '交易所', 'key': 'exchange' },
        { 'name': '股票名称', 'key': 'display_name' },
        { 'name': '收盘价', 'key': 'close' }
      ],
      strategy_name_options: [

      ],
      direction_map: {
        'LONG': '多',
        'SHORT': '空'
      },
      direction_options: [
        {
          value: 'LONG',
          label: '多'
        },
        {
          value: 'SHORT',
          label: '空'
        },
        {
          value: 'NET',
          label: '多和空'
        }
      ],
      rules: {
        strategy_name:
        [
          { required: true, message: '请选择策略名', trigger: 'change' }

        ],
        direction:
        [
          { required: true, message: '选择方向', trigger: 'change' }
        ],
        account_list:
        [
          { required: true, message: '选择账户', trigger: 'change' }
        ]
      },
      data0: [],
      singlePage: true,
      loading: false,
      allTableData: [],
      addDialog: false,
      tableData: [
      ],
      listLoading: true,
      normValue: [],
      pageSize: 10,
      selectDate: '',
      total: 0,
      currentSelect: []
    }
  },
  mounted() {
    this.getData()
    this.getAllStrategy()
  },
  created() {
    console.log(1)
    var day2 = new Date()
    var s2 = day2.getFullYear() + '-' + (day2.getMonth() + 1) + '-' + day2.getDate()
    this.trade_day = s2

    var s3 = day2.getFullYear() + '-' + (day2.getMonth() + 1) + '-' + day2.getDate() + 1
    this.form.trade_day = s2
    console.log(this.$store.state.user.account_list)
    // this.dynamicValidateForm.account_list = this.$store.state.user.account_list.list[0]['account_id']
  },
  methods: {
    handleSelectionChange(val) {
      this.currentSelect = val
    },
    diglogClose() {
      console.log('close')
      this.dynamicValidateForm.strategy_name = ''
      // console.log()
      // this.$refs.dynamicValidateForm.resetFields();
    },
    accountChange() {

    },
    changePicker(val) {
      this.trade_day = val
      this.dynamicValidateForm.trade_day = val
      this.loadData()
    },
    addItem() {
    },
    onSubmit() {
      console.log(this.form)
      this.$store.dispatch('shape/save', this.form).then((data) => {
        console.log(data)
        this.tableData.unshift(data)
        this.$message({
          message: '添加成功',
          type: 'success'
        })
        this.newShape = false
      }).catch((err) => {
        console.error(err)
      })
    },
    directionChange(val) {
      console.log(val)
      this.dynamicValidateForm.direction = val
      this.loadStratgyArgs()
    },
    inpuChange(e) {
      this.$forceUpdate()
    },
    getAllStrategy() {
      this.$store.dispatch('common/all_strategy', {}).then((data) => {
        var tmp = {}
        for (var i in data) {
          if (data[i].strategy_args) {
            var tmp_args = JSON.parse(data[i].strategy_args)
            this.args_map[data[i].strategy_class_name] = tmp_args
            this.args_map_default[data[i].strategy_class_name] = tmp_args
            this.link_table[data[i].strategy_class_name] = data[i].link_table
          }
        }

        this.dynamicValidateForm.strategy_args = this.args_map[this.dynamicValidateForm.strategy_name]
        this.dynamicValidateForm.link_table = this.link_table[this.dynamicValidateForm.strategy_name]

        console.log(this.dynamicValidateForm.link_table)

        this.strategy_name_options = data
      }).catch((err) => {
        console.error(err)
      })
    },
    loadData() {
      this.$store.dispatch('shape/info', this.dynamicValidateForm).then((data) => {
        this.column = data.col
        data = data.list
        this.loading = false
        this.total = data.length
        console.log(this.total > this.pageSize, data.length)
        if (this.total > this.pageSize) {
          this.singlePage = false
        }
        console.log('submitForm', data)
        console.log('this.total', this.total, this.column)
        this.allTableData = data
        this.tableData = this.allTableData.slice(0, (this.pageSize))
      }).catch((err) => {
        console.error(err)
        this.loading = false
      })
    },
    loadStratgyArgs() {
      var symbol = this.dynamicValidateForm.symbol[0]
      var exchange = symbol.split('.')[1]

      var reg = RegExp(/^[a-zA-Z]{1,3}/)

      symbol = symbol.match(reg)[0]

      console.log(exchange, symbol)

      var data = {
        symbol: symbol,
        exchange: exchange,
        strategy_name: this.dynamicValidateForm.strategy_name,
        direction: this.dynamicValidateForm.direction
      }
      var val = this.dynamicValidateForm.strategy_name

      this.$store.dispatch('common/strategy_by_symbol', data).then((data) => {
        if (data.strategy_args) {
          var strategy_args = JSON.parse(data.strategy_args)

          console.log(strategy_args, this.args_map)

          this.dynamicValidateForm.strategy_args = strategy_args
          this.args_map[val] = strategy_args
        } else {
          this.args_map[val] = this.args_map_default[val]
        }

        this.dynamicValidateForm.link_table = this.link_table[val]
      }).catch((err) => {
        console.error(err)
        this.loading = false
      })

      this.dynamicValidateForm.strategy_args = this.args_map[this.dynamicValidateForm.strategy_name]
    },
    strategyChange(val) {
      this.loadStratgyArgs()

      // this.dynamicValidateForm.strategy_name = val
    },
    addClick(row, index) {
      var symbol_list = []
      if (!index) {
        for (var i in this.currentSelect) {
          symbol_list.push(this.currentSelect[i].symbol + '.' + this.currentSelect[i].exchange)
        }
      }

      if ((this.currentSelect.length <= 0) && !row) {
        this.$notify({
          title: '错误',
          message: '选择一个品种',
          type: 'warning'
        })
        return false
      }

      this.addDialog = true
      this.dynamicValidateForm.data = this.currentSelect
      this.dynamicValidateForm.exchange = row.exchange
      this.dynamicValidateForm.offset = row.offset
      this.dynamicValidateForm.symbol = symbol_list.length ? symbol_list : [row.symbol + '.' + row.exchange]
      this.dynamicValidateForm.trade_date = row.trade_date
      // this.dynamicValidateForm.direction = row.direction
      this.dynamicValidateForm.link_table = this.link_table[this.dynamicValidateForm.strategy_name]
      if (!this.dynamicValidateForm.strategy_args) {
        this.dynamicValidateForm.strategy_args = this.args_map[this.dynamicValidateForm.strategy_name]
      }

      this.dynamicValidateForm.curr_index = index

      console.log(this.dynamicValidateForm, this.dynamicValidateForm.strategy_name)
    },
    getData() {
      this.loading = true
      this.outerVisible = false
      this.$store.dispatch('shape/info', this.dynamicValidateForm).then((data) => {
        this.column = data.col
        data = data.list
        this.loading = false
        this.total = data.length
        console.log(this.total > this.pageSize, data.length)
        if (this.total > this.pageSize) {
          this.singlePage = false
        }
        console.log('submitForm', data)
        console.log('this.total', this.total, this.column)
        this.allTableData = data
        this.tableData = this.allTableData.slice(0, (this.pageSize))
      }).catch((err) => {
        console.error(err)
        this.loading = false
      })
    },
    submitForm(formName) {
      this.$refs[formName].validate((valid) => {
        if (valid) {
          this.$store.dispatch('shape/saveopen', this.dynamicValidateForm).then((data) => {
            this.addDialog = false

            this.$notify({
              title: '成功',
              message: '加入成功！',
              type: 'success'
            })
            this.tableData.splice(this.dynamicValidateForm.curr_index, 1)
          }).catch((err) => {
            console.error(err)
          })
        } else {
          console.log('error submit!!')
          return false
        }
      })
    },
    currentChange(page) {
      if (page === 1) {
        this.tableData = this.allTableData.slice(0, page * this.pageSize)
      } else {
        page = page - 1
        console.log(page * this.pageSize, this.pageSize, this.allTableData.slice(page * this.pageSize, (page * this.pageSize) + this.pageSize), this.allTableData)
        this.tableData = this.allTableData.slice(page * this.pageSize, (page * this.pageSize) + this.pageSize)
      }
    }
  }
}
</script>

<style>
.el-form-item__label{
  text-align: left;
  display: block;
}
.el-form-item__content{
  margin-left: 0;
}
</style>
