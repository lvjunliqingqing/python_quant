<template>
  <div class="app-container">
    <el-row style="margin-bottom:1rem">
      <el-button type="primary" @click="outerVisible = true">选择条件</el-button>
      <el-button @click="exportCSV">导出</el-button>
    </el-row>

    <el-dialog title="选择条件" :visible.sync="outerVisible" width="70%">
      <el-form
        ref="dynamicValidateForm"
        :model="dynamicValidateForm"
        label-width="100px"
        label-position="right"
        :rules="rules"
        class="demo-dynamic"
      >
        <el-row :gutter="22">
          <el-col :span="10" style="border-right:1px solid #eee">
            <el-form-item
              label="选股条件"
              prop="condition"
            >
              <el-select
                v-model="dynamicValidateForm.condition"
                multiple
                placeholder="请选择条件"
                label="条件"
                class="select"
                prefix-icon="el-icon-s-opportunity"
                @change="condChange"
              >
                <el-option-group
                  v-for="group in conditionList"
                  :key="group.label"
                  :label="group.label"
                  class="select_group"
                >
                  <el-option
                    v-for="item in group.options"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                    class="select_group_child"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>

            <el-form-item
              label="指定日期"
              prop="end_date"
            >
              <el-date-picker
                v-model="dynamicValidateForm.end_date"
                align="right"
                label="指定日期"
                class="select"
                placeholder="选择日期"
                format="yyyy-MM-dd"
                value-format="yyyy-MM-dd"
                :picker-options="pickerOptions"
              />
            </el-form-item>
            <el-form-item
              label="指定周期"
              prop="cycle"
            >
              <el-select
                v-model="dynamicValidateForm.cycle"
                label="周期"
                class="select"
                placeholder="周期"
              >
                <el-option
                  v-for="item in options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              label="品种"
              prop="sec_type"
            >
              <el-select
                v-model="dynamicValidateForm.sec_type"
                label="品种"
                class="select"
                placeholder="品种"
                @change="secTypeChange()"
              >
                <el-option
                  v-for="item in sec_type_options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>

          </el-col>
          <el-col :span="10">
            <el-form-item
              v-for="(row, index) in dynamicValidateForm.dynamicParams"
              :key="index"
              :label="row.label"
              :rules="{
                required: true, message: '参数不能为空', trigger: 'blur'
              }"
            >
              <div v-if=" row.type == 'select' ">
                <el-select v-model="row.value" placeholder="请选择" style="float:left">
                  <el-option
                    v-for="item in logicOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </div>
              <div v-if=" row.type == 'input' ">
                <el-input-number
                  v-model="row.value"
                  controls-position="right"
                  :min="0"
                  :max="500000000"
                  show-word-limit
                  :precision="row.precision"
                  prefix-icon="el-icon-time"
                  :placeholder="row.label"
                />
              </div>
              <div v-if=" row.type == 'slider'">
                <el-slider
                  v-model="row.value"
                  range
                  :min="row.min"
                  :step="row.step"
                  :max="row.max"
                />
              </div>
            </el-form-item>
            <div v-if="dynamicValidateForm.dynamicParams.length<=0" class="noselect">
              <span style="color:#999;font-size:1rem">请选择条件</span>
            </div>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="outerVisible = false">取 消</el-button>
        <el-button :loading="loading" type="primary" @click="submitForm('dynamicValidateForm')">确 定</el-button>
      </div>
    </el-dialog>
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      style="width: 100%"
    >
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
      >
        <template slot-scope="scope">
          <el-button type="text" size="small" @click="KLineClick(scope.row)">K线图</el-button>
          <el-button type="text" size="small" @click="addClick(scope.row, scope.$index)">加入交易</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top:1rem;float:right"
      background
      layout="prev, pager, next"
      :hide-on-single-page="singlePage"
      :page-size="pageSize"
      :total="total"
      @current-change="currentChange"
    />

    <el-dialog
      :fullscreen="true"
      :visible.sync="kLineDialog"
    >
      <div ref="kline" style="width:100%;height:100%;min-height:700px" />
    </el-dialog>
    <el-dialog
      :visible.sync="addDialog"
      @close="diglogClose"
    >
      <el-row :gutter="20">
        <div style="padding-left:2rem;margin-bottom:1rem">{{ this.dynamicValidateFormStock.display_name }}-({{ this.dynamicValidateFormStock.symbol }}.{{ this.dynamicValidateFormStock.exchange }})</div>
      </el-row>
      <el-form
        ref="dynamicValidateFormStock"
        :model="dynamicValidateFormStock"
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
                v-model="dynamicValidateFormStock.strategy_name"
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
                v-model="dynamicValidateFormStock.direction"
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
          </el-col>
          <el-col v-if=" this.args_map[dynamicValidateFormStock.strategy_name]" :span="12" style="border-left:1px solid #eee;padding-left:2rem">
            <el-form-item
              v-for="(row, index) in this.args_map[dynamicValidateFormStock.strategy_name]"
              :key="index"
              label-width="auto"
              :label="row.name"
              :prop="index"
            >
              <el-input v-model="dynamicValidateFormStock.strategy_args[index].value" style="margin-bottom:1rem"	type="number" :placeholder="row.name" @input="inpuChange($event)" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="addDialog = false">取 消</el-button>
        <el-button :loading="sub_loading" type="primary" @click="submitOpenForm('dynamicValidateFormStock')">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.select {
  margin-bottom: 0;
}
.noselect{
  display: flex;
  justify-content: center;
  align-content: center;
  align-items: center;
  min-height: 10rem;
}
.select_group_child{
  padding-left: 2.2rem;
}
</style>

