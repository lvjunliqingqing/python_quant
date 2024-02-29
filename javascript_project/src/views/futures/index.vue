<template>
  <div class="app-container">
    <el-row style="margin-bottom:1rem">
      <el-button type="primary" @click="outerVisible = true">条件</el-button>
    </el-row>

    <el-dialog title="条件" :visible.sync="outerVisible">
      <el-form
        ref="dynamicValidateForm"
        :model="dynamicValidateForm"
        label-width="80px"
        label-position="right"
        :rules="rules"
        class="demo-dynamic"
      >
        <el-row :gutter="20">
          <el-col :span="10" style="border-right:1px solid #eee">
            <el-form-item
              label="指定条件"
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
                <el-option
                  v-for="item in conditionList"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
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
          </el-col>
          <el-col :span="10">
            <el-form-item
              v-for="(row, index) in dynamicValidateForm.dynamicParams"
              :key="row.key"
              :label="row.label"
              :prop="'dynamicParams.' + index + '.value'"
              :rules="{
                required: true, message: '参数不能为空', trigger: 'blur'
              }"
            >
              <el-input
                v-model="row.value"
                maxlength="5"
                show-word-limit
                type="number"
                prefix-icon="el-icon-time"
                :placeholder="row.label"
              />
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
        prop="trade_date"
        label="收盘日期"
        align="center"
        width="180"
      />
      <el-table-column
        prop="symbol"
        align="center"
        label="股票代码"
        @click="KLineClick(scope.row)"
      />
      <el-table-column
        prop="exchange"
        align="center"
        label="交易所"
      />
      <el-table-column
        prop="display_name"
        align="center"
        label="股票名称"
      />
      <el-table-column
        prop="high"
        align="center"
        label="历史高价"
      />
      <el-table-column
        prop="close"
        align="center"
        sortable
        label="收盘价"
      />
      <el-table-column
        prop="break_bill"
        align="center"
        sortable
        label="突破比例(%)"
      />
      <el-table-column
        fixed="right"
        label="操作"
        width="100"
      >
        <template slot-scope="scope">
          <el-button type="text" size="small" @click="KLineClick(scope.row)">K线图</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top:1rem;float:right"
      background
      layout="prev, pager, next"
      :hide-on-single-page="singlePage"
      :page-size="20"
      :total="total"
      @current-change="currentChange"
    />

    <el-dialog
      :fullscreen="true"
      :visible.sync="kLineDialog"
    >
      <div ref="kline" style="width:100%;height:100%;min-height:700px" />
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
</style>

<script>

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
      allTableData: [],
      kLineDialog: false,
      dynamicFromList: {
        break_high: [
          {
            type: 'input',
            key: 'break_high_value',
            label: '历史周期',
            inputType: 'number',
            logic: '>=',
            icon: 'el-icon-time',
            group: 'break_high'
          }
        ],
        break_ma: [
          {
            type: 'input',
            key: 'break_ma_value',
            label: '均线周期',
            logic: '>=',
            inputType: 'number',
            group: 'break_ma'
          }
        ]
      },
      dynamicValidateForm: {
        dynamicParams: [],
        condition: '',
        end_date: '',
        cycle: ''
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
      conditionList: [
        {
          label: '突破历史高点',
          value: 'break_high'
        },
        {
          label: '突破均线',
          value: 'break_ma'
        }
      ],
      conditionValue: '',
      selectValue: '',
      total: 0
    }
  },
  mounted() {

  },
  created() {
    console.log(1)
    var day2 = new Date()
    var s2 = day2.getFullYear() + '-' + (day2.getMonth() + 1) + '-' + day2.getDate()
    this.dynamicValidateForm.end_date = s2
  },
  methods: {
    KLineClick(row) {
      this.kLineDialog = true

      row.cycle = this.dynamicValidateForm.cycle

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
              data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30']
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
            this.loading = false

            this.total = data.length
            if (this.total > this.pageSize) {
              this.singlePage = false
            }
            console.log('submitForm', data)
            console.log('this.total', this.total)
            this.allTableData = data
            this.tableData = this.allTableData.slice(0, this.pageSize - 1)
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
        this.tableData = this.allTableData.slice(0, page * this.pageSize - 1)
      } else {
        console.log(page * this.pageSize, this.pageSize, this.allTableData.slice(page * this.pageSize, (page * this.pageSize) + this.pageSize - 1), this.allTableData)
        this.tableData = this.allTableData.slice(page * this.pageSize, (page * this.pageSize) + this.pageSize - 1)
      }
    },
    condChange(data) {
      console.log('condChange', data)
      this.dynamicValidateForm.dynamicParams = []
      for (var i in data) {
        var From = this.dynamicFromList[data[i]]
        var tmp = []
        for (var j in From) {
          console.log('From', From[j], j, data[i])
          this.dynamicValidateForm.dynamicParams.push(
            {
              label: From[j].label,
              key: From[j].key,
              value: '',
              logic: From[j].logic,
              group: From[j].group
            }
          )
        }
      }
    }
  }
}
</script>
