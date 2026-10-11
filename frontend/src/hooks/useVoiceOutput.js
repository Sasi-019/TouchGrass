import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "touchgrass_voice_output";

const supported =
  typeof window !== "undefined" &&
  "speechSynthesis" in window &&
  typeof window.SpeechSynthesisUtterance !== "undefined";

function readSaved() {
  try {
    return localStorage.getItem(STORAGE_KEY) === "on";
  } catch {
    return false;
  }
}

/**
 * Optional spoken replies using the browser's built-in speech synthesis.
 *
 * - Off by default; the choice is remembered (per browser) when possible.
 * - `stop()` cuts speech immediately.
 * - If the browser has no speech support, everything quietly stays text-only.
 */
export default function useVoiceOutput() {
  const [enabled, setEnabled] = useState(readSaved);
  const [speaking, setSpeaking] = useState(false);
  const enabledRef = useRef(enabled);

  useEffect(() => {
    enabledRef.current = enabled;
  }, [enabled]);

  const stop = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  const speak = useCallback((text, { force = false } = {}) => {
    if (!supported || !text) return;
    if (!force && !enabledRef.current) return;

    try {
      window.speechSynthesis.cancel();

      const utterance = new window.SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.onstart = () => setSpeaking(true);
      utterance.onend = () => setSpeaking(false);
      utterance.onerror = () => setSpeaking(false);

      window.speechSynthesis.speak(utterance);
    } catch {
      // Voice output is a nicety: failing silently falls back to text.
      setSpeaking(false);
    }
  }, []);

  const toggle = useCallback(() => {
    setEnabled((current) => {
      const next = !current;

      try {
        localStorage.setItem(STORAGE_KEY, next ? "on" : "off");
      } catch {
        /* storage unavailable: keep it in memory only */
      }

      if (!next && supported) {
        window.speechSynthesis.cancel();
        setSpeaking(false);
      }

      return next;
    });
  }, []);

  // Never keep talking after leaving the page.
  useEffect(() => stop, [stop]);

  return { supported, enabled, speaking, speak, stop, toggle };
}
