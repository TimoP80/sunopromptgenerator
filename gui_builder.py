
import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import queue
import os
import shutil
import sys

class BuildGUI:
    def __init__(self, master):
        self.master = master
        master.title("Application Build Tool")
        master.geometry("700x550")

        # Main frame
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Log area
        self.log_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20, width=80, bg="#f0f0f0", fg="#333")
        self.log_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(pady=10, padx=10, fill=tk.X)

        # Options frame
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(pady=5)

        self.disable_upx_var = tk.BooleanVar(value=False)
        self.upx_check = ttk.Checkbutton(options_frame, text="Disable UPX Compression (faster build, larger file)", variable=self.disable_upx_var)
        self.upx_check.pack(side=tk.LEFT, padx=5)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)

        self.build_button = ttk.Button(buttons_frame, text="Start Build", command=lambda: self.start_build_thread(run_after=False))
        self.build_button.pack(side=tk.LEFT, padx=5)

        self.build_and_run_button = ttk.Button(buttons_frame, text="Build and Run", command=lambda: self.start_build_thread(run_after=True))
        self.build_and_run_button.pack(side=tk.LEFT, padx=5)

        self.queue = queue.Queue()
        self.master.after(100, self.process_queue)

    def start_build_thread(self, run_after=False):
        self.build_button.config(state=tk.DISABLED)
        self.build_and_run_button.config(state=tk.DISABLED)
        self.log_area.delete(1.0, tk.END)
        self.progress["value"] = 0
        disable_upx = self.disable_upx_var.get()
        self.thread = threading.Thread(target=self.run_build, args=(disable_upx, run_after))
        self.thread.start()

    def run_build(self, disable_upx, run_after):
        try:
            # Step 1: Cleanup
            self.log("STEP 1: Cleaning up old build artifacts...")
            if os.path.exists("build"): shutil.rmtree("build")
            if os.path.exists("dist"): shutil.rmtree("dist")
            self.log("Cleanup complete.")
            self.update_progress(20)

            # Step 2: Build with PyInstaller
            self.log("\nSTEP 2: Building the executable with PyInstaller...")
            
            spec_file = "SunoPromptGenerator.spec"
            if disable_upx:
                spec_file = "SunoPromptGenerator_noupx.spec"

            pyinstaller_command = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]

            self.log(f"Running command: {' '.join(pyinstaller_command)}")
            self.run_command(pyinstaller_command)
            self.update_progress(80)

            # Step 3: Copy Files
            self.log("\nSTEP 3: Copying required files (ffmpeg, ffprobe)...")
            dist_path = os.path.join("dist", "SunoPromptGenerator")
            if os.path.exists(dist_path):
                shutil.copy("ffmpeg.exe", dist_path)
                shutil.copy("ffprobe.exe", dist_path)
                self.log("Files copied successfully.")
            else:
                self.log("ERROR: Build directory not found. Cannot copy files.")
                raise FileNotFoundError("Build directory not found.")
            self.update_progress(100)

            self.log("\n================ BUILD SUCCEEDED ================")
            self.log(f"Application is ready in: {os.path.abspath(dist_path)}")

            if run_after:
                self.log("\nSTEP 4: Launching the application...")
                executable_path = os.path.join(dist_path, "SunoPromptGenerator.exe")
                if os.path.exists(executable_path):
                    subprocess.Popen(executable_path, cwd=dist_path)
                    self.log("Application launched.")
                else:
                    self.log("ERROR: Executable not found.")

        except Exception as e:
            self.log(f"\nERROR: An unexpected error occurred: {e}")

        finally:
            self.queue.put(("enable_buttons", None))

    def run_command(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        for line in iter(process.stdout.readline, ''):
            self.log(line.strip())
        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

    def log(self, message):
        self.queue.put(("log", message))

    def update_progress(self, value):
        self.queue.put(("progress", value))

    def process_queue(self):
        try:
            while True:
                msg_type, value = self.queue.get_nowait()
                if msg_type == "log":
                    self.log_area.insert(tk.END, value + "\n")
                    self.log_area.see(tk.END)
                elif msg_type == "progress":
                    self.progress["value"] = value
                elif msg_type == "enable_buttons":
                    self.build_button.config(state=tk.NORMAL)
                    self.build_and_run_button.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        self.master.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    gui = BuildGUI(root)
    root.mainloop()
