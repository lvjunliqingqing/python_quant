<template functionals>
  <div style="padding:15px;">
    <el-alert :closable="false" title="市盈率" type="success">
      <template slot="title">
        <div style="font-size: 20px;color:red">市盈率</div>
      </template>
    </el-alert>
    <div class="pe_ration">
      <p>
        1.市盈率是指股票价格/每股收益&nbsp;
      </p>
      <p>
        2.一般来说，市盈率水平为：
        &nbsp; &nbsp;
      </p>
      <p>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&lt;0 ：指该公司盈利为负（因盈利为负，计算市盈率没有意义，一般软件显示为&quot;—&quot;）
        &nbsp; &nbsp;
      </p>
      <p>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;0-13 ：即价值被低估
        &nbsp; &nbsp;
      </p>
      <p>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;14-20：即正常水平
        &nbsp; &nbsp;
      </p>
      <p>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;21-28：即价值被高估
        &nbsp; &nbsp;
      </p>
      <p>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;28+ ：反映股市出现投机性泡沫&nbsp;
      </p>
      <p>
        3.不同行业的市盈率标准的范围是不一样的。&nbsp;
      </p>
      <p>
        4.一般情况下,市盈率越低,投资风险越小,盈利越强。但也不能一概而论,有时、市盈率越低,表明该公司前景欠佳,投资者对其没有太大的信心;市盈率高,表明投资者普遍持乐观态度,对公司充满了信心。投资者要具体股票具体分析,对一些成长性较好的股票其市盈率偏高是较正常的。
      </p>
    </div>
  </div>

</template>

<style scoped>
    .pe_ration{
        margin-left: 60px;
        font: bold normal 15px/15px Arial;
        text-align: left;
        text-indent: 32px;
        color: black;
        overflow: auto;
        line-height:21px;
    }
</style>
