"""FastAPI entry point for RPPG Analyzer."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from . import analyzer

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent            # .../rppg_project/server
UPLOAD_DIR = BASE_DIR / "uploads"
CSV_DIR = BASE_DIR / "csvs"
STATIC_DIR = BASE_DIR / "static"

for d in (UPLOAD_DIR, CSV_DIR, STATIC_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# FastAPI 앱 초기화
# ---------------------------------------------------------------------------
app = FastAPI(title="RPPG Analyzer API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# png 파일 서빙 (/static)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# 라우터: / (메인 페이지 - 테스트용 업로드 폼)
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>RPPG Analyzer</title>
            <style>
                body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                .container { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
                .result { margin-top: 20px; }
                img { max-width: 100%; border: 1px solid #eee; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>RPPG Video Analyzer</h1>
                <p>Upload a face video to analyze BPM, Blink, and Motion.</p>
                
                <form id="uploadForm">
                    <input type="file" id="videoFile" accept="video/*" required>
                    <button type="submit">Analyze</button>
                </form>
                <div id="loading" style="display:none; margin-top:10px; color:blue;">Analyzing... Please wait...</div>
                
                <div id="result" class="result" style="display:none;">
                    <h3>Analysis Result</h3>
                    <p>Video ID: <span id="videoId"></span></p>
                    
                    <h4>Combined Analysis</h4>
                    <img id="combinedPlot" src="" alt="Combined Plot">
                    
                    <h4>Heart Rate (BPM)</h4>
                    <img id="bpmPlot" src="" alt="BPM Plot">
                    
                    <h4>Blink Rate</h4>
                    <img id="blinkPlot" src="" alt="Blink Plot">
                    
                    <h4>Motion Intensity</h4>
                    <img id="motionPlot" src="" alt="Motion Plot">
                </div>
            </div>

            <script>
                document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const fileInput = document.getElementById('videoFile');
                    const file = fileInput.files[0];
                    if (!file) return;

                    const formData = new FormData();
                    formData.append('file', file);

                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('result').style.display = 'none';

                    try {
                        const response = await fetch('/upload_video', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!response.ok) {
                            throw new Error(`Server error: ${response.status}`);
                        }

                        const data = await response.json();
                        
                        document.getElementById('videoId').textContent = data.video_id;
                        document.getElementById('bpmPlot').src = data.bpm_plot_url;
                        document.getElementById('blinkPlot').src = data.blink_plot_url;
                        document.getElementById('motionPlot').src = data.motion_plot_url;
                        document.getElementById('combinedPlot').src = data.combined_plot_url;
                        
                        document.getElementById('result').style.display = 'block';
                    } catch (err) {
                        alert('Analysis failed: ' + err.message);
                    } finally {
                        document.getElementById('loading').style.display = 'none';
                    }
                });
            </script>
        </body>
    </html>
    """


# ---------------------------------------------------------------------------
# 라우터: /upload_video
# ---------------------------------------------------------------------------
@app.post("/upload_video")
def upload_video(file: UploadFile = File(...)):
    """사용자가 업로드한 영상을 분석하고 결과 이미지를 반환한다."""
    # 파일명 검증
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # 허용되는 확장자
    allowed_ext = {".mp4", ".avi", ".mov", ".mkv"}
    file_suffix = Path(file.filename).suffix.lower()
    if file_suffix not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # UUID 기반 파일명 생성
    video_id = uuid.uuid4().hex
    video_filename = f"{video_id}{file_suffix}"
    video_path = UPLOAD_DIR / video_filename

    # 파일 저장
    try:
        with video_path.open("wb") as buffer:
            # file.file은 스풀링된 파일 객체이므로 동기적으로 읽을 수 있음
            # 혹은 shutil.copyfileobj 등을 사용할 수도 있지만,
            # UploadFile.read()는 async 함수이므로 여기서는 동기 처리를 위해
            # file.file.read()를 사용하거나 비동기 코드를 제거
            buffer.write(file.file.read())
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

    # CSV 및 이미지 경로 설정
    rgb_csv_path = CSV_DIR / f"{video_id}_rgb.csv"
    blink_csv_path = CSV_DIR / f"{video_id}_blink.csv"
    bpm_img_path = STATIC_DIR / f"{video_id}_bpm.png"
    blink_img_path = STATIC_DIR / f"{video_id}_blink.png"
    motion_img_path = STATIC_DIR / f"{video_id}_motion.png"
    combined_img_path = STATIC_DIR / f"{video_id}_combined.png"

    # 분석
    try:
        # 1. 영상에서 RGB/Blink 특징 추출 (FPS 반환 받음)
        # Returns: (rgb_csv_path, blink_csv_path, real_fps)
        _, _, real_fps = analyzer.extract_features_from_video(
            video_path=str(video_path),
            rgb_csv_path=str(rgb_csv_path),
            blink_csv_path=str(blink_csv_path),
        )

        # 2. BPM 및 Blink 시각화 (데이터 반환 받음)
        # Returns: (bpm_img_path, blink_img_path, bpm_data, blink_data)
        _, _, bpm_data, blink_data = analyzer.analyze_and_plot(
            rgb_csv_path=str(rgb_csv_path),
            blink_csv_path=str(blink_csv_path),
            bpm_img_path=str(bpm_img_path),
            blink_img_path=str(blink_img_path),
            fps=real_fps  # 실제 FPS 전달
        )

        # 3. Motion 분석 및 시각화 (데이터 반환 받음)
        # Returns: (motion_img_path, time_axis, motion_values)
        _, motion_time, motion_values = analyzer.analyze_motion(
            video_path=str(video_path),
            motion_img_path=str(motion_img_path),
        )
        motion_data = (motion_time, motion_values)

        # 4. 통합 그래프 생성
        analyzer.create_combined_plot(
            bpm_data,
            blink_data,
            motion_data,
            str(combined_img_path)
        )

    except Exception as e:  # pragma: no cover
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # 응답 데이터 구성
    return {
        "video_id": video_id,
        "bpm_plot_url": f"/static/{bpm_img_path.name}",
        "blink_plot_url": f"/static/{blink_img_path.name}",
        "motion_plot_url": f"/static/{motion_img_path.name}",
        "combined_plot_url": f"/static/{combined_img_path.name}",
    }


# ---------------------------------------------------------------------------
# 라우터: 이미지 다운로드
# ---------------------------------------------------------------------------
@app.get("/download/{image_type}/{video_id}")
async def download_image(image_type: str, video_id: str):
    """특정 비디오 ID의 분석 결과 이미지를 다운로드한다."""
    # 이미지 타입 검증
    allowed_types = {"bpm", "blink", "motion", "combined"}
    if image_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid image type")
    
    # 이미지 파일 경로 생성
    img_filename = f"{video_id}_{image_type}.png"
    img_path = STATIC_DIR / img_filename
    
    # 파일 존재 여부 확인
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        path=str(img_path),
        media_type="image/png",
        filename=img_filename
    ) 