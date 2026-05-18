# LLM Agent 代码审查报告

**审查范围**: `ac6bef5b` 之后的 LLMAgent、RandomAgent 实现、前端集成及离线评估相关代码
**审查日期**: 2026-05-17
**最后更新**: 2026-05-18

## 修复进度

| # | 问题 | 状态 | 提交 |
|---|------|------|------|
| #7 | RandomAgent 死代码 | ✅ | 39b7c8c |
| #3 | 前端空指针 | ✅ | c70eb93 |
| #2 | LLMAgent 并发安全 | ✅ | 169627f |
| #1 | `_live_sessions` 内存泄漏 | ✅ | c870952 |
| #4 | 游戏逻辑重复 | ✅ | c653a1d (+测试 487ac44) |
| #5 | `/generate_llm_battle` 冗余 | ✅ | 0caffce |
| #6 | `_get_llm_players()` 浪费 | ✅ | 0caffce |
| #8 | Agent 接口不一致 | ✅ | (doc + isinstance) |
| #9 | 硬编码字符串 | ✅ | d4772a2 |
| #10 | eslint-disable | ✅ | via #14 |
| #11 | 集成测试残留 | ✅ | 6f868ee |
| #12 | 单元测试副作用 | ✅ | bd4970b |
| #13 | 异常类型字符串匹配 | ✅ | 6d8acd4 |
| #14 | PvE 组件过长 | ✅ | 1f1f340 |
| #15 | isinstance 链 | ✅ | (保留 — 可读性好) |

---

## 问题清单

### 严重

#### 1. `_live_sessions` 无过期清理 → 内存泄漏

**位置**: `pve_server/run_douzero.py:302`

Session 仅在 `step["gameOver"]` 时清理。如果用户关闭浏览器、网络断开、或开启 session 后未继续操作，对应条目永久驻留内存。`created_at` 字段已存储但从未用于 TTL 判定。

```python
# 现状：仅在 gameOver 时 pop
if step["gameOver"]:
    _live_sessions.pop(session_id, None)

# _live_sessions 无容量上限，无 TTL 淘汰
```

#### 2. LLMAgent 并发不安全

**位置**: `pve_server/llm_agent.py` + `pve_server/run_douzero.py:42-47`

`_get_llm_players()` 返回全局缓存的单例列表。`act()` 写入 `self.last_analysis`、`self._call_count`、`self.fallback_count`。两个并发 `/predict` 请求会互相覆盖这些字段，导致分析结果串位、fallback 计数错误。

```python
# run_douzero.py:46 — 全局单例
_llm_players = [LLMAgent(0), LLMAgent(1), LLMAgent(2)]

# llm_agent.py:377-378 — 并发写入同一实例
self.last_analysis = data.get("analysis", "") or ""
self.fallback_count += 1  # 非原子操作
```

#### 3. `ConfigurableBattleView.js` 潜在空指针

**位置**: `src/view/ConfigurableBattleView/ConfigurableBattleView.js:88, 219`

```js
currentPlayer: data.playerInfo.find(p => p.role === 'landlord').index
```

`Array.find()` 在未找到时返回 `undefined`，访问 `.index` 会抛 TypeError。如果后端返回的 playerInfo 格式异常，前端直接白屏。

---

### 高优先级

#### 4. `watch_llm_battle.py` 与 `game.py` 游戏逻辑重复

**位置**: `tools/watch_llm_battle.py:76-219` vs `pve_server/game.py`

`run_one_game()` 整段复制了发牌、action seq 维护、bomb 计数、手牌移除等逻辑。两处分别维护，修改规则时极易遗漏。

#### 5. `/generate_llm_battle` 端点冗余

**位置**: `pve_server/run_douzero.py:239-254`

`GET /generate_llm_battle` 硬编码三个位置全用 LLM。`POST /generate_battle` 已支持任意 agent 组合 —— 前者是后者的子集。

#### 6. `/predict` 端点中 `_get_llm_players()` 资源浪费

**位置**: `pve_server/run_douzero.py:42-47, 175-176`

每次 `/predict` 调用使用 1 个 agent，但 `_get_llm_players()` 创建了 3 个 LLMAgent（各含一个 OpenAI client 及其连接池）。

#### 7. `RandomAgent.fallback_count` 死代码

**位置**: `pve_server/random_agent.py:14`

```python
self.fallback_count = 0   # 从未递增，从未读取
```

---

### 中优先级

