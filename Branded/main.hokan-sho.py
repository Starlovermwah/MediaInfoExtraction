import os
import re

def extract_info(file_path):
    info = {"Audio": [], "Subtitles": []}
    section = None
    audio_info = None
    subtitle_info = None
    language_count = 0
    format_count = 0

    filename = os.path.basename(file_path)
    filename_no_ext = ".".join(filename.split(".")[:-1])
    
    if '[' in filename and ']' in filename:
        bracketed_parts = [part.strip() for part in filename.split('[') if ']' in part]
        quality_parts = []
        for part in bracketed_parts:
            quality_part = part.split(']')[0].strip()
            if re.match(r'\d+p|\d+K', quality_part, re.IGNORECASE):
                quality_parts.append(quality_part)
        info["Quality"] = ' '.join(quality_parts) if quality_parts else "N/A"
        filename_no_quality = filename.split('[')[0].strip()
    else:
        info["Quality"] = "N/A"
        filename_no_quality = filename_no_ext
    
    info["Complete name"] = filename_no_quality.strip()

    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("Video"):
                section = "Video"
            elif line.startswith("Audio"):
                if audio_info and all(key in audio_info for key in ["Language", "Format", "Channels", "Sampling rate", "Bit rate"]):
                    info["Audio"].append(audio_info)
                audio_info = {}
                section = "Audio"
                language_count = 0
                format_count = 0
            elif line.startswith("Text"):
                if subtitle_info and all(key in subtitle_info for key in ["Language", "Format"]):
                    info["Subtitles"].append(subtitle_info)
                subtitle_info = {}
                section = "Text"
                language_count = 0
            elif line.startswith("\n"):
                section = None

            if section == "Video":
                if line.startswith("Bit rate") and '/' not in line:
                    bitrate_str = line.split(":", 1)[1].strip()
                    if "bits" in bitrate_str:
                        info["Bit rate"] = bitrate_str.replace("bits", "Bit").strip()
                    else:
                        parts = bitrate_str.split()
                        for part in parts:
                            try:
                                bitrate_numeric = float(part)
                                if len(part) == 8:
                                    bitrate_kbps = f"{int(bitrate_numeric / 1000)} kbps"
                                elif "MB/s" in bitrate_str:
                                    bitrate_kbps = f"{int(bitrate_numeric * 8000)} kbps"
                                elif "Mb/s" in bitrate_str:
                                    bitrate_kbps = f"{int(bitrate_numeric * 1000)} kbps"
                                elif "kb/s" in bitrate_str or "Kb/s" in bitrate_str:
                                    bitrate_kbps = f"{int(bitrate_numeric)} kbps"
                                else:
                                    bitrate_kbps = f"{int(bitrate_numeric / 1000)} kbps"
                                info["Bit rate"] = bitrate_kbps
                                break
                            except ValueError:
                                continue
                elif line.startswith("Frame rate"):
                    fps_str = line.split(":", 1)[1].strip()
                    fps_value = fps_str.split('(')[0].strip()
                    info["Frame rate"] = f"{fps_value.strip()} fps".strip()
                elif line.startswith("Format profile"):
                    info["Format profile"] = line.split(":", 1)[1].strip()
                elif line.startswith("HDR format"):
                    hdr_line = line.split(":", 1)[1].strip()
                    hdr_parts = hdr_line.split('/')
                    for part in hdr_parts:
                        part = part.strip()
                        if "Dolby Vision" in part:
                            info["Dolby Vision"] = "Dolby Vision"
                        elif "HDR10+" in part:
                            info["HDR format"] = "HDR10+"
                        elif "HDR10" in part and "HDR format" not in info:
                            info["HDR format"] = "HDR10"
                elif "Format  " in line:
                    format_values = line.split(":", 1)[1].strip().split()
                    info["Format"] = format_values[1] if len(format_values) > 1 else format_values[0]
                elif line.startswith("Bit depth"):
                    info["Bit depth"] = line.split(":", 1)[1].strip().replace("bits", "Bit")
                elif "Display aspect ratio" in line:
                    if "Active display aspect ratio" not in info:
                        info["Display aspect ratio"] = line.split(":", 1)[1].strip()

            elif section == "Audio":
                if "Language" in line and "Language_More" not in line:
                    language_count += 1
                    if language_count == 2:
                        audio_info["Language"] = line.split(":", 1)[1].strip()
                elif "Format" in line:
                    format_count += 1
                    if format_count == 2 or ("Channels" in audio_info and (audio_info["Channels"] == "7.1" or audio_info["Channels"] == "5.1") and format_count == 1):
                        format_str = line.split(":", 1)[1].strip()
                        format_values = format_str.split()
                        if len(format_values) > 1:
                            if any(word in format_values for word in ["XLL", "DTS"]):
                                format_str = "DTS XLL"
                            elif any(word in format_values for word in ["FBA", "MLP"]):
                                format_str = "MLP FBA 16-ch"
                            else:
                                format_str = format_values[1] if len(format_values[1]) > 2 else format_values[0]
                        audio_info["Format"] = format_str.replace("JOC", "E-AC-3 JOC")
                elif "Channel(s)" in line:
                    channels = line.split(":", 1)[1].strip()
                    channel_count = re.search(r'\d+', channels)
                    if channel_count:
                        channel_count = int(channel_count.group())
                        if channel_count == 8:
                            channels = "7.1"
                        elif channel_count == 6:
                            channels = "5.1"
                        elif channel_count == 2:
                            channels = "2"
                    audio_info["Channels"] = channels
                elif "Sampling rate" in line:
                    audio_info["Sampling rate"] = line.split(":", 1)[1].strip()
                elif "Bit rate" in line:
                    bit_rate = line.split(":", 1)[1].strip()
                    if "kb/s" in bit_rate or "Kb/s" in bit_rate:
                        bit_rate = bit_rate.replace("kb/s", "kbps").replace("Kb/s", "kbps")
                    if len(bit_rate) >= 5 and bit_rate.isdigit():
                        bit_rate = bit_rate[:1] + bit_rate[2:]
                    audio_info["Bit rate"] = bit_rate
                elif "Maximum bit rate" in line:
                    max_bit_rate = line.split(":", 1)[1].strip()
                    if "kb/s" in max_bit_rate or "Kb/s" in max_bit_rate:
                        max_bit_rate = max_bit_rate.replace("kb/s", "kbps").replace("Kb/s", "kbps")
                    if len(max_bit_rate) >= 5 and max_bit_rate.isdigit():
                        max_bit_rate = max_bit_rate[:1] + max_bit_rate[2:]
                    audio_info["Maximum bit rate"] = max_bit_rate

            elif section == "Text":
                if "Language" in line and "Language_More" not in line:
                    language_count += 1
                    if language_count == 2:
                        subtitle_info["Language"] = line.split(":", 1)[1].strip()
                elif "Format" in line:
                    subtitle_info["Format"] = line.split(":", 1)[1].strip()

    if audio_info and all(key in audio_info for key in ["Language", "Format", "Channels", "Sampling rate", "Bit rate"]):
        info["Audio"].append(audio_info)
    
    if subtitle_info and all(key in subtitle_info for key in ["Language", "Format"]):
        info["Subtitles"].append(subtitle_info)

    return info

