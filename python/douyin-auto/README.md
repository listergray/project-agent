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

## 注意

- 首次 保持 `HEADLESS=false`
- 发布 前 请 确认 标题/封面/合规
- 仅 用 于 自己 账号 内容
