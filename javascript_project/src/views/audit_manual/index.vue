<template>
  <div class="app-container">

    <el-row style="margin:10px;">

      <!-- <el-date-picker
        v-model="trade_day"
        align="right"
        type="date"
        placeholder="选择日期"
        format="yyyy-MM-dd"
        value-format="yyyy-MM-dd"
        @change="changePicker"
        :picker-options="pickerOptions">
      </el-date-picker> -->

      <el-select v-model="audit_status" placeholder="审核状态" @change="changeSelect">
        <el-option
          v-for="item in audit_status_options"
          :key="item.value"
          :label="item.label"
          :value="item.value"
          :disabled="item.disabled"
        />
      </el-select>

      <el-select v-model="status" placeholder="状态" @change="statusChangeSelect">
        <el-option
          v-for="item in status_options"
          :key="item.value"
          :label="item.label"
          :value="item.value"
          :disabled="item.disabled"
        />
      </el-select>
    </el-row>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      style="width: 100%"
    >
      <el-table-column
        v-for="(col) in column"
        :key="col.key"
        :prop="col.key"
        :label="col.name"
        :sortable="col.sort"
        :formatter="col.formatter"
        :v-html="col.html"
        align="center"
      >
        <template slot-scope="scope">
          <el-tag
            v-if="col.key == 'direction'"
            effect="dark"
            :type="scope.row.direction === 'SHORT' ? 'success' : 'danger'"
            disable-transitions
          >{{ direction_map[scope.row.direction] }}</el-tag>
          <el-tag
            v-if="col.key == 'audit_status'"
            effect="plain"
            :type="scope.row.audit_status === 1 ? 'success' : 'danger'"
            disable-transitions
          >{{ audit_map[scope.row.audit_status] }}</el-tag>

          <el-tag
            v-if="col.key == 'status'"
            effect="plain"
            :type="scope.row.status === 1 ? 'success' : 'danger'"
            disable-transitions
          >{{ status_map[scope.row.status] }}</el-tag>
          <span v-if="col.key != 'direction' && col.key != 'audit_status' && col.key !='status'">{{ scope.row[col.key] }}</span>
        </template>

      </el-table-column>

      <el-table-column
        fixed="right"
        label="操作"
        width="140"
      >
        <template slot-scope="scope">

          <el-popconfirm
            v-if="scope.row.status == 1"
            confirm-button-text="暂停"
            cancel-button-text="关闭"
            icon="el-icon-info"
            icon-color="red"
            title="关闭或者暂停交易?"
            @onConfirm="PauseClick(scope.row, scope.$index)"
            @onCancel="CloseClick(scope.row, scope.$index)"
          >
            <el-button slot="reference" size="mini" type="warning">暂关</el-button>
          </el-popconfirm>
          <el-popconfirm
            v-if="scope.row.status == 0 || scope.row.status == -1"
            confirm-button-text="打开"
            cancel-button-text="关闭"
            icon="el-icon-info"
            icon-color="red"
            title="关闭或者打开交易?"
            @onConfirm="OpenClick(scope.row, scope.$index)"
            @onCancel="CloseClick(scope.row, scope.$index)"
          >
            <el-button slot="reference" size="mini" type="warning">开关</el-button>
          </el-popconfirm>

          <el-popconfirm
            confirm-button-text="通过"
            cancel-button-text="不通过"
            icon="el-icon-info"
            icon-color="red"
            title="通过审核,加入策略执行交易?"
            @onConfirm="AuditClick(scope.row, scope.$index)"
            @onCancel="AuditClickCancel(scope.row, scope.$index)"
          >
            <el-button slot="reference" size="mini" type="success">审核</el-button>
          </el-popconfirm>
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

  </div>
</template>

<style scoped>
.select {
  margin-bottom: 0;
}

</style>

<script>

