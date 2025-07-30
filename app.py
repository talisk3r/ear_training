# Usage
# streamlit run app.py

import io
import soundfile as sf
import numpy as np
import streamlit as st
import random
import time
import os
import json
import datetime


# === Constants ===
TONALITIES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
CADENCES = ['I-IV-V-I', 'I-V-I', 'II-V-I']
NOTE_NAMES = ['C4', 'C#4', 'D4', 'Eb4', 'E4',
              'F4', 'F#4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4']
AUDIO_DIR = 'audio'
ROUNDS_PER_SESSION = 3
SESSION_LOG = 'session_data.json'

# === Tone generaton ===
SAMPLE_RATE = 44100
DURATION = 0.2  # seconds

NOTE_FREQS = {
    'C4': 261.63,
    'C#4': 277.18,
    'D4': 293.66,
    'Eb4': 311.13,
    'E4': 329.63,
    'F4': 349.23,
    'F#4': 369.99,
    'G4': 392.00,
    'Ab4': 415.30,
    'A4': 440.00,
    'Bb4': 466.16,
    'B4': 493.88,
}


def generate_tone(note_name, duration=DURATION, sample_rate=SAMPLE_RATE):
    freq = NOTE_FREQS[note_name]
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = 0.5 * np.sin(2 * np.pi * freq * t)
    return tone.astype(np.float32)


def note_to_wav(note_name):
    audio_data = generate_tone(note_name)
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, SAMPLE_RATE, format='WAV')
    return buffer.getvalue()


# === Load/save sessions ===
def load_session_data():
    if os.path.exists(SESSION_LOG):
        with open(SESSION_LOG, 'r') as f:
            return json.load(f)
    return []


def save_session_data(data):
    with open(SESSION_LOG, 'w') as f:
        json.dump(data, f, indent=2)


# === Play WAV file ===
def play_wave_file(filename):
    if os.path.exists(filename):
        st.audio(filename, format="audio/wav")
    else:
        st.error(f"Missing audio file: {filename}")


# === Init session state ===
st.set_page_config("Pitch Trainer", layout="wide")

# === Sidebar controls ===
st.sidebar.title("🎵 Pitch Trainer Settings")

tonality = st.sidebar.multiselect("Tonality", TONALITIES, default=['C'])

cadence_types = st.sidebar.multiselect(
    "Cadence types", CADENCES, default=["I-V-I"])

selected_notes = st.sidebar.multiselect(
    "Enabled notes", NOTE_NAMES, default=['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4'])


if "session_active" not in st.session_state:
    st.session_state.session_active = False
    st.session_state.rounds = []
    st.session_state.round_index = 0
    st.session_state.current_note = None
    st.session_state.start_time = None
    st.session_state.next_round_trigger = False
    st.session_state.submitted = None


# Piano-style keyboard note selection
st.sidebar.markdown("### Your input - Which note do you hear?")
cols = st.sidebar.columns(len(NOTE_NAMES))

for i, note in enumerate(NOTE_NAMES):
    if cols[i].button(note, key=f"note_{note}"):
        st.session_state.submitted = note


# Start session button
if st.sidebar.button("🎯 Start Session", disabled=st.session_state.session_active):
    if not selected_notes:
        st.sidebar.error("Select at least one note.")
    elif not cadence_types:
        st.sidebar.error("Select at least one cadence.")
    elif not tonality:
        st.sidebar.error("Select at least one tonality.")
    else:
        st.session_state.session_active = True
        st.session_state.rounds = []
        st.session_state.round_index = 0
        st.session_state.next_round_trigger = True

# === Main title ===
st.title("🎶 Pitch Recognition Trainer")

# === Game logic ===
if st.session_state.session_active:
    if st.session_state.round_index >= ROUNDS_PER_SESSION:
        st.success("✅ Session complete!")
        correct = sum(1 for r in st.session_state.rounds if r["correct"])
        st.write(f"You got {correct} out of {ROUNDS_PER_SESSION} correct.")

        all_sessions = load_session_data()
        all_sessions.append({
            "timestamp": str(datetime.datetime.now()),
            "results": st.session_state.rounds
        })
        save_session_data(all_sessions)

        if st.button("🔁 Start New Session"):
            st.session_state.session_active = False
            st.session_state.round_index = 0
            st.session_state.rounds = []

    else:
        round_num = st.session_state.round_index + 1
        st.subheader(f"🎧 Round {round_num} of {ROUNDS_PER_SESSION}")

        if st.session_state.next_round_trigger:
            chosen_cadence = random.choice(cadence_types)
            chosen_tonality = random.choice(tonality)
            cadence_file = f"{AUDIO_DIR}/{chosen_cadence}_{chosen_tonality}.wav"

            note = random.choice(selected_notes)
            note_audio = note_to_wav(note)

            st.session_state.current_note = note
            st.session_state.submitted = None

            play_wave_file(cadence_file)

            time.sleep(0.2)

            st.audio(note_audio, format="audio/wav")
            st.session_state.start_time = time.time()
            st.session_state.next_round_trigger = False

        else:
            # Check if timeout expired
            elapsed = time.time() - st.session_state.start_time
            timeout = elapsed > 3
            user_guess = st.session_state.submitted

            if timeout or user_guess:
                final_guess = user_guess if user_guess and not timeout else "?"
                correct = final_guess == st.session_state.current_note
                st.session_state.rounds.append({
                    "guess": final_guess,
                    "target": st.session_state.current_note,
                    "correct": correct,
                    "time": elapsed
                })

                if final_guess == "?":
                    st.warning("⏱️ Timed out!")
                elif correct:
                    st.success("✅ Correct!")
                else:
                    st.error(
                        f"❌ Wrong! It was {st.session_state.current_note}")

                st.session_state.round_index += 1
                st.session_state.next_round_trigger = True
                time.sleep(1.5)
else:
    st.info("Click **Start Session** to begin 20 rounds of pitch guessing.")
