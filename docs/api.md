# API 文档

## 后端配置

后端服务器的默认配置定义在 `/src/utils/config.js`：

```javascript
const apiUrl = 'http://127.0.0.1:8000';
const douzeroDemoUrl = 'http://127.0.0.1:5000';
```

目前仅使用 `douzeroDemoUrl`（5000 端口）用于 PvE Flask 服务器。

## 后端 REST API

Flask 后端为斗地主 PvE 和回放功能提供以下接口。

### POST /predict

获取当前游戏状态的 AI 预测。

**参数：**

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `player_position` | int | 玩家位置（0=地主，1=地主下家，2=地主上家） |
| `player_hand_cards` | string | 当前手牌（例如："3456789TJQKA2X"） |
| `num_cards_left_landlord` | int | 地主剩余牌数 |
| `num_cards_left_landlord_down` | int | 地主下家剩余牌数 |
| `num_cards_left_landlord_up` | int | 地主上家剩余牌数 |
| `three_landlord_cards` | string | 三张地主牌 |
| `card_play_action_seq` | string | 出牌动作序列，逗号分隔 |
| `other_hand_cards` | string | 其他玩家手牌合并 |
| `last_move_landlord` | string | 地主上一轮出牌 |
| `last_move_landlord_down` | string | 地主下家上一轮出牌 |
| `last_move_landlord_up` | string | 地主上家上一轮出牌 |
| `bomb_num` | int | 已出炸弹数量 |
| `played_cards_landlord` | string | 地主已出牌 |
| `played_cards_landlord_down` | string | 地主下家已出牌 |
| `played_cards_landlord_up` | string | 地主上家已出牌 |

**响应：**

```json
{
  "status": 0,
  "message": "success",
  "result": {
    "345": "-0.123456",
    "pass": "-0.789012"
  },
  "win_rates": {
    "345": "0.4383",
    "pass": "0.1055"
  }
}
```

### POST /legal

获取给定手牌和对手动作的可行出牌。

**参数：**

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `player_hand_cards` | string | 当前手牌 |
| `rival_move` | string | 需要压制的出牌（第一手为空字符串） |

**响应：**

```json
{
  "status": 0,
  "message": "success",
  "legal_action": "345,3,4,5,pass"
}
```

### GET /generate_replay

生成新的 AI 对战回放。

**响应：**

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
    "initHands": ["S3 H3 D3 C3 ...", "S4 H4 D4 C4 ...", "S5 H5 D5 C5 ..."],
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

### GET /replay/<replay_id>

根据 ID 获取回放数据。

**响应：**

```json
{
  "status": 0,
  "message": "success",
  "data": {
    "replay_id": "a1b2c3d4",
    "playerInfo": [...],
    "initHands": [...],
    "moveHistory": [...]
  }
}
```

### GET /list_replays

列出所有可用回放。

**响应：**

```json
{
  "status": 0,
  "message": "success",
  "replays": [
    {"replay_id": "a1b2c3d4", "created": 1234567890},
    {"replay_id": "e5f6g7h8", "created": 1234567880}
  ]
}
```

## 错误码

| 状态码 | 描述 |
|-------------|-------------|
| 0 | 成功 |
| -1 | 未知错误 |
| 1 | 无效的玩家位置（必须是 0、1 或 2） |
| 2 | 地主手牌数量无效（应为 1-20） |
| 3 | 农民手牌数量无效（应为 1-17） |
| 4 | 剩余牌数与手牌不符 |
| 5 | 剩余牌数不在有效范围内 |
| 6 | 地主牌数量无效（应为 0-3） |
| 7 | 其他手牌数量不符 |

## 牌面编码

牌面使用单字符编码：

| 牌面 | 编码 |
|------|----------|
| 3-10 | 3, 4, 5, 6, 7, 8, 9, T |
| J | J |
| Q | Q |
| K | K |
| A | A |
| 2 | 2 |
| 小王 | X |
| 大王 | D |

显示格式：`S3`（黑桃3）、`H3`（红桃3）、`D3`（方块3）、`C3`（梅花3）、`BJ`（小王）、`RJ`（大王）。
