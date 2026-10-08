import { useRef, useState } from "react";
import {
  Mic,
  Square,
} from "lucide-react";

import {
  transcribeVoice,
} from "../services/api";


export default function VoiceButton({
  onTranscript,
}) {

  const [recording, setRecording] =
    useState(false);

  const [processing, setProcessing] =
    useState(false);

  const recorderRef =
    useRef(null);

  const chunksRef =
    useRef([]);


  const startRecording = async () => {

    try {

      const stream =
        await navigator.mediaDevices
          .getUserMedia({
            audio: true,
          });

      const recorder =
        new MediaRecorder(stream);

      chunksRef.current = [];

      recorderRef.current =
        recorder;


      recorder.ondataavailable =
        (event) => {

          if (
            event.data.size > 0
          ) {
            chunksRef.current.push(
              event.data
            );
          }
        };


      recorder.onstop = async () => {

        setProcessing(true);

        const blob =
          new Blob(
            chunksRef.current,
            {
              type: "audio/webm",
            }
          );

        try {

          const result =
            await transcribeVoice(
              blob
            );

          if (result.text) {
            onTranscript(
              result.text
            );
          }

        } catch (error) {

          console.error(error);

          alert(
            "Could not understand your voice."
          );

        } finally {

          setProcessing(false);
        }
      };


      recorder.start();

      setRecording(true);

    } catch (error) {

      console.error(error);

      alert(
        "Please allow microphone access."
      );
    }
  };


  const stopRecording = () => {

    if (
      recorderRef.current &&
      recorderRef.current.state !==
        "inactive"
    ) {

      recorderRef.current.stop();

      recorderRef.current.stream
        .getTracks()
        .forEach(
          (track) =>
            track.stop()
        );
    }

    setRecording(false);
  };


  return (
    <button
      type="button"
      onClick={
        recording
          ? stopRecording
          : startRecording
      }
      disabled={processing}
      className={`rounded-xl p-3 transition ${
        recording
          ? "bg-red-500 text-white"
          : "bg-white/5 text-gray-300 hover:bg-white/10 hover:text-white"
      } disabled:opacity-50`}
      title={
        recording
          ? "Stop recording"
          : "Talk to TouchGrass"
      }
    >

      {recording ? (
        <Square size={20} />
      ) : (
        <Mic size={20} />
      )}

    </button>
  );
}