# OpenPlan3D（嵌入「我的所有」）

基于 [laanlabs/open3dFloorplan](https://github.com/laanlabs/open3dFloorplan)（MIT）的专业 2D/3D 户型编辑器。

## 怎么用

1. 首次（或依赖变更后）构建静态资源：

```bash
npm run build:openplan
```

输出到 `public/openplan/`（已 gitignore；本地/部署前需构建）。

2. 启动主站 `npm run dev`，打开小屋 → **打开专业编辑器**，或直达 `/home/design`。

3. 在编辑器里画墙、门窗、家具；改动经 postMessage 写入 Dexie `homes.openPlanJson`，随账本备份导出。

## 结构

| 路径 | 作用 |
|------|------|
| `third_party/openplan` | SvelteKit 源码（含 embed 桥） |
| `public/openplan` | 构建产物 |
| `src/pages/OpenPlanDesign.tsx` | 全屏 iframe 壳 |

## 说明

- 简易格网平面图仍保留在 `/home`，与 OpenPlan 工程**并行**（未自动双向同步房间表）。
- 上游项目为 SvelteKit，故以静态嵌入而非 React 重写。
