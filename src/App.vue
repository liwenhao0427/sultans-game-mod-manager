<template>
  <div>
    <h1>Mod 管理程序</h1>
    <el-button type="primary" @click="exportSelected" :disabled="selectedMods.length === 0">
      导出选中
    </el-button>
    <el-table
        :data="mods"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="Mod 名称" width="200" />
      <el-table-column prop="author" label="作者" width="180" />
      <el-table-column prop="version" label="版本" width="120" />
      <el-table-column prop="gameVersion" label="游戏版本" width="160" />
      <el-table-column prop="updateDate" label="更新时间" width="180" />
      <el-table-column label="文件">
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
import JSZip from "jszip";
import { saveAs } from "file-saver";

export default {
  data() {
    return {
      mods: [], // 存储 Mod 信息
      selectedMods: [], // 存储选中的 Mod
    };
  },
  mounted() {
    this.loadMods();
  },
  methods: {
    loadMods() {
      const requireMod = require.context('@/assets/Mods', true, /modConfig\.json$/);
      const modFiles = requireMod.keys();

      this.mods = modFiles.map((filePath) => {
        const modConfig = requireMod(filePath);
        const modDir = filePath.split('/')[1];
        return {
          ...modConfig,
          name: modDir,
        };
      });
    },
    handleSelectionChange(selection) {
      this.selectedMods = selection;
    },
    async exportSelected() {
      const zip = new JSZip();

      for (const mod of this.selectedMods) {
        const modFolder = zip.folder(mod.name);
        for (const file of mod.files) {
          // 修正为public目录直连路径
          const filePath = `/Mods/${mod.name}/${file.source}`;
          const fileContent = await this.loadFile(filePath);
          
          // 创建目录结构
          let currentFolder = modFolder;
          const pathSegments = file.source.split('/').slice(0, -1);
          for (const segment of pathSegments) {
            currentFolder = currentFolder.folder(segment);
          }
          
          currentFolder.file(file.source.split('/').pop(), fileContent);
        }
        // 添加 modConfig.json 文件
        const modConfigContent = JSON.stringify(mod, null, 2);
        modFolder.file('modConfig.json', modConfigContent);
      }
      
      try {
        // 修正批处理文件访问路径
        const bat1Response = await fetch('/Mods/安装mod.txt');
        const bat1Blob = await bat1Response.blob();
        zip.file('安装mod.bat', bat1Blob);

        const bat2Response = await fetch('/Mods/还原mod.txt');
        const bat2Blob = await bat2Response.blob();
        zip.file('还原mod.bat', bat2Blob);
      } catch (error) {
        console.error('文件加载出错:', error);
      }

      zip.generateAsync({ type: "blob" }).then((content) => {
        saveAs(content, "mods.zip");
      });
    },
    async loadFile(filePath) {
      const response = await fetch(filePath);
      return response.blob();
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

.el-table th,
.el-table td {
  text-align: center;
}

.el-button {
  margin: 20px;
}
</style>
