import os
import time
import shutil
import sys
import psutil
import tkinter as tk
from tkinter import messagebox

def kill_process(process_name):
    """Kill any running process that contains the given name."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                proc.kill()  # 강제 종료
                print(f"Killed {process_name} (PID: {proc.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def main():
    target_exe = "YTDL-GUI.exe"
    temp_file = "update.tmp"
    
    # 타겟 파일과 임시 파일의 존재 여부 확인
    if not os.path.exists(target_exe) or not os.path.exists(temp_file):
        print("Target file or temp file not found. Exiting updater.")
        sys.exit(1)  # 파일이 없을 경우 종료

    # 1. YTDL-GUI.exe가 실행 중인지 확인하고 강제 종료
    kill_process(target_exe)

    # 2. 기존 YTDL-GUI.exe 파일 삭제
    try:
        os.remove(target_exe)  # 기존 파일 삭제

        # 3. update.tmp 파일을 YTDL-GUI.exe로 이름 변경
        shutil.move(temp_file, target_exe)

        # 메시지 박스를 표시하려면 Tkinter를 초기화해야 함
        root = tk.Tk()
        root.withdraw()  # 루트 창 숨기기

        # 메시지 박스 표시
        messagebox.showinfo("Update Complete", "YTDL-GUI has been successfully updated!\nApplication will be restart automatically.")
        
        # 4. 업데이트 완료 후 프로그램 재시작
        os.startfile(target_exe)
        
    except Exception as e:
        print(f"Update failed: {e}")
        sys.exit(1)

    # 5. updater 프로그램 종료
    sys.exit(0)

if __name__ == "__main__":
    main()
