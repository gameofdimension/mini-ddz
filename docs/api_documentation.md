# Mini DDZ 前后端交互接口文档

## 项目架构概述

Mini DDZ 是一个斗地主（Dou Dizhu）PvE（人机对战）演示项目，采用前后端分离架构：

- **前端**: React 16.x + Material-UI + Element React
- **后端**: Flask + Flask-CORS
- **AI 推理**: PyTorch / ONNX Runtime (DouZero 模型)

## 基础配置

### 后端地址

```javascript
// src/utils/config.js
const douzeroDemoUrl = 'http://127.0.0.1:5050';
```

后端服务默认运行在 **5050 端口**（可通过启动参数修改）。

### 跨域配置

后端已启用 CORS，允许前端跨域访问：

```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

---

## API 接口列表

### 1. AI 预测接口

#### `POST /predict`

获取当前游戏状态的 AI 预测结果（推荐出牌及胜率）。

**请求参数 (Form Data)**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `player_position` | int | 是 | 玩家位置（0=地主, 1=地主下家, 2=地主上家） |
| `player_hand_cards` | string | 是 | 当前手牌（例如："3456789TJQKA2X"） |
| `num_cards_left_landlord` | int | 是 | 地主剩余牌数 |
| `num_cards_left_landlord_down` | int | 是 | 地主下家剩余牌数 |
| `num_cards_left_landlord_up` | int | 是 | 地主上家剩余牌数 |
| `three_landlord_cards` | string | 是 | 三张地主牌 |
| `card_play_action_seq` | string | 是 | 出牌动作序列，逗号分隔（空字符串表示无） |
| `other_hand_cards` | string | 是 | 其他玩家手牌合并 |
| `last_move_landlord` | string | 是 | 地主上一轮出牌 |
| `last_move_landlord_down` | string | 是 | 地主下家上一轮出牌 |
| `last_move_landlord_up` | string | 是 | 地主上家上一轮出牌 |
| `bomb_num` | int | 是 | 已出炸弹数量 |
| `played_cards_landlord` | string | 是 | 地主已出牌 |
| `played_cards_landlord_down` | string | 是 | 地主下家已出牌 |
| `played_cards_landlord_up` | string | 是 | 地主上家已出牌 |

**成功响应 (200 OK)**:

```json
{
  "status": 0,
  "message": "success",
  "result": {
    "345": "-0.123456",
    "pass": "-0.789012",
    "3334": "0.234567"
  },
  "win_rates": {
    "345": "0.4383",
    "pass": "0.1055",
    "3334": "0.6173"
  }
}
```

**字段说明**:
- `result`: 各动作的置信度值（范围 -1 ~ 1）
- `win_rates`: 转换后的胜率（范围 0 ~ 1），计算公式 `(confidence + 1) / 2`

**错误响应**:

| status | 描述 |
|--------|------|
| -1 | 未知错误 |
| 1 | 无效的玩家位置（必须是 0、1 或 2） |
| 2 | 地主手牌数量无效（应为 1-20） |
| 3 | 农民手牌数量无效（应为 1-17） |
| 4 | 剩余牌数与手牌不符 |
| 5 | 剩余牌数不在有效范围内 |
| 6 | 地主牌数量无效（应为 0-3） |
| 7 | 其他手牌数量不符 |

**前端调用示例**:

```javascript
import axios from 'axios';
import qs from 'query-string';

const requestBody = {
    player_position: 0,
    player_hand_cards: "3456789TJQKA2XD",
    num_cards_left_landlord: 20,
    num_cards_left_landlord_down: 17,
    num_cards_left_landlord_up: 17,
    three_landlord_cards: "XD2",
    card_play_action_seq: "",
    other_hand_cards: "...",
    last_move_landlord: "",
    last_move_landlord_down: "",
    last_move_landlord_up: "",
    bomb_num: 0,
    played_cards_landlord: "",
    played_cards_landlord_down: "",
    played_cards_landlord_up: ""
};

const apiRes = await axios.post(`${douzeroDemoUrl}/predict`, qs.stringify(requestBody));
```

---

### 2. 合法动作查询接口

#### `POST /legal`

获取给定手牌和对手动作的可行出牌列表。

**请求参数 (Form Data)**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `player_hand_cards` | string | 是 | 当前手牌 |
| `rival_move` | string | 是 | 需要压制的出牌（第一手为空字符串） |

**成功响应 (200 OK)**:

```json
{
  "status": 0,
  "message": "success",
  "legal_action": "345,3,4,5,pass"
}
```

**字段说明**:
- `legal_action`: 逗号分隔的合法动作列表，每个动作是牌面字符组合

**前端调用示例**:

```javascript
const requestBody = {
    player_hand_cards: "3456789TJQKA2X",
    rival_move: ""  // 第一手为空，表示任意出牌
};

