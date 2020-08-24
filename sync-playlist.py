
from notion.client import NotionClient

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import toml
import json

import time

# config toml file
config_file = "notion-youtube.toml"

_config = {
    "token_v2": "",
    "notion_database_link": "",
    "api_service_name": "youtube",
    "api_version": "v3",
    "playlist_id" : "",
    "client_secrets_file": "",
    "scopes": ["https://www.googleapis.com/auth/youtube.force-ssl"]
}

def parse_toml():
    config = toml.load(config_file)
    for section in config:
        for name, value in config[section].items():
            _config[name] = value


def get_notion_video_ids():
    client = NotionClient(_config["token_v2"])
    cv = client.get_collection_view(_config["notion_database_link"])

    video_ids = set()
    for row in cv.collection.get_rows():
        if row.feeling_it:
            video_ids.add(row.youtube.split("v=")[1])
    return video_ids


def request_playlist_items():
    youtube = googleapiclient.discovery.build(
        _config["api_service_name"], _config["api_version"], developerKey=_config["api_key"]
        )

    request = youtube.playlistItems().list(
        part="contentDetails",
        maxResults=50,
        playlistId=_config["playlist_id"]
        )
    response = request.execute()
    return response

def response_to_file(response):
    text_file = open("output.json", "w")
    text_file.write(json.dumps(response, sort_keys=True, indent=2))
    text_file.close()


def extract_youtube_video_ids(response):
    id_set = set()
    for item in response["items"]:
        id_set.add(item["contentDetails"]["videoId"])

    return id_set


def make_play_list_item_id_dict():
    playlist_item_id_dict = {}
    for item in response["items"]:
        playlist_item_id_dict[item["contentDetails"]["videoId"]] = item["id"]
    return playlist_item_id_dict


def get_service_with_auth():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        _config["client_secrets_file"], _config["scopes"])
    credentials = flow.run_local_server()

    youtube = googleapiclient.discovery.build(
        _config["api_service_name"], _config["api_version"], credentials=credentials
        )
    return youtube


def insert_videos(youtube, id_list):
    print("Inserting...")
    if len(id_list) == 0:
        print("No videos to add to playlist")
        return

    for video_id in id_list:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": _config["playlist_id"],
                    "position": 0,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        request.execute()
        time.sleep(0.2) # No delay was causing some videos to be missed


def delete_videos(youtube, video_id_list, playlist_item_id_dict):
    print("Deleting...")
    if len(video_id_list)  == 0:
        print("No videos to delete from playlist")
        return

    for video_id in video_id_list:
        request = youtube.playlistItems().delete(
            id=playlist_item_id_dict[video_id]
            )
        request.execute()
        time.sleep(0.2) # No delay was causing some videos to be missed




def main():
    parse_toml()
    response = request_playlist_items()
    # response_to_file(response) # uncomment to see youtube response of playlist info

    notion_video_id_set = get_notion_video_ids()
    youtube_video_id_set = extract_youtube_video_ids(response)

    insert_list = list(notion_video_id_set - youtube_video_id_set)
    delete_list = list(youtube_video_id_set - notion_video_id_set)

    if len(insert_list) == 0 and len(delete_list) == 0:
        print("playlist already in sync. Returning...")
        return

    playlist_item_id_dict = make_play_list_item_id_dict(response)
    youtube = get_service_with_auth()

    insert_videos(youtube, insert_list)
    delete_videos(youtube, delete_list, playlist_item_id_dict)

    print("playlist now in sync.")


if __name__ == "__main__":
    main()