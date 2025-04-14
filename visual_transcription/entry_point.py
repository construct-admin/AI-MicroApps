# run_app.py
import os
import sys
import subprocess
import time # For potential delay/debugging

print("------------------------------------")
print("Launcher Script Initializing...")
print(f"Python Executable: {sys.executable}")
print(f"Frozen: {getattr(sys, 'frozen', False)}")
print(f"MEIPASS: {getattr(sys, '_MEIPASS', 'Not set')}")
print("------------------------------------")

# Define the path to the main Streamlit script
try:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a bundled executable (created by PyInstaller)
        # sys._MEIPASS is the path to the temporary directory where bundled files are extracted
        app_dir = sys._MEIPASS
        print(f"Running bundled. App directory (MEIPASS): {app_dir}")
    else:
        # Running as a normal script (e.g., python run_app.py)
        app_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Running as script. App directory: {app_dir}")

    # Assuming visual_transcripts.py is bundled at the root level (due to --add-data "visual_transcripts.py;.")
    script_path = os.path.join(app_dir, 'visual_transcripts.py')
    print(f"Target Streamlit script path: {script_path}")

    if not os.path.exists(script_path):
         print(f"ERROR: Target script 'visual_transcripts.py' not found at expected location: {script_path}")
         # You might want to search app_dir if the path isn't found immediately
         # print("Contents of app_dir:")
         # try:
         #    for item in os.listdir(app_dir): print(f"- {item}")
         # except Exception as list_e: print(f"Could not list dir: {list_e}")
         raise FileNotFoundError(f"Target script not found at {script_path}")

    # Command: streamlit run visual_transcripts.py
    # We *omit* --server.headless=true to allow Streamlit to try opening the browser
    args = ["run", script_path]

    # Construct the full command path, attempting to use the bundled streamlit entry point
    # This might need adjustment based on how PyInstaller bundles streamlit.
    # Often, just calling 'streamlit' works if PyInstaller includes its entry points in the path.
    command = ["streamlit"] + args

    print(f"Attempting to execute command: {' '.join(command)}")
    print("------------------------------------")

    # Execute the command. subprocess.run will block until the Streamlit server is stopped (e.g., Ctrl+C).
    # Streamlit itself should handle opening the browser window.
    process = subprocess.run(command, check=False) # check=False allows us to see the return code even on failure

    print("------------------------------------")
    print(f"Streamlit process finished with return code: {process.returncode}")
    print("Launcher script exiting.")
    print("------------------------------------")


except FileNotFoundError as e:
     print(f"FATAL ERROR: Required file or command not found.")
     print(f"Details: {e}")
     print("This might mean 'streamlit' is not bundled correctly, PATH issues, or the target script is missing.")
except Exception as e:
     print(f"FATAL ERROR: An unexpected error occurred in the launcher.")
     # Print detailed traceback
     import traceback
     traceback.print_exc()

# Optional: Keep the console window open for a few seconds if you run this
# with pyinstaller's --console flag (or without --windowed) for debugging.
# print("Closing launcher window in 15 seconds...")
# time.sleep(15)