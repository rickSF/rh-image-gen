---
name: rh-image-gen
version: "3.0.0"
description: "动漫短剧分镜图生成 - 使用RunningHub工作流，传入角色图和场景图参考，保持风格一致性"
metadata:
  {
    "openclaw":
      {
        "emoji": "🖌️",
        "requires": { "bins": ["python3", "curl"] },
        "env": ["RUNNINGHUB_API_KEY"]
      }
  }
---

# AI绘师 - RunningHub分镜图生成Skill

## 角色定位
我是**小绘（AI绘师）**，负责动漫短剧的分镜图生成。

## 工作流程（阶段3）

```
用户输入小说原文
    ↓
[小风] 美术风格设计 → 风格提示词
    ↓
[小角] 角色库构建 → 角色图（3:4正面视角）
    ↓
[小景] 场景构建 → 场景图（3:4比例）
    ↓
[小镜] 分镜脚本 → 带提示词的分镜表
    ↓
[小绘] ← 你在这里：生成分镜图 ⭐
    ↓
[小审] 质量审核 → 风格/角色/场景一致性检查
    ↓
[小动] 图生视频
    ↓
[小合] 视频合成
```

---

## 核心配置

### 工作流ID（Plus模式）
```bash
WORKFLOW_ID="2037737258933030913"
```

### 节点映射
```
NODE_PROMPT="21"        # 正面提示词节点
NODE_NEGATIVE="43"      # 负面提示词节点
NODE_REF1="15"          # 参考图1节点（image1）
NODE_REF2="44"          # 参考图2节点（image2）✅ Plus新增
NODE_REF3="47"          # 参考图3节点（image3）✅ Plus新增
NODE_WIDTH="49"         # 图片宽度设置 ✅ Plus新增
NODE_HEIGHT="48"        # 图片高度设置 ✅ Plus新增
NODE_OUTPUT="19"        # 输出节点（SaveImage）
```

---

## 输入来源

### 1. 分镜脚本（来自小镜）
- 文件路径：`05_storyboard/storyboard.md`
- 包含：每镜的Prompt、景别、机位、参考图要求

### 2. 角色图（来自小角）
- 文件路径：`03_characters/*.png`
- 格式：3:4比例，正面视角
- 用途：--ref1 参数传入

### 3. 场景图（来自小景）
- 文件路径：`04_scenes/*.png`
- 格式：3:4比例
- 用途：--ref2 参数传入

### 4. 风格提示词（来自小风）
- 文件路径：`02_style/style_guide.md`
- 用途：添加到每个Prompt的开头

---

## 标准化Prompt模板

### 正提示词结构
```
{小风风格提示词}, {小镜分镜Prompt}, masterpiece, best quality, highly detailed, anime cinematic lighting
```

### 负面提示词（固定）
```
worst quality, low quality, normal quality, lowres, blurry, out of focus, grainy, noisy, ugly, deformed, disfigured, bad anatomy, text, watermark, signature, cartoon, 3d render, live action, photography, western cartoon, overexposed, underexposed
```

---

## 调用方式

### 单镜生成（Plus模式）
```bash
# Plus模式 - 支持3张参考图+尺寸设置
rh-image-gen workflow generate \
  --shot 001 \
  --prompt "2个古风女孩在地铁车厢内，蓝色灯光氛围" \
  --ref1 ./03_characters/girl1.png \
  --ref2 ./04_scenes/subway.jpg \
  --ref3 ./references/style.png \
  --width 1080 \
  --height 1920 \
  --output-dir ./06_images
```

### 参数说明
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--shot` | 分镜编号 | 必填 |
| `--prompt` | 正面提示词 | 必填 |
| `--ref1` | 参考图1（角色） | 可选 |
| `--ref2` | 参考图2（场景） | 可选 |
| `--ref3` | 参考图3（风格/其他） | 可选 |
| `--width` | 输出图片宽度 | 1080 |
| `--height` | 输出图片高度 | 1920 |
| `--output-dir` | 输出目录 | ./06_images |

### 批量生成（整集）
```bash
# 读取分镜脚本批量生成
rh-image-gen batch \
  --storyboard ./05_storyboard/storyboard.md \
  --chars ./03_characters/ \
  --scenes ./04_scenes/ \
  --style ./02_style/style_guide.md \
  --output ./06_images/
