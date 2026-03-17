# [通用BMS大包生成脚本](https://gitee.com/MiyakoMeow/boftt-pack-generator-scripts)

脚本地址：Gitee上搜MiyakoMeow/bms-resource-scripts

## HQ版和LQ版怎么选？

1. HQ版：FLAC/OGG音频，同文件名下只保留一种视频格式，优先MP4/AVI，其次WMV/MPG/MPEG。
2. LQ版：在HQ版的基础上构建，FLAC音频转成OGG，MP4/AVI转成MPG。

选择建议：

1. LR2玩家选LQ版。
2. 希望获得更高的音频质量和BGA质量，选HQ版。
3. 希望占用空间更小的玩家，选LQ版。

提示：

1. 本人并非LR2玩家，LQ版包仅在LR2上对少部分作品做了抽查。
2. 已知问题：部分有BGA的作品，BGA在LR2上无法播放的情况。
3. 如果有将MP4视频转换成LR2**保证可播放**的格式的方法，或者有关于该大包的其他问题，请联系我。

## BOFTT大包下载链接

### 123云盘

- [123盘链接](https://www.123pan.com/s/Sn7lVv-Mhzm)
提取码：ORtY

### 度盘

- [度盘链接](https://pan.baidu.com/s/17seD5TCAlquX2rJ6CS4ZDg?pwd=6i8t)
提取码：6i8t

### 镜像站

- [bms.iidx.ca](https://bms.iidx.ca/bms/BMS/BMS%20%E6%B4%BB%E5%8A%A8%E5%8C%85/BOF%20G2R/%5B2024%5D%20BOFTT/)

## BOFTT大包特殊情况列表

- ！！！no.145, 185, 201, 205, 407：请手动合并更新文件夹。

- no.198, 199, 245, 258, 283, 286, 287, 301 使用了62进制BMS，不兼容LR2和beatoraja 0.8.7之前的版本。

对于LR2玩家，如果导入作品时出现问题，请优先移除以上作品。

- no.239 NSFW作品，提供了可供替换的安全BGI。已包含在大包中，但不默认启用，文件名为*_censored。

- no.155, 312, 452 包含空wav文件，已删除，基本不影响游玩。

- no.472 BMSON文件解析错误（第19行少了一个逗号），已补齐（BMS文件修改注意）。未经修改的文件以_ori为后缀。
经过实测，在beatoraja 0.8.7中，未经修改的谱面文件无法被读取。

## BOFTT大包更新记录

时区：GMT+8（中国标准时间）

- 2024.10.23 开始重新下载所有包。

- 截至 2024.10.24 00:15, 下载至no.270。

- 截至 2024.10.24 05:00, 下载了全部483个作品。

- 2024.10.26 06:00 更新所有登陆情报修正作品。

- 2024.10.28 08:00 更新所有登陆情报修正作品。

- 2024.10.30 08:00 更新所有登陆情报修正作品。

- 2024.11.04 16:00 更新所有登陆情报修正作品，并修正前几次更新时出现的错误。

- 2024.11.09 13:00 更新所有登陆情报修正作品。

- 2024.11.17 17:00 更新所有登陆情报修正作品。

- 2024.11.25 04:00 更新所有登陆情报修正作品。

- 2024.12.01 02:00 更新所有登陆情报修正作品。

- 2024.12.07 15:50 更新所有登陆情报修正作品。

- 2024.12.11 11:10 更新所有登陆情报修正作品。

- 2024.12.20 22:00 更新所有登陆情报修正作品。此后改为不定期更新。

## 脚本使用方式

运行要求：

- 能够使用命令行操作（本项目暂无GUI版）。

### 所需软件

- [Python](https://python.org)

> 版本至少为3.10。

- [ffmpeg](https://ffmpeg.org)

> [下载链接](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z)
> 下载、解压、将exe文件所在目录添加至Path环境变量。

- [oggenc](https://www.rarewares.org/ogg-oggenc.php)

> [下载链接](https://www.rarewares.org/files/ogg/oggenc2.88-1.3.7-x64.zip)
> 下载、解压、将exe文件所在目录添加至Path环境变量。

- [flac](https://xiph.org/flac/index.html)

> [下载链接](https://ftp.osuosl.org/pub/xiph/releases/flac/flac-1.4.3-win.zip)
> 下载、解压、将exe文件所在目录添加至Path环境变量。

### 所需Python库

```commandline
pip install py7zr rarfile
```

### 第一次打包

1. 下载BMS文件至BMS_PACK_DIR。

- 不知道在哪？那就先记住你下载的文件所在的目录，在步骤2和步骤3中填入就好。
- 建议不要将下载的BMS压缩包/媒体文件和其它文件放在同一目录下，以免在步骤2中误识别造成困扰。

2. 运行`rawpack_set_num`，填入步骤1中目录，手动给每个文件的文件名前打上编号。

> - 直接回车刷新文件列表
> - 输入一个数字A：给文件列表中的第一个文件打上编号A
> - 输入两个数字A、B：给文件列表中，下标为A的文件，即第（A+1）个文件，打上编号B

3. 运行`pack_setup_rawpack_to_hq`。

- 先填入步骤1中目录。
- 后填入解压目标文件夹（要求该文件夹不存在，后续程序会创建该文件夹）。

- 以下为示例：

```commandline
python main.py
（选择pack_setup_raw_to_hq)
D:\BMSPacks
E:\BMSCharts\BOFTT
y
```

> - 此脚本会将打上编号后的文件解压或移动至目标路径，然后直接按步骤生成HQ版本BMS目录。

4. 运行`pack_hq_to_lq.py`，填入步骤3填入的解压目标路径。用于制作LQ版本大包。

> - 该脚本会把路径下的mp4文件转换成mpeg文件，flac文件转换成ogg文件。
> - 已知问题：Windows下，将音频转换成ogg文件时概率卡住，此时建议使用命令行（oggenc命令）手动转换。

### 更新差分包生成

1. 下载BMS文件至BMS_PACK_DIR。同第一次打包。

2. 运行`rawpack_set_num.py`，使用方法同第一次打包。

3. 运行`pack_update_rawpack_to_hq.py`。

- 先填入步骤1中目录。
- 再填入差分包文件的存放文件夹（要求该文件夹不存在，后续程序会创建该文件夹）。
- 最后填入此前的HQ版本BMS目录（要求该文件夹存在）。

- 以下为示例：

```commandline
python main.py
（选择pack_update_raw_to_hq)
D:\BMSPacks
E:\BMSCharts\BOFTTCache
E:\BMSCharts\BOFTT
y
```

> - 此脚本会将打上编号后的文件解压或移动至目标路径，然后直接按步骤生成HQ版本BMS目录。
> - 执行完该步后，HQ版本的更新差分包就可以制作了。

4. 运行`pack_hq_to_lq.py`，填入步骤3填入的解压目标路径。用于制作LQ版本更新差分包。注意点同第一次打包。
