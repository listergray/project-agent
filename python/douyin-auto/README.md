# 抖音目录发视频 (Playwright)

方案 B: 独立 FastAPI 后台 + Playwright 自动 上传 创作者中心.

> 非官方 OpenAPI, 依赖 页面 DOM, 上线 UI 变更 时 可能 需调 selector.
> 登录 态 保存 在 `data/browser-profile`, 勿 提交 到 git.

## 启动

```powershell
cd E:\ai-pro\project_agent\python\douyin-auto
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
# edit .env VIDEO_DIR=.../video_html
python run.py
```

后台: http://127.0.0.1:12500

## 使用

1. 填 视频目录 (例 `.../EP29_wechat_voice/video_html`) -> **保存并扫描**
2. **扫码登录** -> Chromium 弹窗 登 创作者中心
3. 找 `技术栈EP.29教程.mp4` - **发布到抖音**
4. 同目录 封面.png / 封面上传版_3比4.png 会 自动 选 为 封面

## 发布进度（MySQL）

库 `douyin_auto`（主机 `twlmac`）：

| 表 | 用途 |
|---|---|
| `dy_meta` | `min_ep=32`、`legacy_through_ep=31` |
| `dy_episode` | 每集状态：`LEGACY` / `SUCCESS` / `FAILED` / `RUNNING` |

启动时自动建库建表，并把 **EP.1–EP.31** 记为 `LEGACY`（历史已发布）。扫描/发布只处理 **EP.32+** 且未 `SUCCESS`/`LEGACY` 的集。

接口：`GET /api/episodes`、`GET /api/health`（含 `db`）。

同目录 sidecar：`标题.txt`、`封面上传版_3比4.png`（优先）、定位默认「北京市朝阳区」。

## 发布等待与封面检查

- 发布按顺序等待浏览器，默认最长 900 秒；等待期间任务显示“等待浏览器……已排队”。后台保活不会抢占已排队的发布。
- 同一集已有等待或执行中的任务时，重复点击会返回该任务。
- 封面选图、保存完成后，最多等待 60 秒，要求横竖封面在各自区域内连续两次预览稳定。支持已加载的图片、CSS 背景图及非空画布；文字模型不参与封面放行判断。
- 未确认封面时仍然停止发布。任务结果附带截图和 `data/debug/cover_check_*.json` 路径，区分选图未完成与预览未确认；历史失败任务保留。
- 可用 `BROWSER_WAIT_TIMEOUT_SEC`、`COVER_VERIFY_TIMEOUT_MS` 调整上述等待时间。`GET /api/health` 的 `coverVerification=stable-previews` 表示当前进程已加载此检查逻辑，`browser` 包含占用状态和排队数量。

## 发布结果确认

- 主发布按钮只点击一次。通过发布接口返回的作品 ID、明确成功提示，或作品管理中对应标题及已发布/审核中状态确认提交结果。
- 提交后回到空上传页时，会到作品管理核对本条视频；空上传页本身不算成功。正常确认默认最长等待 90 秒，期间持续更新进度，管理页核对另有受限的加载等待。
- 无法确认的提交以 `NEEDS_REVIEW`（待核对）结束，保留证据并从候选发布列表排除，防止重复发布。已关闭浏览器产生的清理异常不会覆盖业务结果。
- 任务中的“核对结果”只读取作品管理，不上传或发布视频。接口为 `POST /api/jobs/{jobId}/verify`；查到该作品后同步修正任务和本地数据库。未查到不等于确认未发布，仍应人工核对后再处理。
- 页面在排队/执行期间持续刷新状态，不再固定四分钟后停止轮询。健康接口的 `publishConfirmation=submission-evidence` 表示已加载此次完成识别逻辑。

离线回归测试（需已安装 Playwright Chromium）：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试使用临时浏览器、模拟表单及临时任务文件，不读取账号登录资料，不执行真实上传或发布。

## 注意

- 首次 保持 `HEADLESS=false`
- 发布 前 请 确认 标题/封面/合规
- 仅 用 于 自己 账号 内容
