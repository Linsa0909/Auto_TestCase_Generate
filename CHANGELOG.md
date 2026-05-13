# 变更记录

## 2026-05-11

### Bug 修复

#### BUG-001: 需求解析拆分错误（15个需求实际只有5个）
- **现象**: 导入5条多行格式需求，解析出15条
- **原因**: `parseImport()` 按行拆分，每行当作一条需求。实际格式是以 `#NNNNNN` 开头的多行块
- **修复**: 改为按 `#NNNNNN` 模式分块，每块为一条需求
- **文件**: `frontend/src/views/TestPlanView.vue` — `parseImport()` 函数
- **避免**: 解析器必须先理解数据格式再拆分，不能假设一行一条

#### BUG-002: 需求名称包含负责人
- **现象**: `#194714 【产品】治理框架支持在venus部署 王沁雪 sprint59...` 解析后名称为"治理框架支持在venus部署 王沁雪"
- **原因**: `parseRequirementBlock()` 用 `lines.join(' ')` 合并所有行，名称行和元数据行合并后单空格分隔，`split(/\s{2,}/)` 无法区分
- **修复**: 改为逐行解析 — ID行提取ID，元数据行（含日期/sprint/状态）提取owner/dates/status，其余行提取名称
- **文件**: `frontend/src/views/TestPlanView.vue` — `parseRequirementBlock()` 函数
- **避免**: 多行格式解析必须逐行识别语义，不能 join 后统一处理

#### BUG-003: 导出全部 Method Not Allowed
- **现象**: 点击「导出全部」返回 405 Method Not Allowed
- **原因**: 前端 `exportBatch()` 调用 `POST /api/export-batch`，后端只有 `POST /api/export`（单条导出），缺少批量导出路由
- **修复**: 在 `backend/main.py` 添加 `POST /api/export-batch` 路由
- **文件**: `backend/main.py` — `export_batch_test_cases()` 函数
- **避免**: 前后端接口必须同步定义，新增前端调用时必须确认后端路由存在

#### BUG-004: 生成用例后切出再切回数据丢失
- **现象**: 在测试计划中生成用例后，切到列表再切回来，已生成的测试用例被清空
- **原因**: TestPlanView 组件卸载后内存数据丢失，生成完成后没有自动保存到后端
- **修复**: 每次生成完成后自动调用 `autoSave()` 保存到后端；返回列表时也先保存
- **文件**: `frontend/src/views/TestPlanView.vue` — `generateSingle()`, `batchGenerate()`, `goBack()`
- **避免**: 任何修改操作后必须持久化，不能依赖组件内存状态

#### BUG-005: 测试计划列表进度不刷新
- **现象**: 3/6需求完成后切到列表，进度条和完成数没有更新
- **原因**: PlanListView 只在 `onMounted` 加载一次数据，从 TestPlanView 返回时不会重新加载
- **修复**: Workbench 中 `closePlan()` 时递增 `planListKey`，强制 PlanListView 重新挂载
- **文件**: `frontend/src/views/Workbench.vue` — `closePlan()`, `planListKey`
- **避免**: 子组件数据可能被其他组件修改时，返回时必须刷新

#### BUG-006: Python 中使用 === 比较
- **现象**: 后端代码出现 JavaScript 风格的 `===` 运算符
- **原因**: 编码习惯混淆
- **修复**: 替换为 Python 的 `==`
- **文件**: `backend/main.py`
- **避免**: 注意语言差异，Python 用 `==` 和 `is`

### 功能新增

- 需求解析支持 `【xxx】` 分组提取
- 测试类型选择器（全面覆盖/仅冒烟/功能测试/边界异常）
- 测试计划持久化 CRUD（JSON 文件存储）
- 测试计划列表页 PlanListView
- 自动保存（生成后、返回时）
- DevOps 平台集成（配置 + 一键推送 8 步工作流）
- 批量导出路由 `/api/export-batch`