export default {
  data() {
    return {
      form: {
      },
      newShape: false,
      trade_day: '',
      audit_status: '',
      status: '',
      default_trade_day: '',
      pickerOptions: {
        // disabledDate(time) {
        //   return time.getTime() > Date.now();
        // },
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

      audit_status_options: [

        {
          value: 'all',
          label: '所有'
        },
        {
          value: '0',
          label: '未审核'
        }, {
          value: '1',
          label: '已审核'
        }
      ],
      status_options: [
        {
          value: 'all',
          label: '所有'
        },
        {
          value: '1',
          label: '打开'
        }, {
          value: '0',
          label: '暂停'
        },
        {
          value: '-1',
          label: '关闭'
        }
      ],
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
        ]
      },
      direction_map: {
        'LONG': '多',
        'SHORT': '空',
        'NET': '多和空'
      },
      audit_map: {
        '0': '未通过',
        '1': '已通过'
      },
      status_map: {
        '0': '暂停中',
        '1': '打开中',
        '-1': '关闭中'
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
      audit_data: {}
    }
  },
  mounted() {
    this.loadData()
    this.getAllStrategy()
  },
  created() {
    console.log(1)
    var day2 = new Date()
    var s2 = day2.getFullYear() + '-' + (day2.getMonth() + 1) + '-' + day2.getDate()
    // this.dynamicValidateForm.trade_day = this.trade_day = s2
    this.dynamicValidateForm.audit_status = 'all'
    this.dynamicValidateForm.status = 'all'
  },
  methods: {
    changePicker(val) {
      this.trade_day = val
      this.dynamicValidateForm.trade_day = val
      this.loadData()
    },
    changeSelect(val) {
      this.audit_status = val
      this.dynamicValidateForm.audit_status = val
      this.loadData()
    },
    statusChangeSelect(val) {
      this.status = val
      this.dynamicValidateForm.status = val
      this.loadData()
    },
    getAllStrategy() {
      this.$store.dispatch('common/all_strategy', {}).then((data) => {
        this.strategy_name_options = data
      }).catch((err) => {
        console.error(err)
      })
    },
    loadData() {
      this.$store.dispatch('audit/manual_info', this.dynamicValidateForm).then((data) => {
        var colums = data.col

        for (var i in colums) {
          if (colums[i].key == 'audit_status') {
            colums[i].formatter = function(row, column, cellValue, index) {
              return row.audit_status == 0 ? '未审核' : '已审核'
            }
          } else if (colums[i].key == 'direction') {
            colums[i].formatter = function(row, column, cellValue, index) {
              switch (row.direction) {
                case 'LONG':
                  return '多'
                  break
                case 'SHORT':
                  return '空'
                  break
                case 'NET':
                  return '多&空'
                  break
              }
            }
          } else if (colums[i].key == 'status') {
            colums[i].formatter = function(row, column, cellValue, index) {
              switch (row.status) {
                case 1:
                  return '是'
                  break
                case 0:
                  return '否'
                  break
              }
            }
          }
        }

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
    strategyChange(val) {

      // this.dynamicValidateForm.strategy_name = val
    },
    PauseClick(row) {
      var data = {
        id: row.id,
        status: 0
      }

      this.submitForm(data)
    },
    CloseClick(row) {
      var data = {
        id: row.id,
        status: -1
      }

      this.submitForm(data)
    },
    OpenClick(row) {
      var data = {
        id: row.id,
        status: 1
      }

      this.submitForm(data)
    },
    AuditClick(row, index) {
      this.audit_data = row
      this.audit_data.curr_index = index

      if (row.audit_status) {
        this.$message({
          message: this.audit_data.symbol + '已经通过审核，无需再审核！',
          type: 'warning'
        })
        return
      }

      var data = {
        id: row.id,
        audit_status: 1
      }

      this.submitForm(data)
    },
    AuditClickCancel(row, index) {
      // this.audit_data = row
      this.audit_data.curr_index = index
      var data = {
        id: row.id,
        audit_status: 0
      }

      this.submitForm(data)
    },
    submitForm(data) {
      // this.audit_data.audit_status = audit_status

      this.$store.dispatch('audit/audit_manual', data).then((data) => {
        console.log(data)
        this.addDialog = false

        var msg = this.audit_data.symbol
        this.$notify({
          title: '成功',
          message: msg,
          type: 'success'
        })

        this.tableData.splice(this.audit_data.curr_index, 1)
      }).catch((err) => {
        console.error(err)
      })
    },
    currentChange(page) {
      if (page == 1) {
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
