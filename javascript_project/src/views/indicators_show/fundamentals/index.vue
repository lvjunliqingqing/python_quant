<template>
  <div style="padding:15px;">
    <el-alert :closable="false" title="基本面指标" type="success">
      <template slot="title">
        <div style="font-size: 25px;color:green">基本面指标</div>
      </template>
      <router-view />
    </el-alert>
  </div>
</template>
