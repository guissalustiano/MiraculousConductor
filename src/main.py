from note_processing import extract_notes
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, clips_array
from moviepy.video.fx.resize import resize
from pretty_midi import PrettyMIDI
import matplotlib.pyplot as plt
from random import randint
import numpy as np


def get_all_notes(instruments):
    all_notes = []
    for instrument in instruments:
        all_notes.extend(instrument.notes)
    return all_notes


def get_notes_timed(video_notes: dict, miti):
    music = get_all_notes(miti.instruments)
    music_limits = (min(*music, key=lambda note: note.pitch).pitch,
                    max(*music, key=lambda note: note.pitch).pitch)

    video_notes_limits = (min(video_notes.keys()), max(video_notes.keys()))
    print("music_limits:", music_limits)
    print("video_notes_limits:", video_notes_limits)

    if music_limits[1] - music_limits[0] > video_notes_limits[1] - video_notes_limits[0]:
        print("[x] Sem notas suficiente, notas serão cortadas")
        video_notes_range = video_notes_limits[1] - video_notes_limits[0]
        notes_count = np.dstack(
            np.unique([note.pitch for note in music], return_counts=True))[0]
        max_start = 0
        for i in range(len(notes_count) - video_notes_range):
            if notes_count[i: i + video_notes_range, 1].sum() > notes_count[max_start: max_start + video_notes_range, 1].sum():
                max_start = i
        print(
            f"[o] Maior numero de notas na faixa {max_start} - {max_start + video_notes_range}")
        new_botton_music_limit = notes_count[:, 0][max_start]
        up_pich_in = video_notes_limits[0] - new_botton_music_limit
        print("[o] Deslocando musica em ", up_pich_in)
        for note in music:
            note.pitch += up_pich_in
        print("[o] Removendo notas abaixo de ", video_notes_limits[0])
        len_music = len(music)
        music = [note for note in music if note.pitch in video_notes]
        print(f"[o] {len_music - len(music)} notas perdidas")
    print("[o] Projetando espaçamento")
    last_tick = miti.time_to_tick(miti.get_end_time())
    qtd_note = np.zeros(last_tick, dtype=np.int8)
    for note in music:
        qtd_note[miti.time_to_tick(
            note.start): miti.time_to_tick(note.end)] += 1

    qtd_max_video = np.max(qtd_note)
    print(f"[o] separando em {qtd_max_video} layers")

    layers = [[] for i in range(qtd_max_video)]

    ocupacoes = np.zeros((len(qtd_note), int(qtd_max_video)), dtype=bool)
    v_width, v_heigth = video_notes[music[0].pitch].size
    for note in sorted(music, key=lambda note: note.start):
        faixa_ocupada = ocupacoes[miti.time_to_tick(
            note.start): miti.time_to_tick(note.end)]
        faixa_ocupada_simplificada = np.all(
            faixa_ocupada == faixa_ocupada[0, :], axis=0)
        faixa_desocupada = list(faixa_ocupada_simplificada).index(True)

        # faixa_desocupada = randint(0, qtd_max_video - 1)
        layers[faixa_desocupada].append(
            video_notes[note.pitch]
            # .subclip(0, note.end)
            .set_start(note.start)
        )
        ocupacoes[miti.time_to_tick(note.start): miti.time_to_tick(
            note.end), faixa_desocupada] = 1
    return [layer for layer in layers if layer]  # remove empty layer


def reshape(lst, shape):
    if len(shape) == 1:
        return lst
    n = reduce(mul, shape[1:])
    return [reshape(lst[i*n:(i+1)*n], shape[1:]) for i in range(len(lst)//n)]


if __name__ == "__main__":
    print("[o] Lendo Video")
    video = VideoFileClip("../video.mp4")
    video_notes = extract_notes(video)
    print("[o] Lendo as Notas Musicais")
    miti = PrettyMIDI('../pirata.mid')

    print("[o] Sincronizando com a musica e crindo faixas")
    layers = get_notes_timed(video_notes, miti)

    for i in range(len(layers)):
        layers[i] = CompositeVideoClip(layers[i])

    qtd_layers = len(layers)
    while not (qtd_layers**0.5).is_integer():
        qtd_layers += 1
    qtd_layers_1D = int(qtd_layers**0.5)
    print(f"[o] Usando {qtd_layers} layers")
    final_layers = [[[] for i in range(qtd_layers_1D)] for j in range(qtd_layers_1D)]
    for i in range(len(final_layers)):
        for j in range(len(final_layers[0])):
            print(f"in for {i*qtd_layers_1D + j}")
            if i*qtd_layers_1D + j < len(layers):
                final_layers[i][j] = layers[i*qtd_layers_1D + j]
            else:
                final_layers[i][j] = video.subclip(0, 0.01)
    
    print("[o] Concatentando final")
    video = clips_array(final_layers)

    print("[o] Rendenizando")
    video.write_videofile('../pirata.mp4', threads=4)
