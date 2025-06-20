import streamlit as st
import sounddevice as sd
import numpy as np
import librosa

sr = 22050
duration = 3

def extract_features(audio, sr):
    features = {}
    # Clean the audio buffer to prevent "not finite everywhere" errors
    audio = np.nan_to_num(audio)
    
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    
    try:
        pitch, _ = librosa.piptrack(y=audio, sr=sr)
        pitches = pitch[pitch > 0]
        features["pitch_mean"] = np.mean(pitches) if len(pitches) > 0 else 0
        features["pitch_std"] = np.std(pitches) if len(pitches) > 0 else 0
    except:
        features["pitch_mean"] = 0
        features["pitch_std"] = 0
    
    try:
        features["rms_mean"] = np.mean(librosa.feature.rms(y=audio))
    except:
        features["rms_mean"] = 0
        
    try:
        features["zcr_mean"] = np.mean(librosa.feature.zero_crossing_rate(y=audio))
    except:
        features["zcr_mean"] = 0
        
    try:
        # Use the updated path if available, fall back to the old one
        try:
            from librosa.feature.rhythm import tempo
            features["tempo"] = tempo(y=audio, sr=sr)[0]
        except ImportError:
            features["tempo"] = librosa.beat.tempo(y=audio, sr=sr)[0]
    except:
        features["tempo"] = 0
        
    try:
        features["mfccs"] = np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13), axis=1)
    except:
        features["mfccs"] = np.zeros(13)
        
    try:
        features["spectral_centroid"] = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
    except:
        features["spectral_centroid"] = 0
        
    try:
        features["spectral_bandwidth"] = np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr))
    except:
        features["spectral_bandwidth"] = 0
        
    try:
        features["chroma_mean"] = np.mean(librosa.feature.chroma_stft(y=audio, sr=sr))
    except:
        features["chroma_mean"] = 0
        
    return features

def analyze_speech(features):
    analysis = []

    if features["pitch_mean"] < 100:
        analysis.append("⚠️ Voice may sound dull or low-pitched.")
    elif features["pitch_mean"] > 250:
        analysis.append("⚠️ Voice might be too high-pitched.")
    else:
        analysis.append("✅ Pitch is within a natural speaking range.")
    if features["pitch_std"] < 10:
        analysis.append("⚠️ Try adding more pitch variation for expressiveness.")
    else:
        analysis.append("✅ Good pitch variation detected.")
    if features["rms_mean"] < 0.02:
        analysis.append("⚠️ Speaking too softly. Increase volume.")
    elif features["rms_mean"] > 0.1:
        analysis.append("⚠️ Voice might be too loud or harsh.")
    else:
        analysis.append("✅ Volume level seems appropriate.")
    if features["tempo"] < 90:
        analysis.append("⚠️ You may be speaking too slowly.")
    elif features["tempo"] > 160:
        analysis.append("⚠️ You may be speaking too fast.")
    else:
        analysis.append("✅ Speaking pace looks natural.")
    if features["zcr_mean"] > 0.1:
        analysis.append("⚠️ Speech may be sharp or hissy (check articulation).")
    else:
        analysis.append("✅ Speech articulation is within a normal range.")
    if features["spectral_centroid"] < 1500:
        analysis.append("🔈 Try to speak more clearly or with more energy.")
    if features["spectral_bandwidth"] < 1800:
        analysis.append("📉 Your voice may sound muffled or dull — increase enunciation.")
    if features["chroma_mean"] < 0.3:
        analysis.append("🎵 Add more variation to your pitch for expressive delivery.")
    return analysis

st.title("🎙️ Live Pitch/Tone Analyzer")

placeholder = st.empty()

# Continuous loop - runs indefinitely
while True:
    try:
        audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
        sd.wait()
        chunk = audio.flatten()
        
        # Apply fix for non-finite values
        if not np.isfinite(chunk).all():
            chunk = np.nan_to_num(chunk)

        features = extract_features(chunk, sr)
        analysis = analyze_speech(features)

        with placeholder.container():
            col1,col2 = st.columns([1,1])
            with col1:
                st.subheader("Features")
                st.write(f"Pitch: {features['pitch_mean']:.1f} Hz")
                st.write(f"RMS: {features['rms_mean']:.3f}")
                st.write(f"Tempo: {features['tempo']:.1f} BPM")
            with col2:
                st.subheader("Analysis")
                for item in analysis:
                    st.write("•", item)
    
    except Exception as e:
        # If there's an error, just continue to the next iteration
        with placeholder.container():
            st.error(f"Error in processing: {e}")
            st.info("Continuing with next audio sample...")