#### 8. Agent 接口不一致，依赖 duck typing

**位置**: `pve_server/game.py:239`

```python
if hasattr(players[cp], "last_analysis"):
```

三个 agent 类型没有统一协议基类，可选属性靠 `hasattr` 探测，脆弱且不利于类型检查。

#### 9. Agent type 字符串硬编码分散 6 处

`"deep"` / `"llm"` / `"random"` 散布在 `run_douzero.py`、`watch_llm_battle.py`、`PvEDoudizhuDemoView.js`、`ConfigurableBattleView.js`、`game.py` 中。新增 agent 类型需改动全部位置。

#### 10. `PvEDoudizhuDemoView.js` 过度使用 eslint-disable

**位置**: `src/view/PvEView/PvEDoudizhuDemoView.js:723, 728, 740`

三处 `eslint-disable-next-line react-hooks/exhaustive-deps` 掩盖了 useEffect 依赖数组不完整的问题。

#### 11. 集成测试引用已删除的环境变量

**位置**: `tools/test_llm_integration.py:180`

```python
os.environ["LLM_AGENT_POSITIONS"] = "0,1,2"
```

该变量已在 commit `45c3aa3` 移除，此行具误导性。

#### 12. LLMAgent 单元测试有文件系统副作用

**位置**: `tests/test_llm_agent.py:160-164`

`test_fallback_on_api_error` 中 `act()` 的 except 块会调用 `_save_failed_request()` 写磁盘，未 mock 该函数。

---

### 低优先级

#### 13. `/live-battle/start` 通过字符串匹配判断异常类型

**位置**: `pve_server/run_douzero.py:321`

```python
if "DEEPSEEK_API_KEY" in msg:
```

依赖报错消息的文本来识别配置错误，消息格式变化会导致判断失效。

#### 14. `PvEDoudizhuDemoView.js` 组件过长

单文件 ~1180 行，包含游戏逻辑、API 请求、状态管理、计时器、统计。新增 agent 配置功能后问题加剧。

#### 15. `game.py` `_get_agent_label` 用 isinstance 链

新增 agent 类型时需修改该函数，用映射表更易扩展。

---

## 行动方案

### 第一阶段（立即修复，1-2h）

| # | 问题 | 方案 |
|---|------|------|
| 2 | LLMAgent 并发不安全 | `act()` 中 `last_analysis` 作为返回值带回，不写实例属性；`fallback_count` 改为 `threading.Lock` 保护 |
| 3 | 前端空指针 | `data.playerInfo.find(...)?.index ?? 0` |
| 7 | RandomAgent 死代码 | 移除 `fallback_count` 属性 |

### 第二阶段（本周内，2-4h）

| # | 问题 | 方案 |
|---|------|------|
| 1 | `_live_sessions` 内存泄漏 | 启动后台线程每 5 分钟扫描并清理超过 30 分钟未活动的 session；设置最大容量 100 |
| 4 | 游戏逻辑重复 | `watch_llm_battle.py` 的 `run_one_game()` 改为调用 `game.py` 的 `init_game()` + `step_game()`，仅在外层做终端输出 |
| 5 | `/generate_llm_battle` 冗余 | `LLMBattleView.js` 改用 `POST /generate_battle`，然后移除 `/generate_llm_battle` 端点 |
| 6 | `_get_llm_players()` 浪费 | 改为 `_get_llm_agent(position: int) -> LLMAgent`，按需懒加载单个 agent |

### 第三阶段（后续迭代，3-6h）

| # | 问题 | 方案 |
|---|------|------|
| 8 | Agent 接口不一致 | 定义 `Agent` Protocol 类，含 `act()` 和可选的 `last_analysis` 属性；替换 `hasattr` |
| 9 | 硬编码字符串 | 后端定义 `AgentType` Enum，前端从单一常量导入 |
| 10 | eslint-disable | 修复 useEffect 依赖数组，移除 disable 注释 |
| 11 | 集成测试残留 | 删除 `LLM_AGENT_POSITIONS` 相关行 |
| 12 | 单元测试副作用 | mock `_save_failed_request` |
| 13 | 异常类型字符串匹配 | 定义 `ConfigError(Exception)` 替代 `ValueError` |
| 14 | PvE 组件过长 | 拆分为 `useGameState`、`useAgentConfig` 等 hooks |
| 15 | isinstance 链 | 用 `_AGENT_LABEL_MAP` 字典替代 |
