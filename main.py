import csv
import datetime
import env
import json
from dateutil.relativedelta import relativedelta
from urllib import request

# Constants
API_URL = 'https://www.googleapis.com/youtube/v3'

# 指定された期間のチャンネルのIDとタイトルを取得
def get_video_title_list(published_before, published_after):
  page_token = ''
  next_page_token = 'dummy for first'
  video_title_list = {}
  while page_token != next_page_token:
    search_request = request.urlopen(
      API_URL
      + '/search?channelId=' + env.CHANNEL_ID
      + '&key=' + env.API_KEY
      + '&part=id,snippet'
      + '&maxResults=50'
      + '&publishedBefore=' + published_before
      + '&publishedAfter=' + published_after
      + '&pageToken=' + page_token
    )
    response = search_request.read()
    data = json.loads(response)

    for d in data['items']:
      if 'videoId' in d['id']:
        video_title_list[d['id']['videoId']] = d['snippet']['title']

    page_token = next_page_token
    if 'nextPageToken' in data['items']:
      next_page_token = data['nextPageToken']

  return video_title_list

# IDとタイトルのリストからCSV出力用の動画情報を取得
def filter_video_list(video_title_list):
  video_list = []
  if len(video_title_list) > 0:
    # APIから動画の詳細情報を取得
    video_request = request.urlopen(
      API_URL
      + '/videos?part=snippet,statistics'
      + '&key=' + env.API_KEY
      + '&id=' + ','.join(video_title_list.keys())
    )
    response = video_request.read()
    data = json.loads(response)['items']

    for item in data:
      views = item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else '-'
      likes = item['statistics']['likeCount'] if 'likeCount' in item['statistics'] else '-'
      dislikes = item['statistics']['dislikeCount'] if 'dislikeCount' in item['statistics'] else '-'

      video_list.append({
        'published_at': item['snippet']['publishedAt'],
        'title': video_title_list[item['id']],
        'views': views,
        'likes': likes,
        'dislikes': dislikes
      })

  return video_list

# 指定された期間でCSV出力用の動画情報を取得
def get_video_list(published_before, published_after):
  video_title_list = get_video_title_list(published_before, published_after)
  video_list = filter_video_list(video_title_list)

  return video_list

# 実行関数
def main():
  target_title_list = []
  date = datetime.date.today()
  with open('./data/' + env.CHANNEL_ID + '.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['投稿日時', 'タイトル', '再生回数', 'LIKE数', 'DISLIKE数'])

    video_list = []
    for i in range(int(env.MONTHS)):
      published_before = date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
      date = date - relativedelta(months=1)
      published_after = date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
      video_list.extend(get_video_list(published_before, published_after))

    # 投稿日時順に並び替え
    sorted_video_list = sorted(video_list, key=lambda x:x['published_at'])
    for video in sorted_video_list:
      writer.writerow([video['published_at'], video['title'], video['views'], video['likes'], video['dislikes']])

main()
