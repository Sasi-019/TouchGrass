<<<<<<< HEAD
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
=======
import { useEffect, useState } from "react";
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
import {
  Compass,
  User,
  Sparkles,
<<<<<<< HEAD
  Send,
  RefreshCw,
  MapPin,
  LocateFixed,
  Volume2,
  VolumeX,
  Square,
  Trash2,
  CloudSun,
} from "lucide-react";

import ActivityCard from "../components/ActivityCard";
import VoiceButton from "../components/VoiceButton";
import useBrowserLocation from "../hooks/useBrowserLocation";
import useVoiceOutput from "../hooks/useVoiceOutput";

import {
  getActivities,
  getChatHistory,
  clearChatHistory,
  chatWithAgent,
} from "../services/api";

const QUICK_PROMPTS = [
  "I have 30 minutes. Give me something to do.",
  "I want something new.",
  "What's the weather like for a walk?",
  "Find a park near me.",
];

function formatDistance(meters) {
  if (meters == null) return "";
  return meters < 1000
    ? `${Math.round(meters)} m`
    : `${(meters / 1000).toFixed(1)} km`;
}

// Turns a saved history row into the same shape as a live reply.
function fromHistory(item) {
  return {
    id: `h-${item.id}`,
    role: item.role,
    text: item.content,
    activity: item.activity
      ? {
          ...item.activity,
          reason: item.activity.context?.reason,
        }
      : null,
  };
}
=======
  ArrowRight,
  Clock3,
  MapPin,
  RefreshCw,
  Mic,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import ActivityCard from "../components/ActivityCard";
import VoiceButton from "../components/VoiceButton";

import {
  getActivities,
  chatWithAgent,
} from "../services/api";

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

