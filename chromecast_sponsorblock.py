from datetime import timedelta
import time
import pychromecast
from pychromecast.controllers.youtube import YouTubeController
import sponsorblock as sb

sb_client = sb.Client()

CAST_NAME = 'GR Holo Cast'

def find_chromecast():
    chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[CAST_NAME], discovery_timeout=30)
    cast = chromecasts[0]
    cast.wait()
    time.sleep(1)
    return cast

def get_sponsorblock_segments(video_id):
    return sb_client.get_skip_segments(video_id)

content_id = ''
sponsor_segments = []
last_player_state = 'BUFFERING'
last_time = 0.0

if __name__ == '__main__':
    cast = find_chromecast()
    print("Chromecast found!")
    yt = YouTubeController()
    cast.register_handler(yt)
    while True:
        status = cast.media_controller.status
        print(f"[{status.current_time}] {status.player_state} {status.content_id} ({status.title}) [{round(status.volume_level, 2)}, {status.volume_muted}]")

        # Update video id if changed + get sponsor segments
        if content_id != status.content_id:
            content_id = status.content_id
            sponsor_segments = get_sponsorblock_segments(content_id)
            print(sponsor_segments)

        # Mute in ads
        if last_player_state != 'BUFFERING' and status.player_state == 'BUFFERING':
            print('Ad detected, muting...')
            cast.set_volume_muted(True)
        if last_player_state == 'BUFFERING' and status.player_state != 'BUFFERING':
            print('Ad over, unmuting...')
            cast.set_volume_muted(False)

        # Sponsorblock skips
        for segment in sponsor_segments:
            if segment.duration.seconds > 5:
                if last_time < segment.start and status.current_time > segment.start:
                    print(f"Skipping sponsor [{segment.start}-{segment.end}]")
                    cast.media_controller.seek(segment.end)
                    time.sleep(5)

        last_player_state = status.player_state
        last_time = status.current_time
        time.sleep(3)
        cast.media_controller.update_status()
