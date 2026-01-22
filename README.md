# Wiki Monitor

Confluence Wiki의 페이지 변경사항을 모니터링하여 Slack으로 알림을 보내주는 시스템 트레이 애플리케이션입니다.

## 주요 기능

- 📊 여러 Confluence Space 동시 모니터링
- 🔔 페이지 생성/수정/삭제 시 Slack 알림
- ⚙️ Space별 개별 설정 (체크 주기, 페이지 수, Slack 채널)
- 🎯 특정 부모 페이지 하위만 모니터링 가능
- 💻 시스템 트레이에서 조용히 실행

## 설치 방법

### 1. 필요한 프로그램 설치

```bash
pip install requests pillow pystray urllib3
```

### 2. 설정 파일 생성

```bash
copy config.example.py config.py
```

`config.py` 파일을 열어서 다음 정보를 입력하세요:
- `USERNAME`: Confluence 사용자 아이디
- `TOKEN`: Confluence API 토큰
- `DEFAULT_SLACK_WEBHOOK`: Slack Webhook URL
- `SPACES`: 모니터링할 Space 목록

### 3. 실행

**방법 1: 배치 파일로 실행 (권장)**
```bash
start_wiki_monitor.bat
```

**방법 2: Python으로 직접 실행**
```bash
pythonw monitor_tray.py
```

## 실행 파일 빌드

PyInstaller로 단일 실행 파일(.exe)로 만들 수 있습니다:

```bash
wiki_monitor_build.bat
```

빌드가 완료되면 `wiki_monitor.exe` 파일이 생성됩니다.

## Space 설정 예시

```python
SPACES = [
    {
        "key": "MYSPACE",              # Space Key (필수)
        "page_limit": 100,             # 조회할 페이지 수
        "check_interval": 30,          # 체크 주기 (초)
    },
    {
        "key": "OTHERSPACE",
        "parent_id": "123456",         # 특정 페이지 하위만 모니터링
        "slack_webhook": "https://...", # 다른 Slack 채널로 전송
        "page_limit": 50,
        "check_interval": 600,         # 10분마다 체크
    },
]
```

## 파일 구조

```
wiki-monitor/
├── monitor_tray.py           # 메인 프로그램
├── config.py                 # 설정 파일 (민감정보, Git 제외)
├── config.example.py         # 설정 파일 템플릿
├── openssl.cnf               # SSL 설정
├── start_wiki_monitor.bat    # 실행 스크립트
├── wiki_monitor_build.bat    # 빌드 스크립트
├── .gitignore                # Git 제외 파일 목록
└── README.md                 # 이 파일
```

## 주의사항

⚠️ **중요**: `config.py` 파일에는 민감한 정보(토큰, Webhook URL)가 포함되어 있으므로 GitHub에 올리지 마세요! 
`.gitignore` 파일이 이미 설정되어 있습니다.

## 문제 해결

### SSL 오류가 발생하는 경우
- `start_wiki_monitor.bat`을 사용해서 실행하세요
- OpenSSL 설정이 자동으로 적용됩니다

### 로그 확인
- `monitor_log.txt` 파일에서 실행 로그를 확인할 수 있습니다

## 라이선스

이 프로젝트는 내부 사용을 위해 개발되었습니다.
