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
import base64


# === Constants ===
TONALITIES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
CADENCES = ['I-IV-V-I', 'I-V-I', 'II-V-I']
NOTE_NAMES = ['C4', 'C#4', 'D4', 'Eb4', 'E4',
              'F4', 'F#4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4']
AUDIO_DIR = 'audio'
ROUNDS_PER_SESSION = 3
TIME_TO_GUESS = 6
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


def concat_and_play(cadence_file, note_name):

    if not (os.path.exists(cadence_file)):
        st.error(f"Missing audio file: {cadence_file}")

    # Load cadence
    cadence_audio, sr1 = sf.read(cadence_file)

    # Generate note
    note_audio = generate_tone(note_name)

    # Reshape if needed (cadence might be stereo)
    if len(cadence_audio.shape) == 2:  # Stereo
        note_audio = np.column_stack([note_audio, note_audio])

    # Concatenate
    full_audio = np.concatenate([cadence_audio, note_audio])

    # Export to buffer
    buffer = io.BytesIO()
    sf.write(buffer, full_audio, SAMPLE_RATE, format='WAV')

    # Embed audio in HTML
    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{base64.b64encode(buffer.getvalue()).decode()}" type="audio/wav">
        </audio>
        """,
        unsafe_allow_html=True
    )


# === Load/save sessions ===
def load_session_data():
    if os.path.exists(SESSION_LOG):
        with open(SESSION_LOG, 'r') as f:
            return json.load(f)
    return []


def save_session_data(data):
    with open(SESSION_LOG, 'w') as f:
        json.dump(data, f, indent=2)


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
            st.rerun()

    else:
        round_num = st.session_state.round_index + 1
        st.subheader(f"🎧 Round {round_num} of {ROUNDS_PER_SESSION}")

        if st.session_state.next_round_trigger:
            st.session_state.submitted = None

            chosen_cadence = random.choice(cadence_types)
            chosen_tonality = random.choice(tonality)
            cadence_file = f"{AUDIO_DIR}/{chosen_cadence}_{chosen_tonality}.wav"

            note = random.choice(selected_notes)
            st.session_state.current_note = note
            concat_and_play(cadence_file, note)

            st.session_state.start_time = time.time()
            st.session_state.next_round_trigger = False

        else:
            # Check if timeout expired
            elapsed = time.time() - st.session_state.start_time
            timeout = elapsed > TIME_TO_GUESS
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
                    st.warning(
                        f"⏱️ Timed out! It was {st.session_state.current_note}")
                elif correct:
                    st.success(
                        f"✅ Correct! It was {st.session_state.current_note}")
                else:
                    st.error(
                        f"❌ Wrong! It was {st.session_state.current_note}")
                time.sleep(1.2)

                st.session_state.round_index += 1
                st.session_state.next_round_trigger = True
                st.rerun()

else:
    st.info(
        f"Click **Start Session** to begin {ROUNDS_PER_SESSION} rounds of pitch guessing.\nYou have less than {TIME_TO_GUESS} seconds to guess")
