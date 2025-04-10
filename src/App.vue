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
      <el-button type="primary" @click="showExportDialog" :disabled="selectedMods.length === 0">
        <i class="el-icon-download"></i> 导出选中 ({{ selectedMods.length }})
      </el-button>
      <el-button @click="resetFilters" plain>
        <i class="el-icon-refresh"></i> 重置筛选
      </el-button>
    </div>

    <!-- 导出选项对话框 -->
    <el-dialog
      v-model="exportDialogVisible"
      title="导出选项"
      width="400px"
    >
      <el-form label-position="top">
        <el-form-item label="导出内容">
          <el-checkbox v-model="exportOptions.includeMods" disabled>MOD文件</el-checkbox>
          <el-checkbox v-model="exportOptions.includeManager">MOD管理器(exe)</el-checkbox>
          <el-checkbox v-model="exportOptions.includeScript">MOD安装脚本(py)</el-checkbox>
        </el-form-item>
        <el-form-item label="文件名">
          <el-input v-model="exportOptions.fileName" placeholder="导出文件名"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="exportDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="exportSelected">
            确认导出
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-card class="table-card">
      <el-table
        :data="paginatedData"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
        :default-sort="{prop: 'recommend', order: 'descending'}"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="Mod 名称" width="180" sortable>
          <template v-slot="scope">
            <div class="mod-name">{{ scope.row.name }}</div>
          </template>
        </el-table-column>
        <!-- <el-table-column prop="recommend" label="推荐度" width="180" sortable>
          <template v-slot="scope">
            <el-rate
              v-model="scope.row.recommend"
              disabled
              show-score
              text-color="#ff9900"
            />
          </template>
        </el-table-column> -->
        <el-table-column prop="author" label="作者" width="150" sortable column-key="author" :filters="getColumnFilters('author')" :filter-method="filterHandler">
          <template v-slot="scope">
            <el-tag size="small">{{ scope.row.author }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="100" sortable column-key="version" :filters="getColumnFilters('version')" :filter-method="filterHandler" />
        <el-table-column prop="gameVersion" label="游戏版本" width="120" sortable column-key="gameVersion" :filters="getColumnFilters('gameVersion')" :filter-method="filterHandler">
          <template v-slot="scope">
            <el-tag type="success" size="small">{{ scope.row.gameVersion }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updateDate" label="更新时间" width="150" sortable />
        <el-table-column label="标签" width="200">
          <template v-slot="scope">
            <div class="tag-container">
              <el-tag 
                v-for="(tag, index) in getModTags(scope.row)" 
                :key="index" 
                size="small" 
                :type="tag === '纯替换' ? 'danger' : getTagType(index)" 
                effect="plain"
                class="mod-tag"
              >
                {{ tag }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
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
                      <div class="file-mode">
                        <el-tag :type="getModeTagType(file.mode)" size="mini">
                          {{ getModeDescription(file.mode) }}
                        </el-tag>
                        <span class="file-mode-params" v-if="file.val1">
                          参数1: {{ file.val1 }}
                        </span>
                        <span class="file-mode-params" v-if="file.val2">
                          参数2: {{ file.val2 }}
                        </span>
                      </div>
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
// Remove the unused import
// import { Search } from '@element-plus/icons-vue';

export default {
  name: 'App',
  components: {
    // Remove the unused component registration
    // Search
  },
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
      // 新增导出选项相关数据
      exportDialogVisible: false,
      exportOptions: {
        includeMods: true, // 默认必须包含MOD文件
        includeManager: true, // 默认包含管理器
        includeScript: false, // 默认不包含脚本
        fileName: 'mods.zip'
      },
      // 模式描述映射
      modeDescriptions: {
        'REPLACE': '完全替换',
        'REPLACE0': '查找替换文本',
        'REPLACE1': '替换两个标记间内容',
        'APPEND': '末尾追加内容',
        'INSERT': '指定位置插入内容'
      },
      // 模式标签类型映射
      modeTagTypes: {
        'REPLACE': 'danger',
        'REPLACE0': 'warning',
        'REPLACE1': 'warning',
        'APPEND': 'info',
        'INSERT': 'info'
      }
    };
  },
  computed: {
    filteredMods() {
      if (!this.searchQuery) {
        return this.sortMods(this.mods);
      }
      
      const query = this.searchQuery.toLowerCase();
      const filtered = this.mods.filter(mod => {
        return (
          mod.name.toLowerCase().includes(query) ||
          (mod.author && mod.author.toLowerCase().includes(query)) ||
          (mod.version && mod.version.toLowerCase().includes(query)) ||
          (mod.gameVersion && mod.gameVersion.toLowerCase().includes(query)) ||
          (mod.tag && mod.tag.some(tag => tag.toLowerCase().includes(query)))
        );
      });
      
      return this.sortMods(filtered);
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
    // 显示导出对话框
    showExportDialog() {
      // 设置默认文件名
      this.exportOptions.fileName = `mods_${this.selectedMods.length}.zip`;
      this.exportDialogVisible = true;
    },
    
    async viewFileDetails(modName, fileSource) {
      try {
        // 使用require动态导入文件内容
        const fileContent = await this.getFileContent(modName, fileSource);
        
        // 只有modConfig.json才尝试格式化为JSON
        if (fileSource === 'modConfig.json') {
          try {
            const jsonObj = JSON.parse(fileContent);
            this.fileContent = JSON.stringify(jsonObj, null, 2);
          } catch (e) {
            // 如果解析失败，仍然显示原始文本
            this.fileContent = fileContent;
          }
        } else {
          // 其他JSON文件直接显示为文本
          this.fileContent = fileContent;
        }
        
        this.fileDetailsVisible = true;
      } catch (error) {
        console.error('Error loading file details:', error);
        this.$message.error('无法加载文件详情');
      }
    },
    
    // 修改从assets目录获取文件内容的方法
    async getFileContent(modName, fileSource) {
      try {
        // 根据文件扩展名选择不同的加载方式
        const fileExt = fileSource.split('.').pop().toLowerCase();
        
        if (fileExt === 'json' || fileExt === 'txt' || fileExt === 'config') {
          // 所有文本文件都使用raw-loader，并指定esModule: false
          try {
            const textContent = require(`!!raw-loader?esModule=false!@/assets/Mods/${modName}/${fileSource}`);
            return textContent; // 不再需要 .default，因为设置了 esModule: false
          } catch (error) {
            console.error(`无法加载文件: ${modName}/${fileSource}`, error);
            throw error;
          }
        } else {
          // 其他类型文件
          this.$message.warning(`不支持查看此类型文件: ${fileExt}`);
          return `[不支持查看此类型文件: ${fileExt}]`;
        }
      } catch (error) {
        console.error(`无法加载文件: @/assets/Mods/${modName}/${fileSource}`, error);
        throw new Error(`无法加载文件: ${modName}/${fileSource}`);
      }
    },
    sortMods(mods) {
      return [...mods].sort((a, b) => {
        const recommendA = a.recommend || this.defaultRecommend;
        const recommendB = b.recommend || this.defaultRecommend;
        return recommendB - recommendA;
      });
    },
    loadMods() {
      this.loading = true;
      try {
        // 使用require.context获取所有modConfig.json文件
        const requireMod = require.context('@/assets/Mods', true, /modConfig\.json$/);
        const modFiles = requireMod.keys();
  
        this.mods = modFiles.map((filePath) => {
          try {
            // 获取文本内容
            const modConfigText = requireMod(filePath);
            
            // 手动解析JSON
            const modConfig = JSON.parse(modConfigText);
            const modDir = filePath.split('/')[1];
            return {
              ...modConfig,
              name: modDir,
              recommend: modConfig.recommend || this.defaultRecommend,
            };
          } catch (error) {
            console.error(`解析modConfig.json失败: ${filePath}`, error);
            // 返回一个基本的mod对象，避免整个加载过程失败
            const modDir = filePath.split('/')[1];
            return {
              name: modDir,
              author: '未知',
              version: '未知',
              gameVersion: '未知',
              updateDate: '未知',
              files: [],
              tag: ['加载失败'],
              recommend: this.defaultRecommend,
            };
          }
        });
      } catch (error) {
        console.error('加载Mods失败:', error);
        this.mods = [];
      }
      this.loading = false;
    },
    getModTags(mod) {
      const tags = [...(mod.tag || [])];
      // 检查是否所有文件都是替换模式
      const isAllReplace = mod.files?.every(file => 
        file.mode === 'REPLACE' || 
        file.mode === 'REPLACE0' || 
        file.mode === 'REPLACE1'
      );
      
      if (isAllReplace && mod.files?.length > 0) {
        tags.unshift('纯替换');
      }
      
      return tags;
    },
    handleSelectionChange(selection) {
      this.selectedMods = selection;
    },
    // 修改导出方法
    async exportSelected() {
      this.loading = true;
      this.exportDialogVisible = false;
      
      const zip = new JSZip();
  
      // 创建Mods文件夹
      const modsFolder = zip.folder("Mods");
  
      // 根据选项添加主程序文件
      if (this.exportOptions.includeManager) {
        try {
          // 二进制文件需要使用file-loader，并指定esModule: false
          const mainAppPath = require('!!file-loader?esModule=false!@/assets/苏丹的游戏mod管理器.exe');
          const mainAppResponse = await fetch(mainAppPath);
          const mainAppBlob = await mainAppResponse.blob();
          zip.file('苏丹的游戏mod管理器.exe', mainAppBlob);
        } catch (error) {
          console.error('主程序加载出错:', error);
          this.$message.warning('无法加载主程序文件，但Mod文件将正常导出');
        }
      }
      
      // 根据选项添加安装脚本
      if (this.exportOptions.includeScript) {
        try {
          const scriptPath = require('!!raw-loader?esModule=false!@/assets/mod_installer.py');
          zip.file('mod_installer.py', scriptPath);
        } catch (error) {
          console.error('安装脚本加载出错:', error);
          this.$message.warning('无法加载安装脚本，但其他文件将正常导出');
        }
      }
  
      // 添加MOD文件
      for (const mod of this.selectedMods) {
        const modFolder = modsFolder.folder(mod.name);
        
        // 添加modConfig.json
        try {
          // 作为文本加载modConfig.json，并指定esModule: false
          const modConfigText = require(`!!raw-loader?esModule=false!@/assets/Mods/${mod.name}/modConfig.json`);
          modFolder.file('modConfig.json', modConfigText);
        } catch (error) {
          console.error(`无法加载modConfig.json: ${mod.name}`, error);
        }
        
        // 添加其他文件
        for (const file of mod.files) {
          try {
            const fileExt = file.source.split('.').pop().toLowerCase();
            let fileContent;
            
            if (fileExt === 'json' || fileExt === 'txt' || fileExt === 'config') {
              // 所有文本文件都使用raw-loader，并指定esModule: false
              const textModule = require(`!!raw-loader?esModule=false!@/assets/Mods/${mod.name}/${file.source}`);
              fileContent = textModule;
            } else {
              // 其他类型文件，尝试作为二进制处理
              const filePath = require(`!!file-loader?esModule=false!@/assets/Mods/${mod.name}/${file.source}`);
              const response = await fetch(filePath);
              fileContent = await response.blob();
            }
            
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
          } catch (error) {
            console.error(`加载文件出错: ${mod.name}/${file.source}`, error);
            this.$message.warning(`无法加载文件: ${file.source}`);
          }
        }
      }
  
      // 使用用户指定的文件名
      const fileName = this.exportOptions.fileName.endsWith('.zip') 
        ? this.exportOptions.fileName 
        : `${this.exportOptions.fileName}.zip`;
  
      zip.generateAsync({ type: "blob" }).then((content) => {
        saveAs(content, fileName);
        this.loading = false;
        
        // 构建成功消息
        let successMsg = `已成功导出 ${this.selectedMods.length} 个Mod`;
        if (this.exportOptions.includeManager) {
          successMsg += '，包含MOD管理器';
        }
        if (this.exportOptions.includeScript) {
          successMsg += '，包含安装脚本';
        }
        
        this.$message.success(successMsg);
      });
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
      // 重置表格筛选
      this.$refs.table && this.$refs.table.clearFilter();
    },
    // 获取标签类型（循环使用不同颜色）
    getTagType(index) {
      const types = ['', 'success', 'info', 'warning', 'danger'];
      return types[index % types.length];
    },
    // 获取模式描述
    getModeDescription(mode) {
      return this.modeDescriptions[mode] || mode;
    },
    // 获取模式标签类型
    getModeTagType(mode) {
      return this.modeTagTypes[mode] || '';
    },
    // 获取列筛选选项
    getColumnFilters(prop) {
      if (!this.mods || this.mods.length === 0) return [];
      
      // 获取唯一值
      const uniqueValues = [...new Set(this.mods.map(mod => mod[prop]))].filter(Boolean);
      
      // 转换为筛选选项格式
      return uniqueValues.map(value => ({
        text: value,
        value: value
      }));
    },
    filterHandler(value, row, column) {
      const property = column.property;
      return row[property] === value;
    }
  }
};
</script>

<style>
/* ... existing styles ... */

/* 添加导出对话框样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
