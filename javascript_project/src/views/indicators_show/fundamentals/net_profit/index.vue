<template functionals>
  <div style="padding:15px;">
    <el-alert :closable="false" title="净利润" type="success">
      <template slot="title">
        <div style="font-size: 20px;color:red">净利润</div>
      </template>
    </el-alert>
    <div class="net_profit">
      <p>
        1.净利润:
        &nbsp;是指利润总额和除所得税后的利润
      </p>
      <p>
        2.公司净利润多，企业的经营效益就好；净利润少，企业的经营效益就差，它是衡量一个企业经营效益的主要指标。
      </p>
      <p>
        3.并不是净利润大的公司比净利润小的公司经营效益好，只有在公司资产规模在等同的情况下，才能说净利润大的公司比净利润小的公司经营效益好。
      </p>
      <p>
        4.净利润只能表示公司在盈利，不能直接用于公司和公司的比较。
      </p>
    </div>
  </div>

</template>

<style scoped>
    .net_profit{
        margin-left: 60px;
        font: bold normal 15px/15px Arial;
        text-align: left;
        text-indent: 32px;
        color: black;
        overflow: auto;
        line-height:21px;
    }
</style>
