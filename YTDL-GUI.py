import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import subprocess
import json
import os
import requests
import threading
import sys
import re
from pydub import AudioSegment
from datetime import datetime

from urllib.request import urlopen
from io import BytesIO
from PIL import Image, ImageTk


class YoutubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.title("YouTube Downloader_Hangoon")
        self.geometry("500x275")
        ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        self.iconbitmap(ico_path)
        self.resizable(False, False)        
        
        frame_top = tk.Frame(self,borderwidth=0,relief="solid")
        frame_top.pack(side="top")
        
        frame_mid = tk.Frame(self,borderwidth=0,relief="solid")
        frame_mid.pack(fill="x", expand=True)  

        frame_mleft = tk.Frame(frame_mid,borderwidth=0,relief="solid")
        frame_mleft.pack(side="left")
        frame_mcenter = tk.Frame(frame_mid,borderwidth=0,relief="solid")
        frame_mcenter.pack(side="left")
        frame_mright = tk.Frame(frame_mid,borderwidth=0,relief="solid", width=250, height=160)
        frame_mright.pack(side="right", fill="both")
        
        frame_bot = tk.Frame(self,borderwidth=0,relief="solid")
        frame_bot.pack(side="bottom",fill="x")

        # URL Entry
        self.url_label = ttk.Label(frame_top, text="YouTube URL:", width=11)
        self.url_label.grid(row=1,column=1,pady=10, sticky=tk.SW)
        
        self.url_entry = ttk.Entry(frame_top, width=45)
        self.url_entry.grid(row=1,column=2,pady=10, sticky=tk.SW)
        
        # Search Button
        self.search_button = ttk.Button(frame_top, text="Search", command=self.search_for_formats, width=10)
        self.search_button.grid(row=1,column=3,pady=10, sticky=tk.SW)
        
        # Cookie dropdown menu
        self.cookies_label = ttk.Label(frame_top, text="Cookie 사용 :", width=9)
        self.cookies_label.grid(row=2,column=1, sticky=tk.NW)
        self.cookie_options = [
            "No Cookies",
            #"cookies.txt",
            "Browser: Chrome",
            "Browser: Edge",            
            "Browser: Firefox",
            #"Browser: Safari"
        ]
        self.cookie_dropdown = ttk.Combobox(frame_top, values=self.cookie_options, width=41)
        self.cookie_dropdown.grid(row=2, column=2, sticky=tk.NW, padx=5)        
        self.cookie_dropdown.set("No Cookies")
        self.cookie_dropdown.bind("<<ComboboxSelected>>", self.on_combobox_selected)
        

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
        self.download_button = ttk.Button(frame_bot, text="Download", command=self.download_video, width=40)
        self.download_button.grid(row=0, column=0, sticky=tk.NW, padx=5)    
        
        # Convert to MP3,WAV option
        self.convert_options = [
            "No converting",
            "Convert to MP3 (320kbps)",
            "Convert to WAV (24bit/48khz)",
            "Combine Audio and Video"
        ]
        self.convert_dropdown = ttk.Combobox(frame_bot, values=self.convert_options, width=23)
        self.convert_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5)        
        self.convert_dropdown.set("No converting")        
        self.convert_dropdown.bind("<<ComboboxSelected>>", self.on_combobox_selected)
        
        # self.convert_var = tk.IntVar()
        # self.convert_checkbox = ttk.Checkbutton(frame_bot, text="Convert to MP3 (320kbps)", variable=self.convert_var)
        # self.convert_checkbox.grid(row=0,column=1)
        
        frame_bot = tk.Frame(self,borderwidth=0,relief="solid")
        frame_bot.pack(side="bottom",fill="x")

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
            self.format_listbox.selection_clear(0,self.format_listbox.size()-1)
            for index in self.full_selected_format_indices:
                self.format_listbox.select_set(index)
        elif len(self.selected_format_indices) == 1:
            self.first_selected = self.format_listbox.get(self.format_listbox.curselection()).split()[0]
            # print(self.first_selected)
        elif len(self.selected_format_indices) == 2:
            selected_type1 = ""
            selected_type2 = ""            
            match = re.search(r"\[(.*?)\]", self.format_listbox.get(self.selected_format_indices[0]))
            if match:
                selected_type1 = match.group(1)            
            match = re.search(r"\[(.*?)\]", self.format_listbox.get(self.selected_format_indices[1]))
            if match:
                selected_type2 = match.group(1)

            if (selected_type1 == "Audio Only" and selected_type2 != "Video Only") \
                or (selected_type1 == "Video Only" and selected_type2 != "Audio Only") \
                or selected_type1 == "Video + Audio" or selected_type2 == "Video + Audio":
                for index in self.selected_format_indices:
                    # print('index: ', index)
                    if self.first_selected == self.format_listbox.get(index).split()[0]:
                        self.format_listbox.selection_clear(index)
                        self.first_selected = self.format_listbox.get(self.format_listbox.curselection()).split()[0]
                        # print(self.first_selected)
                        break
            else:
                self.full_selected_format_indices = self.format_listbox.curselection()

    def check_threads(self):
        if self.download_thread and not self.download_thread.is_alive():
            self.download_button['state'] = 'normal'  # Download 버튼 활성화
            self.search_button['state'] = 'normal'  # Search 버튼 활성화
            self.download_thread = None  # 스레드 참조 제거

        if self.search_thread and not self.search_thread.is_alive():
            self.download_button['state'] = 'normal'  # Download 버튼 활성화
            self.search_button['state'] = 'normal'  # Search 버튼 활성화
            self.search_thread = None  # 스레드 참조 제거

        self.after(100, self.check_threads)

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
            #'--flat-playlist',
            '--skip-download',
            '--print-json',
            url
        ]
        
        # Adjust command for cookies
        cookie_selection = self.cookie_dropdown.get()
        # print("cookies: ", cookie_selection)
        if cookie_selection == "cookies.txt" and os.path.exists("cookies.txt"):
            command.extend(['--cookies', 'cookies.txt'])
        elif "Browser:" in cookie_selection:
            browser = cookie_selection.split(":")[1].strip().upper()
            command.extend(['--cookies-from-browser', browser])
        # print("command ", command)
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
            self.video_info = json.loads(yt_dlp_output)           

            # Update video title
            self.video_title_label.config(text=self.video_info['title'])
    
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
                if format_vcodec == 'none' and format_acodec != 'none' and format_entry.get('format_id', 'N/A') in ['140','141','251']:
                    format_type = "Audio Only"
                    is_good_format = True
                elif format_vcodec != 'none' and format_acodec != 'none' and any(resolution in format_entry.get('format_note', 'N/A') for resolution in ['720p','1080p','1440p','2160p']):
                    format_type = "Video + Audio"
                    is_good_format = True
                elif format_vcodec != 'none' and format_acodec == 'none' and any(resolution in format_entry.get('format_note', 'N/A') for resolution in ['720p','1080p','1440p','2160p']) and format_entry.get('ext','N/A') == 'mp4':
                    format_type = "Video Only"
                    is_good_format = True
                    
                if is_good_format == True:
                    format_description = f"{format_entry['format_id']} - {format_entry.get('format_note', 'N/A')} ({format_entry['ext']}) [{format_type}]"
                    self.format_listbox.insert(tk.END, format_description)
    
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"An error occurred while fetching formats: {e.output}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to decode the output from yt-dlp.")
 
    def download_video(self):
        self.download_button['state'] = 'disabled'  # 버튼 비활성화
        self.search_button['state'] = 'disabled'  # 버튼 비활성화      
        self.download_thread = threading.Thread(target=self.download_video_threaded)
        self.download_thread.start()       
 
    def download_video_threaded(self):
        url = self.url_entry.get()
        convert_selection = self.convert_dropdown.get()       
        self.get_selected_items()
        # selected_format = self.format_listbox.get(tk.ACTIVE).split(' ')[0]  
        selected_formats_list = [self.format_listbox.get(index).split(' ')[0] for index in self.selected_format_indices]   # Extract the format_id from the selected item     

        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        filename = self.video_info['title']
        for char in invalid_chars:
            filename = filename.replace(char, '_')  # 이 예에서는 '_'로 대체하였습니다.        

        # Define download path (for simplicity, we'll download to the current directory with a fixed name)
        output_path = os.path.join(os.getcwd(), filename + '.%(ext)s')
                
        audio_filename=""
        video_filename=""
        
        Index = 0        
        for selected_format in selected_formats_list:
            Index += 1
            # selected_format = self.format_listbox.get(self.format_listbox.curselection()).split()[0]
            
            # Use yt-dlp to download the video
            command = [
                'yt-dlp.exe', 
                '-f', selected_format,
                '-o', output_path,
                url
            ]
            # Adjust command for cookies
            cookie_selection = self.cookie_dropdown.get()
            # print("cookies: ", cookie_selection)
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
    
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                messagebox.showerror("Error", stderr.decode())
                return
                
            # Set the audio_file_path after downloading using yt-dlp
            for format_entry in self.video_info['formats']:
                if format_entry['format_id'] == selected_format:
                    audio_file_path = os.path.join(os.getcwd(), filename + '.' + format_entry['ext'])
                    break
    
            # Check if the selected format is audio only
            is_audio_only = False
            for format_entry in self.video_info['formats']:
                if format_entry['format_id'] == selected_format:
                    # print("vcodec value: ", format_entry.get('vcodec'))
                    if format_entry.get('vcodec') in ['audio_only', 'none']:
                        is_audio_only = True
                    break
                    
            # Print the values for debugging
            # print("Convert to MP3 option:", convert_to_mp3)
            # print("Is audio only:", is_audio_only)
            
            # If the downloaded file is audio and the user chose to convert to MP3, convert using ffmpeg
            if "Convert to" in convert_selection and is_audio_only:
                ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')
                
                if "MP3" in convert_selection:
                    # print("Converting to mp3")
                    # print("Audio file path:", audio_file_path)
                    
                    convert_file_path = os.path.splitext(audio_file_path)[0] + ".mp3"                
                        
                    ffmpeg_command = [
                        ffmpeg_path,
                        '-i', audio_file_path,
                        '-b:a', '320k',  # Set audio bitrate to 320kbps                    
                        convert_file_path
                    ]
                
                    # print("ffmpeg command:", ffmpeg_command)
                elif "WAV" in convert_selection:    
                    convert_file_path = os.path.splitext(audio_file_path)[0] + ".wav"
                        
                    ffmpeg_command = [
                        ffmpeg_path,
                        '-i', audio_file_path,
                        '-acodec', 'pcm_s24le','-ar','48000',  # Set audio format                    
                        convert_file_path
                    ]           
                ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                stdout, stderr = ffmpeg_process.communicate()
                
                if ffmpeg_process.returncode != 0:
                    messagebox.showerror("Error", stderr.decode())
                    return
                
                # Optionally, delete the original audio file after conversion
                os.remove(audio_file_path)
                
            if len(selected_formats_list) == 2 and "Combine" in convert_selection:
                if is_audio_only:
                    audio_filename = audio_file_path
                else:
                    video_filename = audio_file_path
                if (Index == 2 and audio_filename and video_filename):
                    ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')
                    convert_file_path = os.path.splitext(audio_file_path)[0] + "_combined.mp4"
                    
                    ffmpeg_command = [
                        ffmpeg_path,
                        '-i', audio_filename,
                        '-i', video_filename,
                        '-c:v','copy', '-c:a', 'aac', '-strict', 'experimental',
                        convert_file_path
                    ]                     

                    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                    stdout, stderr = ffmpeg_process.communicate()
                    
                    if ffmpeg_process.returncode != 0:
                        messagebox.showerror("Error", stderr.decode())
                        return
                        
                    os.remove(audio_filename)
                    os.remove(video_filename)

        messagebox.showinfo("Download Complete", "Your video has been downloaded and converted (if applicable)!")                

    def check_and_update_ytdlp(self):
        if sys.platform == "win32":
            # Windows에서 콘솔 창 숨기기
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Check if yt-dlp needs an update and update if necessary.
        try:        
            # Check if yt-dlp.exe exists in the current directory
            yt_dlp_path = "yt-dlp.exe"
            if not os.path.exists(yt_dlp_path):
                current_version_str = "Not Installed"
                current_version = datetime.min
            else:
                # Get current yt-dlp version
                current_version_str = subprocess.check_output([yt_dlp_path, '--version'], startupinfo=startupinfo).decode().strip()
                current_version = datetime.strptime(current_version_str, "%Y.%m.%d")
    
            # Fetch the latest yt-dlp version from GitHub API
            response = requests.get('https://api.github.com/repos/yt-dlp/yt-dlp/releases')
            response.raise_for_status()
            latest_version_str = response.json()[0]['tag_name']
            latest_version = datetime.strptime(latest_version_str, "%Y.%m.%d")
    
            if latest_version > current_version:
                # Ask the user if they want to update
                message = f"A new version of yt-dlp is available.\nCurrent version: {current_version_str}\nLatest version: {latest_version_str}\nWould you like to update?"
                update_choice = messagebox.askyesno("Update Available", message)
    
                if update_choice:
                    # Update yt-dlp
                    url = f"https://github.com/yt-dlp/yt-dlp/releases/download/{latest_version_str}/yt-dlp.exe"
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    with open(yt_dlp_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    # Notify the user that the update is complete
                    messagebox.showinfo("Update Complete", "yt-dlp has been successfully updated!")  
                    
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to update yt-dlp: {e}")

        
    def on_closing(self):
        self.destroy()        

# 앱 실행
app = YoutubeDownloader()

# check_and_update_ytdlp 함수를 별도의 스레드에서 실행
update_thread = threading.Thread(target=app.check_and_update_ytdlp)
update_thread.start()
    
app.mainloop()
update_thread.join()  # 앱이 종료되면 스레드가 완료될 때까지 기다림

if app.search_thread and app.search_thread.is_alive():  # 스레드가 실행 중인지 확인
    app.search_thread.join()
    
    
# 컴파일 코드
# pyinstaller --add-data=icon.ico;. --add-binary=ffmpeg.exe;. --onefile --icon=icon.ico --noconsole YTDL-GUI.py
