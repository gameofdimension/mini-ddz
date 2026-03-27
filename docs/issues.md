# Mini DDZ — 已发现问题清单

> 生成日期：2026-03-27

---

## Bug

### 1. models.py 重复层赋值（死代码）

- **文件**：`pve_server/models.py`
- **位置**：第 14-15 行（LandlordLstmModel）、第 44-45 行（FarmerLstmModel）
- **描述**：`self.dense5` / `self.dense4` 被赋值 3 次，中间赋值为死代码，可能导致模型结构不符合预期。
- **优先级**：高
- **修复方案**：检查正确的层定义顺序，移除重复赋值。

---

## 无用代码

### 2. socket.io-client 未使用依赖

- **文件**：`package.json`
- **描述**：`socket.io-client@4.7.0` 已声明为运行时依赖，但项目中没有任何代码 import 或使用它。
- **优先级**：低
- **修复方案**：执行 `npm uninstall socket.io-client`。

### 3. config.js 未使用变量

- **文件**：`src/utils/config.js`
- **描述**：`apiUrl`（`http://127.0.0.1:8000`）已导出但从未被引用。
- **优先级**：低
- **修复方案**：移除该变量。

---

## 硬编码

### 4. 后端 URL 硬编码为 localhost

- **文件**：`src/utils/config.js`
- **描述**：`douzeroDemoUrl` 硬编码为 `http://127.0.0.1:5050`，无法在不同部署环境（测试/生产）中切换。
- **优先级**：中
- **修复方案**：使用环境变量（如 `REACT_APP_API_URL`）配置，开发环境提供 `.env.local` 默认值。

---

## 国际化 (i18n) 缺失

### 5. 多处硬编码文本未纳入 i18n

- **文件**：`src/components/Navbar.js`、`src/view/ReplayView/DoudizhuReplayView.js`、`src/view/AIBattleView/AIBattleView.js`
- **描述**：
  - **Navbar.js**：硬编码中文 `"3 AI 对战"`、`"回放"`
  - **ReplayView / AIBattleView**：硬编码英文 `"Pass"`、`"Waiting..."`、`"Game Ends!"`、`"Landlord Wins"`、`"Peasants Win"`、`"Game Speed"`、`"Turn"`、`"Start"`、`"Pause"`、`"Resume"`、`"Restart"` 等
- **优先级**：中
- **修复方案**：将所有用户可见文本提取到 `src/locales/en/translation.json` 和 `src/locales/zh/translation.json` 中。

---

## 架构问题

### 6. PvEView 模块级可变状态

- **文件**：`src/view/PvEView/PvEDoudizhuDemoView.js`（1142 行）
- **描述**：使用模块级 `let` 变量（`gameHistory`、`bombNum`、`legalActions` 等）管理游戏状态，导致组件难以测试、不可复用、热重载时状态丢失。
- **优先级**：中
- **修复方案**：重构为 React `useState` / `useReducer`，或将游戏状态封装为独立的状态管理模块。

### 7. AIBattleView 与 ReplayView 高度重复

- **文件**：`src/view/AIBattleView/AIBattleView.js`、`src/view/ReplayView/DoudizhuReplayView.js`
- **描述**：两个组件代码结构几乎一致，仅数据来源不同（前者调用 `/generate_ai_battle`，后者从 `/replay/<id>` 加载）。
- **优先级**：中
- **修复方案**：提取公共组件（如 `GamePlaybackView`），通过 props 传入数据源差异。

### 8. 类组件与函数组件混用

- **文件**：`DoudizhuGameBoard.js`、`DoudizhuReplayView.js`、`AIBattleView.js`（类组件）；`PvEDoudizhuDemoView.js`、`ReplayListView.js`、`Navbar.js`（函数组件）
- **描述**：项目无统一组件风格，增加维护成本。
- **优先级**：低（重构风险较高）
- **修复方案**：逐步将类组件迁移为函数组件 + hooks。

---

## 工程化 / DevOps

### 9. 缺少 CI/CD 流水线

- **描述**：项目无任何自动化 CI/CD 配置（无 GitHub Actions、无 Docker、无部署脚本）。
- **优先级**：中
- **修复方案**：
  - 添加 `.github/workflows/ci.yml`，包含 ruff check、ruff format、mypy、npm test、pytest
  - 可选：添加 Dockerfile 简化部署

## 优先级汇总

| 优先级 | 编号 | 问题 |
|--------|------|------|
| 高 | #1 | models.py 重复层赋值 |
| 中 | #4 | 后端 URL 硬编码 |
| 中 | #5 | i18n 缺失 |
| 中 | #6 | PvEView 模块级可变状态 |
| 中 | #7 | AIBattleView / ReplayView 重复 |
| 中 | #9 | 缺少 CI/CD |
| 低 | #2 | socket.io-client 未使用 |
| 低 | #3 | apiUrl 未使用 |
| 低 | #8 | 组件风格不统一 |
