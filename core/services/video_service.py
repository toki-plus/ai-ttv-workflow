import os
import re
import pysrt
import platform
import traceback
import subprocess
import tempfile
from datetime import timedelta
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class VideoCreationService:
    @staticmethod
    def create_video_background(avatar_path: str, font_path: str, output_path: str, author_name: str, sub_text: str, width: int = 1920, height: int = 1080) -> bool:
        try:
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)

            try:
                avatar = Image.open(avatar_path).convert("RGBA")
                avatar_size = 200
                avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new('L', (avatar_size, avatar_size), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                avatar_x = (width - avatar_size) // 2
                avatar_y = 150
                img.paste(avatar, (avatar_x, avatar_y), mask)
            except (FileNotFoundError, IOError) as e:
                print(f"警告: 加载头像文件 '{avatar_path}' 失败: {e}。将跳过头像绘制。")

            try:
                font = ImageFont.truetype(font_path, size=36)
            except IOError:
                print(f"错误: 无法加载字体文件 '{font_path}'。")
                return False

            bbox_sub = draw.textbbox((0, 0), sub_text, font=font)
            text_width_sub = bbox_sub[2] - bbox_sub[0]
            draw.text((width - text_width_sub - 50, 100), sub_text, font=font, fill='white')

            bbox_author = draw.textbbox((0, 0), author_name, font=font)
            text_width_author = bbox_author[2] - bbox_author[0]
            draw.text(((width - text_width_author) / 2, height - 150), author_name, font=font, fill='white')

            img.save(output_path, 'JPEG', quality=95)
            return True
        except Exception as e:
            print(f"生成背景图片时发生错误: {e}")
            return False

    @staticmethod
    def create_cover_image(title: str, subtitle: str, author_name: str, avatar_path: str, font_path: str, output_path: str, width: int = 900, height: int = 1200) -> bool:
        try:
            border_height = int(height * 0.2)
            content_width, content_height = width, height - (2 * border_height)

            content_img = Image.new('RGB', (content_width, content_height), color='black')
            content_draw = ImageDraw.Draw(content_img)

            scale_factor = width / 540.0

            try:
                title_font = ImageFont.truetype(font_path, size=int(80 * scale_factor))
                subtitle_font = ImageFont.truetype(font_path, size=int(40 * scale_factor))
                author_font = ImageFont.truetype(font_path, size=int(40 * scale_factor))
            except IOError:
                print(f"错误: 无法加载字体文件 '{font_path}'。")
                return False

            text_fill_color = 'white'

            title_bbox = content_draw.textbbox((0, 0), title, font=title_font)
            title_width, title_height = title_bbox[2] - title_bbox[0], title_bbox[3] - title_bbox[1]
            title_x, title_y = (content_width - title_width) // 2, int(height * 0.3) - border_height
            content_draw.text((title_x, title_y), title, font=title_font, fill=text_fill_color)

            subtitle_bbox = content_draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width, subtitle_height = subtitle_bbox[2] - subtitle_bbox[0], subtitle_bbox[3] - subtitle_bbox[1]
            subtitle_x, subtitle_y = (content_width - subtitle_width) // 2, title_y + title_height + int(25 * scale_factor)
            content_draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill=text_fill_color)

            line_y = subtitle_y + subtitle_height + int(25 * scale_factor)
            line_width = int(content_width * 0.6)
            line_x1, line_x2 = (content_width - line_width) // 2, (content_width + line_width) // 2
            content_draw.line((line_x1, line_y, line_x2, line_y), fill=text_fill_color, width=int(2 * scale_factor))

            try:
                avatar_rgba = Image.open(avatar_path).convert("RGBA")
                avatar_size = int(130 * scale_factor)
                avatar_rgba = avatar_rgba.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new('L', (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                avatar_x = content_width - avatar_size - int(60 * scale_factor)
                avatar_y = line_y + int(20 * scale_factor)
                content_img.paste(avatar_rgba, (avatar_x, avatar_y), mask)
            except (FileNotFoundError, IOError):
                print(f"警告: 未找到头像文件 '{avatar_path}'。将跳过头像绘制。")
                avatar_size, avatar_y = 0, 0

            author_bbox = content_draw.textbbox((0, 0), author_name, font=author_font)
            author_height = author_bbox[3] - author_bbox[1]
            author_x = int(100 * scale_factor)
            author_y_aligned = avatar_y + (avatar_size // 2) - (author_height // 2)
            content_draw.text((author_x, author_y_aligned), author_name, font=author_font, fill=text_fill_color)

            background_img = content_img.resize((width, height), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=30))
            background_img.paste(content_img, (0, border_height))

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            background_img.save(output_path, 'JPEG', quality=95)
            return True
        except Exception as e:
            print(f"生成封面图时发生错误: {e}\n{traceback.format_exc()}")
            return False

    @staticmethod
    def process_subtitles(input_srt_path: str, output_srt_path: str, max_chars_per_line: int, max_lines_per_sub: int) -> bool:
        if not os.path.exists(input_srt_path):
            print(f"错误: 字幕文件 '{input_srt_path}' 不存在。")
            return False
        try:
            subs = pysrt.open(input_srt_path, encoding='utf-8')
            char_timestamps = []
            full_text_list = []
            for sub in subs:
                text = sub.text_without_tags.strip().replace('\n', ' ')
                if not text: continue

                duration_ms = sub.end.ordinal - sub.start.ordinal
                time_per_char = duration_ms / len(text) if len(text) > 0 else 0

                for i, char in enumerate(text):
                    char_time = pysrt.SubRipTime.from_ordinal(sub.start.ordinal + int(i * time_per_char))
                    char_timestamps.append(char_time)

                full_text_list.append(text)

            full_text = "".join(full_text_list)
            if not full_text:
                print("警告: 字幕文件内容为空。")
                with open(output_srt_path, 'w', encoding='utf-8') as f: pass
                return True

            clauses = re.split(r'([，。！？、,.:;!?])', full_text)
            semantic_clauses = [clauses[i] + (clauses[i+1] if i + 1 < len(clauses) else '') for i in range(0, len(clauses), 2)]

            final_lines = []
            for clause in semantic_clauses:
                clause = clause.strip()
                if not clause: continue
                while len(clause) > max_chars_per_line:
                    final_lines.append(clause[:max_chars_per_line])
                    clause = clause[max_chars_per_line:]
                if clause:
                    final_lines.append(clause)

            new_subs = pysrt.SubRipFile()
            char_offset = 0
            punctuation_marks = '，。！？、,.:;!?'

            for i in range(0, len(final_lines), max_lines_per_sub):
                text_block_lines = final_lines[i : i + max_lines_per_sub]
                if len(text_block_lines) > 1 and len(text_block_lines[-1]) == 1 and text_block_lines[-1] in punctuation_marks:
                    punctuation = text_block_lines.pop()
                    text_block_lines[-1] += punctuation

                new_text = '\n'.join(text_block_lines).strip()
                if not new_text: continue

                cleaned_text = new_text.lstrip(punctuation_marks)
                text_length_for_sub = len("".join(text_block_lines))

                if not cleaned_text:
                    char_offset += text_length_for_sub
                    continue

                start_char_idx, end_char_idx = char_offset, char_offset + text_length_for_sub - 1

                if start_char_idx >= len(char_timestamps) or end_char_idx >= len(char_timestamps):
                    continue

                start_time, end_time = char_timestamps[start_char_idx], char_timestamps[end_char_idx]
                if end_time < start_time:
                    end_time = start_time + timedelta(milliseconds=100)

                new_subs.append(pysrt.SubRipItem(index=len(new_subs) + 1, start=start_time, end=end_time, text=cleaned_text))
                char_offset += text_length_for_sub

            for sub in new_subs:
                lines = sub.text.split('\n')
                if len(lines) == 2:
                    combined = "".join(lines)
                    if len(combined) <= max_chars_per_line:
                        sub.text = combined
                    else:
                        sub.text = f"{combined[:max_chars_per_line]}\n{combined[max_chars_per_line:]}"

            new_subs.save(output_srt_path, encoding='utf-8')
            return True
        except Exception as e:
            print(f"处理字幕时发生严重错误: {e}\n{traceback.format_exc()}")
            return False

    @staticmethod
    def _escape_ffmpeg_path(path: str) -> str:
        if platform.system() == "Windows":
            return path.replace('\\', '/').replace(':', '\\:')
        return path

    @staticmethod
    def create_video_with_ffmpeg(background_image: str, audio_file: str, srt_file: str, font_path: str, output_file: str, use_gpu: bool, bgm_file: Optional[str]) -> bool:
        for file_path, name in [(background_image, "背景图片"), (audio_file, "音频文件"), (srt_file, "字幕文件"), (font_path, "字体文件")]:
            if not os.path.exists(file_path):
                print(f"错误: {name} '{file_path}' 不存在。合成中止。")
                return False

        sanitized_font_dir = VideoCreationService._escape_ffmpeg_path(os.path.dirname(os.path.abspath(font_path)))
        sanitized_srt_file = VideoCreationService._escape_ffmpeg_path(os.path.abspath(srt_file))

        try:
            internal_font_name = ImageFont.truetype(font_path, size=10).getname()[0]
        except Exception:
            internal_font_name = os.path.splitext(os.path.basename(font_path))[0]

        subtitle_style = f"force_style='FontName={internal_font_name},FontSize=42,Alignment=2,MarginV=80,PrimaryColour=&HFFFFFF,Bold=1,Shadow=0.8'"
        subtitle_filter = f"subtitles='{sanitized_srt_file}':fontsdir='{sanitized_font_dir}':{subtitle_style}"

        command = ['ffmpeg', '-y', '-loop', '1', '-i', background_image, '-i', audio_file]
        maps, filter_complex_parts = [], [f"[0:v]{subtitle_filter}[v]"]
        maps.extend(['-map', '[v]'])

        if bgm_file and os.path.exists(bgm_file):
            command.extend(['-stream_loop', '-1', '-i', bgm_file])
            filter_complex_parts.append("[2:a]volume=0.15[bgm];[1:a][bgm]amix=inputs=2:duration=first[a]")
            maps.extend(['-map', '[a]'])
        else:
            maps.extend(['-map', '1:a'])

        command.extend(['-filter_complex', ";".join(filter_complex_parts), *maps])

        if use_gpu:
            command.extend(['-c:v', 'h264_nvenc', '-preset', 'fast', '-cq', '24'])
        else:
            command.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '18'])

        command.extend(['-c:a', 'aac', '-b:a', '192k', '-shortest', '-pix_fmt', 'yuv420p', output_file])

        try:
            run_kwargs = {'check': True, 'capture_output': True, 'text': True, 'encoding': 'utf-8', 'errors': 'ignore'}
            if platform.system() == "Windows":
                run_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            subprocess.run(command, **run_kwargs)
            return True
        except FileNotFoundError:
            print("错误: 'ffmpeg' 命令未找到。请确保FFmpeg已安装并添加到系统PATH环境变量中。")
            return False
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg 命令执行失败。返回码: {e.returncode}\n命令: {' '.join(command)}\n错误输出:\n{e.stderr}")
            return False

    @staticmethod
    def run_generation_workflow(params: Dict[str, Any]) -> str:
        with tempfile.TemporaryDirectory() as temp_dir:
            bg_output = os.path.join(temp_dir, "background.jpg")
            if not VideoCreationService.create_video_background(params['avatar'], params['font'], bg_output, params['author'], params['subtext']):
                raise RuntimeError("生成视频背景图失败")

            if params['cover_title']:
                cover_basename = f"cover_{os.path.splitext(os.path.basename(params['video_output']))[0]}.jpg"
                cover_output_path = os.path.join(os.path.dirname(params['video_output']), cover_basename)
                if not VideoCreationService.create_cover_image(params['cover_title'], params['cover_subtitle'], params['author'], params['avatar'], params['font'], cover_output_path):
                    print("警告: 封面图生成失败，将继续。")
            else:
                print("未提供封面标题，跳过封面生成。")

            srt_processed_output = os.path.join(temp_dir, "subtitles_processed.srt")
            if not VideoCreationService.process_subtitles(params['srt'], srt_processed_output, 12, 2):
                raise RuntimeError("处理字幕文件失败")

            if not VideoCreationService.create_video_with_ffmpeg(bg_output, params['audio'], srt_processed_output, params['font'], params['video_output'], params['use_gpu'], params['bgm']):
                raise RuntimeError("FFmpeg合成视频失败, 请检查控制台错误日志。")

        return params['video_output']