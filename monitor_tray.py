"""
Confluence -> Slack 알림 프로그램 (트레이 아이콘 버전)
실행: pythonw monitor_tray.py (또는 start_tray.bat)
"""

# ============================================
# SSL 레거시 문제 해결 (맨 위에 있어야 함!)
# ============================================
import os
import sys
import ssl

os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

import requests
import urllib3

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

try:
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except:
    pass

try:
    requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += ':HIGH:!DH:!aNULL'
except:
    pass

# ============================================
# 나머지 import
# ============================================
import json
import time
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item

# 설정 불러오기
import config

# ============================================
# 로그 파일 설정
# ============================================
LOG_FILE = "monitor_log.txt"

def log(message):
    """로그 파일에 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    except:
        pass

# ============================================
# 전역 변수
# ============================================
is_running = True
last_status = "시작 중..."
change_count = {"new": 0, "updated": 0, "deleted": 0}

# ============================================
# SSL 세션 생성
# ============================================
def create_session():
    session = requests.Session()
    session.verify = False
    return session

SESSION = create_session()

# ============================================
# 트레이 아이콘 이미지 생성
# ============================================
def create_icon_image(color="green"):
    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    if color == "green":
        fill_color = (34, 197, 94)
    elif color == "yellow":
        fill_color = (234, 179, 8)
    elif color == "red":
        fill_color = (239, 68, 68)
    else:
        fill_color = (107, 114, 128)
    
    draw.ellipse([4, 4, size-4, size-4], fill=fill_color)
    draw.text((22, 16), "W", fill="white")
    
    return image

# ============================================
# 상태 파일 관리
# ============================================
STATE_FILE = "monitor_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"spaces": {}, "first_run": True}

def save_state(state):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"상태 저장 실패: {e}")

# ============================================
# Confluence API
# ============================================
def get_recent_pages(space_config):
    """Space 설정에 따라 페이지 목록 조회"""
    space_key = space_config["key"]
    parent_id = space_config.get("parent_id")
    page_limit = space_config.get("page_limit", config.DEFAULT_PAGE_LIMIT)
    
    url = f"{config.CONFLUENCE_URL}/rest/api/search"
    
    # CQL 쿼리 구성
    if parent_id:
        # 특정 페이지 하위만 조회
        cql = f"space = {space_key} AND type = page AND ancestor = {parent_id} ORDER BY lastmodified DESC"
    else:
        # Space 전체 조회
        cql = f"space = {space_key} AND type = page ORDER BY lastmodified DESC"
    
    params = {
        "cql": cql,
        "limit": page_limit,
        "expand": "content.version"
    }
    
    headers = {
        "Authorization": f"Bearer {config.TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = SESSION.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        log(f"[{space_key}] API 오류: {e}")
        return None

def get_page_detail(page_id):
    url = f"{config.CONFLUENCE_URL}/rest/api/content/{page_id}"
    params = {"expand": "version,history.lastUpdated"}
    headers = {
        "Authorization": f"Bearer {config.TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = SESSION.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except:
        return None

# ============================================
# Slack 알림
# ============================================
def send_slack(message, webhook_url=None, color="#0066cc"):
    """Slack으로 메시지 보내기 (파란색 세로줄 포함)"""
    if webhook_url is None:
        webhook_url = config.DEFAULT_SLACK_WEBHOOK
    
    try:
        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": message
                }
            ]
        }
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            log("Slack 전송 성공")
            return True
        else:
            log(f"Slack 전송 실패: {response.status_code}")
            return False
    except Exception as e:
        log(f"Slack 오류: {e}")
        return False

# ============================================
# 모니터링 로직
# ============================================
def check_changes_for_space(state, space_config):
    """특정 Space의 변경사항 확인"""
    global change_count
    
    space_key = space_config["key"]
    slack_webhook = space_config.get("slack_webhook", config.DEFAULT_SLACK_WEBHOOK)
    
    pages = get_recent_pages(space_config)
    
    if pages is None:
        return state
    
    log(f"[{space_key}] {len(pages)}개 페이지 조회")
    
    is_first_run = state.get("first_run", True)
    
    # Space별 상태 키 생성 (parent_id가 있으면 구분)
    parent_id = space_config.get("parent_id")
    state_key = f"{space_key}_{parent_id}" if parent_id else space_key
    
    if "spaces" not in state:
        state["spaces"] = {}
    if state_key not in state["spaces"]:
        state["spaces"][state_key] = {}
    
    saved_pages = state["spaces"][state_key]
    current_page_ids = set()
    
    for item_data in pages:
        content = item_data.get("content", {})
        page_id = content.get("id")
        title = item_data.get("title") or content.get("title", "제목없음")
        
        if not page_id:
            continue
        
        current_page_ids.add(page_id)
        
        detail = get_page_detail(page_id)
        if detail:
            version_info = detail.get("version", {})
            version = version_info.get("number", 1)
            modifier = version_info.get("by", {}).get("displayName", "알 수 없음")
            # 변경 시간 파싱
            modified_when = version_info.get("when", "")
            if modified_when:
                try:
                    # ISO 형식 파싱 후 포맷 변경
                    from datetime import datetime
                    dt = datetime.fromisoformat(modified_when.replace('Z', '+00:00'))
                    # 한국 시간으로 변환 (UTC+9)
                    from datetime import timedelta
                    dt_kst = dt #+ timedelta(hours=9)
                    modified_time = dt_kst.strftime("%Y-%m-%d %H:%M")
                except:
                    modified_time = "알 수 없음"
            else:
                modified_time = "알 수 없음"
        else:
            version = 1
            modifier = "알 수 없음"
            modified_time = "알 수 없음"
        
        link = f"{config.CONFLUENCE_URL}/pages/viewpage.action?pageId={page_id}"
        
        if page_id not in saved_pages:
            saved_pages[page_id] = {"version": version, "title": title}
            
            if not is_first_run:
                change_count["new"] += 1
                log(f"생성: {title}")
                send_slack(
                    f"{space_key} {modified_time} 생성\n"
                    f"제목: <{link}|*{title}*>\n"
                    f"작성: {modifier}",
                    slack_webhook
                )
        else:
            old_version = saved_pages[page_id].get("version", 0)
            
            if version > old_version:
                saved_pages[page_id] = {"version": version, "title": title}
                change_count["updated"] += 1
                log(f"수정: {title} (v{old_version} -> v{version})")
                send_slack(
                    f"{space_key} {modified_time} 수정\n"
                    f"제목: <{link}|*{title}*>\n"
                    f"작성: {modifier}\n"
                    f"버전: v{old_version} -> v{version}",
                    slack_webhook
                )
    
    if not is_first_run:
        deleted_ids = set(saved_pages.keys()) - current_page_ids
        for deleted_id in list(deleted_ids):
            deleted_title = saved_pages[deleted_id].get("title", "제목없음")
            change_count["deleted"] += 1
            log(f"삭제: {deleted_title}")
            send_slack(
                f"{space_key} 삭제\n"
                f"제목: *{deleted_title}*",
                slack_webhook
            )
            del saved_pages[deleted_id]
    
    state["spaces"][state_key] = saved_pages
    return state

# ============================================
# 트레이 메뉴 함수
# ============================================
def on_quit(icon, item):
    global is_running
    log("사용자 종료 요청")
    is_running = False
    icon.stop()

def get_status_text(item=None):
    spaces_str = ", ".join([s["key"] for s in config.SPACES])
    total = change_count["new"] + change_count["updated"] + change_count["deleted"]
    return f"Space: {spaces_str} | 알림: {total}건"

# ============================================
# 메인
# ============================================
def main():
    global is_running, last_status
    
    log("=" * 40)
    log("모니터링 시작")
    
    # 상태 로드
    state = load_state()
    spaces_str = ", ".join([s["key"] for s in config.SPACES])
    
    # 시작 알림 (기본 채널로)
    send_slack(f"모니터링 시작\nSpace: {spaces_str}\n확인 주기: {config.DEFAULT_CHECK_INTERVAL}초")
    
    # 트레이 아이콘 생성
    icon = pystray.Icon("wiki_monitor")
    icon.icon = create_icon_image("green")
    icon.title = "Wiki Monitor"
    icon.menu = pystray.Menu(
        item(get_status_text, lambda: None, enabled=False),
        item('종료', on_quit)
    )
    
    # 모니터링 함수 (트레이 실행 후 호출됨)
    def monitor_job():
        nonlocal state
        global is_running, last_status
        
        while is_running:
            try:
                icon.icon = create_icon_image("yellow")
                
                for space_config in config.SPACES:
                    if not is_running:
                        break
                    
                    space_key = space_config["key"]
                    check_interval = space_config.get("check_interval", config.DEFAULT_CHECK_INTERVAL)
                    
                    # Space별 마지막 체크 시간 확인
                    last_check_key = f"last_check_{space_key}"
                    last_check_time = state.get(last_check_key, 0)
                    current_time = time.time()
                    
                    # check_interval이 지났으면 확인
                    if current_time - last_check_time >= check_interval:
                        state = check_changes_for_space(state, space_config)
                        state[last_check_key] = current_time
                
                state["first_run"] = False
                state["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_state(state)
                
                icon.icon = create_icon_image("green")
                
                # 1초마다 체크 (각 Space의 interval은 개별 관리)
                for _ in range(10):
                    if not is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                log(f"모니터링 오류: {e}")
                icon.icon = create_icon_image("red")
                time.sleep(10)
        
        # 종료 처리
        save_state(state)
        send_slack(f"모니터링 종료\nSpace: {spaces_str}")
        log("모니터링 종료")
    
    # 백그라운드 스레드에서 모니터링 실행
    def setup(icon):
        icon.visible = True
        thread = threading.Thread(target=monitor_job, daemon=True)
        thread.start()
    
    # 트레이 실행
    icon.run(setup)

if __name__ == "__main__":
    main()
