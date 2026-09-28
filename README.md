# Samsung Electronics DART Financial Analysis Agent

삼성전자(005930)의 DART 정기보고서(사업보고서·반기보고서·분기보고서)를 OpenDART API로 수집하고, 핵심 재무수치·재무비율을 계산해 GitHub Pages 대시보드로 공개하는 자동화 프로젝트입니다.

> **중요:** OpenDART의 `fnlttSinglAcntAll`/`fnlttSinglAcnt` 재무정보 API는 공식 가이드상 **2015년 이후 데이터만 제공**합니다. 따라서 2010~2014년은 이 API만으로 자동 재무수치 수집이 불가능합니다. 프로젝트는 `START_YEAR=2010`으로 설정되어 있으며, 2010~2014는 `legacy_status.csv`에 제한사항을 기록하고, 필요하면 DART 원문 자료를 별도 보강할 수 있게 설계했습니다. citeturn1search1turn1search2

## 🔗 대시보드 바로가기

[![대시보드 바로가기](https://img.shields.io/badge/🔗%20대시보드%20바로가기-000000?style=for-the-badge&logo=github&logoColor=white)](https://hsc-class01.github.io/HSC_samsung/)

## Dashboard

https://hsc-class01.github.io/HSC_samsung/

## 구조

```text
HSC_samsung/
├─ src/
│  └─ opendart_agent.py       # OpenDART 수집/정규화/비율 계산
├─ docs/
│  └─ index.html               # GitHub Pages 대시보드
├─ data/
│  ├─ financials.csv           # 핵심 재무수치
│  ├─ ratios.csv               # 재무비율
│  ├─ filings.csv              # 정기보고서 메타데이터
│  ├─ legacy_status.csv        # 2010~2014 제한사항
│  └─ peers.csv                # 국내 peer firms
├─ raw/
│  └─ .gitkeep (zip에는 포함하지 않음)
├─ config/
│  └─ settings.json
├─ github_workflows/
│  ├─ monthly_update.yml       # .github/workflows/ 로 복사
│  └─ pages_deploy.yml         # .github/workflows/ 로 복사
├─ tests/
│  └─ test_agent.py
├─ requirements.txt
└─ README.md
```

## 1. OpenDART API 설정

OpenDART 개발가이드에서 API 인증키를 발급합니다.

- OpenDART: https://opendart.fss.or.kr/
- 기업개황 API: 삼성전자 고유번호는 공식 가이드 예시에 `00126380`으로 제시되어 있습니다. citeturn1search6
- 단일회사 전체 재무제표 API: `fnlttSinglAcntAll.json` citeturn1search1
- 공시서류 원본파일 API: `document.xml` citeturn1search0

### GitHub Secret

Repository → **Settings → Secrets and variables → Actions → New repository secret**

```text
Name: DART_API_KEY
Value: 발급받은 40자리 OpenDART API 인증키
```

API 키를 코드나 README에 직접 입력하지 마세요.

## 2. 첫 실행

로컬 테스트:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Windows PowerShell
$env:DART_API_KEY="YOUR_KEY"

# macOS/Linux
export DART_API_KEY="YOUR_KEY"

python src/opendart_agent.py
```

## 3. 매월 1일 자동 업데이트

GitHub Actions의 `schedule`은 POSIX cron을 사용하고 기본적으로 UTC 기준입니다. citeturn0search0turn0search1

기본 workflow는 한국시간 매월 1일 오전 6시(UTC 21:00 전날)에 실행하도록 `0 21 1 * *`을 사용합니다. 정각 부하를 피하기 위해 00분 대신 21시 UTC를 사용했습니다.

zip 파일에는 숨김 경로를 넣지 않기 위해 workflow를 `github_workflows/`에 넣었습니다. 압축을 푼 뒤 아래처럼 복사하세요.

```text
github_workflows/monthly_update.yml
→ .github/workflows/monthly_update.yml

github_workflows/pages_deploy.yml
→ .github/workflows/pages_deploy.yml
```

## 4. GitHub Pages 배포

Repository → **Settings → Pages → Source: GitHub Actions** 로 설정합니다.

`pages_deploy.yml`은 `docs/`를 Pages artifact로 배포합니다.

예상 대시보드 주소:

```text
https://hsc-class01.github.io/HSC_samsung/
```

Repository의 오른쪽 **About → Website**에는 위 주소를 넣어 주세요.

## 5. 수집 범위

- 사업보고서: `11011`
- 반기보고서: `11012`
- 1분기보고서: `11013`
- 3분기보고서: `11014`

OpenDART 공식 API가 위 보고서 코드를 사용합니다. citeturn1search1

### 주요 재무수치

실무 가이드에 따라 다음 범주를 저장합니다.

- 재무상태: 총자산, 현금및현금성자산, 매출채권, 재고자산, 유형자산, 총부채, 이자부차입금, 자본총계
- 손익: 매출액, 매출총이익, 판매비와관리비, 영업이익, 세전이익, 당기순이익, 지배주주순이익, EBITDA
- 현금흐름: 영업활동현금흐름(CFO), 투자활동현금흐름, 재무활동현금흐름, CAPEX, FCF, 순차입금
- 비율: 매출총이익률, 영업이익률, 순이익률, EBITDA 마진, ROA, ROE, ROIC, 유동비율, 당좌비율, 부채비율, 자기자본비율, 차입금의존도, 이자보상배율, 순차입금/EBITDA, 총자산회전율, DSO, DIO, DPO, CCC, 매출증가율, CFO/순이익

이 항목은 첨부된 `재무제표_재무비율_실무가이드.docx`의 핵심 수치와 비율을 기준으로 구성했습니다. fileciteturn3file0L53-L88 fileciteturn3file0L90-L151 fileciteturn3file0L153-L228

## 6. 연결재무제표 기준

기본값은 `CFS`(연결)입니다. OpenDART는 `fs_div`에 `OFS`(별도)와 `CFS`(연결)를 사용합니다. citeturn1search1

## 7. 2010~2014 데이터

OpenDART 재무정보 API의 공식 제공 범위가 2015년 이후이므로 2010~2014는 자동 재무수치 테이블에 임의의 값을 넣지 않습니다. 이 기간은 `legacy_status.csv`에 `API_UNAVAILABLE_PRE_2015`로 표시합니다. citeturn1search1turn1search2

원문 공시를 추가 확보한 경우에는 `raw/legacy/`에 저장하고 별도 parser를 연결할 수 있습니다. OpenDART의 원본파일 API는 접수번호(`rcept_no`)를 받아 ZIP 원문을 제공합니다. citeturn1search0

## 8. 국내 Peer Firms

대시보드와 README에는 국내 IT/전자·반도체 대형주 비교군으로 다음 기업을 기본 등록합니다.

- SK하이닉스
- LG전자
- 삼성SDI
- LG디스플레이
- 삼성전기
- LG이노텍

Peer는 업종·사업구조가 완전히 동일하다는 뜻이 아니라, 삼성전자와 국내 IT 대형주/반도체·전자 공급망의 실적 및 재무 비교에 활용할 수 있는 비교군이라는 의미입니다. 공개 리서치의 국내 IT 대형주 비교표에서도 삼성전자, LG전자, LG디스플레이, 삼성SDI, SK하이닉스, 삼성전기, LG이노텍 등이 함께 비교된 사례가 있습니다. citeturn5search24turn5search23

## 9. GitHub About 링크

GitHub repository 오른쪽 About → Website에 다음 주소를 입력합니다.

```text
https://hsc-class01.github.io/HSC_samsung/
```

## 10. 보안 주의

- `DART_API_KEY`는 GitHub Secret으로만 저장
- `.env`, API key가 들어간 파일, 개인 토큰을 commit하지 않음
- 원본 DART 파일은 필요 시 `raw/`에 저장하되 저장소 용량을 확인
- zip 패키지에는 `.git`, `.github`, `.env`, `__pycache__` 등 hidden/system files를 포함하지 않음
