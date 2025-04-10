<template>
  <div class="mod-manager-container">
    <div class="header">
      <h1>苏丹的游戏 MOD 管理器</h1>
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索Mod名称、作者或版本..."
          prefix-icon="el-icon-search"
          clearable
          @clear="handleSearchClear"
          style="width: 300px;" 
        />
      </div>
    </div>

    <div class="toolbar">
      <div>
        <el-button type="primary" @click="showExportDialog" :disabled="selectedMods.length === 0">
          <i class="el-icon-download"></i> 导出选中 ({{ selectedMods.length }})
        </el-button>
        <el-button @click="resetFilters" plain>
          <i class="el-icon-refresh"></i> 重置筛选
        </el-button>
      </div>
      <div>
        <el-tag type="info">总计 {{ mods.length }} 个MOD</el-tag>
      </div>
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
        ref="table"
        :data="paginatedData"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
        @filter-change="handleFilterChange"
        :default-sort="{prop: 'recommend', order: 'descending'}"
        v-loading="loading"
        row-key="name"
        stripe
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="MOD名称" min-width="140" sortable>
          <template v-slot="scope">
            <div 
              class="mod-name" 
              v-tooltip="scope.row.remark ? { content: scope.row.remark, placement: 'top' } : null"
              @click="showRemarkDetails(scope.row)"
              :class="{ 'has-remark': scope.row.remark }"
            >
              {{ scope.row.name }}
              <i v-if="scope.row.remark" class="el-icon-info remark-icon"></i>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="recommend" label="推荐度" width="100" sortable>
          <template v-slot="scope">
            {{ scope.row.recommend || this.defaultRecommend }}
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="100" sortable column-key="author" :filters="getColumnFilters('author')" :filter-method="filterHandler">
          <template v-slot="scope">
            <el-tag size="small">{{ scope.row.author }}</el-tag>
            <!-- 添加source链接 -->
            <a v-if="scope.row.source && scope.row.source.url" 
               :href="scope.row.source.url" 
               target="_blank" 
               class="source-link-icon">
              <i class="el-icon-link"></i>
            </a>
          </template>
        </el-table-column>
        <!-- <el-table-column prop="version" label="版本" width="80" column-key="version" :filters="getColumnFilters('version')" :filter-method="filterHandler" /> -->
        <el-table-column prop="gameVersion" label="游戏版本" width="120" sortable column-key="gameVersion" :filters="getColumnFilters('gameVersion')" :filter-method="filterHandler">
          <template v-slot="scope">
            <el-tag type="success" size="small">{{ scope.row.gameVersion }}</el-tag>
          </template>
        </el-table-column>
        
        <!-- 添加来源列 -->
        <el-table-column label="来源" width="150">
          <template v-slot="scope">
            <a 
              v-if="scope.row.source && scope.row.source.url" 
              :href="scope.row.source.url" 
              target="_blank" 
              class="source-link"
            >
              {{ scope.row.source?.name || '未知来源' }}
              <i class="el-icon-link"></i>
            </a>
            <span v-else>未知来源</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="updateDate" label="更新时间" width="120" sortable />
        <el-table-column label="标签" width="150" column-key="tag" :filters="getTagFilters()" :filter-method="filterTagHandler">
          <template v-slot="scope">
            <div class="tag-container">
              <el-tag 
                v-for="(tag, index) in getModTags(scope.row)" 
                :key="index" 
                size="small" 
                :type="tag === '纯替换' ? 'danger' : (tag === '压缩包' ? 'warning' : getTagType(index))" 
                effect="plain"
                class="mod-tag"
              >
                {{ tag }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="文件" >
          <template v-slot="scope">
            <el-collapse accordion>
              <el-collapse-item>
                <template #title>
                  <span class="file-count" >{{ scope.row.files.length }} 个文件</span>
<!--                  <span class="file-count" v-else>-->
<!--                    <el-tag type="info" size="small">压缩包</el-tag> {{ scope.row.zipFile }}-->
<!--                  </span>-->
                </template>
                <div v-if="scope.row.zipFile" class="zip-file-notice">
                  <i class="el-icon-info"></i> 该MOD包含大量文件，已打包为压缩文件。导出时会自动解压并包含所有文件。
                </div>
                <el-list v-else>
                  <el-list-item v-for="(file, index) in scope.row.files" :key="index" class="file-item">
                    <!-- 原有的文件列表内容 -->
                    <div class="file-info">
                      <div class="file-source">{{ file.source }}</div>
                      <div class="file-mode">
<!--                        <el-tag :type="getModeTagType(file.mode)" size="mini">-->
<!--                          {{ getModeDescription(file.mode) }}-->
<!--                        </el-tag>-->
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
          background
        />
      </div>
    </el-card>

    <!-- 添加MOD说明详情对话框 -->
    <el-dialog
      title="MOD说明详情"
      v-model="remarkDetailsVisible"
      width="60%"
      class="remark-details-dialog"
    >
      <div v-if="currentModName" class="mod-name-header">
        <h3>{{ currentModName }}</h3>
      </div>
      <div class="remark-content-container">
        <pre>{{ currentRemark }}</pre>
      </div>
      <template #footer>
        <el-button @click="remarkDetailsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <el-dialog
      title="文件详情"
      v-model="fileDetailsVisible"
      width="80%"
      class="file-details-dialog"
    >
      <!-- 添加source信息展示 -->
      <div v-if="currentModSource" class="mod-source-info">
        <span>来源: </span>
        <a :href="currentModSource.url" target="_blank" class="source-link">{{ currentModSource.name || currentModSource.url }}</a>
      </div>
      <div class="file-content-container">
        <pre>{{ fileContent }}</pre>
      </div>
      <template #footer>
        <el-button @click="fileDetailsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <div class="footer">
      <p>苏丹的游戏 MOD 管理器 &copy; 2025 by <a href="https://github.com/liwenhao0427/sultans-game-mod-manager" target="_blank">liwenhao0427</a></p>
    </div>
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
      remarkDetailsVisible: false,
      currentRemark: '',
      currentModName: '',
      columnFilters: {}, // 存储当前应用的列筛选
      authorColors: {}, // 用于存储作者对应的颜色类型
      defaultRecommend: 3, // 默认推荐值
      fileDetailsVisible: false,
      fileContent: '', // Stores the content of the selected file
      currentModSource: null, // 存储当前查看的MOD的source信息
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
      let result = this.mods;
      
      // 应用搜索筛选
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(mod => {
          return (
            mod.name.toLowerCase().includes(query) ||
            (mod.author && mod.author.toLowerCase().includes(query)) ||
            (mod.gameVersion && mod.gameVersion.toLowerCase().includes(query)) ||
            (mod.tag && mod.tag.some(tag => tag.toLowerCase().includes(query)))
          );
        });
      }
      
      // 应用表格列筛选
      if (this.columnFilters && Object.keys(this.columnFilters).length > 0) {
        Object.entries(this.columnFilters).forEach(([key, values]) => {
          if (values && values.length > 0) {
            result = result.filter(mod => {
              if (key === 'tag') {
                // 标签特殊处理
                const modTags = this.getModTags(mod);
                return values.some(value => modTags.includes(value));
              } else {
                // 普通列筛选
                return values.includes(mod[key]);
              }
            });
          }
        });
      }
      
      // 排序
      return this.sortMods(result);
    },
    paginatedData() {
      const startIndex = (this.currentPage - 1) * this.pageSize;
      const endIndex = startIndex + this.pageSize;
      return this.filteredMods.slice(startIndex, endIndex);
    }
  },
  mounted() {
    this.loadMods();
    
    // Use setTimeout to ensure DOM is fully rendered
    setTimeout(() => {
      if (this.$refs.table) {
        try {
          this.$refs.table.doLayout();
        } catch (error) {
          console.warn('Table layout calculation deferred:', error);
        }
      }
    }, 500);
  },
  methods: {
    // 显示MOD说明详情
    showRemarkDetails(mod) {
      if (mod.remark) {
        this.currentModName = mod.name;
        this.currentRemark = mod.remark;
        this.remarkDetailsVisible = true;
      }
    },
    // 处理表格筛选变化
    handleFilterChange(filters) {
      // 更新筛选状态
      Object.keys(filters).forEach(key => {
        if (filters[key] && filters[key].length > 0) {
          this.columnFilters[key] = filters[key];
        } else {
          // 如果筛选被清除，从状态中移除
          if (this.columnFilters[key]) {
            delete this.columnFilters[key];
          }
        }
      });
      
      // 重置到第一页
      this.currentPage = 1;
    },
    // 显示导出对话框
    showExportDialog() {
      // 设置默认文件名
      this.exportOptions.fileName = `mods_${this.selectedMods.length}.zip`;
      this.exportDialogVisible = true;
    },
    
    async viewFileDetails(modName, fileSource) {
      try {
        // 获取当前MOD的source信息
        const currentMod = this.mods.find(mod => mod.name === modName);
        this.currentModSource = currentMod?.source || null;
        
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
    // 修改排序方法，使用recommend字段，相同时按日期倒序
    sortMods(mods) {
      return [...mods].sort((a, b) => {
        const recommendA = a.recommend !== undefined ? a.recommend : this.defaultRecommend;
        const recommendB = b.recommend !== undefined ? b.recommend : this.defaultRecommend;
        
        // 如果推荐度不同，按推荐度排序
        if (recommendB !== recommendA) {
          return recommendB - recommendA;
        }
        
        // 如果推荐度相同，按更新日期倒序排序
        const dateA = a.updateDate || '';
        const dateB = b.updateDate || '';
        return dateB.localeCompare(dateA);
      });
    },

    // 获取作者标签类型
    getAuthorTagType(author) {
      return this.authorColors[author] || '';
    },
    
    // 获取标签筛选选项
    getTagFilters() {
      if (!this.mods || this.mods.length === 0) return [];
      
      // 收集所有标签
      const allTags = [];
      this.mods.forEach(mod => {
        console.log('Processing mod:', mod); // Add this log to check the mode
        const tags = this.getModTags(mod);
        tags.forEach(tag => {
          if (!allTags.includes(tag)) {
            allTags.push(tag);
          }
        });
      });
      
      // 转换为筛选选项格式
      return allTags.map(tag => ({
        text: tag,
        value: tag
      }));
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
      
      // 如果有zipFile，直接添加"压缩包"标签
      if (mod.zipFile) {
        tags.unshift('压缩包');
        return tags;
      }
      
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
    // 添加检查MOD冲突的方法
    checkModConflicts(mods) {
      // 用于存储每个文件路径对应的MOD和操作模式
      const filePathMap = new Map();
      const conflicts = [];
      
      // 遍历所有选中的MOD
      for (const mod of mods) {
        if (!mod.files || !Array.isArray(mod.files)) continue;
        
        // 遍历MOD中的每个文件
        for (const file of mod.files) {
          if (!file.source) continue;
          
          // 获取目标路径（如果没有destination则使用source）
          const targetPath = file.destination || file.source;
          const mode = file.mode || 'REPLACE'; // 默认为REPLACE模式
          
          // 检查此路径是否已存在于映射中
          if (filePathMap.has(targetPath)) {
            const existingEntry = filePathMap.get(targetPath);
            
            // 检查是否至少有一个是全量替换模式
            const isCurrentReplace = mode === 'REPLACE';
            const hasExistingReplace = existingEntry.modes.includes('REPLACE');
            
            if (isCurrentReplace || hasExistingReplace) {
              // 添加当前MOD到已存在的条目
              existingEntry.mods.push(mod.name);
              existingEntry.modes.push(mode);
              
              // 如果这是第一次发现冲突，添加到冲突列表
              if (existingEntry.mods.length === 2) {
                conflicts.push({
                  filePath: targetPath,
                  mods: [...existingEntry.mods],
                  modes: [...existingEntry.modes]
                });
              }
            }
          } else {
            // 添加新条目到映射
            filePathMap.set(targetPath, {
              mods: [mod.name],
              modes: [mode]
            });
          }
        }
      }
      return conflicts;
    },
    // 修改导出方法
    async exportSelected() {
      // 检查MOD之间的文件冲突
      const conflicts = this.checkModConflicts(this.selectedMods);
      
      if (conflicts.length > 0) {
        // 构建冲突提示信息
        let conflictMessage = '检测到以下可能的MOD冲突：\n\n';
        
        conflicts.forEach(conflict => {
          conflictMessage += `文件路径: ${conflict.filePath}\n`;
          conflictMessage += `冲突MOD: ${conflict.mods.join(', ')}\n`;
          conflictMessage += `操作类型: ${conflict.modes.map(mode => this.getModeDescription(mode)).join(', ')}\n\n`;
        });
        
        conflictMessage += '这些MOD可能会相互覆盖或产生冲突，确定要继续导出吗？';
        
        // 显示确认对话框
        const confirmed = await this.$confirm(conflictMessage, '发现MOD冲突', {
          confirmButtonText: '继续导出',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: false
        }).catch(() => false);
        
        if (!confirmed) {
          return; // 用户取消导出
        }
      }
      
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
        
        // 检查是否有zipFile属性
        if (mod.zipFile) {
          try {
            // 加载zip文件
            const zipFilePath = require(`!!file-loader?esModule=false!@/assets/Mods/${mod.name}/${mod.zipFile}`);
            const zipFileResponse = await fetch(zipFilePath);
            const zipFileBlob = await zipFileResponse.blob();
            
            // 解压zip文件
            const modZip = await JSZip.loadAsync(zipFileBlob);
            
            // 将解压后的文件添加到导出包中
            for (const filename in modZip.files) {
              if (!modZip.files[filename].dir) {
                const fileContent = await modZip.files[filename].async('blob');
                modFolder.file(filename, fileContent);
              } else {
                // 创建目录
                modFolder.folder(filename);
              }
            }
            
            this.$message.success(`已从压缩包加载MOD: ${mod.name}`);
          } catch (error) {
            console.error(`无法加载或解压zip文件: ${mod.name}/${mod.zipFile}`, error);
            this.$message.error(`无法加载压缩包: ${mod.zipFile}`);
            
            // 如果zip文件加载失败，回退到常规方式加载文件
            await this.addModFilesRegular(mod, modFolder);
          }
        } else {
          // 常规方式加载文件
          await this.addModFilesRegular(mod, modFolder);
        }
      }
      
      try {
        // 生成zip文件并下载
        const content = await zip.generateAsync({
          type: 'blob',
          compression: 'DEFLATE',
          compressionOptions: {
            level: 9
          }
        });
        
        saveAs(content, this.exportOptions.fileName);
        this.$message.success('导出成功！');
      } catch (error) {
        console.error('导出出错:', error);
        this.$message.error('导出失败，请查看控制台获取详细信息');
      } finally {
        this.loading = false;
      }
    },
    
    // 添加新方法：常规方式加载MOD文件
    async addModFilesRegular(mod, modFolder) {
      // 如果有zipFile属性，不处理files
      if(mod.zipFile){
        // 这里不需要做任何事情，因为导出方法中已经处理了zipFile
        return;
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
          const fileName = file.source.split('/').pop();
          
          if (pathSegments.length > 0) {
            // 创建嵌套文件夹
            let folderPath = '';
            for (const segment of pathSegments) {
              folderPath += (folderPath ? '/' : '') + segment;
              currentFolder = modFolder.folder(folderPath);
            }
          }
          
          // 添加文件到对应文件夹
          currentFolder.file(fileName, fileContent);
        } catch (error) {
          console.error(`无法加载文件: ${mod.name}/${file.source}`, error);
        }
      }
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
      // 先清空搜索和筛选状态
      this.searchQuery = '';
      this.currentPage = 1;
      this.columnFilters = {}; // 清空所有筛选状态
      
      // 使用nextTick确保状态更新后再操作DOM
      this.$nextTick(() => {
        if (this.$refs.table) {
          try {
            // 获取表格实例
            const table = this.$refs.table;
            
            // 清除所有列的筛选
            const columnKeys = ['author', 'gameVersion', 'tag'];
            columnKeys.forEach(key => {
              table.clearFilter(key);
            });
            
            // 强制更新表格数据
            this.$forceUpdate();
            
            // 额外延时确保UI更新
            setTimeout(() => {
              // 再次强制更新组件
              this.$forceUpdate();
              // 重新布局表格
              table.doLayout();
            }, 200);
          } catch (error) {
            console.warn('清除表格筛选时出错:', error);
          }
        }
      });
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
     // 修改筛选处理方法
     filterHandler(value, row, column) {
      const property = column.property || column.columnKey;
      
      // 更新筛选状态
      if (!this.columnFilters[property]) {
        this.columnFilters[property] = [];
      }
      
      // 如果值不在筛选列表中，添加它
      if (!this.columnFilters[property].includes(value)) {
        this.columnFilters[property].push(value);
      }
      
      return true; // 返回true，因为我们在computed中处理筛选
    },
    
    // 标签筛选处理函数
    filterTagHandler(value) {
      // 更新筛选状态
      if (!this.columnFilters['tag']) {
        this.columnFilters['tag'] = [];
      }
      
      // 如果值不在筛选列表中，添加它
      if (!this.columnFilters['tag'].includes(value)) {
        this.columnFilters['tag'].push(value);
      }
      
      return true; // 返回true，因为我们在computed中处理筛选
    },
  }
};
</script>

<style>
.mod-manager-container {
  max-width: 1500px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eaeaea;
}

.header h1 {
  margin: 0;
  color: #409EFF;
  font-size: 28px;
}

.search-bar {
  display: flex;
  align-items: center;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.mod-name {
  font-weight: bold;
  color: #303133;
}

.tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.mod-tag {
  margin-right: 5px;
}

.file-count {
  font-size: 14px;
  color: #606266;
}

.file-item {
  display: block;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  flex: 1;
}

.file-source {
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
}

.file-mode {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.file-mode-params {
  font-size: 12px;
  color: #909399;
  margin-left: 5px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.file-content-container {
  background-color: #f8f8f8;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow: auto;
}

.file-content-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', Courier, monospace;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

/* 美化表格 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.el-table th {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: bold;
}

.el-table--border th, .el-table--border td {
  border-right: 1px solid #ebeef5;
}

/* 美化按钮 */
.el-button {
  border-radius: 4px;
  font-weight: 500;
}

.el-button--primary {
  background-color: #409EFF;
}

.el-button--primary:hover {
  background-color: #66b1ff;
}

/* 美化对话框 */
.el-dialog {
  border-radius: 8px;
  overflow: hidden;
}

.el-dialog__header {
  background-color: #f5f7fa;
  padding: 15px 20px;
}

.el-dialog__title {
  font-weight: bold;
  color: #303133;
}

.el-dialog__body {
  padding: 20px;
}

/* 美化折叠面板 */
.el-collapse {
  border: none;
}

.el-collapse-item__header {
  background-color: #f5f7fa;
  padding: 0 15px;
  border-radius: 4px;
  height: 40px;
  line-height: 40px;
}

.el-collapse-item__content {
  padding: 15px;
  background-color: #fafafa;
  border-radius: 0 0 4px 4px;
}

/* 添加导出对话框样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.footer {
  margin-top: 30px;
  text-align: center;
  color: #606266;
  padding: 20px 0;
  border-top: 1px solid #eaeaea;
}

.footer a {
  color: #409EFF;
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}

.mod-source-info {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.source-link {
  color: #409EFF;
  text-decoration: none;
}

.source-link:hover {
  text-decoration: underline;
}

.source-link-icon {
  margin-left: 8px;
  color: #409EFF;
  font-size: 14px;
}

.source-link {
  color: #409EFF;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 5px;
}

.source-link:hover {
  text-decoration: underline;
}

.source-link .el-icon-link {
  font-size: 14px;
}

.zip-file-notice {
  padding: 15px;
  background-color: #f0f9eb;
  border-radius: 4px;
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.zip-file-notice .el-icon-info {
  font-size: 18px;
}

.mod-name {
  font-weight: bold;
  color: #303133;
  cursor: default;
  display: flex;
  align-items: center;
}

.mod-name.has-remark {
  cursor: pointer;
}

.mod-name.has-remark:hover {
  color: #409EFF;
}

.remark-icon {
  margin-left: 5px;
  font-size: 14px;
  color: #909399;
}

.mod-name-header {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eaeaea;
}

.remark-content-container {
  background-color: #f8f8f8;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow: auto;
}

.remark-content-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', Courier, monospace;
}
</style>
