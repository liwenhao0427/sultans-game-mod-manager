<template>
  <div class="mod-manager-container">
    <div class="header">
      <h1>Mod 管理程序</h1>
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索Mod名称、作者或版本..."
          prefix-icon="el-icon-search"
          clearable
          @clear="handleSearchClear"
        />
      </div>
    </div>

    <div class="toolbar">
      <el-button type="primary" @click="exportSelected" :disabled="selectedMods.length === 0">
        <i class="el-icon-download"></i> 导出选中 ({{ selectedMods.length }})
      </el-button>
      <el-button @click="resetFilters" plain>
        <i class="el-icon-refresh"></i> 重置筛选
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table
        :data="paginatedData"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
        :default-sort="{prop: 'updateDate', order: 'descending'}"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="Mod 名称" width="200" sortable>
          <template v-slot="scope">
            <div class="mod-name">{{ scope.row.name }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="180" sortable>
          <template v-slot="scope">
            <el-tag size="small">{{ scope.row.author }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="120" sortable />
        <el-table-column prop="gameVersion" label="游戏版本" width="160" sortable>
          <template v-slot="scope">
            <el-tag type="success" size="small">{{ scope.row.gameVersion }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updateDate" label="更新时间" width="180" sortable />
        <el-table-column label="文件">
          <template v-slot="scope">
            <el-collapse accordion>
              <el-collapse-item>
                <template #title>
                  <span class="file-count">{{ scope.row.files.length }} 个文件</span>
                </template>
                <el-list>
                  <el-list-item v-for="(file, index) in scope.row.files" :key="index" class="file-item">
                    <div class="file-info">
                      <div class="file-source">{{ file.source }}</div>
                      <div class="file-mode">{{ file.modeDesc }}</div>
                    </div>
                    <el-button type="primary" size="small" @click="viewFileDetails(scope.row.name, file.source)">
                      查看详情
                    </el-button>
                  </el-list-item>
                </el-list>
              </el-collapse-item>
            </el-collapse>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[5, 10, 20, 50]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredMods.length"
        />
      </div>
    </el-card>

    <el-dialog
      title="文件详情"
      v-model="fileDetailsVisible"
      width="80%"
      class="file-details-dialog"
    >
      <div class="file-content-container">
        <pre>{{ fileContent }}</pre>
      </div>
      <template #footer>
        <el-button @click="fileDetailsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import JSZip from "jszip";
import { saveAs } from "file-saver";

export default {
  data() {
    return {
      fileDetailsVisible: false,
      fileContent: '', // Stores the content of the selected file
      mods: [], // 存储 Mod 信息
      selectedMods: [], // 存储选中的 Mod
      loading: true,
      searchQuery: '',
      currentPage: 1,
      pageSize: 10,
    };
  },
  computed: {
    filteredMods() {
      if (!this.searchQuery) {
        return this.mods;
      }
      
      const query = this.searchQuery.toLowerCase();
      return this.mods.filter(mod => {
        return (
          mod.name.toLowerCase().includes(query) ||
          (mod.author && mod.author.toLowerCase().includes(query)) ||
          (mod.version && mod.version.toLowerCase().includes(query)) ||
          (mod.gameVersion && mod.gameVersion.toLowerCase().includes(query))
        );
      });
    },
    paginatedData() {
      const startIndex = (this.currentPage - 1) * this.pageSize;
      const endIndex = startIndex + this.pageSize;
      return this.filteredMods.slice(startIndex, endIndex);
    }
  },
  mounted() {
    this.loadMods();
  },
  methods: {
    async viewFileDetails(modName, fileSource) {
      const filePath = `/Mods/${modName}/${fileSource}`;
      console.log(filePath)
      try {
        const response = await fetch(filePath);
        if (!response.ok) {
          throw new Error(`Failed to fetch file: ${filePath}`);
        }
        this.fileContent = await response.text();
        this.fileDetailsVisible = true;
      } catch (error) {
        console.error('Error fetching file details:', error);
        this.$message.error('无法加载文件详情');
      }
    },
    loadMods() {
      this.loading = true;
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
      this.loading = false;
    },
    handleSelectionChange(selection) {
      this.selectedMods = selection;
    },
    async exportSelected() {
      this.loading = true;
      const zip = new JSZip();

      // 添加sed.exe到zip根目录
      try {
        const sedResponse = await fetch('/苏丹的游戏mod管理器.exe');
        const sedBlob = await sedResponse.blob();
        zip.file('苏丹的游戏mod管理器.exe', sedBlob);
      } catch (error) {
        console.error('苏丹的游戏mod管理器.exe加载出错:', error);
      }

      // 创建Mods文件夹
      const modsFolder = zip.folder("Mods");

      for (const mod of this.selectedMods) {
        const modFolder = modsFolder.folder(mod.name);
        for (const file of mod.files) {
          const filePath = `/Mods/${mod.name}/${file.source}`;
          const fileContent = await this.loadFile(filePath);

          // 创建目录结构
          let currentFolder = modFolder;
          const pathSegments = file.source.split('/').slice(0, -1);
          for (const segment of pathSegments) {
            currentFolder = currentFolder.folder(segment);
          }

          const fileName = file.source.split('/').pop();
          currentFolder.file(fileName, fileContent);

          // 创建.config文件
          const configFileName = fileName.replace('.json', '.config');
          const targetPath = file.destination || file.source;

          let configContent = file.mode + '\n';
          configContent += targetPath + '\n';
          configContent += (file.val1 || '') + '\n';
          configContent += (file.val2 || '');

          currentFolder.file(configFileName, configContent);
        }
      }

      zip.generateAsync({ type: "blob" }).then((content) => {
        saveAs(content, "mods.zip");
        this.loading = false;
        this.$message.success(`已成功导出 ${this.selectedMods.length} 个Mod`);
      });
    },
    async loadFile(filePath) {
      const response = await fetch(filePath);
      return response.blob();
    },
    handleSizeChange(val) {
      this.pageSize = val;
      this.currentPage = 1;
    },
    handleCurrentChange(val) {
      this.currentPage = val;
    },
    handleSearchClear() {
      this.searchQuery = '';
    },
    resetFilters() {
      this.searchQuery = '';
      this.currentPage = 1;
    }
  },
};
</script>

<style scoped>
.mod-manager-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

h1 {
  color: #409EFF;
  font-size: 28px;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

.search-bar {
  width: 300px;
}

.toolbar {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 20px;
  gap: 10px;
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.mod-name {
  font-weight: bold;
  color: #409EFF;
}

.file-count {
  color: #606266;
  font-size: 14px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #EBEEF5;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.file-source {
  font-weight: bold;
  color: #303133;
}

.file-mode {
  font-size: 12px;
  color: #909399;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.file-details-dialog .file-content-container {
  max-height: 70vh;
  overflow-y: auto;
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', Courier, monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #303133;
}

.el-tag {
  margin-right: 5px;
}
</style>
