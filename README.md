# rh-image-gen

> 🖌️ AI绘师 - RunningHub 动漫短剧分镜图生成 Skill（v3.0.0）

使用 RunningHub Plus 工作流，传入角色图和场景图参考，保持动漫短剧分镜图的风格一致性。

## ✨ 功能特性

- **Plus 工作流模式**：支持 3 张参考图（角色/场景/风格）+ 自定义尺寸
- **单镜生成**：精确控制每一镜的提示词和参考图
- **批量生成**：读取分镜脚本，一键生成整集分镜图
- **自动上传参考图**：图片自动上传至 RunningHub 服务器
- **质量自检**：生成后自动检查动漫风格、角色/场景一致性

## 🎬 在制作流程中的位置

```
小说原文 → 美术风格设计 → 角色库构建 → 场景构建 → 分镜脚本
                                                        ↓
                                              【小绘】分镜图生成 ⭐（你在这里）
                                                        ↓
                                              质量审核 → 图生视频 → 视频合成
```

## 📋 前置要求

- Python 3.7+
- RunningHub API Key（[注册获取](https://www.runninghub.cn/?inviteCode=rh-v1382)）

```bash
pip install -r requirements.txt
```

## 🚀 快速开始

```bash
# 设置 API Key
export RUNNINGHUB_API_KEY="your_api_key_here"

# 单镜生成
python scripts/rh_image_gen.py generate \
  --shot 001 \
  --prompt "2个古风女孩在地铁车厢内，蓝色灯光氛围" \
  --ref1 ./03_characters/girl1.png \
  --ref2 ./04_scenes/subway.jpg \
  --ref3 ./references/style.png \
  --width 1080 \
  --height 1920 \
  --output-dir ./06_images

# 批量生成（整集）
python scripts/rh_image_gen.py batch \
  --storyboard ./05_storyboard/storyboard.md \
  --chars ./03_characters/ \
  --scenes ./04_scenes/ \
  --style ./02_style/style_guide.md \
  --output ./06_images/
```

## 📖 参数说明

### 单镜生成

| 参数 | 必选 | 描述 | 默认值 |
| :--- | :--- | :--- | :--- |
| `--shot` | ✅ | 分镜编号 | 无 |
| `--prompt` | ✅ | 正面提示词 | 无 |
| `--ref1` | ❌ | 参考图1（角色） | 无 |
| `--ref2` | ❌ | 参考图2（场景） | 无 |
| `--ref3` | ❌ | 参考图3（风格/其他） | 无 |
| `--width` | ❌ | 输出宽度 | `1080` |
| `--height` | ❌ | 输出高度 | `1920` |
| `--output-dir` | ❌ | 输出目录 | `./06_images` |

### 批量生成

| 参数 | 必选 | 描述 |
| :--- | :--- | :--- |
| `--storyboard` | ✅ | 分镜脚本路径 |
| `--chars` | ❌ | 角色图目录 |
| `--scenes` | ❌ | 场景图目录 |
| `--style` | ❌ | 风格提示词文件 |
| `--output` | ❌ | 输出目录 |

## 🔧 核心配置

### 工作流节点映射

```
NODE_PROMPT="21"    # 正面提示词
NODE_NEGATIVE="43"  # 负面提示词
NODE_REF1="15"      # 参考图1（角色）
NODE_REF2="44"      # 参考图2（场景）
NODE_REF3="47"      # 参考图3（风格）
NODE_WIDTH="49"     # 图片宽度
NODE_HEIGHT="48"    # 图片高度
```

### 输出规范

| 项目 | 要求 |
| :--- | :--- |
| 格式 | PNG |
| 比例 | 3:4（竖版） |
| 分辨率 | 1080×1920 或更高 |
| 命名 | `shot_001.png`, `shot_002.png`... |
| 路径 | `./06_images/` |

## 📁 文件结构

```
rh-image-gen/
├── SKILL.md                  # Skill 定义文件
├── config.example.json       # 配置示例
├── requirements.txt          # Python 依赖
├── rh-image-gen              # Bash wrapper 脚本
├── scripts/
│   └── rh_image_gen.py       # 核心 Python 脚本
└── .gitignore
```

## 🔗 API 文档参考

- [RunningHub API 文档首页](https://www.runninghub.cn/runninghub-api-doc-cn/)
- [AI 应用完整接入示例](https://www.runninghub.cn/runninghub-api-doc-cn/doc-8287339)
- [工作流完整接入示例](https://www.runninghub.cn/runninghub-api-doc-cn/doc-8287342)
- [接口错误码说明](https://www.runninghub.cn/runninghub-api-doc-cn/doc-8287338)

## ⚠️ 注意事项

- API Key 从环境变量 `RUNNINGHUB_API_KEY` 读取，切勿硬编码
- 参考图需确保路径正确，上传失败会自动重试 3 次
- 任务超时上限 300 秒（5 分钟）
- 输出图片为 3:4 竖版比例，适配动漫短剧竖屏场景

## 📄 License

MIT