def format_output(info, is_remux, media_type, encoded_by):
    video_info = (f"Video: {info.get('Complete name', 'N/A')} / "
                  f"{info.get('Bit rate', 'N/A')} / "
                  f"{info.get('Quality', 'N/A')} / "  
                  f"{info.get('Frame rate', 'N/A')} / "
                  f"{info.get('Format profile', 'N/A')} /")

    if "Dolby Vision" in info:
        video_info += f" {info['Dolby Vision']} /"

    if "HDR format" in info:
        video_info += f" {info['HDR format']} /"

    video_info += (f" {info.get('Bit depth', 'N/A')} / "
                   f"{info.get('Display aspect ratio', 'N/A')} / "
                   f"{info.get('Format', 'N/A')} / "
                   f"{media_type}")

    audio_info = []
    for a in info["Audio"]:
        if all(key in a for key in ["Language", "Format", "Channels", "Sampling rate"]):
            bit_rate_key = "Maximum bit rate" if a["Channels"] == "7.1" or a["Channels"] == "8" else "Bit rate"
            if bit_rate_key in a:
                bit_rate = a[bit_rate_key].replace(' ', '').replace('kbps', ' kbps')
                audio_line = f"Audio: {a['Language']} / {a['Format']} / {a['Channels']} / {a['Sampling rate']} / {bit_rate} / {media_type}"
                audio_info.append(audio_line)

    audio_info = "\n".join(audio_info)
    
    subtitle_info = []
    for s in info["Subtitles"]:
        if all(key in s for key in ["Language", "Format"]):
            subtitle_line = f"Subtitles: {s['Language']} / {s['Format']} / {media_type}"
            subtitle_info.append(subtitle_line)
    
    subtitle_info = "\n".join(subtitle_info)

    file_name = f"{info['Complete name']} [{info['Quality']}]"
    if "Dolby Vision" in info:
        file_name += f" [{info['Dolby Vision']}]"
    if "HDR format" in info:
        file_name += f" [{info['HDR format']}]"
    if is_remux:
        file_name += " [Remux]"
    file_name += f" [Encoded by {encoded_by}]"

    output = (f"File name: {file_name}\n\n"
              f"{video_info}\n\n"
              f"{audio_info}\n\n"
              f"{subtitle_info}")

    return output

def main():
    input_file = input("Enter path to MediaInfo.txt file: ").strip('"')
    is_remux = input("remux? [Y/N]: ").strip().lower() == 'y'
    encoded_by = input("Who encoded this? ")

    print("Choose the media source:")
    print("1. Blu-Ray")
    print("2. DVD")
    print("3. Netflix")
    print("4. Crunchyroll")
    print("5. Amazon")
    print("6. HULU")
    choice = input("Enter your choice (1-6): ").strip()
    
    media_type = ""
    if choice == "1":
        media_type = "BD"
    elif choice == "2":
        media_type = "DVD"
    elif choice == "3":
        media_type = "NF"
    elif choice == "4":
        media_type = "CR"
    elif choice == "5":
        media_type = "AMZN"
    elif choice == "6":
        media_type = "HULU"
    else:
        print("Using default (BD).")
        media_type = "BD"

    output_file = "MediaInfo Extracted.txt"

    info = extract_info(input_file)
    output = format_output(info, is_remux, media_type, encoded_by)

    with open(output_file, 'w') as file:
        file.write(output)

    print(f"Output written to {output_file}")

if __name__ == "__main__":
    main()
