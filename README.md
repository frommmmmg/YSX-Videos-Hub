# 本地视频素材库（v1.0）

本项目提供本地桌面场景下的短视频素材处理链路，重点覆盖：

- 视频导入与基础信息入库
- 固定 4 秒切片
- 关键帧抽取与缩略图生成
- 标签接口预留（默认 Mock）
- 素材库列表与详情
- 原视频追溯与延展导出

第一版保留 VLM 接口，不绑定在线/本地模型，默认使用 Mock 标签返回，可切换到：

- 本地 Ollama（`TAGGER_BACKEND=ollama`）
- StepFun 视觉模型（`TAGGER_BACKEND=stepfun`）

## 快速启动

```bash
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
run.bat
```

可直接在 `run.bat` 中取消注释配置行来切换后端，例如：

```bat
set TAGGER_BACKEND=ollama
set OLLAMA_API_BASE=http://127.0.0.1:11434
set OLLAMA_MODEL=llava:7b

:: 或
set TAGGER_BACKEND=stepfun
set STEPFUN_API_KEY=your_api_key
set STEPFUN_MODEL=step-1v-8k
```

启动后会自动创建以下目录：

- `library_data/originals/`
- `library_data/clips/`
- `library_data/thumbnails/`
- `library_data/keyframes/`
- `library_data/exports/`
- `library_data/database/`
- `library_data/logs/`
- `library_data/temp/`

以及 `library_data/database/library.db` 数据库文件。

## 目录说明

```text
app/
  config/
  db/
  services/
  ui/
  utils/
```

## CLI 自动化接口

支持通过 CLI 调用核心流程，适配 AI/脚本直接编排。

示例（默认输出 JSON）：

```bash
python -m app.cli import "D:\素材\example.mp4"
python -m app.cli process "D:\素材\example.mp4" --tag
python -m app.cli split 1 --target-duration 4.0
python -m app.cli keyframes 12
python -m app.cli tag 12
python -m app.cli export 12 --before 1 --after 1 --mode copy
python -m app.cli search "夜景"
python -m app.cli stats
```

常用参数：

```bash
python -m app.cli import --help
python -m app.cli process --help
```