const apiRes = await axios.post(`${douzeroDemoUrl}/legal`, qs.stringify(requestBody));
const legalActions = apiRes.data.legal_action.split(',');
```

---

### 3. 生成回放接口

#### `GET /generate_ai_battle`

生成新的 AI 对战回放数据（运行一局完整的 AI 对战）。

**请求参数**: 无

**成功响应 (200 OK)**:

```json
{
  "status": 0,
  "message": "success",
  "replay_id": "a1b2c3d4",
  "data": {
    "replay_id": "a1b2c3d4",
    "playerInfo": [
      {"id": 0, "index": 0, "role": "landlord", "agentInfo": {"name": "DouZero-Landlord"}},
      {"id": 1, "index": 1, "role": "peasant", "agentInfo": {"name": "DouZero-Peasant"}},
      {"id": 2, "index": 2, "role": "peasant", "agentInfo": {"name": "DouZero-Peasant"}}
    ],
    "initHands": [
      "S3 H3 D3 C3 S4 H4 D4 C4 ...",
      "S5 H5 D5 C5 S6 H6 D6 C6 ...",
      "S7 H7 D7 C7 S8 H8 D8 C8 ..."
    ],
    "moveHistory": [
      {
        "playerIdx": 0,
        "move": "S3 H3 D3",
        "info": {
          "values": {
            "333": 0.85,
            "33": 0.72,
            "3": 0.65
          }
        }
      }
    ]
  }
}
```

**前端调用示例**:

```javascript
const response = await axios.get(`${douzeroDemoUrl}/generate_ai_battle`);
const replayData = response.data.data;
```

---

### 4. 保存回放接口

#### `POST /save_replay`

保存用户游戏的回放到数据库。

**请求参数 (JSON Body)**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `playerInfo` | array | 玩家信息数组 |
| `initHands` | array | 初始手牌数组 |
| `moveHistory` | array | 出牌历史记录 |

**请求体示例**:

```json
{
  "playerInfo": [
    {"id": 0, "index": 0, "role": "landlord", "agentInfo": {"name": "Player"}},
    {"id": 1, "index": 1, "role": "peasant", "agentInfo": {"name": "DouZero"}},
    {"id": 2, "index": 2, "role": "peasant", "agentInfo": {"name": "DouZero"}}
  ],
  "initHands": ["S3 H3 ...", "S4 H4 ...", "S5 H5 ..."],
  "moveHistory": [
    {"playerIdx": 0, "move": "S3 H3 D3", "info": {}}
  ]
}
```

**成功响应 (200 OK)**:

```json
{
  "status": 0,
  "message": "success",
  "replay_id": "e5f6g7h8"
}
```

**前端调用示例**:

```javascript
const replayData = {
    playerInfo: [...],
    initHands: [...],
    moveHistory: [...]
};

