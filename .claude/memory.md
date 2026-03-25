# Claude Memory - Project Conventions

## Git 工作流规范

### 禁止直接推送到 main 分支

**严重错误：** 曾经直接将代码推送到 main 分支（commit a53bddd），而不是通过 PR 流程。

**正确流程：**
1. 从 main 分支创建 feature 分支：`git checkout -b feature/xxx`
2. 在 feature 分支上进行开发
3. 推送 feature 分支到 origin：`git push origin feature/xxx`
4. **创建 PR** 将 feature 分支合并到 main
5. 等待代码审查通过后合并

**例外情况：**
- 紧急修复（hotfix）
- 明确的维护者权限且项目允许
- 个人项目且明确选择不遵循 PR 流程

### 提交前检查清单
- [ ] 是否在 feature 分支上？
- [ ] 是否推送到 origin 的 feature 分支？
- [ ] 是否创建了 PR？
- [ ] 是否等待审查/合并？

**切记：永远不要 `git push origin main`**
