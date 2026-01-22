"""
Wiki Monitor Launcher
이 파일만 exe로 컴파일되며, monitor_tray.py를 실행합니다.
"""

import os
import sys
import subprocess

def main():
    # 실행 파일의 디렉토리 찾기
    if getattr(sys, 'frozen', False):
        # exe로 실행된 경우
        current_dir = os.path.dirname(sys.executable)
    else:
        # py로 실행된 경우
        current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # monitor_tray.py 경로
    monitor_script = os.path.join(current_dir, "monitor_tray.py")
    
    # monitor_tray.py가 없으면 에러
    if not os.path.exists(monitor_script):
        print(f"오류: {monitor_script} 파일을 찾을 수 없습니다.")
        print("monitor_tray.py 파일이 실행 파일과 같은 폴더에 있어야 합니다.")
        input("아무 키나 눌러 종료...")
        sys.exit(1)
    
    # Python 인터프리터 찾기
    python_exe = sys.executable
    if getattr(sys, 'frozen', False):
        # exe인 경우 pythonw.exe 경로 찾기
        python_exe = "pythonw.exe"  # PATH에서 찾음
    
    # monitor_tray.py 실행
    try:
        # 창 없이 실행
        if sys.platform == "win32":
            subprocess.Popen(
                [python_exe, monitor_script],
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=current_dir
            )
        else:
            subprocess.Popen([python_exe, monitor_script], cwd=current_dir)
    except Exception as e:
        print(f"실행 오류: {e}")
        input("아무 키나 눌러 종료...")
        sys.exit(1)

if __name__ == "__main__":
    main()