<script>

import FileSaver from 'file-saver'
const Json2csvParser = require('json2csv').Parser

const echarts = require('echarts/lib/echarts')
require('echarts/lib/chart/candlestick')
require('echarts/lib/chart/bar')
require('echarts/lib/chart/line')
require('echarts/lib/component/dataZoomInside')
require('echarts/lib/component/dataZoomSelect')
require('echarts/lib/component/dataZoomSlider')
require('echarts/lib/component/tooltip')
require('echarts/lib/component/legend')
require('echarts/lib/component/grid')
require('echarts/lib/component/title')
require('echarts/lib/component/calendar')
require('echarts/lib/component/markLine')
require('echarts/lib/component/markPoint')
require('echarts/lib/component/visualMapContinuous')
require('echarts/lib/component/visualMapPiecewise')

const datetime = Date.now()
const exportCSV = (data, filename = `${datetime}.csv`) => {
  const parser = new Json2csvParser()
  const csvData = parser.parse(data)
  const blob = new Blob(['\uFEFF' + csvData], { type: 'text/plain;charset=utf-8;' })
  FileSaver.saveAs(blob, filename)
}

export default {
  data() {
    const generateData = _ => {
      const data = []
      const cities = [
        {
          key: 'high',
          label: '突破高点'
        }
      ]
      const pinyin = ['shanghai', 'beijing']
      cities.forEach((obj, index) => {
        data.push({
          label: obj.label,
          key: obj.key,
          pinyin: pinyin[index]
        })
      })
      return data
    }

    return {
      column: [
        { 'name': '收盘日期', 'key': 'trade_date' },
        { 'name': '股票代码', 'key': 'symbol' },
        { 'name': '交易所', 'key': 'exchange' },
        { 'name': '股票名称', 'key': 'display_name' },
        { 'name': '收盘价', 'key': 'close' }
      ],
      logicOptions: [
        {
          label: '大于等于',
          key: 'gte',
          value: 'gte'
        },
        {
          label: '小于等于',
          key: 'lte',
          value: 'lte'
        }
      ],
      trade_day: '',
      form: {
        trade_day: '',
        symbol: '',
        direction: ''
      },
      default_trade_day: '',
      args_map: {},
      args_map_default: {},
      dynamicValidateFormStock: {
        'strategy_name': 'a11_full_auto_twodays_half'
      },
      link_table: {

      },
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
        ]
      },
      addDialog: false,
      kLineTitle: 'K线图',
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
      data0: [],
      singlePage: true,
      loading: false,
      sub_loading: false,
      allTableData: [],
      kLineDialog: false,
      dynamicFromList: {
        net_profit: [
          {
            type: 'select',
            key: 'net_profit_logic',
            label: '净利润条件',
            inputType: 'number',
            group: 'net_profit'
          },
          {
            type: 'input',
            key: 'net_profit_value',
            label: '净利润(万)',
            inputType: 'number',
            group: 'net_profit'
          }
        ]
      },
      dynamicValidateForm: {
        dynamicParams: [],
        condition: '',
        end_date: '',
        cycle: '',
        sec_type: 'stock'
      },
      rules: {
        cycle:
        [
          { required: true, message: '请选择周期', trigger: 'change' }
        ],
        condition:
        [
          { required: true, message: '请选择指定条件', trigger: 'change' }
        ],
        end_date:
        [
          { required: true, message: '请选择指定日期', trigger: 'change' }
        ]
      },
      tableData: [
      ],
      normData: generateData(),
      listLoading: true,
      outerVisible: false,
      normValue: [],
      pageSize: 10,
      selectDate: '',
      filterMethod(query, item) {
        return item.pinyin.indexOf(query) > -1
      },
      options: [
        {
          value: 'day',
          label: '日线'
        },
        {
          value: 'month',
          label: '月线'
        }
      ],
      options_bak: [
        {
          value: 'day',
          label: '日线'
        },
        {
          value: 'month',
          label: '月线'
        }
      ],
      sec_type_options: [
        {
          value: 'stock',
          label: '股票'
        },
        {
          value: 'futures',
          label: '期货'
        }
      ],
      conditionList: [],
      conditionValue: '',
      selectValue: '',
      total: 0
    }
  },

  mounted() {
    this.$store.dispatch('common/condition_list').then((data) => {
      this.conditionList = data
      console.log('data:', JSON.stringify((this.conditionList)))
    })

    this.$store.dispatch('common/dynamic_from_list').then((data) => {
      this.dynamicFromList = data
    })

    this.getAllStrategy()
  },
  created() {
    var day2 = new Date()
    var s2 = day2.getFullYear() + '-' + (day2.getMonth() + 1) + '-' + day2.getDate()
    this.dynamicValidateForm.end_date = s2
  },
  methods: {
    addClick(row, index) {
      this.addDialog = true
      this.dynamicValidateFormStock.data = row
      this.dynamicValidateFormStock.exchange = row.exchange
      this.dynamicValidateFormStock.offset = 'OPEN'
      this.dynamicValidateFormStock.display_name = row.display_name
      this.dynamicValidateFormStock.symbol = row.symbol
      this.dynamicValidateFormStock.trade_date = row.trade_date
      this.dynamicValidateFormStock.direction = 'LONG'
      this.dynamicValidateFormStock.link_table = this.link_table[this.dynamicValidateFormStock.strategy_name]
      if (!this.dynamicValidateFormStock.strategy_args) {
        this.dynamicValidateFormStock.strategy_args = this.args_map[this.dynamicValidateFormStock.strategy_name]
      }

      this.dynamicValidateFormStock.curr_index = index
    },
    submitOpenForm(formName) {
      this.$refs[formName].validate((valid) => {
        if (valid) {
          this.dynamicValidateFormStock.link_table = 'dhtz_stock_open_symbol_data'
          this.$store.dispatch('stock/stock_saveopen', this.dynamicValidateFormStock).then((data) => {
            this.addDialog = false

            this.$notify({
              title: '成功',
              message: '加入成功！',
              type: 'success'
            })
            this.tableData.splice(this.dynamicValidateFormStock.curr_index, 1)
          }).catch((err) => {
            console.error(err)
          })
        } else {
          console.log('error submit!!')
          return false
        }
      })
    },
    strategyChange(value) {
      this.loadStratgyArgs()
    },
    directionChange() {

    },
    diglogClose() {

    },
    secTypeChange() {
      if (this.dynamicValidateForm.sec_type == 'futures') {
        this.options = [this.options.shift()]
        this.dynamicValidateForm.cycle = 'day'
      } else {
        var opt = []
        opt = JSON.parse(JSON.stringify(this.options_bak))
        this.options = opt
      }
      console.log(this.options)
      // this.options =
    },
    exportCSV() {
      var list = []
      for (var i in this.allTableData) {
        list.push({ 'symbol': '' + this.allTableData[i]['symbol'] })
      }
      exportCSV(list)
    },
    loadStratgyArgs() {
      var symbol = this.dynamicValidateFormStock.data.symbol

      // var reg = RegExp(/^[a-zA-Z]{1,3}/)

      // symbol = symbol.match(reg)[0]
      console.log(symbol)

      var data = {
        symbol: symbol,
        exchange: this.dynamicValidateFormStock.data.exchange,
        strategy_name: this.dynamicValidateFormStock.strategy_name,
        direction: this.dynamicValidateFormStock.direction
      }
      var val = this.dynamicValidateFormStock.strategy_name

      this.$store.dispatch('common/strategy_by_symbol', data).then((data) => {
        if (data.strategy_args) {
          var strategy_args = JSON.parse(data.strategy_args)

          console.log(strategy_args, this.args_map)

          this.dynamicValidateFormStock.strategy_args = strategy_args
          this.args_map[val] = strategy_args
        } else {
          this.args_map[val] = this.args_map_default[val]
        }

        this.dynamicValidateFormStock.link_table = this.link_table[val]
      }).catch((err) => {
        console.error(err)
        this.loading = false
      })

      this.dynamicValidateFormStock.strategy_args = this.args_map[this.dynamicValidateFormStock.strategy_name]
    },
    getAllStrategy() {
      this.$store.dispatch('stock/get_dhtz_stock_strategy_desc', {}).then((data) => {
        var tmp = {}
        for (var i in data) {
          if (data[i].strategy_args) {
            var tmp_args = JSON.parse(data[i].strategy_args)
            this.args_map[data[i].strategy_class_name] = tmp_args
            this.args_map_default[data[i].strategy_class_name] = tmp_args
            this.link_table[data[i].strategy_class_name] = data[i].link_table
          }
        }

        this.dynamicValidateFormStock.strategy_args = this.args_map[this.dynamicValidateFormStock.strategy_name]
        this.dynamicValidateFormStock.link_table = this.link_table[this.dynamicValidateFormStock.strategy_name]

        console.log(this.dynamicValidateFormStock.link_table)

        this.strategy_name_options = data
      }).catch((err) => {
        console.error(err)
      })
    },
    KLineClick(row) {
      this.kLineDialog = true
      row.cycle = this.dynamicValidateForm.cycle
      row.sec_type = this.dynamicValidateForm.sec_type
      this.$store.dispatch('stock/kline', row).then((data) => {
        this.loading = false
        this.kLineTitle = (row.display_name + '(' + row.symbol + ')')
        // 数据意义：开盘(open)，收盘(close)，最低(lowest)，最高(highest)
        console.log('data', data)
        this.data0 = this.splitData(data)
        this.$nextTick(() => {
          console.log('this.data0', this.data0)
          var myChart = echarts.init(this.$refs.kline)
          var upColor = '#ec0000'
          var upBorderColor = '#8A0000'
          var downColor = '#00da3c'
          var downBorderColor = '#008F28'
          var option = {
            title: {
              text: this.kLineTitle,
              left: 0
            },
            tooltip: {
              trigger: 'axis',
              axisPointer: {
                type: 'cross'
              },
              backgroundColor: 'rgba(245, 245, 245, 0.8)',
              borderWidth: 1,
              borderColor: '#ccc',
              padding: 10,
              textStyle: {
                color: '#000'
              }
              // extraCssText: 'width: 170px'
            },
            legend: {
              data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30'],
              selected: {
                '日K': true,
                'MA5': false,
                'MA10': false,
                'MA20': false,
                'MA30': false
              }
            },
            axisPointer: {
              link: {
                xAxisIndex: 'all'
              },
              label: {
                backgroundColor: '#777'
              }
            },
            grid: [
              {
                left: '10%',
                right: '8%',
                height: '50%'
              },
              {
                left: '10%',
                right: '8%',
                top: '63%',
                height: '16%'
              }
            ],
            visualMap: {
              show: false,
              seriesIndex: 5,
              dimension: 2,
              pieces: [{
                value: 1,
                color: downColor
              }, {
                value: -1,
                color: upColor
              }]
            },
            xAxis: [
              {
                type: 'category',
                data: this.data0.categoryData,
                scale: true,
                boundaryGap: false,
                axisLine: { onZero: false },
                splitLine: { show: false },
                splitNumber: 20,
                min: 'dataMin',
                max: 'dataMax'
              },
              {
                type: 'category',
                gridIndex: 1,
                data: this.data0.categoryData,
                scale: true,
                boundaryGap: false,
                axisLine: { onZero: false },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false },
                splitNumber: 20,
                min: 'dataMin',
                max: 'dataMax'
              }
            ],
            yAxis: [
              {
                scale: true,
                splitArea: {
                  show: true
                }
              },
              {
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: { show: false },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { show: false }
              }
            ],
            dataZoom: [
              {
                type: 'inside',
                start: 80,
                xAxisIndex: [0, 1],
                end: 100
              },
              {
                show: true,
                type: 'slider',
                xAxisIndex: [0, 1],
                top: '90%',
                start: 80,
                end: 100
              }
            ],
            series: [
              {
                name: '日K线',
                type: 'candlestick',
                data: this.data0.values,
                itemStyle: {
                  color: upColor,
                  color0: downColor,
                  borderColor: upBorderColor,
                  borderColor0: downBorderColor
                },
                tooltip: {
                  formatter: function(param) {
                    param = param[0]
                    return [
                      'Date: ' + param.name + '<hr size=1 style="margin: 3px 0">',
                      'Open: ' + param.data[0] + '<br/>',
                      'Close: ' + param.data[1] + '<br/>',
                      'Lowest: ' + param.data[2] + '<br/>',
                      'Highest: ' + param.data[3] + '<br/>'
                    ].join('')
                  }
                }
              },
              {
                name: 'MA5',
                type: 'line',
                data: this.calculateMA(5),
                smooth: true,
                lineStyle: {
                  opacity: 0.5
                }
              },
              {
                name: 'MA10',
                type: 'line',
                data: this.calculateMA(10),
                smooth: true,
                lineStyle: {
                  opacity: 0.5
                }
              },
              {
                name: 'MA20',
                type: 'line',
                data: this.calculateMA(20),
                smooth: true,
                lineStyle: {
                  opacity: 0.5
                }
              },
              {
                name: 'MA30',
                type: 'line',
                data: this.calculateMA(30),
                smooth: true,
                lineStyle: {
                  opacity: 0.5
                }
              },
              {
                name: 'Volume',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: this.data0.volumes
              }
            ]
          }
          myChart.setOption(option)
        })
      }).catch((err) => {
        console.error(err)
        this.loading = false
      })
    },
    splitData(rawData) {
      var categoryData = []
      var values = []
      var volumes = []
      for (var i = 0; i < rawData.length; i++) {
        categoryData.push(rawData[i].splice(0, 1)[0])
        values.push(rawData[i])
        volumes.push([i, rawData[i][4], rawData[i][0] > rawData[i][1] ? 1 : -1])
      }
      return {
        categoryData: categoryData,
        values: values,
        volumes: volumes
      }
    },
    calculateMA(dayCount) {
      var result = []
      for (var i = 0, len = this.data0.values.length; i < len; i++) {
        if (i < dayCount) {
          result.push('-')
          continue
        }
        var sum = 0
        for (var j = 0; j < dayCount; j++) {
          sum += this.data0.values[i - j][1]
        }
        result.push((sum / dayCount).toFixed(2))
      }
      return result
    },
    submitForm(formName) {
      this.$refs[formName].validate((valid) => {
        if (valid) {
          this.loading = true
          this.outerVisible = false
          this.$store.dispatch('stock/condition', this.dynamicValidateForm).then((data) => {
            this.column = data.col
            data = data.list
            this.loading = false
            this.total = data.length
            console.log(this.total > this.pageSize)
            if (this.total > this.pageSize) {
              this.singlePage = false
            }
            console.log('submitForm', data)
            console.log('this.total', this.total, this.column)
            this.allTableData = data
            this.tableData = this.allTableData.slice(0, this.pageSize)
          }).catch((err) => {
            console.error(err)
            this.loading = false
          })
          console.log(this.dynamicValidateForm)
        } else {
          console.log('error submit!!')
          return false
        }
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
    },
    condChange(data) {
      console.log('condChange', data)
      this.dynamicValidateForm.dynamicParams = []
      for (var i in data) {
        var From = this.dynamicFromList[data[i]]
        for (var j in From) {
          console.log('From', From[j], j, data[i])
          this.dynamicValidateForm.dynamicParams.push(
            From[j]
          )
        }
      }
      console.log('this.dynamicValidateForm.dynamicParams', this.dynamicValidateForm.dynamicParams)
    }
  }
}
</script>
