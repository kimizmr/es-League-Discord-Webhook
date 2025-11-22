import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# Your Discord webhook URL
webhook_url = "https://discord.com/api/webhooks/1439977725157703700/rxAQax9ieAcZYasjf7B6mGxEB7Tf3Ut6uijzbRvtyTaBEHSx1cFLxAfR7_-oN9M2UinG"

# Your team name
your_team = "Los Primos VFC"

# URLs
club_profile_url = "https://es-league.games/malaysia/fifa/club/?clubno=716"
matches_url = "https://es-league.games/malaysia/fifa/league/date.php?leagueno=0397"

# Optional: Use local HTML file as fallback (set use_local_file = True)
use_local_file = False
local_file_path = "es-League-matches.html"

# === SCRAPE CLUB PROFILE ===
print("[*] Fetching club profile...")
try:
    club_res = requests.get(club_profile_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    club_res.raise_for_status()
    club_soup = BeautifulSoup(club_res.text, "html.parser")
except requests.exceptions.RequestException as e:
    print(f"[ERROR] Error fetching club profile: {e}")
    exit(1)

# === CLUB BASIC INFO ===
try:
    club_name_elem = club_soup.find("div", class_="club-contents-area-data-main-name")
    club_name = club_name_elem.text.strip() if club_name_elem else your_team
except:
    club_name = your_team

try:
    since_elem = club_soup.find("div", class_="club-contents-area-data-main-text")
    since = since_elem.text.strip() if since_elem else "Unknown"
except:
    since = "Unknown"

try:
    ranking_elem = club_soup.find("div", class_="club-contents-area-data-es-ranking")
    ranking = ranking_elem.text.strip() if ranking_elem else "Unknown"
except:
    ranking = "Unknown"

try:
    logo_div = club_soup.find("div", class_="club-contents-area-data-image")
    if logo_div:
        img_tag = logo_div.find("img")
        if img_tag and img_tag.get("src"):
            logo_img = "https://es-league.games" + img_tag["src"].replace("../../../", "/")
        else:
            logo_img = None
    else:
        logo_img = None
except:
    logo_img = None

# === SUPPORTER COUNT ===
supporter_block = club_soup.find_all("div", class_="club-data-contents")
supporters = supporter_block[1].text.strip() if len(supporter_block) > 1 else "Unknown"

# === RECENT STATS (NATIONAL TAB) ===
stats_tab = club_soup.find("div", id="data01")
recent_stats = {}

if stats_tab:
    for blk in stats_tab.find_all("div", class_="club-contents-area-data-score-block"):
        title = blk.find("div", class_="club-contents-area-data-score-title").text.strip()
        value = blk.find("div", class_="club-contents-area-data-score-number").text.strip()
        recent_stats[title] = value

# === PREVIOUS MATCH RESULTS ===
prev_matches_raw = club_soup.find_all("div", class_="club-versus-area")
prev_matches = []

for m in prev_matches_raw[:2]:  # take 2 latest
    try:
        tournament_elem = m.find("div", class_="club-versus-title")
        opponent_elem = m.find("div", class_="mt3")
        score_elem = m.find("div", class_="club-versus-result-score")
        
        if tournament_elem and opponent_elem and score_elem:
            tournament = tournament_elem.text.strip()
            opponent = opponent_elem.text.strip()
            score = score_elem.text.strip()
            prev_matches.append(f"🏆 **{tournament}**\n⚔️ *vs {opponent}* → **{score}**")
    except:
        continue

# === PARSE MATCHES HTML ===
print("[*] Fetching matches data...")
if use_local_file:
    try:
        with open(local_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
    except FileNotFoundError:
        print(f"[ERROR] Local file not found: {local_file_path}")
        exit(1)
else:
    try:
        res = requests.get(matches_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error fetching matches: {e}")
        exit(1)

# === EXTRACT LEAGUE TITLE ===
league_title = "eS-League Malaysia"
title_elem = soup.find("title")
if title_elem:
    league_title = title_elem.text.strip().replace(" | FIFA", "")

# === EXTRACT DATE GROUPS ===
date_groups = []
date_blocks = soup.find_all("div", class_="comps-match-list-data")
for block in date_blocks:
    name_elem = block.find("div", class_="comps-match-list-data-name")
    date_elem = block.find("div", class_="comps-match-list-data-date")
    if name_elem and date_elem:
        date_groups.append({
            "name": name_elem.text.strip(),
            "date": date_elem.text.strip()
        })

# === EXTRACT MATCHES BY GROUP ===
all_matches = []
group_tabs = soup.find_all("div", class_="menu-open-tab")

for group_tab in group_tabs:
    group_name = group_tab.text.strip()
    group_div = group_tab.find_next_sibling("div")
    
    if not group_div:
        continue
    
    matches = []
    match_areas = group_div.find_all("div", class_="comps-match-schedule-area")
    
    for match_area in match_areas:
        # Get team names
        club_areas = match_area.find_all("div", class_="comps-match-list-club-area")
        team1_name = ""
        team2_name = ""
        
        if len(club_areas) >= 2:
            team1_elem = club_areas[0].find("div", class_="comps-match-list-club-name")
            team2_elem = club_areas[1].find("div", class_="comps-match-list-club-name")
            
            if team1_elem:
                team1_name = team1_elem.text.strip()
            if team2_elem:
                team2_name = team2_elem.text.strip()
        
        # Get score
        vs_elem = match_area.find("div", class_="comps-match-list-vs")
        score = "TBD"
        if vs_elem:
            score_link = vs_elem.find("a")
            if score_link:
                score = score_link.text.strip()
        
        if team1_name and team2_name:
            matches.append({
                "team1": team1_name,
                "team2": team2_name,
                "score": score
            })
    
    if matches:
        all_matches.append({
            "group": group_name,
            "matches": matches
        })

# === HELPER FUNCTIONS ===
def is_upcoming(score):
    """Check if match is upcoming (not yet played)"""
    if score == "TBD":
        return True
    # If score contains numbers separated by dash, it's a completed match
    if " - " in score and any(char.isdigit() for char in score):
        return False
    # If it's just "vs" or similar, it's upcoming
    return True

def extract_group_number(group_name):
    """Extract group number from group name (e.g., 'Group 1' from 'eS-League MALAYSIA S 17 Group 1')"""
    match = re.search(r'Group\s+(\d+)', group_name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def convert_date_format(date_str):
    """Convert date from mm.dd.yyyy to dd/mm/yyyy"""
    if not date_str:
        return None
    # Split by space to get just the date part (before time)
    date_part = date_str.split()[0] if " " in date_str else date_str
    # Split by dots to get [month, day, year]
    parts = date_part.split(".")
    if len(parts) == 3:
        # Reorder from mm.dd.yyyy to dd/mm/yyyy
        month, day, year = parts[0], parts[1], parts[2]
        return f"{day}/{month}/{year}"
    # Fallback: just replace dots with slashes if format is unexpected
    return date_part.replace(".", "/")

def find_date_for_group(group_number, date_groups):
    """Find the date for a specific group number (returns only date, no time, in dd/mm/yyyy format)"""
    if not group_number:
        return None
    
    for dg in date_groups:
        # Check if group number is in the date group name (e.g., "Group 1・Group 2" contains Group 1)
        group_nums = re.findall(r'Group\s+(\d+)', dg['name'], re.IGNORECASE)
        if group_nums and any(int(gn) == group_number for gn in group_nums):
            # Extract only the date part (before the space/time)
            full_date = dg['date']
            # Split by space and take the first part (the date)
            date_only = full_date.split()[0] if full_date else None
            # Convert format from dd.mm.yyyy to dd/mm/yyyy
            return convert_date_format(date_only)
    return None

# === FILTER FOR YOUR TEAM'S UPCOMING MATCHES ===
upcoming_matches = []

for group_data in all_matches:
    group_number = extract_group_number(group_data["group"])
    match_date = find_date_for_group(group_number, date_groups) if group_number else None
    
    for match in group_data["matches"]:
        # Check if your team is in this match
        if your_team.lower() in match["team1"].lower() or your_team.lower() in match["team2"].lower():
            # Only include upcoming matches
            if is_upcoming(match["score"]):
                opponent = match["team2"] if your_team.lower() in match["team1"].lower() else match["team1"]
                upcoming_matches.append({
                    "group": group_data["group"],
                    "opponent": opponent,
                    "is_home": your_team.lower() in match["team1"].lower(),
                    "date": match_date
                })

# === FORMAT FOR DISCORD ===
# Limit to 4 upcoming matches
upcoming_matches = upcoming_matches[:4]

# === SINGLE EMBED WITH ALL INFO ===
club_embed = {
    "title": f"{club_name} — eS-League Info",
    "color": 0x00aaff,
    "fields": []
}

# Add thumbnail only if logo exists
if logo_img:
    club_embed["thumbnail"] = {"url": logo_img}

# Recent Stats
if recent_stats:
    stats_text = "\n".join([f"**{k}**: {v}" for k, v in recent_stats.items()])
    club_embed["fields"].append({
        "name": "📊 Recent Stats",
        "value": stats_text,
        "inline": False
    })

# Upcoming Matches
if upcoming_matches:
    matches_text = []
    for match in upcoming_matches:
        home_away = "🏠 Home" if match["is_home"] else "✈️ Away"
        date_str = f"\n   📅 {match['date']}" if match.get("date") else ""
        match_str = f"{home_away} vs **{match['opponent']}**\n   📍 {match['group']}{date_str}"
        matches_text.append(match_str)
    
    upcoming_text = "\n\n".join(matches_text)
    club_embed["fields"].append({
        "name": "🔜 Upcoming Matches",
        "value": upcoming_text if upcoming_text else "No upcoming matches found",
        "inline": False
    })
else:
    club_embed["fields"].append({
        "name": "🔜 Upcoming Matches",
        "value": "No upcoming matches found for your team.",
        "inline": False
    })

embeds = [club_embed]

# === SEND TO DISCORD ===
data = {
    "content": f" 📢 Info for **{club_name}**",
    "embeds": embeds
}

headers = {"Content-Type": "application/json"}
r = requests.post(webhook_url, data=json.dumps(data), headers=headers)

if r.status_code in [200, 204]:
    print("[OK] Sent to Discord Successfully!")
    print(f"[INFO] Club: {club_name}")
    print(f"[INFO] Found {len(upcoming_matches)} upcoming match(es) for {your_team}")
    print(f"[SENT] Sent 1 embed to Discord")
else:
    print(f"[ERROR] Error {r.status_code}: {r.text}")

