import streamlit as st
import os
import glob
from parth_dl import InstagramDownloader
import yt_dlp

st.title("📹 Ultimate All-in-One Downloader")
st.write("Download high-quality videos from **Instagram**, **YouTube**, **Facebook**, or **Twitter (X)** instantly.")

# User Input URL
url = st.text_input("Paste social media video URL here:", "")

def get_standard_label(height):
    """Maps custom platform heights to recognizable standard video resolutions."""
    # List of standard vertical resolutions
    standards = [144, 240, 360, 480, 720, 1080, 1440, 2160]
    # Find the standard resolution closest to the detected height
    closest = min(standards, key=lambda x: abs(x - height))
    return f"{closest}p"

if url:
    is_ytdlp_platform = any(domain in url for domain in [
        "youtube.com", "youtu.be", 
        "facebook.com", "fb.watch", 
        "twitter.com", "x.com"
    ])
    
    if "instagram.com" in url:
        st.success("🎯 Detected Instagram link (Using parth-dl backend)")
        chosen_format_id = None
        selected_quality = "Best Available"

    elif is_ytdlp_platform:
        st.info("🔍 Fetching available video quality options from platform...")
        
        try:
            ydl_opts_info = {'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                formats = info_dict.get('formats', [])
            
            # Maps clean readable labels -> the real yt-dlp height number
            display_to_actual_height = {}
            
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('height'):
                    actual_height = int(f.get('height'))
                    
                    # Convert weird heights (like 1200) to standard labels (like 1080p)
                    clean_label = get_standard_label(actual_height)
                    
                    # Store the highest exact resolution matched to that standard label
                    if clean_label not in display_to_actual_height:
                        display_to_actual_height[clean_label] = actual_height
                    else:
                        if actual_height > display_to_actual_height[clean_label]:
                            display_to_actual_height[clean_label] = actual_height
            
            if display_to_actual_height:
                # Sort the standard labels from highest to lowest quality numerical value
                sorted_labels = sorted(
                    list(display_to_actual_height.keys()), 
                    key=lambda x: int(x.replace('p', '')), 
                    reverse=True
                )
                
                selected_quality = st.selectbox("Select Video Quality:", sorted_labels)
                
                # Fetch the actual raw height needed to construct the yt-dlp string
                target_height = display_to_actual_height[selected_quality]
                chosen_format_id = f"bestvideo[height={target_height}]+bestaudio/best"
            else:
                st.warning("Could not filter explicit resolutions. Defaulting to best automatic stream.")
                chosen_format_id = "best"
                selected_quality = "Best Dynamic"
                
        except Exception as e:
            st.error(f"Could not parse quality tracks: {str(e)}")
            chosen_format_id = "best"
            selected_quality = "Best Dynamic"
    else:
        st.error("❌ Unsupported URL. Please enter a valid Instagram, YouTube, Facebook, or Twitter/X link.")
        st.stop()

    if st.button("🚀 Fetch and Process Media"):
        with st.spinner("Downloading stream files from cloud..."):
            try:
                pre_existing = glob.glob("*.mp4") + glob.glob("*.jpg") + glob.glob("*.webp") + glob.glob("*.mkv")
                pre_existing_files = set(pre_existing)
                
                if "instagram.com" in url:
                    dl = InstagramDownloader()
                    dl.download(url)
                else:
                    st.info(f"Downloading stream in chosen quality: {selected_quality}...")
                    ydl_opts = {
                        'format': chosen_format_id,
                        'outtmpl': '%(title)s.%(ext)s',
                        'merge_output_format': 'mp4',
                        'noplaylist': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                
                current_files = set(glob.glob("*.mp4") + glob.glob("*.jpg") + glob.glob("*.webp") + glob.glob("*.mkv"))
                new_files = current_files - pre_existing_files
                
                if new_files:
                    latest_file = list(new_files)
                    
                    with open(latest_file, "rb") as f:
                        file_bytes = f.read()
                    
                    st.success("✅ File Prepared Successfully!")
                    
                    st.download_button(
                        label="💾 Download File to Device",
                        data=file_bytes,
                        file_name=os.path.basename(latest_file),
                        mime="video/mp4"
                    )
                    
                    os.remove(latest_file)
                else:
                    st.error("Could not locate the generated media file on the local file system path.")
                    
            except Exception as e:
                st.error(f"An unexpected download error occurred: {str(e)}")
else:
    st.warning("Please paste a link to get started.")
