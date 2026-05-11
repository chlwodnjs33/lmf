# 최종 제출 안내

## 1. 제출물 (GitHub repo)

repo 루트에 다음 파일을 둡니다. URL만 폼으로 제출합니다. **Public repo만 허용됩니다. Private repo는 금지입니다.**

| 파일 | 누가 |
|---|---|
| `main.py` | 모든 학생 |
| `train.py` | **모든 학생** |
| `report.md` | 모든 학생 |
| `requirements.txt` | **표준 환경 외 패키지 사용 시만** |
| `model.*` (`.pkl`, `.pt` 등) | ML 사용 학생만 |

> ⚠️ 참신성·일치성 채점은 **`report.md` + `train.py`** 를 기준으로 합니다. `main.py`가 아닙니다.  
> 비ML 학생도 `train.py`는 필수입니다. 비ML 학생은 `main.py`와 같은 내용을 그대로 복사해서 제출하면 됩니다.

---

## 2. 표준 실행 환경

채점기는 다음 버전으로 실행합니다. **이 외 패키지 사용 시 `requirements.txt`가 필수입니다.**

| 패키지 | 버전 |
|---|---|
| Python | 3.12.3 |
| numpy | 2.4.4 |
| scipy | 1.17.1 (`scipy.io`, `scipy.optimize` 포함) |
| pytorch | 2.8.0 |
| scikit-learn | 1.8.0 |
| matplotlib | 3.10.8 |
| pandas | 2.3.x |

위 패키지만 사용하면 `requirements.txt`는 불필요합니다.  
다른 패키지를 사용할 경우 `pip install -r requirements.txt`로 설치 가능하도록 `requirements.txt`를 작성해야 합니다.

---

## 3. 데이터

채점에 쓰이는 `.mat` 파일은 다음 3개 변수를 담고 있습니다.

| 변수 | 모양 | 의미 |
|---|---:|---|
| `p` | `(2, N)` | 정답 사용자 위치 `(x, y)` |
| `d_hat` | `(18, N)` | 18개 기지국이 측정한 RTT |
| `p_bs` | `(2, 18)` | 18개 기지국의 좌표 |

전체 사용자 UE는 **1000명**입니다.  
그중 **700명만 학생에게 제공**되고, 나머지 **300명은 조교가 hidden test set으로 보유**합니다.

채점 시 채점기는 hidden 데이터로 학생의 `main.py`를 실행합니다.  
따라서 학생이 받은 데이터에만 over-fitting한 코드는 성능에서 손해를 볼 수 있습니다.

---

## 4. `main.py` 작성 규격

아래 구조를 기준으로 작성합니다.

```python
import numpy as np
import scipy.io as sio

def your_algorithm(d_hat_u, p_bs):
    """
    본인 알고리즘 작성
    필요시 상단에 추가적인 함수 작성 가능
    """
    return 측위결과

def main():
    # 1) 입력 데이터 로드
    # 채점기가 같은 폴더에 .mat 파일 자동 배치
    data_path = 'DH_FR1.mat'

    data = sio.loadmat(data_path, squeeze_me=False)
    p_bs  = np.asarray(data['p_bs'], dtype=float)      # (2, 18)
    d_hat = np.asarray(data['d_hat'], dtype=float)     # (18, num_user)
    p     = np.asarray(data['p'], dtype=float)         # (2, num_user), GT 위치

    # 2) 본인 알고리즘
    # 사용자 수는 입력에서 동적으로 받기
    num_user = d_hat.shape[1]
    p_hat = np.zeros((2, num_user))

    for u in range(num_user):
        p_hat[:, u] = your_algorithm(d_hat[:, u], p_bs)

    # 3) 결과 반환
    # numpy 배열, 모양 (2, num_user)
    return p_hat

if __name__ == "__main__":
    main()
```

⭐ 터미널에서 다음 명령으로 실행 가능해야 합니다.

```bash
python main.py
```

### `main.py` 규칙

| 규칙 | 설명 |
|---|---|
| `main()` 함수 정의 | 채점기가 호출합니다. |
| 결과 반환 | `numpy` 배열, 모양 `(2, num_user)` |
| 좌표 형식 | 첫 행은 x 좌표, 둘째 행은 y 좌표 |
| 사용자 수 하드코딩 금지 | `num_user = d_hat.shape[1]`처럼 입력에서 받아야 합니다. |
| 실행 시간 제한 | 10분 안에 `main()`이 끝나야 합니다. |
| 데이터 파일명 | `DH_FR1.mat` |
| 시간 초과 시 | 강제 종료되며 성능 점수 최하점 처리 |

---

## 5. `report.md` 작성 규칙

### 5.1 필수 섹션

`report.md`에는 아래 **4개 섹션만** 포함해야 합니다.

## 1. 모티베이션 & 인트로

중간발표까지의 실험 결과와 고찰을 정리합니다.  
그 과정에서 본 알고리즘 아이디어가 어떻게 도출되었는지 설명합니다.  
알고리즘의 high-level 개요도 함께 소개합니다.

## 2. 알고리즘 설명

알고리즘이 어떻게 동작하는지 구체적으로 설명합니다.  
설명은 **말과 수식으로만** 작성합니다.  
이 설명만 듣고도 코드 구현이 가능할 정도로 자세해야 합니다.

## 3. Agent AI 활용 방안

ChatGPT, Claude Code, Gemini 등 Agent AI를 어떤 방식으로 활용했는지 구체적으로 작성합니다.  
AI가 한 역할과 본인이 직접 수행한 역할을 구분해서 설명해야 합니다.

## 4. 결과 도출 & 디스커션

수치의 단순 비교만 작성하면 안 됩니다.  
다음 내용을 포함해 본인의 사고 과정을 설명해야 합니다.

- 본인의 사고와 구현이 문제에 적합했는가
- baseline과의 비교가 fair한가
- 예: 딥러닝 모델과 단순 삼각측량을 직접 비교하는 것은 unfair할 수 있음
- 알고리즘의 장점과 단점
- future work
- 본인이 사용한 자체 평가 방식의 fairness

---

### 5.2 형식 제한

| 제한 | 이유 |
|---|---|
| ❌ 코드 블록 금지 | 코드는 `main.py`로 평가합니다. |
| ❌ 의사코드 금지 | 보고서는 자연어 설명을 평가합니다. |
| ❌ 이미지, 그림, 플롯, 스크린샷 첨부 금지 | 채점 LLM이 이미지를 참조하지 않습니다. |
| ✅ 모든 결과 수치는 markdown 표로 작성 | 자동 채점기가 정확히 파싱하기 위함입니다. |
| ⚠️ 파일 크기 100 KB 제한 | `report.md`가 100 KB를 넘으면 채점에서 잘릴 수 있습니다. |

---

## 6. 평가

채점은 다음 영역으로 나뉩니다.

| 영역 | 평가 내용 |
|---|---|
| 성능 | Hidden test set 300명으로 `main.py` 실행 결과 |
| 참신성 | 본인 알고리즘과 다른 학생들 알고리즘 간 similarity 비교 |
| 보고서 | `report.md`의 필수 4개 섹션 종합 평가 |

세부 가중치와 임계값은 비공개입니다.

---

## 7. 마감

| 구분 | 마감 |
|---|---|
| 1차 제출 마감 | **2026년 6월 4일 목요일 자정** |
| 2차 제출 마감 | **2026년 6월 7일 일요일 자정** |
