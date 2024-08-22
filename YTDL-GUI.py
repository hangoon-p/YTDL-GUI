import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import subprocess
import json
import os
import requests
import threading
import sys
import re
import unicodedata

from pydub import AudioSegment
from datetime import datetime

from urllib.request import urlopen
from io import BytesIO
from PIL import Image, ImageTk


class YoutubeDownloader(tk.Tk):
    build_number = "2024082101"

    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.title("YouTube Downloader_Hangoon")
        self.geometry("500x295")
        ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        self.iconbitmap(ico_path)
        self.resizable(False, False)        
        
        frame_top = tk.Frame(self, borderwidth=0, relief="solid")
        frame_top.pack(side="top")
        
        frame_mid = tk.Frame(self, borderwidth=0, relief="solid")
        frame_mid.pack(fill="x", expand=True)  

        frame_mleft = tk.Frame(frame_mid, borderwidth=0, relief="solid")
        frame_mleft.pack(side="left")
        frame_mcenter = tk.Frame(frame_mid, borderwidth=0, relief="solid")
        frame_mcenter.pack(side="left")
        frame_mright = tk.Frame(frame_mid, borderwidth=0, relief="solid", width=250, height=160)
        frame_mright.pack(side="right", fill="both")
        
        frame_third = tk.Frame(self, borderwidth=0, relief="solid")
        frame_third.pack(fill="x", expand=True) 
        
        frame_bot = tk.Frame(self, borderwidth=0, relief="solid")
        frame_bot.pack(side="bottom", fill="x")

        # URL Entry
        self.url_label = ttk.Label(frame_top, text="YouTube URL:", width=11)
        self.url_label.grid(row=1, column=1, pady=10, sticky=tk.SW)
        
        self.url_entry = ttk.Entry(frame_top, width=45)
        self.url_entry.grid(row=1, column=2, pady=10, sticky=tk.SW)
        
        # Search Button
        self.search_button = ttk.Button(frame_top, text="Search", command=self.search_for_formats, width=10)
        self.search_button.grid(row=1, column=3, pady=10, sticky=tk.SW)
        
        # Cookie dropdown menu
        self.cookies_label = ttk.Label(frame_top, text="Cookie 사용 :", width=9)
        self.cookies_label.grid(row=2, column=1, sticky=tk.NW)
        self.cookie_options = [
            "No Cookies",
            #"cookies.txt",
            "Browser: Chrome",
            "Browser: Edge",
            "Browser: Whale",
            "Browser: Firefox",
            #"Browser: Safari"
        ]
        self.cookie_dropdown = ttk.Combobox(frame_top, values=self.cookie_options, width=41)
        self.cookie_dropdown.grid(row=2, column=2, sticky=tk.NW, padx=5)
        self.cookie_dropdown.set("No Cookies")
        self.cookie_dropdown.bind("<<ComboboxSelected>>", self.on_combobox_selected)

        # Progress Bar
        self.progress = ttk.Progressbar(frame_top, orient="horizontal", length=80, mode="determinate")
        self.progress.grid(row=2, column=3, pady=0, ipady=0, sticky=tk.NW)
        #self.progress.grid_remove()      

        # Format Listbox
        self.empty_label = ttk.Label(frame_mleft)
        self.empty_label.pack(padx=1)
        
        self.scrollbar = tk.Scrollbar(frame_mcenter)
        self.scrollbar.pack(side="right", fill="y")
        
        self.format_listbox = tk.Listbox(frame_mcenter, yscrollcommand=self.scrollbar.set, selectmode=tk.MULTIPLE, width=30, height=10)
        self.format_listbox.pack(expand=True)
        
        self.scrollbar.config(command=self.format_listbox.yview)
        
        self.format_listbox.bind("<<ListboxSelect>>", self.on_listbox_selected)
        self.selected_format_indices = None
        
        # Create a Canvas and draw a rentangle 
        self.canvas = tk.Canvas(frame_mright, width=260, height=180)
        self.canvas.pack()

        # Draw a rectangle (250x160)
        self.canvas.create_rectangle(5, 5, 255, 175, outline="black")

        # Create a label to display the video thumbnail inside the canvas
        self.thumbnail_label = tk.Label(self.canvas)
        self.thumbnail_label.place(x=10, y=10)

        # Create a label to display the video title inside the canvas
        bold_font = font.Font(weight='bold')
        self.video_title_label = tk.Label(self.canvas, font=bold_font)
        self.video_title_label.place(x=10, y=150)
        
        # Download Button
        self.download_button = ttk.Button(frame_third, text="Download", command=self.download_video, width=40)
        self.download_button.grid(row=0, column=0, sticky=tk.NW, padx=5)
        
        # Convert to MP3, WAV option
        self.convert_options = [
            "No converting",
            "Convert to MP3 (320kbps)",
            "Convert to WAV (24bit/48khz)",
            "Combine Audio and Video"
        ]
        self.convert_dropdown = ttk.Combobox(frame_third, values=self.convert_options, width=23)
        self.convert_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.convert_dropdown.set("No converting")
        self.convert_dropdown.bind("<<ComboboxSelected>>", self.on_combobox_selected)
        
        italic_font = font.Font(slant='italic', size=8)
        self.buildtxt = ttk.Label(frame_bot, text="build : ", font=italic_font)
        self.buildtxt.grid(row=0, column=0, sticky=tk.NW, padx=10)
        self.buildnum = ttk.Label(frame_bot, text=YoutubeDownloader.build_number, font=italic_font, width=38)
        self.buildnum.grid(row=0, column=1, sticky=tk.NW)
        self.copyright = ttk.Label(frame_bot, text="© 2023 Hangoon <elegize@naver.com>", font=italic_font)
        self.copyright.grid(row=0, column=2, sticky=tk.NE)
        
        self.download_thread = None
        self.search_thread = None        
        self.after(100, self.check_threads)  # 100ms마다 check_threads 함수 호출

    def on_combobox_selected(self, event):
        # Restore the listbox selection when dropdown menu is selected
        if self.selected_format_indices is not None:
            for index in self.selected_format_indices:
                if index is not None:
                    self.format_listbox.select_set(index)
        
    def on_listbox_selected(self, event):
        # Save the listbox selection state
        self.get_selected_items()
        # You might have additional logic here for listbox selection event

    def get_selected_items(self):
        self.selected_format_indices = self.format_listbox.curselection()
        if len(self.selected_format_indices) > 2:
            self.format_listbox.selection_clear(0, self.format_listbox.size()-1)
            for index in self.full_selected_format_indices:
                self.format_listbox.select_set(index)
        elif len(self.selected_format_indices) == 1:
            self.first_selected = self.format_listbox.get(self.format_listbox.curselection()).split()[0]
        elif len(self.selected_format_indices) == 2:
            selected_type1 = ""
            selected_type2 = ""
            match = re.search(r"\[(.*?)\]", self.format_listbox.get(self.selected_format_indices[0]))
            if match:
                selected_type1 = match.group(1)
            match = re.search(r"\[(.*?)\]", self.format_listbox.get(self.selected_format_indices[1]))
            if match:
                selected_type2 = match.group(1)

            if (
                (selected_type1 == "Audio" and selected_type2 != "Video") or 
                (selected_type1 == "Video" and selected_type2 != "Audio") or 
                selected_type1 == "Video+Audio" or 
                selected_type2 == "Video+Audio"
            ):
                for index in self.selected_format_indices:
                    if self.first_selected == self.format_listbox.get(index).split()[0]:
                        self.format_listbox.selection_clear(index)
                        self.first_selected = self.format_listbox.get(self.format_listbox.curselection()).split()[0]
                        break
            else:
                self.full_selected_format_indices = self.format_listbox.curselection()

    def check_threads(self):
        if self.download_thread and not self.download_thread.is_alive():
            self.download_button.config(text="Download")
            self.download_button['state'] = 'normal'  # Download 버튼 활성화
            self.search_button['state'] = 'normal'  # Search 버튼 활성화
            self.progress['value'] = 0  # 프로그레스 바 완료
            #self.progress.grid_remove()  # 프로그레스 바 숨기기
            self.download_thread = None  # 스레드 참조 제거
    
        if self.search_thread and not self.search_thread.is_alive():            
            self.download_button['state'] = 'normal'  # Download 버튼 활성화
            self.search_button['state'] = 'normal'  # Search 버튼 활성화
            self.search_thread = None  # 스레드 참조 제거

        self.after(100, self.check_threads)

    def update_progress_bar(self, output, task=""):
        match = re.search(r'\[download\]\s+(\d+.\d+)%', output)
        if match:
            progress = float(match.group(1))
            self.progress['value'] = progress
            self.download_button.config(text=f"{task}... {progress:.2f}%")
            self.update_idletasks()

    def search_for_formats(self):
        self.download_button['state'] = 'disabled'  # 버튼 비활성화
        self.search_button['state'] = 'disabled'  # 버튼 비활성화
        self.search_thread = threading.Thread(target=self.search_for_formats_threaded)
        self.search_thread.start()
    
    def search_for_formats_threaded(self):
        # Clear the listbox
        self.format_listbox.delete(0, tk.END)

        url = self.url_entry.get().strip()
        
        # Use yt-dlp to fetch available formats
        command = [
            'yt-dlp.exe', 
            '--skip-download',
            '--print-json',
            url
        ]
        
        # Adjust command for cookies
        cookie_selection = self.cookie_dropdown.get()
        if cookie_selection == "cookies.txt" and os.path.exists("cookies.txt"):
            command.extend(['--cookies', 'cookies.txt'])
        elif "Browser:" in cookie_selection:
            browser = cookie_selection.split(":")[1].strip().upper()
            command.extend(['--cookies-from-browser', browser])
        
        startupinfo = None
        if sys.platform == "win32":
            # Windows에서 콘솔 창 숨기기
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            yt_dlp_output = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT, startupinfo=startupinfo)
            #f = open("yt-dlp-response.txt",'w')
            #f.write(yt_dlp_output)
            #f.close()
            
            # JSON 시작 위치 찾기
            start_index = yt_dlp_output.find('{"id":')

            # JSON 문자열 추출
            json_str = yt_dlp_output[start_index:]
            
            # 마지막 중괄호의 위치 찾기
            end_index = json_str.rfind('}')

            # JSON 문자열 추출
            json_str = json_str[:end_index + 1]           
            
            #f = open("yt-dlp-response1.txt",'w')
            #f.write(json_str)
            #f.close()
            
            # JSON 형식 객체로 decode
            self.video_info = json.loads(json_str)           

            # Update video title
            title = self.video_info['title']
            normalized_title = unicodedata.normalize('NFC', title)  # 정규화
            self.video_title_label.config(text=normalized_title)                        

            # Update thumbnail
            thumbnail_url = self.video_info['thumbnail']
            response = requests.get(thumbnail_url, stream=True)
            response.raw.decode_content = True  # Ensure that the raw response content is decoded
            thumbnail_image = Image.open(response.raw)
            thumbnail_image = thumbnail_image.resize((240, 135), Image.LANCZOS)  # Resize the image
            thumbnail_photo = ImageTk.PhotoImage(thumbnail_image)
            self.thumbnail_label.config(image=thumbnail_photo)
            self.thumbnail_label.image = thumbnail_photo  # Keep a reference to avoid garbage collection

            # Populate the listbox with available formats
            self.format_listbox.delete(0, tk.END)  # Clear the listbox
            for format_entry in self.video_info['formats']:
                is_good_format = False
                format_vcodec = format_entry.get('vcodec', 'N/A')
                format_acodec = format_entry.get('acodec', 'N/A')
                format_note = format_entry.get('format_note', 'N/A')
                resolution = format_entry.get('resolution', 'N/A')
                tbr = format_entry.get('tbr', 'N/A')
                if tbr is not None and tbr != 'null' and tbr != 'N/A':
                    tbr = str(int(round(float(tbr)))) + 'k'
                
                if (
                    format_vcodec == 'none' 
                    and format_acodec != 'none'
                    and resolution == 'audio only'
                    and any(quality in format_note for quality in ['medium','high'])
                ):
                    format_type = "Audio"
                    is_good_format = True
                elif (
                    format_vcodec != 'none'
                    and format_acodec != 'none'
                    and (
                        any(format_res in format_note for format_res in ['720p', '1080p', '1440p', '2160p'])
                        or any(res in resolution for res in ['x720', 'x1080', 'x1440', 'x2160'])
                    )
                ):
                    format_type = "Video+Audio"
                    is_good_format = True
                elif (
                    format_vcodec != 'none'
                    and format_acodec == 'none'
                    and (
                        any(format_res in format_note for format_res in ['720p', '1080p', '1440p', '2160p'])
                        or any(res in resolution for res in ['x720', 'x1080', 'x1440', 'x2160'])
                    )                    
                ):
                    format_type = "Video"
                    is_good_format = True
                    
                if is_good_format == True:
                    if format_note == 'N/A':
                        resolution_index = resolution.find('x')
                        format_note = resolution[resolution_index + 1:] + 'p'
                    format_description = f"[{format_type}] {format_entry['format_id']} - {format_note} | {tbr} ({format_entry['ext']})"
                    self.format_listbox.insert(tk.END, format_description)

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"An error occurred while fetching formats: {e.output}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to decode the output from yt-dlp.")
 
    def download_video(self):
        self.download_button['state'] = 'disabled'  # 버튼 비활성화
        self.search_button['state'] = 'disabled'  # 버튼 비활성화
        #self.progress.grid()  # 프로그레스 바 표시        
        self.progress['value'] = 0  # 프로그레스 바 초기화
        self.download_button.config(text="Downloading... 0%")
        self.update_idletasks()  # 업데이트 적용
        self.download_thread = threading.Thread(target=self.download_video_threaded)
        self.download_thread.start()
 
    def download_video_threaded(self):
        url = self.url_entry.get()
        convert_selection = self.convert_dropdown.get()
        self.get_selected_items()
        # selected_format = self.format_listbox.get(tk.ACTIVE).split(' ')[0]  
        selected_formats_list = [self.format_listbox.get(index).split(' ')[1] for index in self.selected_format_indices]   # Extract the format_id from the selected item     

        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        filename_raw = self.video_info['title']        
        for char in invalid_chars:
            filename_raw = filename_raw.replace(char, '_')        
        filename = unicodedata.normalize('NFC', filename_raw)  # 정규화            

        output_path = os.path.join(os.getcwd(), filename + '.%(ext)s')
                    
        audio_filename = ""
        video_filename = ""
                        
        Index = 0        
        for selected_format in selected_formats_list:
            Index += 1
    
            is_audio_only = False
            for format_entry in self.video_info['formats']:
                if format_entry['format_id'] == selected_format:
                    if format_entry.get('vcodec') in ['audio_only', 'none']:
                        is_audio_only = True
                    break
    
            if len(selected_formats_list) == 2 and "Combine" in convert_selection:
                if is_audio_only:
                    output_path = os.path.join(os.getcwd(), filename + '_audio' + '.%(ext)s')
                    audio_filename = os.path.join(os.getcwd(), filename + '_audio' + '.' + format_entry['ext'])
                else:
                    output_path = os.path.join(os.getcwd(), filename + '_video' + '.%(ext)s')
                    video_filename = os.path.join(os.getcwd(), filename + '_video' + '.' + format_entry['ext'])
                    video_ext = format_entry['ext']
    
            # Use yt-dlp to download the video
            command = [
                'yt-dlp.exe', 
                '-f', selected_format,
                '-o', output_path,
                '--progress',  # 다운로드 진행률을 출력
                url
            ]
            cookie_selection = self.cookie_dropdown.get()
            if cookie_selection == "cookies.txt" and os.path.exists("cookies.txt"):
                command.extend(['--cookies', 'cookies.txt'])
            elif "Browser:" in cookie_selection:
                browser = cookie_selection.split(":")[1].strip().upper()
                command.extend(['--cookies-from-browser', browser])
    
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, text=True)
    
            while True:
                output = process.stdout.readline()
                if process.poll() is not None and output == '':
                    break
                if output:
                    self.update_progress_bar(output.strip(), task="Downloading")
            
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                messagebox.showerror("Error", stderr_output)
                return
                
            for format_entry in self.video_info['formats']:
                if format_entry['format_id'] == selected_format:
                    audio_file_path = os.path.join(os.getcwd(), filename + '.' + format_entry['ext'])
                    break
    
            if "Convert to" in convert_selection and is_audio_only:
                self.progress['value'] = 0
                self.download_button.config(text="Converting...")
                ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')
                
                if "MP3" in convert_selection:
                    convert_file_path = os.path.splitext(audio_file_path)[0] + ".mp3"
                    ffmpeg_command = [
                        ffmpeg_path,
                        '-y', '-i', audio_file_path,
                        '-b:a', '320k',
                        convert_file_path
                    ]
                elif "WAV" in convert_selection:
                    convert_file_path = os.path.splitext(audio_file_path)[0] + ".wav"
                    ffmpeg_command = [
                        ffmpeg_path,                        
                        '-y', '-i', audio_file_path,
                        '-acodec', 'pcm_s24le','-ar','48000',  # Set audio format                    
                        convert_file_path
                    ]
    
                ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                stdout, stderr = ffmpeg_process.communicate()
                
                if ffmpeg_process.returncode != 0:
                    messagebox.showerror("Error", ffmpeg_process.stderr.read())
                    return
                    
                os.remove(audio_file_path)
                    
            if len(selected_formats_list) == 2 and "Combine" in convert_selection:
                if (Index == 2 and audio_filename and video_filename):
                    self.progress['value'] = 0
                    self.download_button.config(text="Combining...")
                    ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')
                    convert_file_path = os.path.splitext(audio_file_path)[0] + "." + video_ext
                    
                    ffmpeg_command = [
                        ffmpeg_path,
                        '-y',
                        '-i', audio_filename,
                        '-i', video_filename,
                        '-c:v', 'copy', '-c:a', 'libvorbis' if video_ext == 'webm' else 'aac', '-strict', 'experimental',
                        convert_file_path
                    ]
    
                    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                    stdout, stderr = ffmpeg_process.communicate()
                    
                    if ffmpeg_process.returncode != 0:
                        messagebox.showerror("Error", ffmpeg_process.stderr.read())
                        return
                        
                    os.remove(audio_filename)
                    os.remove(video_filename)
    
        self.progress['value'] = 100  # 프로그레스 바 완료
        self.download_button.config(text="Completed")
        self.update_idletasks()  # 업데이트 적용
        messagebox.showinfo("Download Complete", "Your video has been downloaded and converted (if applicable)!")
        #self.progress.grid_remove()  # 프로그레스 바 숨기기
        self.download_button.config(text="Download")


    def check_and_update_app(self, mode="yt-dlp"):
        if sys.platform == "win32":
            # Windows에서 콘솔 창 숨기기
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        try:        
            if mode == "yt-dlp":
                app_path = "yt-dlp.exe"
                app_url = 'https://api.github.com/repos/yt-dlp/yt-dlp/releases'
                # Check if yt-dlp.exe exists in the current directory            
                if not os.path.exists(app_path):
                    current_version_str = "Not Installed"
                    current_version = datetime.min
                else:
                    current_version_str = subprocess.check_output([app_path, '--version'], startupinfo=startupinfo).decode().strip()
                    current_version = datetime.strptime(current_version_str, "%Y.%m.%d")                
              
            elif mode == "YTDL-GUI":
                app_path = "update.tmp"
                app_url = 'https://api.github.com/repos/hangoon-p/YTDL-GUI/releases'                
                current_version_str = YoutubeDownloader.build_number[:8]
                current_version = datetime.strptime(current_version_str, "%Y%m%d")                
                
            response = requests.get(app_url)
            response.raise_for_status()
            latest_version_str = response.json()[0]['tag_name']            
            if mode == "yt-dlp":
                latest_version = datetime.strptime(latest_version_str, "%Y.%m.%d")
            else:
                latest_version = datetime.strptime(latest_version_str, "%Y%m%d")

            if latest_version > current_version:
                # Ask the user if they want to update                
                message = f"A new version of {mode} is available.\nCurrent version: {current_version_str}\nLatest version: {latest_version_str}\nWould you like to update?"
                update_choice = messagebox.askyesno("Update Available", message)                
                
                if update_choice:
                
                    # Update app
                    if mode == "yt-dlp":
                        url = f"https://github.com/yt-dlp/yt-dlp/releases/download/{latest_version_str}/yt-dlp.exe"
                    elif mode == "YTDL-GUI":
                        url = f"https://github.com/hangoon-p/YTDL-GUI/releases/download/{latest_version_str}/YTDL-GUI.exe"
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    with open(app_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            
                    if mode == "yt-dlp":
                        messagebox.showinfo("Update Complete", f"{mode} has been successfully updated!" + ("\nPlease restart the application to use latest version." if mode == "YTDL-GUI" else ""))
                    elif mode == "YTDL-GUI":
                        if not os.path.exists("updater.exe"):  
                            url = f"https://github.com/hangoon-p/YTDL-GUI/releases/download/{latest_version_str}/updater.exe"
                            response = requests.get(url, stream=True)
                            response.raise_for_status()
                            with open("updater.exe", "wb") as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)             
                        os.startfile("updater.exe")
                        os._exit(0)                       
                    
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to update {mode}: {e}")

    def on_closing(self):
        self.destroy()

# 앱 실행
app = YoutubeDownloader()

# check_and_update_ytdlp 함수를 별도의 스레드에서 실행
update_thread = threading.Thread(target=app.check_and_update_app, args=('yt-dlp',))
update_thread.start()
if getattr(sys, 'frozen', False):
    self_update_thread = threading.Thread(target=app.check_and_update_app, args=('YTDL-GUI',))
    self_update_thread.start()
    
app.mainloop()
update_thread.join()  # 앱이 종료되면 스레드가 완료될 때까지 기다림
if app.search_thread and app.search_thread.is_alive():  
    app.search_thread.join()    
if self_update_thread and self_update_thread.is_alive():  
    app.search_thread.join()
