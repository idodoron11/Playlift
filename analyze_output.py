import json

with open("output.log", "r") as f:
    lines = f.readlines()
unmatched_tracks_jsons = []
for index, line in enumerate(lines):
    if "Could not match" in line:
        track_json = "".join(lines[index+1:index+9])
        json_start_idx = track_json.find("{")
        track_json = track_json[json_start_idx:]
        unmatched_tracks_jsons.append(json.loads(track_json))

print("\n".join(map(lambda t: t["track id"], unmatched_tracks_jsons)))