export default function Home({ onProfile }) {
  const navigate = useNavigate();

<<<<<<< HEAD
  const [messages, setMessages] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [activities, setActivities] = useState([]);

  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Message to re-send automatically once the user shares their location.
  const [retryAfterLocation, setRetryAfterLocation] = useState(null);

  const bottomRef = useRef(null);
  const nextId = useRef(0);

  // Both are optional: the app works the same without them.
  const location = useBrowserLocation();
  const voice = useVoiceOutput();

  const goProfile = onProfile || (() => navigate("/my-profile"));

  // ----------------------------------------------------------
  // Load the previous conversation + activity list
  // ----------------------------------------------------------

  const loadActivities = useCallback(async () => {
    try {
      const data = await getActivities();
      setActivities(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load activities:", err);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const history = await getChatHistory();

        if (!cancelled && Array.isArray(history)) {
          setMessages(history.map(fromHistory));
        }
      } catch (err) {
        console.error("Failed to load chat history:", err);
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    })();

    loadActivities();

    return () => {
      cancelled = true;
    };
  }, [loadActivities]);

  // Keep the newest message in view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  // ----------------------------------------------------------
  // Talk to the agent
  // ----------------------------------------------------------

  const send = async (text) => {
    const message = (text ?? input).trim();

    if (!message || busy) return;

    const id = () => `l-${nextId.current++}`;

    setMessages((current) => [
      ...current,
      { id: id(), role: "user", text: message },
    ]);
    setInput("");
    setBusy(true);
    setError("");
    voice.stop();

    let timezone = null;

    try {
      timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || null;
    } catch {
      timezone = null;
    }

    try {
      const result = await chatWithAgent({
        message,
        // Only present when the user chose "Use my location".
        latitude: location.coords?.latitude ?? null,
        longitude: location.coords?.longitude ?? null,
        timezone,
        voice_enabled: voice.enabled,
      });

      setMessages((current) => [
        ...current,
        {
          id: id(),
          role: "assistant",
          text: result.message || "",
          activity:
            result.activity && result.activity_id
              ? { id: result.activity_id, ...result.activity }
              : null,
          weather: result.weather || null,
          places: Array.isArray(result.nearby_places)
            ? result.nearby_places
            : [],
          needsLocation: Boolean(result.needs_location),
          originalMessage: message,
        },
      ]);

      voice.speak(result.message);

      if (result.activity) loadActivities();
    } catch (err) {
      console.error("Agent request failed:", err);

      setMessages((current) => [
        ...current,
        {
          id: id(),
          role: "assistant",
          isError: true,
          text:
            err.response?.data?.detail ||
            (err.request
              ? "I can't reach TouchGrass right now. Check your connection and try again."
              : "Something went wrong. Please try again."),
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  // After the user shares their location, repeat the request that needed it.
  useEffect(() => {
    if (retryAfterLocation && location.status === "granted" && !busy) {
      const message = retryAfterLocation;
      setRetryAfterLocation(null);
      send(message);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retryAfterLocation, location.status]);

  const shareLocationFor = (message) => {
    setRetryAfterLocation(message || null);
    location.request();
  };

  const handleVoiceTranscription = async (transcript) => {
    if (!transcript?.trim()) return;
    await send(transcript);
  };

  const handleNewChat = async () => {
    if (!messages.length) return;

    if (!window.confirm("Start a new conversation? Your activities are kept.")) {
=======
  const [activities, setActivities] = useState([]);
  const [request, setRequest] = useState(
    "Give me something meaningful to do today."
  );

  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");
  const [voiceProcessing, setVoiceProcessing] = useState(false);


  // ============================================================
  // LOAD EXISTING ACTIVITIES
  // ============================================================

  useEffect(() => {
    loadActivities();
  }, []);


  const loadActivities = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getActivities();

      setActivities(
        Array.isArray(data) ? data : []
      );

    } catch (err) {
      console.error("Failed to load activities:", err);

      setError(
        err.response?.data?.detail ||
        "Could not load your activities."
      );

    } finally {
      setLoading(false);
    }
  };


  // ============================================================
  // ASK TOUCHGRASS
  // ============================================================

  const handleAsk = async () => {
    const message = request.trim();

    if (!message || asking) {
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
      return;
    }

    try {
<<<<<<< HEAD
      await clearChatHistory();
      setMessages([]);
      setError("");
      voice.stop();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Couldn't start a new conversation."
      );
    }
  };

  const lastMessageId = messages[messages.length - 1]?.id;

  // ----------------------------------------------------------
  // UI
  // ----------------------------------------------------------

  return (
    <div className="flex min-h-screen flex-col bg-[#0d0a07] text-white">
      {/* NAVBAR */}
      <nav className="sticky top-0 z-20 border-b border-amber-900/30 bg-[#110c08]/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
=======
      setAsking(true);
      setError("");

      const result = await chatWithAgent({
        message,
        latitude: null,
        longitude: null,
        voice_enabled: false,
      });

      if (result.activity) {
        const newActivity = {
          id: result.activity_id,
          title: result.activity.title,
          description: result.activity.description,
          category: result.activity.category,
          duration_minutes:
            result.activity.duration_minutes,
          status: "suggested",
          context: {
            reason: result.reason,
          },
        };

        setActivities((current) => [
          newActivity,
          ...current,
        ]);
      }

      // Clear the request after successful generation.
      setRequest("");

    } catch (err) {
      console.error(
        "Agent request failed:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "TouchGrass could not generate an activity."
      );

    } finally {
      setAsking(false);
    }
  };


  // ============================================================
  // VOICE TRANSCRIPTION
  // ============================================================

  const handleVoiceTranscription = async (
    transcript
  ) => {
    if (!transcript?.trim()) {
      return;
    }

    setRequest(transcript.trim());

    // Automatically send the transcribed request
    // to the existing LangGraph agent.
    try {
      setVoiceProcessing(true);
      setError("");

      const result = await chatWithAgent({
        message: transcript.trim(),
        latitude: null,
        longitude: null,
        voice_enabled: true,
      });

      if (result.activity) {
        const newActivity = {
          id: result.activity_id,
          title: result.activity.title,
          description: result.activity.description,
          category: result.activity.category,
          duration_minutes:
            result.activity.duration_minutes,
          status: "suggested",
          context: {
            reason: result.reason,
          },
        };

        setActivities((current) => [
          newActivity,
          ...current,
        ]);
      }

      setRequest("");

    } catch (err) {
      console.error(
        "Voice agent request failed:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "TouchGrass could not process your voice request."
      );

    } finally {
      setVoiceProcessing(false);
    }
  };


  // ============================================================
  // QUICK PROMPTS
  // ============================================================

  const quickPrompts = [
    "I want to explore something new.",
    "Give me something creative to do.",
    "I want to spend time outdoors.",
    "I want to meet people.",
  ];


  const isBusy =
    asking || voiceProcessing;


  return (
    <div className="min-h-screen bg-[#0d0a07] text-white">

      {/* ======================================================
          NAVBAR
      ======================================================= */}

      <nav className="border-b border-amber-900/30 bg-[#110c08]/90 backdrop-blur">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
          <button
            onClick={() => navigate("/home")}
            className="flex items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500 text-black">
              <Compass size={22} />
            </div>

            <div className="text-left">
<<<<<<< HEAD
              <h1 className="text-lg font-bold leading-tight">TouchGrass</h1>
              <p className="text-xs text-amber-200/50">Less screen. More life.</p>
            </div>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleNewChat}
              disabled={!messages.length}
              className="flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-white/60 transition hover:bg-white/5 hover:text-white disabled:opacity-30"
              title="Start a new conversation"
            >
              <Trash2 size={16} />
              <span className="hidden sm:inline">New chat</span>
            </button>

            <button
              onClick={goProfile}
              className="flex items-center gap-2 rounded-xl border border-amber-800/40 bg-amber-950/20 px-3 py-2 text-sm text-amber-100 transition hover:bg-amber-900/30"
            >
              <User size={16} />
              <span className="hidden sm:inline">My Profile</span>
            </button>
          </div>
        </div>
      </nav>

      {/* CHAT */}
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 pt-6 sm:px-6">
        <div className="flex-1 space-y-5 pb-6">
          {historyLoading ? (
            <div className="flex items-center justify-center py-24 text-sm text-white/40">
              <RefreshCw size={18} className="mr-2 animate-spin text-amber-400" />
              Loading your conversation...
            </div>
          ) : messages.length === 0 ? (
            <div className="py-12 text-center">
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400">
                <Sparkles size={30} />
              </div>

              <h2 className="text-3xl font-bold sm:text-4xl">
                What do you feel like <span className="text-amber-400">doing?</span>
              </h2>

              <p className="mx-auto mt-3 max-w-md text-white/50">
                Tell me how much time you have, how you feel, or where you are.
                I'll give you one thing to do, then you can put your phone away.
              </p>

              <div className="mt-7 flex flex-wrap justify-center gap-2">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => send(prompt)}
                    disabled={busy}
                    className="rounded-full border border-amber-900/40 bg-[#15100c] px-4 py-2 text-sm text-white/65 transition hover:border-amber-500/50 hover:text-amber-200 disabled:opacity-40"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) =>
              message.role === "user" ? (
                <div key={message.id} className="flex justify-end">
                  <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-amber-500 px-4 py-3 text-black">
                    {message.text}
                  </div>
                </div>
              ) : (
                <div key={message.id} className="flex flex-col items-start gap-3">
                  <div
                    className={`max-w-[90%] whitespace-pre-wrap rounded-2xl rounded-bl-md border px-4 py-3 leading-7 ${
                      message.isError
                        ? "border-red-900/40 bg-red-950/20 text-red-300"
                        : "border-white/10 bg-white/5 text-gray-100"
                    }`}
                  >
                    {message.text}

                    {!message.isError && voice.supported && (
                      <button
                        onClick={() => voice.speak(message.text, { force: true })}
                        className="mt-2 flex items-center gap-1 text-xs text-white/35 transition hover:text-white"
                        title="Read this aloud"
                      >
                        <Volume2 size={14} />
                        Listen
                      </button>
                    )}
                  </div>

                  {message.weather?.summary && (
                    <div className="flex max-w-[90%] items-start gap-2 rounded-xl border border-sky-900/40 bg-sky-950/20 px-3 py-2 text-sm text-sky-200">
                      <CloudSun size={16} className="mt-0.5 shrink-0" />
                      <span>
                        {message.weather.location
                          ? `${message.weather.location}: `
                          : ""}
                        {message.weather.summary}
                      </span>
                    </div>
                  )}

                  {message.places?.length > 0 && (
                    <ul className="max-w-[90%] space-y-1 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white/70">
                      {message.places.slice(0, 5).map((place, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <MapPin size={14} className="mt-1 shrink-0 text-amber-400" />
                          <span>
                            {place.name}
                            {place.type ? ` (${place.type})` : ""}
                            {place.distance_m != null
                              ? ` · ${formatDistance(place.distance_m)}`
                              : ""}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}

                  {message.needsLocation &&
                    message.id === lastMessageId &&
                    location.status !== "granted" && (
                      <button
                        onClick={() => shareLocationFor(message.originalMessage)}
                        disabled={location.status === "asking"}
                        className="flex items-center gap-2 rounded-full bg-amber-500 px-4 py-2 text-sm font-semibold text-black transition hover:bg-amber-400 disabled:opacity-50"
                      >
                        <LocateFixed size={15} />
                        {location.status === "asking"
                          ? "Finding you..."
                          : "Use my location and try again"}
                      </button>
                    )}

                  {message.activity && (
                    <div className="w-full">
                      <ActivityCard
                        activity={message.activity}
                        onClick={() => navigate(`/activity/${message.activity.id}`)}
                      />
                      <p className="mt-2 text-center text-xs text-white/35">
                        Do it, then tap the card to tell me how it went.
                      </p>
                    </div>
                  )}
                </div>
              )
            )
          )}

          {busy && (
            <div className="flex items-center gap-2 text-sm text-white/45">
              <RefreshCw size={15} className="animate-spin text-amber-400" />
              TouchGrass is thinking...
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* COMPOSER (stays at the bottom) */}
        <div className="sticky bottom-0 z-10 -mx-4 border-t border-amber-900/30 bg-[#0d0a07]/95 px-4 pb-4 pt-3 backdrop-blur sm:-mx-6 sm:px-6">
          <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
            {location.status === "granted" ? (
              <button
                type="button"
                onClick={location.clear}
                className="flex items-center gap-1.5 rounded-full border border-green-700/40 bg-green-950/30 px-3 py-1.5 text-green-300 transition hover:bg-green-900/30"
                title="Stop sharing location"
              >
                <MapPin size={13} />
                Location on
              </button>
            ) : (
              <button
                type="button"
                onClick={() => shareLocationFor(null)}
                disabled={
                  location.status === "asking" ||
                  location.status === "unsupported"
                }
                className="flex items-center gap-1.5 rounded-full border border-amber-800/40 bg-amber-950/20 px-3 py-1.5 text-amber-100 transition hover:bg-amber-900/30 disabled:opacity-40"
              >
                <LocateFixed size={13} />
                {location.status === "asking" ? "Finding you..." : "Use my location"}
              </button>
            )}

            {voice.supported && (
              <>
                <button
                  type="button"
                  onClick={voice.toggle}
                  aria-pressed={voice.enabled}
                  className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 transition ${
                    voice.enabled
                      ? "border-amber-500/50 bg-amber-500/15 text-amber-200"
                      : "border-white/10 bg-white/5 text-white/50 hover:text-white"
                  }`}
                >
                  {voice.enabled ? <Volume2 size={13} /> : <VolumeX size={13} />}
                  Voice {voice.enabled ? "ON" : "OFF"}
                </button>

                {voice.speaking && (
                  <button
                    type="button"
                    onClick={voice.stop}
                    className="flex items-center gap-1.5 rounded-full border border-red-800/50 bg-red-950/30 px-3 py-1.5 text-red-300 transition hover:bg-red-900/30"
                  >
                    <Square size={11} />
                    Stop
                  </button>
                )}
              </>
            )}

            <span className="text-white/30">
              {location.status === "denied"
                ? "Location is off. No problem, I'll work without it."
                : location.status === "unavailable"
                  ? "Couldn't get your location. Continuing without it."
                  : location.status === "unsupported"
                    ? "This browser can't share location."
                    : ""}
            </span>
          </div>

          {error && (
            <div className="mb-3 rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-2 text-sm text-red-300">
              {error}
            </div>
          )}

          <div className="flex items-end gap-2 rounded-2xl border border-amber-900/40 bg-[#15100c] p-2">
            <VoiceButton
              onTranscription={handleVoiceTranscription}
              disabled={busy}
            />

            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  send();
                }
              }}
              rows={1}
              disabled={busy}
              placeholder="Message TouchGrass..."
              className="max-h-32 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/25"
            />

            <button
              onClick={() => send()}
              disabled={busy || !input.trim()}
              className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-500 text-black transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-30"
              title="Send"
            >
              <Send size={18} />
            </button>
          </div>
        </div>

        {/* PAST ACTIVITIES */}
        {activities.length > 0 && (
          <section className="pb-16 pt-10">
            <h3 className="mb-1 text-xl font-bold">Your activities</h3>
            <p className="mb-5 text-sm text-white/40">
              Tap one to mark it done and tell me how it went.
            </p>

            <div className="grid gap-4 sm:grid-cols-2">
              {activities.slice(0, 8).map((activity) => (
                <ActivityCard
                  key={activity.id}
                  activity={activity}
                  onClick={() => navigate(`/activity/${activity.id}`)}
                />
              ))}
            </div>
          </section>
        )}
      </main>
=======
              <h1 className="text-lg font-bold">
                TouchGrass
              </h1>

              <p className="text-xs text-amber-200/50">
                Less screen. More life.
              </p>
            </div>
          </button>


          <button
            onClick={onProfile}
            className="flex items-center gap-2 rounded-xl border border-amber-800/40 bg-amber-950/20 px-4 py-2 text-sm text-amber-100 transition hover:bg-amber-900/30"
          >
            <User size={17} />
            My Profile
          </button>

        </div>

      </nav>


      {/* ======================================================
          MAIN
      ======================================================= */}

      <main className="mx-auto max-w-7xl px-6 py-10">

        {/* HERO */}

        <section className="mb-10">

          <div className="mb-3 flex items-center gap-2 text-sm text-amber-400">
            <Sparkles size={16} />
            <span>Your real-world activity agent</span>
          </div>

          <h2 className="max-w-3xl text-4xl font-bold leading-tight md:text-5xl">
            What do you feel like
            <span className="text-amber-400">
              {" "}doing?
            </span>
          </h2>

          <p className="mt-4 max-w-2xl text-base leading-7 text-white/55">
            Tell TouchGrass what you want.
            Type it or speak naturally.
            Your agent will turn it into something
            meaningful you can actually do.
          </p>

        </section>


        {/* ====================================================
            REQUEST BOX
        ===================================================== */}

        <section className="mb-10">

          <div className="rounded-3xl border border-amber-900/40 bg-[#15100c] p-5 shadow-2xl">

            <div className="flex flex-col gap-4 md:flex-row md:items-end">

              {/* TEXT INPUT */}

              <div className="flex-1">

                <label className="mb-2 block text-sm font-medium text-amber-100/70">
                  Tell me what you want
                </label>

                <textarea
                  value={request}
                  onChange={(event) =>
                    setRequest(event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" &&
                      !event.shiftKey
                    ) {
                      event.preventDefault();
                      handleAsk();
                    }
                  }}
                  rows={3}
                  disabled={isBusy}
                  placeholder="Example: I want to do something outdoors today..."
                  className="w-full resize-none rounded-2xl border border-amber-900/40 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/25 focus:border-amber-500/60"
                />

              </div>


              {/* VOICE + ASK */}

              <div className="flex gap-3">

                <VoiceButton
                  onTranscription={
                    handleVoiceTranscription
                  }
                  disabled={isBusy}
                />

                <button
                  onClick={handleAsk}
                  disabled={
                    isBusy ||
                    !request.trim()
                  }
                  className="flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-amber-500 px-6 font-semibold text-black transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-40"
                >

                  {asking ? (
                    <>
                      <RefreshCw
                        size={18}
                        className="animate-spin"
                      />

                      Thinking...
                    </>
                  ) : (
                    <>
                      <Sparkles size={18} />

                      Ask TouchGrass

                      <ArrowRight size={17} />
                    </>
                  )}

                </button>

              </div>

            </div>


            {/* VOICE STATUS */}

            {voiceProcessing && (
              <div className="mt-4 flex items-center gap-2 text-sm text-amber-300">

                <Mic size={15} />

                <span>
                  Listening to your request...
                </span>

              </div>
            )}


            {/* ERROR */}

            {error && (
              <div className="mt-4 rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}

          </div>

        </section>


        {/* ====================================================
            QUICK PROMPTS
        ===================================================== */}

        <section className="mb-12">

          <div className="mb-4 flex items-center gap-2">
            <Sparkles
              size={17}
              className="text-amber-400"
            />

            <h3 className="font-semibold">
              Try saying...
            </h3>
          </div>


          <div className="flex flex-wrap gap-3">

            {quickPrompts.map((prompt) => (

              <button
                key={prompt}
                onClick={() =>
                  setRequest(prompt)
                }
                disabled={isBusy}
                className="rounded-full border border-amber-900/40 bg-[#15100c] px-4 py-2 text-sm text-white/65 transition hover:border-amber-500/50 hover:text-amber-200 disabled:opacity-40"
              >
                {prompt}
              </button>

            ))}

          </div>

        </section>


        {/* ====================================================
            ACTIVITIES
        ===================================================== */}

        <section>

          <div className="mb-6 flex items-center justify-between">

            <div>

              <h3 className="text-2xl font-bold">
                Your activities
              </h3>

              <p className="mt-1 text-sm text-white/40">
                Things TouchGrass thinks you might enjoy.
              </p>

            </div>


            <button
              onClick={loadActivities}
              disabled={loading}
              className="rounded-xl border border-amber-900/40 p-2 text-white/50 transition hover:bg-amber-900/20 hover:text-amber-200"
              title="Refresh activities"
            >
              <RefreshCw
                size={17}
                className={
                  loading
                    ? "animate-spin"
                    : ""
                }
              />
            </button>

          </div>


          {loading ? (

            <div className="flex items-center justify-center rounded-3xl border border-amber-900/30 bg-[#15100c] py-20">

              <div className="text-center">

                <RefreshCw
                  size={28}
                  className="mx-auto mb-3 animate-spin text-amber-400"
                />

                <p className="text-sm text-white/40">
                  Loading your activities...
                </p>

              </div>

            </div>

          ) : activities.length === 0 ? (

            <div className="rounded-3xl border border-dashed border-amber-900/40 bg-[#15100c] px-6 py-16 text-center">

              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400">

                <Compass size={26} />

              </div>

              <h4 className="text-lg font-semibold">
                Nothing here yet
              </h4>

              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-white/40">
                Tell TouchGrass what you're in the mood
                for and your first real-world challenge
                will appear here.
              </p>

            </div>

          ) : (

            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">

              {activities.map((activity) => (

                <ActivityCard
                  key={activity.id}
                  activity={activity}
                  onClick={() =>
                    navigate(
                      `/activity/${activity.id}`
                    )
                  }
                />

              ))}

            </div>

          )}

        </section>


        {/* ====================================================
            FOOTER MESSAGE
        ===================================================== */}

        <div className="mt-16 flex items-center justify-center gap-2 text-center text-xs text-white/25">

          <MapPin size={13} />

          <span>
            TouchGrass is designed to get you away
            from the screen and into the real world.
          </span>

        </div>

      </main>

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    </div>
  );
}
