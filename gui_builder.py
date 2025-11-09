
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
        master.title("AI Music Studio - Build Tool")
        master.geometry("700x600")

        self.process = None
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Main frame
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # System Check frame
        check_frame = ttk.LabelFrame(main_frame, text="System Check", padding=10)
        check_frame.pack(pady=10, padx=10, fill=tk.X)
        self.pyinstaller_status_label = ttk.Label(check_frame, text="PyInstaller: Checking...")
        self.pyinstaller_status_label.grid(row=0, column=0, padx=5, sticky="w")
        self.upx_status_label = ttk.Label(check_frame, text="UPX: Checking...")
        self.upx_status_label.grid(row=1, column=0, padx=5, sticky="w")

        self.install_deps_button = ttk.Button(check_frame, text="Install Dependencies", command=self.install_dependencies, state=tk.DISABLED)
        self.install_deps_button.grid(row=0, column=1, rowspan=2, padx=10)

        # Log area
        self.log_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20, width=80, bg="#2b2b2b", fg="#dcdcdc", font=("Consolas", 9))
        self.log_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.log_area.tag_config("INFO", foreground="#bbbbbb")
        self.log_area.tag_config("STEP", foreground="#61afef", font=("Consolas", 9, "bold"))
        self.log_area.tag_config("SUCCESS", foreground="#98c379")
        self.log_area.tag_config("ERROR", foreground="#e06c75")
        self.log_area.tag_config("CMD", foreground="#c678dd")

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(pady=10, padx=10, fill=tk.X)

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Build Options", padding=10)
        options_frame.pack(pady=10, padx=10, fill=tk.X)

        # --- Build Target ---
        self.build_target_var = tk.StringVar(value="gui")
        gui_radio = ttk.Radiobutton(options_frame, text="GUI Application", variable=self.build_target_var, value="gui")
        gui_radio.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        cli_radio = ttk.Radiobutton(options_frame, text="Command-Line Application", variable=self.build_target_var, value="cli")
        cli_radio.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        # --- UPX Compression ---
        self.disable_upx_var = tk.BooleanVar(value=False)
        self.upx_check = ttk.Checkbutton(options_frame, text="Disable UPX Compression (faster build, larger file)", variable=self.disable_upx_var)
        self.upx_check.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)

        self.build_button = ttk.Button(buttons_frame, text="Start Build", command=lambda: self.start_build_thread(run_after=False))
        self.build_button.pack(side=tk.LEFT, padx=5)

        self.build_and_run_button = ttk.Button(buttons_frame, text="Build and Run", command=lambda: self.start_build_thread(run_after=True))
        self.build_and_run_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttk.Button(buttons_frame, text="Open Output Folder", command=self.open_output_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)

        self.queue = queue.Queue()
        self.master.after(100, self.process_queue)

        self.check_dependencies()

    def check_dependencies(self):
        """Checks for required build tools like PyInstaller and UPX."""
        try:
            import PyInstaller
            self.pyinstaller_status_label.config(text="✓ PyInstaller: Found", foreground="green")
            pyinstaller_ok = True
        except ImportError:
            self.pyinstaller_status_label.config(text="✗ PyInstaller: Not Found", foreground="red")
            pyinstaller_ok = False

        if shutil.which("upx"):
            self.upx_status_label.config(text="✓ UPX: Found", foreground="green")
        else:
            self.upx_status_label.config(text="✗ UPX: Not Found (Recommended for smaller files)", foreground="orange")

        if not pyinstaller_ok:
            self.install_deps_button.config(state=tk.NORMAL)
            self.build_button.config(state=tk.DISABLED)
            self.build_and_run_button.config(state=tk.DISABLED)
            self.log("ERROR: PyInstaller is not installed. Please install dependencies.")

    def install_dependencies(self):
        """Install dependencies from requirements.txt."""
        self.log("Installing dependencies from requirements.txt...")
        self.install_deps_button.config(state=tk.DISABLED)
        threading.Thread(target=self._run_pip_install, daemon=True).start()

    def _run_pip_install(self):
        try:
            command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            self.run_command(command)
            self.log("\nDependencies installed successfully.")
            self.log("Please restart the build tool to reflect the changes.")
            self.queue.put(("check_deps", None))
        except Exception as e:
            self.log(f"\nERROR: Failed to install dependencies: {e}")
        finally:
            self.queue.put(("enable_install_button", None))


    def start_build_thread(self, run_after=False):
        self.build_button.config(state=tk.DISABLED)
        self.build_and_run_button.config(state=tk.DISABLED)
        self.open_folder_button.config(state=tk.DISABLED)
        self.log_area.delete(1.0, tk.END)
        self.progress["value"] = 0
        disable_upx = self.disable_upx_var.get()
        build_target = self.build_target_var.get()
        self.thread = threading.Thread(target=self.run_build, args=(build_target, disable_upx, run_after))
        self.thread.start()

    def run_build(self, build_target, disable_upx, run_after):
        try:
            self.log("Starting build process...", "STEP")
            
            # Step 1: Terminate existing process
            self.log("Checking for running application instances...", "STEP")
            
            executable_name_to_kill = "AIMusicStudio_gui.exe" if build_target == "gui" else "AIMusicStudio_cli.exe"
            
            try:
                subprocess.run(["taskkill", "/F", "/IM", executable_name_to_kill], check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.log(f"Terminated running {executable_name_to_kill} instance.", "INFO")
            except subprocess.CalledProcessError:
                self.log(f"No running {executable_name_to_kill} instance found.", "INFO")

            # Step 2: Cleanup
            self.log("Cleaning up old build artifacts...", "STEP")
            if os.path.exists("build"): shutil.rmtree("build")
            if os.path.exists("dist"): shutil.rmtree("dist")
            self.log("Cleanup complete.", "SUCCESS")
            self.update_progress(20)

            # Step 3: Build with PyInstaller
            self.log("Building the executable with PyInstaller...", "STEP")
            
            # Determine which spec file to use
            if build_target == "gui":
                spec_file = "AIMusicStudio_gui_noupx.spec" if disable_upx else "AIMusicStudio_gui.spec"
            else: # cli
                spec_file = "AIMusicStudio_cli_noupx.spec" if disable_upx else "AIMusicStudio_cli.spec"

            self.log(f"Using spec file: {spec_file}", "INFO")

            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dist_path = os.path.join(script_dir, "dist")
            work_path = os.path.join(script_dir, "build")

            pyinstaller_command = [
                sys.executable, "-m", "PyInstaller", "--clean",
                spec_file
            ]

            self.log(f"Running command: {' '.join(pyinstaller_command)}", "CMD")
            self.run_command(pyinstaller_command)

            # Step 4: Finalizing build...
            self.log("Finalizing build...", "STEP")
            # The output folder is named after the spec file (without .spec)
            output_folder_name = os.path.splitext(os.path.basename(spec_file))[0]
            dist_path = os.path.join("dist", output_folder_name)

            if not os.path.exists(dist_path):
                self.log(f"Build directory not found at {dist_path}", "ERROR")
                raise FileNotFoundError(f"Build directory '{dist_path}' not found after PyInstaller run.")

            self.update_progress(100)

            self.log("BUILD SUCCEEDED", "SUCCESS")
            self.log(f"Application is ready in: {os.path.abspath(dist_path)}", "INFO")
            self.queue.put(("build_success", dist_path))

            if run_after:
                self.log("Launching the application...", "STEP")
                executable_name_to_run = "AIMusicStudio_gui.exe" if build_target == "gui" else "AIMusicStudio_cli.exe"
                executable_path = os.path.join(dist_path, executable_name_to_run)
                if os.path.exists(executable_path):
                    self.process = subprocess.Popen(executable_path, cwd=dist_path, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log("Application launched.", "SUCCESS")
                else:
                    self.log(f"Executable '{executable_path}' not found.", "ERROR")

        except Exception as e:
            self.log(f"An unexpected error occurred: {e}", "ERROR")

        finally:
            self.queue.put(("enable_buttons", None))

    def run_command(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # PyInstaller build steps and their corresponding progress values
        pyinstaller_steps = {
            # Analysis & Hooks (20 -> 40)
            "Analyzing": 25,
            "Running hook": 28,
            "Collected hidden imports": 30,
            "Collected data files": 32,
            "Manually collecting FFmpeg binaries": 34,
            "Found and added": 36,
            "Looking for ctypes DLLs": 38,
            "Performing binary vs. data reclassification": 39,
            # Main build steps (40 -> 80)
            "Building PYZ archive": 40,
            "Building PKG archive": 60,
            "Building EXE from EXE-00.toc": 70,
            "Appending archive to EXE": 75,
        }

        for line in iter(process.stdout.readline, ''):
            stripped_line = line.strip()
            self.log(stripped_line, "INFO")
            
            # Check for PyInstaller steps to update progress
            if len(command) > 2 and "pyinstaller" in command[2].lower():
                for step, progress in pyinstaller_steps.items():
                    if step in stripped_line:
                        log_message = f"PyInstaller: {step}"
                        # Provide more detailed log messages for specific steps
                        if step == "Running hook":
                            try:
                                # e.g., "INFO: Running hook hook-torchaudio.py" -> "torchaudio"
                                hook_name = stripped_line.split("hook-")[-1].split(".")[0]
                                log_message = f"PyInstaller: Running hook for {hook_name}"
                            except IndexError:
                                pass  # Use default message
                        elif "Collected" in step or "Found" in step or "Manually collecting" in step:
                            # Try to extract the core message from the hook's log
                            # e.g., "INFO: hook-torchaudio.py: Collected 57 hidden imports for torchaudio."
                            # becomes "PyInstaller: Collected 57 hidden imports for torchaudio."
                            try:
                                details = stripped_line.split(":", 2)[-1].strip()
                                log_message = f"PyInstaller: {details}"
                            except IndexError:
                                pass  # Use default message
                        elif step == "Performing binary vs. data reclassification":
                            try:
                                # e.g., "INFO: ... Performing binary vs. data reclassification (2259 entries)"
                                details = stripped_line.split('(')[-1].split(')')[0]
                                log_message = f"PyInstaller: Reclassifying files ({details})..."
                            except IndexError:
                                log_message = "PyInstaller: Reclassifying files..."

                        self.log(log_message, "STEP")
                        self.update_progress(progress)
                        break # Move to next line once a step is found

        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

    def log(self, message, level="INFO"):
        self.queue.put(("log", (message, level)))

    def update_progress(self, value):
        self.queue.put(("progress", value))

    def process_queue(self):
        try:
            while True:
                msg_type, value = self.queue.get_nowait()
                if msg_type == "log":
                    message, level = value
                    self.log_area.insert(tk.END, f"[{level}] {message}\n", level)
                    self.log_area.see(tk.END)
                elif msg_type == "progress":
                    self.progress["value"] = value
                elif msg_type == "enable_buttons":
                    self.build_button.config(state=tk.NORMAL)
                    self.build_and_run_button.config(state=tk.NORMAL)
                elif msg_type == "build_success":
                    self.open_folder_button.config(state=tk.NORMAL)
                    self.output_path = value
                elif msg_type == "enable_install_button":
                    self.install_deps_button.config(state=tk.NORMAL)
                elif msg_type == "check_deps":
                    self.check_dependencies()
        except queue.Empty:
            pass
        self.master.after(100, self.process_queue)

    def open_output_folder(self):
        if hasattr(self, 'output_path') and os.path.exists(self.output_path):
            subprocess.Popen(f'explorer "{os.path.abspath(self.output_path)}"')
        else:
            self.log("Output path not found or build has not been run yet.", "ERROR")

    def on_closing(self):
        """Handle window closing event."""
        if self.process and self.process.poll() is None:
            self.log("Terminating running application...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                self.log("Application terminated.")
            except subprocess.TimeoutExpired:
                self.log("Application did not terminate in time, killing it.")
                self.process.kill()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = BuildGUI(root)
    root.mainloop()
