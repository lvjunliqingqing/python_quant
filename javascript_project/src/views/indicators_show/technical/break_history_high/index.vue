<template technical>
  <div style="padding:15px;">
    <el-alert :closable="false" title="突破历史高点" type="success">
      <template slot="title">
        <div style="font-size: 20px;color:red">突破历史高点</div>
      </template>
    </el-alert>
    <div class="break_history_high">
      <p>
        1.突破历史高点，相当突破历史行情压力位，压力位变成支持位，一般有一段上涨行情到来。
      </p>
      <p>
        2.选股条件-突破历史高点-历史周期：
      </p>
      <p>
        &nbsp;&nbsp;&nbsp;&nbsp;比如历史周期设置为5，则表示突破前5天的高价。设置为10则表示突破前10天的高价。
      </p>
    </div>
  </div>

</template>

<style scoped>
    .break_history_high{
        margin-left: 60px;
        font: bold normal 15px/15px Arial;
        text-align: left;
        text-indent: 32px;
        color: black;
        overflow: auto;
        line-height:21px;
    }
</style>
