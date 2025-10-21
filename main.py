# -*- coding: utf-8 -*-

import os
import json
import time
from rich.console import Console
from rich.prompt import Prompt
from yt_dlp import YoutubeDL

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
console = Console()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_save_path(config):
    if "save_path" in config and os.path.isdir(config["save_path"]):
        return config["save_path"]
    
    while True:
        path = Prompt.ask("[bold cyan]Введите путь для сохранения видео[/bold cyan]")
        if os.path.isdir(path):
            config["save_path"] = path
            save_config(config)
            return path
        console.print("[bold red]Указанный путь не существует. Пожалуйста, введите корректный путь.[/bold red]")

def get_video_info(url):
    ydl_opts = {'quiet': True}
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        return info_dict

def choose_format(formats):
    filtered_formats = {}
    for f in formats:
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
            height = f.get('height')
            fps = f.get('fps')
            if height in [480, 720, 1080]:
                if height not in filtered_formats:
                    filtered_formats[height] = {}
                if fps not in filtered_formats[height]:
                    filtered_formats[height][fps] = f
    
    if not filtered_formats:
        console.print("[bold red]Не найдено подходящих форматов (480p, 720p, 1080p MP4).[/bold red]")
        return None

    console.print("[bold yellow]Выберите качество видео:[/bold yellow]")
    options = []
    for height in sorted(filtered_formats.keys()):
        for fps in sorted(filtered_formats[height].keys()):
            format_info = filtered_formats[height][fps]
            filesize_mb = format_info.get('filesize')
            if filesize_mb:
                filesize_str = f"{filesize_mb / (1024*1024):.2f}MB"
            else:
                filesize_str = "N/A"
            options.append((f"{height}p @ {fps}fps ({filesize_str})", format_info['format_id']))

    for i, (label, _) in enumerate(options, 1):
        console.print(f"[cyan]{i}[/cyan]: {label}")

    while True:
        try:
            choice = int(Prompt.ask("[bold cyan]Введите номер желаемого качества[/bold cyan]"))
            if 1 <= choice <= len(options):
                return options[choice - 1] # Return (label, format_id)
            else:
                console.print("[bold red]Неверный номер. Пожалуйста, выберите из списка.[/bold red]")
        except ValueError:
            console.print("[bold red]Пожалуйста, введите число.[/bold red]")

class MyLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        console.print(f"[bold red]ERROR: {msg}[/bold red]")


def my_hook(d):
    if d['status'] == 'downloading':
        p = d['_percent_str']
        p = p.replace('%','')
        console.print(f"Downloading: {d['filename']} | {p}% of {d['_total_bytes_str']} at {d['_speed_str']}", end='\r')
    if d['status'] == 'finished':
        console.print(f"\n[bold green]Done downloading, now converting ...[/bold green]")


def download_video(url, format_id, save_path):
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    console.print("[bold green]--- YouTube Downloader ---[/bold green]")
    config = load_config()
    save_path = get_save_path(config)
    console.print(f"[cyan]Видео будут сохранены в: {save_path}[/cyan]")

    video_url = Prompt.ask("[bold cyan]Введите или перетащите URL видео с YouTube[/bold cyan]").strip(' "')
    
    try:
        video_info = get_video_info(video_url)
        formats = video_info.get('formats')
        video_title = video_info.get('title', 'неизвестное видео')

        if formats:
            chosen_format_info = choose_format(formats)
            if chosen_format_info:
                format_label, format_id = chosen_format_info
                console.print(f"[yellow]Начало скачки \"{video_title}\" в \"{format_label}\"[/yellow]")
                
                start_time = time.time()
                download_video(video_url, format_id, save_path)
                end_time = time.time()
                
                download_duration = end_time - start_time
                
                console.clear()
                console.print(f"[bold green]Видео \"{video_title}\" успешно скачано за {download_duration:.2f} секунд[/bold green]")
        else:
            console.print("[bold red]Не удалось получить форматы видео.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Произошла ошибка: {e}[/bold red]")


if __name__ == "__main__":
    main()
