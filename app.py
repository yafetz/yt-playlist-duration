from datetime import timedelta
import re
import os
from flask import Flask, Response, request, render_template
from googleapiclient.discovery import build
import requests
import json
import datetime
import isodate


api_key = os.environ['APIS'].strip('][').split(',')

# get the playlistid from the link
def get_id(playlist_link):
    p = re.compile('^([\S]+list=)?([\w_-]+)[\S]*$')
    m = p.match(playlist_link)
    if m:
        return m.group(2)
    else:
        return 'invalid_playlist_link'




app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def home():
    if(request.method == 'GET'):
        return render_template("home.html")

    else:
        playlist_link = request.form.get('search_string').strip()
        playlist_id = get_id(playlist_link)
        test = ''.join(playlist_id)
        

        youtube = build('youtube', 'v3', developerKey=api_key)

        hours_pattern = re.compile(r'(\d+)H')
        minutes_pattern = re.compile(r'(\d+)M')
        seconds_pattern = re.compile(r'(\d+)S')

        total_seconds = 0

        nextPageToken = None
        while True:
            pl_request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=500,
                pageToken=nextPageToken
            )

            pl_response = pl_request.execute()

            vid_ids = []
            for item in pl_response['items']:
                vid_ids.append(item['contentDetails']['videoId'])

            vid_request = youtube.videos().list(
                part="contentDetails",
                id=','.join(vid_ids)
            )

            vid_response = vid_request.execute()

            for item in vid_response['items']:
                duration = item['contentDetails']['duration']

                hours = hours_pattern.search(duration)
                minutes = minutes_pattern.search(duration)
                seconds = seconds_pattern.search(duration)

                hours = int(hours.group(1)) if hours else 0
                minutes = int(minutes.group(1)) if minutes else 0
                seconds = int(seconds.group(1)) if seconds else 0

                video_seconds = timedelta(
                    hours=hours,
                    minutes=minutes,
                    seconds=seconds
                ).total_seconds()

                total_seconds += video_seconds

            nextPageToken = pl_response.get('nextPageToken')

            if not nextPageToken:
                break

        total_seconds = int(total_seconds)

        time = str(datetime.timedelta(seconds=total_seconds))

        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        display_text = 'Total length of videos: ' + time

        return render_template("home.html", display_text=display_text)


@app.errorhandler(500)
def internal_error(error):
    display_text = 'Invalid link'
    return render_template("home.html", display_text=display_text)


@app.errorhandler(404)
def not_found(error):
    display_text = 'Invalid link'
    return render_template("home.html", display_text=display_text)


if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)
