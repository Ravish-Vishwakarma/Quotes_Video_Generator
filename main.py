import os
import re
import textwrap
import subprocess
from collections import defaultdict

def escape_drawtext(text):
    """Escape special characters for FFmpeg's drawtext filter."""
    return text.replace("'", r"\'").replace(":", r'\:').replace('\\', r'\\\\').replace('%', r'\%')

def get_video_resolution(video_path):
    """Get the resolution of a video using FFmpeg."""
    result = subprocess.run(
        ['ffmpeg', '-i', video_path],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    output = result.stderr.decode('utf-8')
    
    match = re.search(r'(\d{3,4})x(\d{3,4})', output)
    if match:
        return int(match.group(1)), int(match.group(2))  
    else:
        return None
def add_text_overlay(video_path, text, author, output_path, font_path, video_width=1080, video_height=1920):
    font_size = 120  # Increase the main text size (was 80)
    author_size = 80  # Increase the author text size (was 50)
    line_height = font_size + 10

    # Wrap text and escape special characters as before
    wrapped_text = textwrap.fill(text, width=22)  
    num_lines = wrapped_text.count("\n") + 1
    wrapped_text = escape_drawtext(wrapped_text)
    author = escape_drawtext(author)

    # Adjust for smaller videos if necessary
    if video_width < 1280 or video_height < 720:
        font_size = 100  # Adjust the size for smaller resolutions
        author_size = 70

    # Positioning the text
    text_x = "(w-text_w)/2"
    text_y = int(video_height * 0.3)  
    text_height = num_lines * line_height
    author_x = "(w-text_w)/2"
    author_y = f"{text_y} + {text_height} + 70"  

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    command = [
        'ffmpeg', '-y', '-i', video_path,
        '-vf', (
            f"drawtext=text='{wrapped_text}':fontfile='{font_path}':fontsize={font_size}:fontcolor=white:"
            f"box=1:boxcolor=black@0.5:boxborderw=50:x={text_x}:y={text_y},"
            f"drawtext=text='- {author}':fontfile='{font_path}':fontsize={author_size}:fontcolor=white:"
            f"box=1:boxcolor=black@0.5:boxborderw=30:x={author_x}:y={author_y}"
        ),
        '-c:v', 'h264_nvenc', '-preset', 'fast', '-b:v', '5M', '-c:a', 'copy', output_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"[✔] Generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"[✖] Failed to process video for '{author}': {e}")


video_path = 'assets/media/media.mp4'
text_file = 'assets/text.txt'
font_path = 'assets/fonts/times.ttf'


author_count = defaultdict(int)


with open(text_file, 'r', encoding='utf-8') as file:
    for idx, line in enumerate(file, start=1):
        if '"' in line and ' - ' in line:
            quote, author = line.strip().rsplit(' - ', 1)
            quote = quote.strip('"')

            clean_author = re.sub(r'[\/:*?"<>|]', '', author).strip()
            author_count[clean_author] += 1
            count = author_count[clean_author]

            hashtags = "#quote #viral #motivation #success #inspiration #wisdom"
            filename = f"A quote by {clean_author} ({count})" if count > 1 else f"A quote by {clean_author}"
            output_path = os.path.join("output", f"{filename} {hashtags}.mp4")

            
            video_width, video_height = get_video_resolution(video_path)

            add_text_overlay(video_path, quote, author, output_path, font_path, video_width, video_height)
