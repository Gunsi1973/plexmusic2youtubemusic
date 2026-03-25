import os
import re
import sys
import json
import difflib
import questionary
from ytmusicapi import YTMusic
from colorama import init, Fore, Style

# Initialize Colorama
init()

MISSING_FILE = 'missing_tracks.txt'

def setup_ytmusic():
    with open("browser.json", "r", encoding="utf-8") as f:
        auth_dict = json.load(f)
    return YTMusic(auth=auth_dict)

def calculate_similarity(target_artist, target_title, yt_result):
    yt_title = yt_result.get('title', '').lower()
    yt_artists = yt_result.get('artists', [{'name': ''}])
    yt_artist_name = yt_artists[0]['name'].lower() if yt_artists else ''
    
    t_artist = target_artist.lower()
    t_title = target_title.lower()
    
    # Artist similarity (1.0 if one contains the other)
    if t_artist in yt_artist_name or yt_artist_name in t_artist:
        artist_score = 1.0
    else:
        artist_score = difflib.SequenceMatcher(None, t_artist, yt_artist_name).ratio()
        
    # Title similarity (1.0 if one contains the other)
    if t_title in yt_title or yt_title in t_title:
        title_score = 1.0
    else:
        title_score = difflib.SequenceMatcher(None, t_title, yt_title).ratio()
    
    # Heavy weight on the artist (70%) to filter out cover bands and karaoke versions
    return (artist_score * 0.7) + (title_score * 0.3)

def parse_duration(duration_str):
    if duration_str == "Unknown" or not duration_str:
        return None
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        pass
    return None

def update_missing_file(tracks):
    with open(MISSING_FILE, 'w', encoding='utf-8') as f:
        for track in tracks:
            f.write(f"{track}\n")

def resolve_missing():
    if not os.path.exists(MISSING_FILE):
        print(f"{Fore.GREEN}No '{MISSING_FILE}' found. Everything seems to be synced!{Style.RESET_ALL}")
        return

    with open(MISSING_FILE, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print(f"{Fore.GREEN}'{MISSING_FILE}' is empty.{Style.RESET_ALL}")
        return

    print("Connecting to YouTube Music...")
    try:
        yt = setup_ytmusic()
    except Exception as e:
        print(f"{Fore.RED}Error loading authentication: {e}{Style.RESET_ALL}")
        return

    print("Loading your playlists to map internal IDs...")
    yt_playlists = yt.get_library_playlists(limit=1000)
    yt_playlist_dict = {p['title']: p['playlistId'] for p in yt_playlists}

    pattern = re.compile(r"^(.*?)\s+-\s+(.*?)\s+\|\s+(.*?)\s+\(Playlist:\s+(.*?)\)$")
    remaining_tracks = lines.copy()

    for line in lines:
        match = pattern.match(line)
        if not match:
            print(f"{Fore.YELLOW}Could not parse line format, skipping: {line}{Style.RESET_ALL}")
            continue

        artist, title, duration_str, playlist_name = match.groups()
        target_duration_sec = parse_duration(duration_str)
        
        playlist_id = yt_playlist_dict.get(playlist_name)
        if not playlist_id:
            print(f"{Fore.RED}Playlist '{playlist_name}' not found on YouTube Music. Skipping track.{Style.RESET_ALL}")
            continue

        print(f"\n{'='*60}")
        print(f"Target: {Fore.CYAN}{artist} - {title}{Style.RESET_ALL} | Duration: {Fore.CYAN}{duration_str}{Style.RESET_ALL} (for playlist '{playlist_name}')")
        
        search_query = f"{artist} {title}"
        # Increased limit to 20 to fetch more candidates, then sort the best ones to the top
        results = yt.search(search_query, filter="songs", limit=20)

        if not results:
            print(f"{Fore.RED}No results found on YouTube Music for this query.{Style.RESET_ALL}")
            # If no results exist, we should probably keep it in the list or skip it.
            # We'll leave it in the list so the user can manually search YT later.
            continue

        results.sort(key=lambda r: calculate_similarity(artist, title, r), reverse=True)

        choices = []
        for res in results[:10]: # Only show the top 10 best matches after sorting to avoid clutter
            res_title = res.get('title', 'Unknown')
            res_artists = res.get('artists', [{'name': 'Unknown'}])
            res_artist_name = res_artists[0]['name'] if res_artists else 'Unknown'
            res_duration = res.get('duration', '?:??')
            res_duration_sec = res.get('duration_seconds')
            
            album_info = res.get('album')
            res_album = album_info.get('name', 'Unknown Album') if album_info else 'No Album'
            
            match_indicator = ""
            if target_duration_sec and res_duration_sec:
                if abs(target_duration_sec - res_duration_sec) <= 5:
                    match_indicator = " [*** PERFECT TIME MATCH ***]"
            
            display_text = f"{res_artist_name} - {res_title} | Duration: {res_duration}{match_indicator} | Album: {res_album}"
            choices.append(questionary.Choice(title=display_text, value=res['videoId']))
        
        choices.append(questionary.Choice(title="--> Skip and REMOVE this track from list", value="SKIP"))

        selected_video_id = questionary.select(
            "Select the correct matching track:",
            choices=choices
        ).ask()

        if selected_video_id is None:
            print(f"\n{Fore.YELLOW}Script aborted by user. Progress has been saved.{Style.RESET_ALL}")
            sys.exit(0)

        if selected_video_id != "SKIP":
            yt.add_playlist_items(playlist_id, [selected_video_id])
            print(f"{Fore.GREEN}-> Track successfully added to '{playlist_name}'.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}-> Skipped. Track removed from missing list.{Style.RESET_ALL}")
            
        # Remove from tracking list and save immediately (applies to both ADD and SKIP)
        remaining_tracks.remove(line)
        update_missing_file(remaining_tracks)

    print(f"\n{Fore.GREEN}Review complete. '{MISSING_FILE}' has been updated with {len(remaining_tracks)} remaining tracks.{Style.RESET_ALL}")

if __name__ == "__main__":
    resolve_missing()