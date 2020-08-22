
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json

from notion.client import NotionClient

# Obtain the `token_v2` value by inspecting your browser cookies on a logged-in session on Notion.so
client = NotionClient("token_v2=your-token-v2-here")

# Notion Songs Database Link
cv = client.get_collection_view("your-youtube-videos-notion-database-link-here")

# Notion automated YouTube playlist id
playlist_id = "your-youtube-playlist-id-here"

def get_video_ids():
    video_ids = []
    for row in cv.collection.get_rows():
        if row.feeling_it:
            video_ids.append(row.youtube.split("v=")[1])
    return video_ids


def main():
    client_secrts_file = "client_secret.json"
    scopes =["https://www.googleapis.com/auth/youtube.force-ssl"]
    api_service_name = "youtube"
    api_version = "v3"

    # OAuth credentials
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrts_file, scopes)
    credentials = flow.run_local_server()

    # Get service
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    # insert videos from database into playlist
    video_id_list = get_video_ids()
    for video_id in video_id_list:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "position": 0,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()

if __name__ == "__main__":
    main()