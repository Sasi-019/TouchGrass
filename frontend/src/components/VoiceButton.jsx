import { useRef, useState } from "react";
import { Mic, Square, Loader2 } from "lucide-react";
import { transcribeVoice } from "../services/api";

export default function VoiceButton({
  onTranscription,
  disabled = false,
}) {
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const getSupportedMimeType = () => {
    const types = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
    ];

    for (const type of types) {
      if (
        window.MediaRecorder &&
        MediaRecorder.isTypeSupported(type)
      ) {
        return type;
      }
    }

    return "";
  };

  const startRecording = async () => {
    if (disabled || recording || processing) {
      return;
    }

    try {
      setError("");

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Your browser does not support microphone access."
        );
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      streamRef.current = stream;
      chunksRef.current = [];

      const mimeType = getSupportedMimeType();

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = (event) => {
        console.error(
          "MediaRecorder error:",
          event.error
        );

        setError(
          "Something went wrong while recording."
        );
      };

      recorder.onstop = async () => {
        try {
          setRecording(false);
          setProcessing(true);

          const finalMimeType =
            recorder.mimeType || "audio/webm";

          const audioBlob = new Blob(
            chunksRef.current,
            {
              type: finalMimeType,
            }
          );

          if (audioBlob.size === 0) {
            throw new Error(
              "No audio was recorded."
            );
          }

          const result =
            await transcribeVoice(audioBlob);

          const transcript =
            result?.text?.trim();

          if (!transcript) {
            throw new Error(
              "No speech was detected."
            );
          }

          if (onTranscription) {
            await onTranscription(
              transcript
            );
          }
        } catch (err) {
          console.error(
            "Voice transcription failed:",
            err
          );

          setError(
            err.response?.data?.detail ||
              err.message ||
              "Could not transcribe your voice."
          );
        } finally {
          setProcessing(false);

          if (streamRef.current) {
            streamRef.current
              .getTracks()
              .forEach((track) =>
                track.stop()
              );

            streamRef.current = null;
          }

          mediaRecorderRef.current = null;
          chunksRef.current = [];
        }
      };

      recorder.start();

      setRecording(true);
    } catch (err) {
      console.error(
        "Microphone access failed:",
        err
      );

      if (
        err.name ===
        "NotAllowedError"
      ) {
        setError(
          "Microphone permission was denied."
        );
      } else if (
        err.name ===
        "NotFoundError"
      ) {
        setError(
          "No microphone was found."
        );
      } else {
        setError(
          err.message ||
            "Could not access the microphone."
        );
      }

      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) =>
            track.stop()
          );

        streamRef.current = null;
      }
    }
  };

  const stopRecording = () => {
    const recorder =
      mediaRecorderRef.current;

    if (
      recorder &&
      recorder.state !== "inactive"
    ) {
      recorder.stop();
    }
  };

  const handleClick = () => {
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleClick}
        disabled={
          disabled || processing
        }
        title={
          recording
            ? "Stop recording"
            : "Speak to TouchGrass"
        }
        className={`flex min-h-12 min-w-12 items-center justify-center rounded-2xl border transition ${
          recording
            ? "border-red-500/60 bg-red-500/15 text-red-300 hover:bg-red-500/25"
            : "border-amber-800/50 bg-amber-950/20 text-amber-300 hover:border-amber-500/60 hover:bg-amber-900/30"
        } disabled:cursor-not-allowed disabled:opacity-40`}
      >
        {processing ? (
          <Loader2
            size={19}
            className="animate-spin"
          />
        ) : recording ? (
          <Square
            size={18}
            fill="currentColor"
          />
        ) : (
          <Mic size={20} />
        )}
      </button>

      {error && (
        <div className="absolute right-0 top-14 z-20 w-64 rounded-xl border border-red-900/50 bg-[#1a0d0d] px-3 py-2 text-xs leading-5 text-red-300 shadow-xl">
          {error}
        </div>
      )}
    </div>
  );
}