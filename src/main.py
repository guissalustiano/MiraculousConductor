from note_processing import extract_notes
from moviepy.editor import VideoFileClip, concatenate_videoclips

def play_istrument(notes, music):
    for note in music:
        yield notes[note]

if __name__ == "__main__":
    video = VideoFileClip("../video.mp4")
    notes = extract_notes(video)
    music = [60, 62, 64, 65, 65, 65, 60, 62, 60, 62, 62, 62, 60, 67, 65, 64, 64, 64, 60, 62, 64, 65, 65, 65]
    
    concatenate_videoclips(list(play_istrument(notes, music))).write_videofile('firstMusic.mp4')


