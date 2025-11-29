#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import shlex
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog

# -----------------------------
# FILE PICKER USING TKINTER
# -----------------------------
def pick_files(prompt="Select files", allow_multiple=True, initial_dir=None):
    root = tk.Tk()
    root.withdraw()  # hide main window

    if initial_dir is None:
        initial_dir = os.path.expanduser("~/Downloads")
        if not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~/Desktop")

    filetypes = [("All files", "*.*")]

    if allow_multiple:
        paths = filedialog.askopenfilenames(
            title=prompt,
            initialdir=initial_dir,
            filetypes=filetypes
        )
    else:
        path = filedialog.askopenfilename(
            title=prompt,
            initialdir=initial_dir,
            filetypes=filetypes
        )
        paths = (path,) if path else ()

    paths = list(paths)
    if not paths:
        print("Cancelled by user.")
        return []

    print(f"Selected {len(paths)} file(s):")
    for p in paths:
        print("  • " + os.path.basename(p))
    return paths

# -----------------------------
# SAFE SAVE PATH
# -----------------------------
def safe_save_path(base_name: str, extension: str = ".mp4") -> str:
    desktop = os.path.expanduser("~/Desktop")
    name = base_name.strip() or "Untitled music video"
    candidate = os.path.join(desktop, f"{name}{extension}")
    root, ext = os.path.splitext(candidate)
    i = 1
    while os.path.exists(candidate):
        candidate = f"{root}-{i}{ext}"
        i += 1
    return candidate

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
def main():
    print("\n" + "="*70)
    print("   VIDEO + AUDIO STITCHER - TKINTER VERSION")
    print("="*70 + "\n")

    # --- VIDEO SELECTION ---
    video_paths = pick_files("Select video clips (order matters)", True)
    if not video_paths:
        return

    if input(f"\nProceed with {len(video_paths)} video(s)? (y/n): ").lower() != 'y':
        return

    print("\nLoading videos...")
    clips = []
    total_dur = 0.0
    for p in tqdm(video_paths, desc="Videos"):
        try:
            c = VideoFileClip(p).without_audio()
            clips.append(c)
            total_dur += c.duration or 0
        except Exception as e:
            print(f"\nError loading {os.path.basename(p)} -> {e}")
            return

    if total_dur <= 0:
        print("Video content is empty.")
        return
    print(f"Total video length: {total_dur:.2f} seconds")

    # --- AUDIO SELECTION ---
    audio_paths = pick_files("Select ONE audio file", False)
    if not audio_paths:
        return

    audio_path = audio_paths[0]
    try:
        audio = AudioFileClip(audio_path)
        audio_dur = audio.duration or 0
    except Exception as e:
        print(f"Audio error: {e}")
        return
    print(f"Audio: {os.path.basename(audio_path)} ({audio_dur:.2f} seconds)")

    # --- OUTPUT NAME ---
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
    default_name = f"{audio_name} music video"
    print(f"\nSuggested name: {default_name}.mp4")
    user_input = input("Enter custom name (or press Enter for default): ").strip()
    export_name = user_input if user_input else default_name
    output_path = safe_save_path(export_name, ".mp4")
    print(f"Saving to: {output_path}")

    # --- LOOP VIDEO TO MATCH AUDIO ---
    loops = max(1, math.ceil(audio_dur / total_dur))
    if loops > 1:
        print(f"Looping video {loops} times")

    seq = clips * loops
    final_video = concatenate_videoclips(seq, method="compose")
    if final_video.duration > audio_dur:
        final_video = final_video.subclip(0, audio_dur)
    final = final_video.set_audio(audio)

    # --- EXPORT ---
    print("\nExporting...")
    try:
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="medium", logger=None)
    except Exception as e:
        print(f"Export error: {e}")
        return

    print("\nExport complete!")
    subprocess.run(["qlmanage", "-p", shlex.quote(output_path)], stderr=subprocess.DEVNULL)

    # --- CLEANUP ---
    for c in clips:
        c.close()
    audio.close()
    final_video.close()
    final.close()
    print("\nDone! Your music video is on Desktop.")

# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    if sys.platform != "darwin":
        print("This script only runs on macOS.")
        sys.exit(1)
    main()
