# 本地视频素材库（v1.0）

本项目提供本地桌面场景下的短视频素材处理链路，重点覆盖：

- 视频导入与基础信息入库
- 固定 4 秒切片
- 关键帧抽取与缩略图生成
- 标签接口预留（默认 Mock）
- 素材库列表与详情
- 原视频追溯与延展导出

第一版保留 VLM 接口，不绑定在线/本地模型，默认使用 Mock 标签返回，后续可替换为任意 AI 模型服务。

## 快速启动

```bash
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
run.bat
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
