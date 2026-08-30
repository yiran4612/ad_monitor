# Layer: service
"""素材文件本地存储实现（OSS / STS 的临时替代方案）。

目录结构（MEDIA_ROOT 之下）：
- ``creatives/images/<uuid4hex>.<ext>``   图片素材
- ``creatives/videos/<uuid4hex>.<ext>``   视频素材
- ``creatives/covers/<uuid4hex>.jpg``     视频封面（抽帧成功才有）

设计约定：
- 文件重命名为 ``uuid4().hex + 小写扩展名``，不保留中文名（Windows / URL 编码坑），
  同名文件二次上传也会生成新文件，不覆盖旧文件。
- 所有校验（大小 / 后缀白名单 / 类型一致性）在 Service 层完成，View 只取
  ``request.FILES['file']``。
- 后续接 OSS 时：只替换本文件 ``save`` / ``abs_path`` 的实现（上传到 bucket、
  返回 OSS URL），View / URL / 响应结构均不需要改动。
"""

import uuid
from pathlib import Path

from django.conf import settings

from apps.ads.exceptions import UploadParamError, UploadTypeMismatch

IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}
VIDEO_EXTS = {"mp4", "mov", "avi", "mkv"}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200MB

# material_type → 后缀白名单 / 子目录
_TYPE_EXTS = {"image": IMAGE_EXTS, "video": VIDEO_EXTS}
_TYPE_DIR = {"image": "images", "video": "videos"}


class LocalStorageService:
    """本地 media 存储：落盘 + 校验 + 元信息提取。"""

    @staticmethod
    def save(uploaded_file, material_type: str) -> dict:
        """校验并落盘一个上传文件，返回元信息。

        返回 ``{url, cover_url, duration, filename, size}``，
        其中 ``url`` / ``cover_url`` 为相对路径（``/media/...``），
        由 View 层用 ``request.build_absolute_uri`` 拼成完整地址。
        """
        if material_type not in _TYPE_EXTS:
            raise UploadParamError("素材类型只支持 image / video")

        ext = LocalStorageService._ext(uploaded_file.name)
        if ext not in _TYPE_EXTS[material_type]:
            raise UploadTypeMismatch("文件类型与素材类型不一致")

        # 大小上限在调用处读模块常量（测试可 monkeypatch）
        max_size = MAX_IMAGE_SIZE if material_type == "image" else MAX_VIDEO_SIZE
        if uploaded_file.size > max_size:
            raise UploadParamError("文件过大（图片10M/视频200M）")

        sub_dir = _TYPE_DIR[material_type]
        target_dir = settings.MEDIA_ROOT / "creatives" / sub_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.{ext}"
        target = target_dir / filename

        # 分块写入，不用 request.body 全量吃内存
        with open(target, "wb") as out:
            for chunk in uploaded_file.chunks():
                out.write(chunk)

        meta = {
            "url": f"{settings.MEDIA_URL}creatives/{sub_dir}/{filename}",
            "filename": uploaded_file.name,
            "size": uploaded_file.size,
            "cover_url": "",
            "duration": 0.0,
        }
        if material_type == "video":
            duration, cover_path = LocalStorageService._probe_video(target)
            meta["duration"] = duration
            if cover_path is not None:
                meta["cover_url"] = f"{settings.MEDIA_URL}creatives/covers/{cover_path.name}"
        return meta

    @staticmethod
    def abs_path(relative_url: str) -> Path:
        """素材相对路径 → 本地绝对路径（P3 检测任务读取用）。

        换 OSS 时此处改为：从 STS 临时 URL 下载到本地临时目录后返回该路径。
        """
        if not relative_url:
            return Path()
        relative = relative_url
        if relative.startswith(settings.MEDIA_URL):
            relative = relative[len(settings.MEDIA_URL) :]
        return settings.MEDIA_ROOT / relative.lstrip("/")

    @staticmethod
    def _ext(filename: str) -> str:
        """取小写扩展名，无扩展名返回空串。"""
        return Path(filename).suffix.lstrip(".").lower()

    @staticmethod
    def _probe_video(video_path: Path) -> tuple[float, Path | None]:
        """尝试探测视频时长与首帧封面。

        无 moviepy / ffmpeg 环境时返回 ``(0.0, None)``，
        绝不抛异常影响上传主流程（前端 hotImgUrl 留空即可）。
        """
        try:
            from moviepy.editor import VideoFileClip  # type: ignore[import-not-found]
        except Exception:
            return 0.0, None

        try:
            clip = VideoFileClip(str(video_path))
            duration = float(clip.duration or 0.0)
            covers_dir = settings.MEDIA_ROOT / "creatives" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            cover_path = covers_dir / f"{video_path.stem}.jpg"
            clip.save_frame(str(cover_path), t=min(1.0, max(duration - 0.01, 0.0)))
            clip.close()
            return duration, cover_path
        except Exception:
            return 0.0, None
