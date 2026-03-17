# BMS 资源打包脚本

用于管理和打包 BMS（Beatmania）游戏谱面资源的自动化工具集。

## 功能特点

- **BMS 文件解析**：支持解析 BMS/BME/BML/PMS/BMSON 文件，提取标题、艺术家、难度等信息
- **媒体处理**：支持音频（FLAC/WAV/OGG）和视频（MP4/AVI/WMV/MPEG）格式转换
- **大包生成**：一键生成 HQ/LQ 版本 BMS 大包
- **目录管理**：批量重命名、文件夹合并、相似文件检测等

## 环境要求

- Python 3.12+
- [ffmpeg](https://ffmpeg.org)
- [flac](https://xiph.org/flac/)
- [oggenc](https://www.rarewares.org/ogg-oggenc.php)

## 安装

1. 克隆项目：

```bash
git clone https://gitee.com/MiyakoMeow/bms-resource-scripts
cd bms-resource-scripts
```

2. 使用 uv 安装依赖（推荐）：

```bash
uv sync
```

3. 配置外部工具：

将 ffmpeg、flac、oggenc 的可执行文件所在目录添加到系统 Path 环境变量。

## 使用方式

运行主程序进入交互式菜单：

```bash
uv run main.py
```

按功能分类显示所有可用选项，输入编号即可执行对应功能。

## 功能列表

### BMS 解析

| 功能 | 说明 |
|------|------|
| 跳转至作品信息页 | 打开 BMS 活动作品页面 |

### BMS 根目录

| 功能 | 说明 |
|------|------|
| 按照 BMS 设置文件夹名 | 根据 BMS 文件信息重命名文件夹为"标题 [艺术家]" |
| 按照 BMS 追加文件夹名 | 在现有文件夹名后追加"标题 [艺术家]" |
| 按照 BMS 追加文件夹艺术家名 | 仅追加艺术家名称 |
| 克隆带编号的文件夹名 | 将源目录的带编号文件夹名同步到目标目录 |
| 扫描相似文件夹名 | 检测名称相似的文件夹 |
| 撤销重命名 | 撤销之前的重命名操作 |
| 移除大小为0的媒体文件和临时文件 | 清理无效文件 |

### BMS 大包目录

| 功能 | 说明 |
|------|------|
| 将该目录下的作品，按照首字符分成多个文件夹 | 按首字符（A-Z、平假名、片假名、汉字等）分类 |
| 将目录A下的作品，移动到目录B | 移动并合并作品目录 |
| 移出一层目录 | 减少一层目录嵌套 |
| 将文件名相似的子文件夹合并 | 智能合并相似目录 |

### BMS 媒体

| 功能 | 说明 |
|------|------|
| 音频转换 | WAV ↔ FLAC、FLAC → OGG 等格式转换 |
| 视频转换 | MP4 → AVI/WMV/MPEG，512x512/480p 分辨率转换 |

### BMS 原文件

| 功能 | 说明 |
|------|------|
| 将赋予编号的文件解压或放置至指定根目录 | 自动处理编号文件，解压到对应编号目录 |
| 将文件解压或放置至指定根目录 | 按原文件名创建目录 |
| 赋予编号 | 为文件添加数字前缀编号 |

### 大包脚本

| 功能 | 说明 |
|------|------|
| 原包 → HQ版大包 | 从原始压缩包生成 HQ 版本大包 |
| HQ版大包 → LQ版大包 | 将 HQ 版转换为 LR2 兼容的 LQ 版 |
| 差分包更新 | 生成增量更新包 |

## 目录结构

```
bms-resource-scripts/
├── bms/                    # BMS 文件解析模块
│   ├── parse.py           # BMS/BMSON 文件解析
│   ├── encoding.py        # 编码处理（支持 Shift-JIS、GBK 等）
│   └── work.py            # 工作信息提取
├── media/                 # 媒体处理模块
│   ├── audio.py           # 音频格式转换
│   └── video.py           # 视频格式转换
├── fs/                    # 文件系统操作模块
│   ├── move.py            # 文件移动与合并
│   ├── sync.py            # 文件夹同步
│   ├── rawpack.py         # 压缩包处理
│   └── name.py            # 文件名处理
├── options/               # 命令行选项模块
├── scripts/               # 打包脚本
├── main.py                # 主入口
└── pyproject.toml         # 项目配置
```

## 典型工作流程

### 首次打包 HQ 版大包

1. 下载 BMS 压缩包到指定目录
2. 运行 `uv run main.py`，选择 `BMS原文件：赋予编号`，为每个文件添加编号
3. 运行 `大包生成脚本：原包 -> HQ版大包`
4. 选择压缩包目录和目标目录

### 生成 LR2 兼容的 LQ 版

在完成 HQ 版后，运行 `BMS大包脚本：HQ版大包 -> LQ版大包`

- FLAC → OGG 转换
- MP4/AVI → MPG/WMV 转换

## 技术细节

### 支持的 BMS 文件格式

- `.bms`、`.bme`、`.bml`、`.pms`（BMS 格式）
- `.bmson`（BMSON JSON 格式）

### 支持的媒体格式

- 音频：`.flac`、`.ogg`、`.wav`
- 视频：`.mp4`、`.mkv`、`.avi`、`.wmv`、`.mpg`、`.mpeg`

### 编码支持

- Shift-JIS（日文）
- GB2312/GBK/GB18030（中文）
- UTF-8

项目还包含 BOFTT（Beatmania Open Files Two Turn）活动的专用配置。

## 相关链接

- [Gitee 仓库](https://gitee.com/MiyakoMeow/bms-resource-scripts)
- BOFTT 大包下载：[123云盘](https://www.123pan.com/s/Sn7lVv-Mhzm)（提取码：ORtY）

## 许可证

Apache License 2.0