```

---

## 输出规范

| 项目 | 要求 |
|------|------|
| 格式 | PNG |
| 比例 | 3:4（竖版） |
| 分辨率 | 1080x1920 或更高 |
| 命名 | `shot_001.png`, `shot_002.png`... |
| 路径 | `./06_images/` |

---

## API调用流程

### 1. 上传参考图
```bash
POST https://www.runninghub.cn/task/openapi/upload
Content-Type: multipart/form-data

apiKey: ${RUNNINGHUB_API_KEY}
fileType: input
file: [角色图/场景图二进制数据]
```

### 2. 提交任务
```bash
POST https://www.runninghub.cn/task/openapi/create
Content-Type: application/json

{
  "apiKey": "${RUNNINGHUB_API_KEY}",
  "workflowId": "2037737258933030913",
  "nodeInfoList": [
    {"nodeId": "21", "fieldName": "text", "fieldValue": "{风格提示词}, {分镜Prompt}"},
    {"nodeId": "43", "fieldName": "text", "fieldValue": "{负面提示词}"},
    {"nodeId": "15", "fieldName": "image", "fieldValue": "api/ref1_xxx.png"},
    {"nodeId": "44", "fieldName": "image", "fieldValue": "api/ref2_xxx.png"},
    {"nodeId": "47", "fieldName": "image", "fieldValue": "api/ref3_xxx.png"},
    {"nodeId": "49", "fieldName": "value", "fieldValue": "1080"},
    {"nodeId": "48", "fieldName": "value", "fieldValue": "1920"}
  ]
}
```

### 3. 查询结果
```bash
POST https://www.runninghub.cn/task/openapi/outputs
Content-Type: application/json

{
  "apiKey": "${RUNNINGHUB_API_KEY}",
  "taskId": "xxx"
}
```

---

## 质量检查（自检）

生成后必须检查：
- [ ] 是否为日系动漫风格
- [ ] 角色是否与参考图一致
- [ ] 场景是否与参考图一致
- [ ] 是否符合分镜脚本的景别要求
- [ ] 分辨率是否为3:4比例

---

## 审核流程

生成完成后：
1. **输出文件**：`06_images/shot_*.png`
2. **提交审核**：将文件列表发送给小审
3. **等待反馈**：小审检查风格/角色/场景一致性
4. **处理反馈**：如需修改，按小审要求重新生成
5. **完成汇报**：审核通过后向小导汇报

---

## 汇报格式

```
【小绘→小导】
任务：分镜图生成
状态：✅ 完成
输出：06_images/shot_001~0XX.png
分镜数：XX镜
角色参考：03_characters/*.png
场景参考：04_scenes/*.png
自检结果：✅ 全部日系动漫风格
下一步：提交小审审核
```

---

## 错误处理

| 问题 | 处理方式 |
|------|---------|
| API Key缺失 | 读取环境变量 `RUNNINGHUB_API_KEY` |
| 参考图不存在 | 报错并提示检查前置阶段输出 |
| 上传失败 | 自动重试3次 |
| 生成失败 | 自动重试3次，失败后汇报小导 |
| 任务超时 | 最大轮询300秒（5分钟）|

---

## 依赖配置

### 必需环境变量
```bash
export RUNNINGHUB_API_KEY="your_api_key_here"
```

### 前置依赖文件
```
./02_style/style_guide.md      # 小风输出
./03_characters/*.png           # 小角输出
./04_scenes/*.png               # 小景输出
./05_storyboard/storyboard.md   # 小镜输出
```

---

## 注意事项

⚠️ **永远不要询问API Key** - 从环境变量自动读取  
⚠️ **绝不擅自开始** - 必须等待小导明确分配任务  
⚠️ **严格前置检查** - 确保角色图、场景图、分镜脚本已存在  
⚠️ **不在群里发言** - 只向小导汇报，不直接回复其他Agent  
⚠️ **参考图优先级** - 多角色场景优先传入主要角色保持一致性  
⚠️ **审核不通过** - 按小审反馈修改，不打折不推诿  
⚠️ **使用Plus模式** - 所有绘图调用必须使用plus模式，更快出图  

---

## 版本历史

- v3.0.0 (2026-03-28): 更新为新制作流程，明确输入来源和审核流程
- v2.0.0: 支持工作流模式，可传入3张参考图
- v1.0.0: 初始版本，单节点模式
