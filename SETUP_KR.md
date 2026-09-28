# 배포 체크리스트

## A. OpenDART
1. https://opendart.fss.or.kr/ 접속
2. OpenAPI 인증키 발급
3. GitHub Repository → Settings → Secrets and variables → Actions
4. `DART_API_KEY`라는 이름으로 40자리 키 저장

## B. Workflow 설치
zip 압축을 풀고:

- `github_workflows/monthly_update.yml` → `.github/workflows/monthly_update.yml`
- `github_workflows/pages_deploy.yml` → `.github/workflows/pages_deploy.yml`

`.github` 폴더는 GitHub Actions가 인식하는 표준 위치입니다.

## C. Pages
Repository → Settings → Pages → Source에서 `GitHub Actions`를 선택합니다.

배포 주소:
`https://hsc-class01.github.io/HSC_samsung/`

## D. About
Repository 오른쪽 About → Website에:
`https://hsc-class01.github.io/HSC_samsung/`

## E. README badge
README 최상단의 대시보드 배지를 그대로 사용합니다. 별도 이미지가 있으면 badge 이미지 URL만 교체하면 됩니다.

## F. 수동 테스트
Actions → Monthly DART update → Run workflow로 최초 수집을 먼저 실행합니다.

## G. 월간 자동화
한국시간 매월 1일 오전 6시 실행: `0 21 1 * *` (UTC). GitHub Actions 스케줄은 UTC를 기본으로 하며 POSIX cron을 사용합니다.
