<template>
  <div style="padding:5px;">
    <el-alert :closable="false" title="指标使用说明" type="success">
      <template slot="title">
        <div style="font-size: 30px;color:black">指标使用说明</div>
      </template>
      <router-view />
    </el-alert>
  </div>
</template>
