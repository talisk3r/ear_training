import streamlit as st
import random
import time
import os
import json
import datetime
import pygame

# === Constants ===
TONALITIES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
CADENCES = ['I-IV-V-I', 'I-V-I', 'II-V-I']
NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
AUDIO_DIR = 'audio'
ROUNDS_PER_SESSION = 20
SESSION_LOG = 'session_data.json'

# === Init Pygame mixer ===
# pygame.mixer.init()

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


def play_sound(filename):
    # if os.path.exists(filename):
    # pygame.mixer.music.load(filename)
    # pygame.mixer.music.play()
    # while pygame.mixer.music.get_busy():
    time.sleep(0.1)
    # else:
    # st.error(f"Missing audio file: {filename}")


# === Init session state ===
st.set_page_config("Pitch Trainer", layout="wide")

if "session_active" not in st.session_state:
    st.session_state.session_active = False
    st.session_state.rounds = []
    st.session_state.round_index = 0
    st.session_state.current_note = None
    st.session_state.start_time = None
    st.session_state.next_round_trigger = False
    st.session_state.enabled_notes = NOTE_NAMES.copy()

# === Sidebar controls ===
st.sidebar.title("🎵 Pitch Trainer Settings")

tonality = st.sidebar.selectbox("Tonality", TONALITIES, index=0)
cadence_types = st.sidebar.multiselect(
    "Cadence types", CADENCES, default=["I-IV-V-I", "I-V-I"])

# Piano-style keyboard note selection
st.sidebar.markdown("### Select Notes to Guess")
cols = st.sidebar.columns(len(NOTE_NAMES))
enabled_set = set(st.session_state.enabled_notes)

for i, note in enumerate(NOTE_NAMES):
    label = f"{'✅' if note in enabled_set else '❌'} {note}"
    if cols[i].button(label, key=f"note_{note}"):
        if note in enabled_set:
            enabled_set.remove(note)
        else:
            enabled_set.add(note)

st.session_state.enabled_notes = sorted(enabled_set)

# Start session button
if st.sidebar.button("🎯 Start Session", disabled=st.session_state.session_active):
    if not st.session_state.enabled_notes:
        st.sidebar.error("Select at least one note.")
    elif not cadence_types:
        st.sidebar.error("Select at least one cadence.")
    else:
        st.session_state.session_active = True
        st.session_state.rounds = []
        st.session_state.round_index = 0
        st.session_state.next_round_trigger = True
        st.experimental_rerun()

# === App title ===
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
            st.experimental_rerun()
    else:
        round_num = st.session_state.round_index + 1
        st.subheader(f"🎧 Round {round_num} of {ROUNDS_PER_SESSION}")

        if st.session_state.next_round_trigger:
            chosen_cadence = random.choice(cadence_types)
            cadence_file = f"{AUDIO_DIR}/{chosen_cadence}_{tonality}.wav"
            note = random.choice(st.session_state.enabled_notes)
            note_file = f"{AUDIO_DIR}/{note}.wav"
            st.session_state.current_note = note
            st.session_state.start_time = time.time()

            with st.spinner(f"Playing cadence `{chosen_cadence}` in `{tonality}`..."):
                play_sound(cadence_file)
            time.sleep(0.5)
            st.audio(note_file)
            st.session_state.next_round_trigger = False
            st.experimental_rerun()

        # Check if timeout expired
        elapsed = time.time() - st.session_state.start_time
        timeout = elapsed > 3

        guess = st.text_input("Which note did you hear?",
                              key=f"guess_{round_num}")
        submitted = st.button("Submit Guess")

        if timeout or submitted:
            final_guess = guess.strip().upper() if guess and not timeout else "?"
            correct = final_guess == st.session_state.current_note
            st.session_state.rounds.append({
                "guess": final_guess,
                "target": st.session_state.current_note,
                "correct": correct,
                "time": elapsed
            })

            feedback = "✅ Correct!" if correct else f"❌ Wrong! It was {st.session_state.current_note}" if final_guess != "?" else "⏱️ Timed out!"
            st.write(feedback)

            st.session_state.round_index += 1
            st.session_state.next_round_trigger = True
            time.sleep(1.5)
            st.experimental_rerun()
else:
    st.info("Click **Start Session** to begin 20 rounds of pitch guessing.")
