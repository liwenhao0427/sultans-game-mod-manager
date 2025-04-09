# 

## 快速使用
1. 进入网站 https://liwenhao0427.github.io/sultans-game-mod-manager/
2. 勾选您希望使用的mod，点击左上角的 `导出选中` 按钮，下载 mod 整合包
3. 解压到游戏根目录（选择解压到当前文件夹），运行根目录下的 苏丹的游戏mod管理器.exe 
4. 完成了！请享受游戏吧！


## 额外说明
1. Mod 会存放在游戏根目录的 Mods 目录下，您可以随时移除不想要的 mod，之后重新运行 苏丹的游戏mod管理器.exe 即可完成更新
2. 每次游戏版本更新后，请先检查游戏完整性，将游戏配置还原到默认，然后手动删除\Sultan's Game_Data\StreamingAssets\bak文件夹（之后会增加一个删除的命令），重新运行 苏丹的游戏mod管理器.exe 即可完成更新


## Mod 配置文件结构
`modConfig.json`
```json
{
  "name": "string",
  "author": "string",
  "version": "string",
  "gameVersion": "string",
  "updateDate": "YYYY.MM.DD",
  "files": [
    {
      "source": "string",
      "destination": "string",
      "mode": "enum",
      "modeDesc": "string",
      "val1": "string",
      "val2": "string"
    }
  ]
}
```

## 字段说明

### 基本信息字段

| 字段名        | 类型   | 是否必填 | 描述                       | 示例值              |
|---------------|--------|---------|--------------------------|---------------------|
| `name`        | string | 否       | Mod 的名称标识                | "困难模式骰子成功率下降" |
| `author`      | string | 否       | Mod 的作者名称                | "萧敷艾荣"          |
| `version`     | string | 否       | Mod 版本号（推荐使用语义化版本格式）     | "1.0.0"            |
| `gameVersion` | string | 否       | 兼容的游戏版本号，后续版本通常也支持，但不做保证 | "17954583"         |
| `updateDate`  | string | 否       | 最后更新日期（格式：YYYY.MM.DD）    | "2025.04.08"       |

### 文件配置字段（files[]数组）

| 字段名         | 类型   | 是否必填 | 描述                                                                 | 示例值                              |
|----------------|--------|----------|----------------------------------------------------------------------|-------------------------------------|
| `source`       | string | 是       | Mod 包内源文件路径（相对路径）                                       | "init/1.json"                      |
| `destination`  | string | 否       | 游戏内目标文件路径（绝对路径）                                       | "/Sultan's Game_Data/StreamingAssets/config/init/1.json" |
| `mode`         | enum   | 是       | 文件修改模式（见下方模式枚举说明）                                   | "REPLACE1"                         |
| `modeDesc`     | string | 否       | 对当前模式的文字说明                                                 | "替换两个标记之间的内容"           |
| `val1`         | string | 条件必填 | 模式参数1（根据不同的 mode 决定是否必需）                            | "\"difficulty\":"                 |
| `val2`         | string | 条件必填 | 模式参数2（根据不同的 mode 决定是否必需）                            | "// 俺寻思仪式id"                 |

### 模式枚举（mode）说明

#### 替换类模式
| 模式值        | 描述            | 必需参数               | 参数说明             |
|------------|---------------|------------------------|------------------|
| `REPLACE`  | 完全替换目标文件      | 无                     | 不推荐，随版本更新可能无法会报错； |
| `REPLACE0` | 查找替换文本        | `val1`: 起始标记           | 替换标记行为目标mod文件内容  |
| `REPLACE1` | 替换两个文本标记之间的内容 | `val1`: 起始标记<br>`val2`: 结束标记 | 替换包含标记在内的中间内容，标记所在行都会被替换   |

#### 插入类模式
| 模式值      | 描述           | 必需参数               | 参数说明          |
|----------|--------------|------------------------|---------------|
| `APPEND` | 在文件末尾追加内容    | `val1`: 定位标记       | val1表示倒数第几行   |
| `INSERT` | 在指定标记位置后插入内容 | `val1`: 定位标记 | 在标记所在行之后插入新内容 |

### 示例配置

```json
{
  "name": "困难模式骰子成功率下降",
  "author": "萧敷艾荣",
  "version": "1.0.0",
  "gameVersion": "17954583",
  "updateDate": "2025.04.08",
  "files": [
    {
      "source": "init/1.json",
      "destination": "/Sultan's Game_Data/StreamingAssets/config/init/1.json",
      "mode": "REPLACE1",
      "modeDesc": "替换两个标记之间的内容",
      "val1": "\"difficulty\":",
      "val2": "// 俺寻思仪式id"
    }
  ]
}
```
