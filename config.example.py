# ============================================
# Confluence -> Slack 알림 설정 (예시)
# ============================================
# 이 파일을 복사해서 config.py로 만들고 실제 값을 입력하세요!
# 명령어: copy config.example.py config.py

# Confluence 설정
CONFLUENCE_URL = "https://wiki.domain.net"

# 인증 정보 (아이디, 토큰)
USERNAME = "your_username"  # 여기에 실제 아이디 입력
TOKEN = "your_api_token"    # 여기에 실제 토큰 입력

# 기본 Slack Webhook URL
DEFAULT_SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# 기본 모니터링 설정
DEFAULT_CHECK_INTERVAL = 30   # 기본 확인 주기 (초)
DEFAULT_PAGE_LIMIT = 100      # 기본 페이지 조회 수

# ============================================
# Space별 설정
# ============================================
# 각 Space 설정:
#   - key: Space Key (필수)
#   - slack_webhook: (선택) 다른 Slack 채널로 보내고 싶을 때
#   - parent_id: (선택) 특정 페이지 하위만 모니터링할 때
#   - page_limit: (선택) 페이지 조회 수 (기본값: DEFAULT_PAGE_LIMIT)
#   - check_interval: (선택) 확인 주기 (기본값: DEFAULT_CHECK_INTERVAL)

SPACES = [
    {
        "key": "keyname1",
        "page_limit": 100,
        "check_interval": 30,
    },
    {
        "key": "keyname2",
        "page_limit": 100,
        "check_interval": 30,
    },
    {
        "key": "keyname3",
        "parent_id": "419980311",
        "slack_webhook": "https://hooks.slack.com/services/YOUR/SECOND/WEBHOOK",
        "page_limit": 50,
        "check_interval": 600,
    },
]
