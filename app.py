import streamlit as st
import random
import time
import os
import json
import datetime
import pygame

# === Initialize audio ===
# pygame.mixer.init()  # TODO Couldn't open audio device: No such file or directory

# === Constants ===
TONALITIES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
CADENCES = ['I-IV-V-I', 'I-V-I', 'II-V-I']
NOTES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
AUDIO_DIR = 'audio'
ROUNDS_PER_SESSION = 20
SESSION_LOG = 'session_data.json'

# === Load session stats ===


def load_session_data():
    if os.path.exists(SESSION_LOG):
        with open(SESSION_LOG, 'r') as f:
            return json.load(f)
    return []


def save_session_data(data):
    with open(SESSION_LOG, 'w') as f:
        json.dump(data, f, indent=2)

# === Play WAV file ===


def play_sound(filename):
    # TODO
    # pygame.mixer.music.load(filename)
    # pygame.mixer.music.play()
    # while pygame.mixer.music.get_busy():
    time.sleep(0.1)


# === App State ===
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "current_note" not in st.session_state:
    st.session_state.current_note = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# === Sidebar controls ===
st.sidebar.title("Pitch Trainer Settings")
tonality = st.sidebar.selectbox("Tonality (Major/Minor)", TONALITIES, index=0)
cadence_types = st.sidebar.multiselect(
    "Cadence types", CADENCES, default=["I-IV-V-I", "I-V-I"])
enabled_notes = st.sidebar.multiselect(
    "Notes to guess from", NOTES, default=NOTES)
start_button = st.sidebar.button("🎵 Start Next Round")

# === Game logic ===
st.title("🎶 Pitch Recognition Trainer")
if len(st.session_state.rounds) >= ROUNDS_PER_SESSION:
    st.success("Session complete!")
    correct = sum(1 for r in st.session_state.rounds if r["correct"])
    st.write(f"✅ You got {correct} out of {ROUNDS_PER_SESSION} correct.")
    if st.button("Start New Session"):
        all_sessions = load_session_data()
        all_sessions.append({
            "timestamp": str(datetime.datetime.now()),
            "results": st.session_state.rounds
        })
        save_session_data(all_sessions)
        st.session_state.rounds = []

elif start_button:
    if not enabled_notes:
        st.warning("Please select at least one note.")
    elif not cadence_types:
        st.warning("Please select at least one cadence.")
    else:
        chosen_cadence = random.choice(cadence_types)
        # cadence_file = f"{AUDIO_DIR}/{chosen_cadence}_{tonality}.wav"
        target_note = random.choice(enabled_notes)
        # note_file = f"{AUDIO_DIR}/{target_note}.wav"
        st.session_state.current_note = target_note
        st.session_state.start_time = time.time()

        st.write(f"🎧 Playing cadence: `{chosen_cadence}` in `{tonality}`...")
        # play_sound(cadence_file)
        time.sleep(0.5)
        st.write("🎵 Guess this note!")
        # play_sound(note_file)

# === User response ===
if st.session_state.current_note:
    guess = st.text_input("Which note did you hear?", max_chars=2)
    if guess:
        elapsed = time.time() - st.session_state.start_time
        is_correct = guess.strip().upper() == st.session_state.current_note.upper()
        st.session_state.rounds.append({
            "guess": guess.strip().upper(),
            "target": st.session_state.current_note,
            "correct": is_correct,
            "time": elapsed
        })
        st.write(
            "✅ Correct!" if is_correct else f"❌ Wrong! It was {st.session_state.current_note}")
        st.session_state.current_note = None
