const micBtn = document.getElementById("micBtn");
const statusText = document.getElementById("status");

let isRecording = false;
let mediaRecorder;
let audioStream;
let audioChunks = [];

// ==========================
// MIC BUTTON
// ==========================

micBtn.addEventListener("click", async () => {
  if (!isRecording) {
    try {
      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

      mediaRecorder = new MediaRecorder(audioStream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        await sendAudioToBackend(audioBlob);
      };

      mediaRecorder.start();

      isRecording = true;
      micBtn.textContent = "🛑 Stop Listening";
      micBtn.classList.add("recording");
      statusText.textContent = "Listening... speak now 🎙️";

    } catch (err) {
      alert("Microphone permission denied!");
      console.error(err);
    }
  } else {
    mediaRecorder.stop();
    audioStream.getTracks().forEach(track => track.stop());

    isRecording = false;
    micBtn.textContent = "🎤 Start Listening";
    micBtn.classList.remove("recording");
    statusText.textContent = "Processing...";
  }
});

// ==========================
// SEND AUDIO → GET TEXT
// ==========================

async function sendAudioToBackend(audioBlob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "user_voice.webm");

  try {
    const response = await fetch("http://localhost:8000/upload-audio", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    statusText.textContent = "Teacher is speaking ";

    playTTS(data.answer);

  } catch (err) {
    console.error(err);
    statusText.textContent = "Failed to process audio ❌";
  }
}

// ==========================
// WEBSOCKET TTS (SENTENCE-LEVEL BUFFERING)
// ==========================

function playTTS(text) {
  const ws = new WebSocket("ws://localhost:8000/ws/tts");
  ws.binaryType = "arraybuffer";

  let sentenceChunks = [];
  let audioQueue = [];
  let isPlaying = false;

  ws.onopen = () => {
    ws.send(text);
  };

  ws.onmessage = (event) => {
    // Text signals from backend
    if (typeof event.data === "string") {

      if (event.data === "__SENTENCE__") {
        queueSentenceAudio();
      }

      if (event.data === "__END__") {
        ws.close();
      }

      return;
    }

    // Binary audio data
    sentenceChunks.push(event.data);
  };

  function queueSentenceAudio() {
    if (!sentenceChunks.length) return;

    const blob = new Blob(sentenceChunks, { type: "audio/wav" });
    const url = URL.createObjectURL(blob);

    audioQueue.push(url);
    sentenceChunks = [];

    if (!isPlaying) playNext();
  }

  function playNext() {
    if (!audioQueue.length) {
      isPlaying = false;
      statusText.textContent = "Done ✅";
      return;
    }

    isPlaying = true;
    const audio = new Audio(audioQueue.shift());
    audio.play();

    audio.onended = () => {
      playNext();
    };
  }
}
