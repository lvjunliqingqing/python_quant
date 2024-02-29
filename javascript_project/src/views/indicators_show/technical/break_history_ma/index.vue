<template technical>
  <div style="padding:15px;">
    <el-alert :closable="false" title="突破日均线" type="success">
      <template slot="title">
        <div style="font-size: 20px;color:red">突破日均线</div>
      </template>
    </el-alert>
    <div class="break_history_ma">
      <p>
        日均线在日K线图中一般白线、黄线、紫线、绿线、蓝线依次分别表示：5、10、20、30、60日移动平均线
      </p>
      <p>
        移动平均线
      </p>
      <p>
        （MA）理论是股市最常见的一种技术分析方法，它对股市操作具有神奇的指导作用。
      </p>
      <p>
        1、”黄金交叉”
      </p>
      <p>
        当10日均线由下往上穿越30日均线，形成10日均线在上，30日均线在下时，其交叉点就是黄金交叉，黄金交叉是多头的表现，出现黄金交叉后，后市会有一定的<a target="_blank" href="https://baike.baidu.com/item/%E6%B6%A8%E5%B9%85" style="color: rgb(19, 110, 194); text-decoration-line: none;">涨幅</a>空间，这是进场的最佳时机。
      </p>
      <p>
        2、”<a target="_blank" href="https://baike.baidu.com/item/%E6%AD%BB%E4%BA%A1%E4%BA%A4%E5%8F%89" style="color: rgb(19, 110, 194); text-decoration-line: none;">死亡交叉</a>”
      </p>
      <p>
        当10日均线由上往下穿越30日均线，形成30日均线在上，10日均线在下时，其交点称之为”死亡交叉”，”死亡交叉”预示空头市场来临，<a target="_blank" href="https://baike.baidu.com/item/%E8%82%A1%E5%B8%82/1390595" style="color: rgb(19, 110, 194); text-decoration-line: none;">股市</a>将下跌此时是出场的最佳时机。
      </p>
      <p>
        <br>
      </p>
      <p>
        移动平均线反映股票价格的变化，可以利用移动平均线理论来把握股票的买进和卖出时机：
      </p>
      <p>
        1、10日均线由K线图上方穿越K线图，位于K线之下方。由空转多，是买进时机。
      </p>
      <p>
        2、10日均线、30日均线和72日均线均由上而下穿越K线图，则表明该股<a target="_blank" href="https://baike.baidu.com/item/%E5%A4%9A%E5%A4%B4" style="color: rgb(19, 110, 194); text-decoration-line: none;">多头</a>的气势极为旺盛，涨势已成定局，是买进时机。
      </p>
      <p>
        3、10日均线、30日均线和72日均线位于K线图下方呈平行状，则表示是多头市场，后市<a target="_blank" href="https://baike.baidu.com/item/%E6%B6%A8%E5%B9%85" style="color: rgb(19, 110, 194); text-decoration-line: none;">涨幅</a>极大，是买进时机。
      </p>
      <p>
        4、10日均线由K线图下方穿越K线图至K线图上方。表示短线由多转空，是卖出时机。
      </p>
      <p>
        5、10日均线、30日均线和72日均线成由下而上顺次穿过K线图，该股将会有很深的跌幅，应及时卖出股票。
      </p>
      <p>
        6、72日、30日均线继10日均线之后，从下而上穿越K线图，右下方移动，跌幅将会很深，应及时卖出股票。
      </p>
      <p>
        7、10日、30日与72日平均线位于K线图上方且三线呈平行状，表明空头市场已确立，应卖出所有的股票。
      </p>
      <p>
        8、72日均线上升趋势转为平缓或向下方转折时，为卖出时机。
      </p>
      <p>
        <br>
      </p>
    </div>
  </div>

</template>

<style scoped>
    .break_history_ma{
        margin-left: 60px;
        font: bold normal 15px/15px Arial;
        text-align: left;
        text-indent: 32px;
        color: black;
        overflow: auto;
        line-height:21px;
    }
</style>
