# Tino 캐릭터 조작

`arena.png` 위에서 Tino의 대기, 걷기, 달리기를 구현하는 Python/pico2d 프로젝트입니다.

## 실행 환경

- Windows 데스크톱 및 키보드
- 검증 환경: Python 3.13.15, pico2d 1.5.1
- 실행에 필요한 `arena.png`와 `tino_sprite_pico2d_final.png`를 프로젝트 루트에 유지합니다.
- 이전 `tino_sprite_pico2d.png`는 보존용이며 실행 시 사용하지 않습니다.

PowerShell에서 프로젝트 루트를 기준으로 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```powershell
.\.venv\Scripts\python.exe main.py
```

Esc 또는 창 닫기로 종료합니다. 상세 요구 사항은 `PRD.md`에 있습니다.

## 조작

| 입력 | 동작 |
| --- | --- |
| 입력 없음 또는 R 키만 누름 | IDLE 대기 |
| 방향키 | WALK, 초당 160픽셀 |
| R 키를 누른 채 방향키 | RUN, 초당 320픽셀 |
| 반대 방향키 동시 입력 | 해당 축 상쇄 |

대각선 속도는 직선과 같고, 캐릭터 전체가 화면 안에 머뭅니다. 상하 이동과 정지 시 마지막 수평 방향을 유지합니다. 창이 키보드 포커스를 잃으면 입력을 초기화합니다.

새 시트는 768 × 384픽셀, 128 × 128픽셀 프레임의 6열 × 3행입니다. 이미지의 위에서부터 RUN/WALK/IDLE이며 각각 14/10/6 FPS로 반복 재생합니다. 파일 누락·손상 또는 규격 불일치 시 오류를 표시하고 종료하며 이전 시트로 대체하지 않습니다.

## 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe verify_runtime.py --seconds 5 --fps 30 --assume-focus
.\.venv\Scripts\python.exe verify_runtime.py --seconds 5 --fps 60 --assume-focus
.\.venv\Scripts\python.exe verify_runtime.py --seconds 300 --fps 60 --assume-focus
```

`verify_runtime.py`는 실제 SDL 창과 이벤트 큐로 조작을 자동 재생하고 종료합니다. `--assume-focus`는 비대화형 검증 환경에서만 포커스 조회를 대체합니다. 게임의 포커스 처리를 변경하지 않으며, 실제 키보드·Alt+Tab 검증을 대신하지 않습니다. 일반 데스크톱에서 포커스를 확보할 수 있으면 이 옵션 없이 실행할 수 있습니다.

검증 결과 및 미확인 항목은 `VALIDATION.md`, 단계별 커밋 기록은 `DEVELOPMENT.md`에 있습니다.
