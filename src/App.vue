<template>
  <div>
    <h1>Mod 管理程序</h1>
    <el-table :data="mods" style="width: 100%" border>
      <el-table-column prop="name" label="Mod 名称" width="200" />
      <el-table-column prop="author" label="作者" width="180" />
      <el-table-column prop="version" label="版本" width="120" />
      <el-table-column prop="gameVersion" label="游戏版本" width="160" />
      <el-table-column prop="updateDate" label="更新时间" width="180" />
      <el-table-column label="文件" >
        <template v-slot="scope">
          <el-ul>
            <li v-for="(file, index) in scope.row.files" :key="index">
              {{ file.source }}
              <br />
              <small>{{ file.modeDesc }} </small>
            </li>
          </el-ul>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      mods: [], // 存储 Mod 信息
    };
  },
  mounted() {
    this.loadMods();
  },
  methods: {
    loadMods() {
      // 动态加载 Mods 目录下的所有 modConfig.json 文件
      const requireMod = require.context('@/assets/Mods', true, /modConfig\.json$/); // 读取所有 modConfig.json 文件
      const modFiles = requireMod.keys();

      this.mods = modFiles.map((filePath) => {
        // 读取每个 modConfig.json 内容
        const modConfig = requireMod(filePath);
        const modDir = filePath.split('/')[2]; // 获取文件夹名，作为 mod 名称
        return {
          ...modConfig,
          name: modDir, // 设置 mod 名称为文件夹名
        };
      });
    },
  },
};
</script>

<style scoped>
/* 样式美化 */
h1 {
  text-align: center;
  margin-bottom: 20px;
  color: #42b983;
}

.el-table {
  margin: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.el-table-column {
  text-align: center;
}

.el-ul {
  list-style-type: none;
  padding-left: 0;
}

.el-ul li {
  font-size: 14px;
  color: #666;
}

.el-table th, .el-table td {
  text-align: center;
}
</style>
