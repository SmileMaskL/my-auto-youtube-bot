def post_comment(video_id, text):
    youtube = build("youtube", "v3", credentials=creds)
    
    comment_body = {
        "snippet": {
            "videoId": video_id,
            "textOriginal": text
        }
    }

    comment_request = youtube.commentThreads().insert(
        part="snippet",
        body=comment_body
    )
    
    comment_response = comment_request.execute()
    print(f"댓글이 성공적으로 게시되었습니다: {comment_response['snippet']['topLevelComment']['snippet']['textDisplay']}")

