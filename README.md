## SOGAETING : AI 기반 소의 승가 행위 탐지 서비스

### 📌 프로젝트 개요

- 소의 발정기(승가 행위) 미탐지로 인한 경제적 손실 감소를 위한 AI 솔루션  
- 야간에 주로(65%) 발생하는 승가 행위를 실시간 탐지하여 농가에 알림 제공
- **YOLOv10** 기반의 고정밀 객체 탐지 모델 개발

<br>

### 📌 주요 기능

- **실시간 승가 행위 탐지**  
  AI 모델을 활용한 자동 승가 탐지

- **데이터베이스 저장**  
  CCTV 데이터 및 승가 탐지 데이터 저장

<br>

### 📌 Target

- 소 번식 관리를 위한 축산 농가
- 대규모 목장 운영 기업

<br>

### 📌 데이터 셋

- **회사 제공 데이터**  
  : 승가 라벨링 데이터 & 실제 농가 CCTV 영상(주간/야간)

- **Roboflow**  
  : 소 객체 탐지용 라벨링 데이터

- **AIHub**  
  : 한우/젖소 발정행동 영상 데이터

<br>

### 📌 진행 과정
#### YOLOv10 파라미터튜닝
- epoch: 50
- batch: 32
- imgsz: 640
- mosaic=0.5
- mixup=0.1
- copy_paste=0.5
- hsv_h=0.05
- hsv_v=0.6
#### 추가 필터링 조건
- confidence >= 0.75
- bounding box의 높이 차 >= 10 heights
- 승가 탐지 frames > 5
- 탐지 간의 frames 수가 30개가 넘으면 서로 다른 탐지로 분류

<br>

### 📌 최종 결과
| Metric | 값   | 달성률 |
|--------|-----|-------|
| Recall(탐지율) | 93.7% | ✅ 90% 초과 |
| FPR(오탐율)    | 16.6% | ✅ 20% 미만 |

### 📌 기술 스택

#### AI Framework
<img src="https://img.shields.io/badge/YOLOv10-00FFFF?style=for-the-badge&logo=YOLO&logoColor=black"> <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=PyTorch&logoColor=white">

#### Backend
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"> <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=OpenCV&logoColor=white"> <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white">