const response = await axios.post(`${douzeroDemoUrl}/save_replay`, replayData);
```

---

### 5. 获取回放接口

#### `GET /replay/<replay_id>`

根据 ID 获取回放数据。

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `replay_id` | string | 回放唯一标识符 |

**成功响应 (200 OK)**:

```json
{
  "status": 0,
  "message": "success",
  "data": {
    "replay_id": "a1b2c3d4",
    "playerInfo": [...],
    "initHands": [...],
    "moveHistory": [...],
    "created": "2024-01-15 10:30:00"
  }
}
```

**前端调用示例**:

```javascript
const replayId = "a1b2c3d4";
const response = await axios.get(`${douzeroDemoUrl}/replay/${replayId}`);
const replayData = response.data.data;
```

---

### 6. 列出回放接口

#### `GET /list_replays`

列出所有可用的回放（按创建时间倒序）。

**请求参数**: 无

**成功响应 (200 OK)**:

```json
{
  "status": 0,
  "message": "success",
  "replays": [
    {"replay_id": "a1b2c3d4", "created": "2024-01-15 10:30:00"},
    {"replay_id": "e5f6g7h8", "created": "2024-01-15 09:20:00"}
  ]
}
```

**前端调用示例**:

```javascript
const response = await axios.get(`${douzeroDemoUrl}/list_replays`);
const replays = response.data.replays;
```

---

### 7. 删除回放接口

#### `DELETE /delete_replay/<replay_id>`

删除指定 ID 的回放。

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `replay_id` | string | 回放唯一标识符 |

**成功响应 (200 OK)**:

```json
{
  "status": 0,
  "message": "success"
}
```

**前端调用示例**:

```javascript
const replayId = "a1b2c3d4";
const response = await axios.delete(`${douzeroDemoUrl}/delete_replay/${replayId}`);
```

---

## 数据格式规范

### 牌面编码

#### 内部编码（后端 AI 使用）

| 牌面 | 编码 |
|------|------|
| 3-9 | 3, 4, 5, 6, 7, 8, 9 |
| 10 | T |
| J | J |
| Q | Q |
| K | K |
| A | A |
| 2 | 2 |
| 小王 | X |
| 大王 | D |

#### 显示编码（前端展示使用）

| 牌面 | 编码 | 说明 |
|------|------|------|
| 黑桃 | S | Spade |
| 红桃 | H | Heart |
| 方块 | D | Diamond |
| 梅花 | C | Club |
| 小王 | BJ | Black Joker |
| 大王 | RJ | Red Joker |

**示例**:
- `S3` = 黑桃3
- `H3` = 红桃3
- `D3` = 方块3
- `C3` = 梅花3
- `BJ` = 小王
- `RJ` = 大王

### 玩家位置定义

| 位置值 | 角色 | 说明 |
|--------|------|------|
| 0 | landlord | 地主 |
| 1 | landlord_down | 地主下家（农民） |
| 2 | landlord_up | 地主上家（农民） |

### 动作类型

后端支持的动作类型（`move_detector.py` 中定义）：

| 类型常量 | 值 | 说明 |
|----------|-----|------|
| TYPE_0_PASS | 0 | 过牌 |
| TYPE_1_SINGLE | 1 | 单张 |
| TYPE_2_PAIR | 2 | 对子 |
| TYPE_3_TRIPLE | 3 | 三张 |
| TYPE_4_BOMB | 4 | 炸弹（四张） |
| TYPE_5_KING_BOMB | 5 | 王炸 |
| TYPE_6_3_1 | 6 | 三带一 |
| TYPE_7_3_2 | 7 | 三带二 |
| TYPE_8_SERIAL_SINGLE | 8 | 顺子 |
| TYPE_9_SERIAL_PAIR | 9 | 连对 |
| TYPE_10_SERIAL_TRIPLE | 10 | 飞机 |
| TYPE_11_SERIAL_3_1 | 11 | 飞机带单 |
| TYPE_12_SERIAL_3_2 | 12 | 飞机带对 |
| TYPE_13_4_2 | 13 | 四带二 |
| TYPE_14_4_22 | 14 | 四带两对 |

---

## 前端页面与 API 对应关系

| 页面 | 路径 | 使用的 API |
|------|------|-----------|
| PvE 对战 | `/pve/doudizhu-demo` | `/predict`, `/legal`, `/save_replay` |
| 回放观看 | `/replay/doudizhu` | `/generate_ai_battle`, `/replay/<id>` |
| 回放列表 | `/replay/list` | `/list_replays`, `/delete_replay/<id>` |

---

## 后端核心模块

### 文件结构

```
pve_server/
├── run_douzero.py      # Flask 主服务器，API 路由定义
├── deep.py             # 深度学习模型包装器 (DeepAgent)
├── models.py           # PyTorch 模型定义 (LSTM)
├── replay_db.py        # SQLite 数据库操作
└── utils/
    ├── move_generator.py   # 动作生成器
    ├── move_detector.py    # 动作类型检测
    ├── move_selector.py    # 动作筛选器
    └── utils.py            # 通用工具
```

### AI 模型

- **地主模型**: `landlord.ckpt` / `landlord.onnx`
- **地主上家模型**: `landlord_up.ckpt` / `landlord_up.onnx`
- **地主下家模型**: `landlord_down.ckpt` / `landlord_down.onnx`

支持 PyTorch 和 ONNX Runtime 两种推理方式。

---

## 错误处理

所有 API 返回统一格式的响应：

```json
{
  "status": 0,      // 0 表示成功，非 0 表示错误
  "message": "...", // 状态描述
  "data": {...}     // 成功时的数据（可选）
}
```

前端应始终检查 `status` 字段，不为 0 时根据 `message` 进行错误处理。
