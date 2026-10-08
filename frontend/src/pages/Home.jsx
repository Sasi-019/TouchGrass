import {
  useEffect,
  useState,
} from "react";

import {
  MapPin,
  User,
  Send,
  Volume2,
  Sparkles,
  Clock,
} from "lucide-react";

import {
  chatWithAgent,
  getProfile,
} from "../services/api";

import VoiceButton from "../components/VoiceButton";


export default function Home({
  onProfile,
}) {

  const [profile, setProfile] =
    useState(null);

  const [message, setMessage] =
    useState("");

  const [conversation, setConversation] =
    useState([]);

  const [activity, setActivity] =
    useState(null);

  const [environment, setEnvironment] =
    useState(null);

  const [location, setLocation] =
    useState(null);

  const [loading, setLoading] =
    useState(false);


  useEffect(() => {

    getProfile()
      .then(setProfile)
      .catch(console.error);


    if (
      navigator.geolocation
    ) {

      navigator.geolocation
        .getCurrentPosition(
          (position) => {

            setLocation({
              latitude:
                position.coords.latitude,

              longitude:
                position.coords.longitude,
            });

          },

          (error) => {

            console.warn(
              "Location unavailable:",
              error
            );

          }
        );
    }

  }, []);


  const speak = (text) => {

    if (
      !window.speechSynthesis ||
      !text
    ) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance =
      new SpeechSynthesisUtterance(
        text
      );

    utterance.rate = 1;

    window.speechSynthesis.speak(
      utterance
    );
  };


  const sendMessage = async (
    suppliedMessage
  ) => {

    const text =
      (
        suppliedMessage ??
        message
      ).trim();

    if (!text || loading) {
      return;
    }


    setConversation(
      (previous) => [
        ...previous,
        {
          role: "user",
          text,
        },
      ]
    );

    setMessage("");

    setLoading(true);


    try {

      const result =
        await chatWithAgent({
          message: text,

          latitude:
            location?.latitude,

          longitude:
            location?.longitude,
        });


      setActivity(
        result.activity
      );

      setEnvironment(
        result.environment
      );


      const response =
        result.activity
          ? `${result.activity.title}. ${result.activity.description}`
          : result.reason ||
            "I have an idea for you.";


      setConversation(
        (previous) => [
          ...previous,
          {
            role: "assistant",
            text: response,
          },
        ]
      );


      speak(response);

    } catch (error) {

      console.error(error);

      setConversation(
        (previous) => [
          ...previous,
          {
            role: "assistant",
            text:
              "I couldn't reach the TouchGrass agent. Please try again.",
          },
        ]
      );

    } finally {

      setLoading(false);
    }
  };


  const handleVoice = (
    transcript
  ) => {

    setMessage(transcript);

    sendMessage(transcript);
  };


  const interests =
    profile?.interests || [];


  return (
    <div className="min-h-screen bg-[#090706] text-white">

      {/* Header */}

      <header className="border-b border-white/10 bg-[#0d0a08]/90 backdrop-blur">

        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500 text-black">

              <Sparkles size={20} />

            </div>

            <div>

              <h1 className="font-bold">
                TouchGrass
              </h1>

              <p className="text-xs text-gray-500">
                Your real-world AI companion
              </p>

            </div>

          </div>


          <button
            onClick={onProfile}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-300 transition hover:bg-white/10 hover:text-white"
          >

            <User size={17} />

            My Profile

          </button>

        </div>

      </header>


      <main className="mx-auto max-w-6xl px-5 py-8">

        <div className="grid gap-6 lg:grid-cols-[1fr_300px]">


          {/* Assistant */}

          <section>

            <div className="mb-6">

              <p className="text-sm font-medium text-amber-400">
                YOUR AI ASSISTANT
              </p>

              <h2 className="mt-2 text-3xl font-bold sm:text-4xl">
                What do you feel like doing?
              </h2>

              <p className="mt-2 text-gray-500">
                Don't plan. Just tell me what
                you're feeling.
              </p>

            </div>


            {/* Conversation */}

            <div className="min-h-[400px] space-y-4 rounded-3xl border border-white/10 bg-white/[0.025] p-5">

              {conversation.length ===
                0 && (

                <div className="flex min-h-[350px] flex-col items-center justify-center text-center">

                  <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400">

                    <Sparkles size={30} />

                  </div>

                  <h3 className="text-xl font-semibold">
                    Talk to TouchGrass
                  </h3>

                  <p className="mt-2 max-w-md text-gray-500">
                    Tell me what you're
                    interested in, how you're
                    feeling, how much time you
                    have, or where you want to
                    go.
                  </p>


                  <div className="mt-6 flex flex-wrap justify-center gap-2">

                    {[
                      "Give me something to do",
                      "I'm tired",
                      "I want to go outside",
                      "Find a park nearby",
                      "Find a restaurant",
                    ].map(
                      (item) => (

                        <button
                          key={item}
                          onClick={() =>
                            sendMessage(
                              item
                            )
                          }
                          className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-400 hover:border-amber-500/30 hover:text-white"
                        >
                          {item}
                        </button>

                      )
                    )}

                  </div>

                </div>

              )}


              {conversation.map(
                (item, index) => (

                  <div
                    key={index}
                    className={
                      item.role === "user"
                        ? "ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-amber-500 px-4 py-3 text-black"
                        : "max-w-[85%] rounded-2xl rounded-bl-md border border-white/10 bg-white/5 px-4 py-3 text-gray-200"
                    }
                  >

                    <div>
                      {item.text}
                    </div>


                    {item.role ===
                      "assistant" && (

                      <button
                        onClick={() =>
                          speak(
                            item.text
                          )
                        }
                        className="mt-2 text-gray-500 hover:text-white"
                      >
                        <Volume2
                          size={16}
                        />
                      </button>

                    )}

                  </div>

                )
              )}


              {loading && (

                <div className="max-w-[85%] rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-gray-500">

                  TouchGrass is thinking...

                </div>

              )}

            </div>


            {/* Activity */}

            {activity && (

              <div className="mt-5 rounded-3xl border border-amber-500/20 bg-amber-500/[0.06] p-6">

                <div className="flex items-center gap-2 text-amber-400">

                  <Sparkles size={17} />

                  <span className="text-sm font-semibold">
                    Your challenge
                  </span>

                </div>


                <h3 className="mt-3 text-2xl font-bold">
                  {activity.title}
                </h3>


                <p className="mt-3 leading-7 text-gray-300">
                  {activity.description}
                </p>


                <div className="mt-5 flex flex-wrap gap-2">

                  {activity.duration_minutes && (

                    <span className="flex items-center gap-2 rounded-full bg-white/5 px-3 py-2 text-sm text-gray-400">

                      <Clock size={14} />

                      {
                        activity.duration_minutes
                      }{" "}
                      minutes

                    </span>

                  )}


                  {activity.place?.name && (

                    <span className="flex items-center gap-2 rounded-full bg-white/5 px-3 py-2 text-sm text-gray-400">

                      <MapPin size={14} />

                      {
                        activity.place.name
                      }

                    </span>

                  )}

                </div>

              </div>

            )}


            {/* Composer */}

            <div className="mt-5 flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-2">

              <VoiceButton
                onTranscript={
                  handleVoice
                }
              />


              <input
                value={message}
                onChange={(event) =>
                  setMessage(
                    event.target.value
                  )
                }
                onKeyDown={(event) => {

                  if (
                    event.key ===
                    "Enter"
                  ) {
                    sendMessage();
                  }

                }}
                placeholder="Talk to TouchGrass..."
                className="flex-1 bg-transparent px-3 py-3 text-white outline-none placeholder:text-gray-600"
              />


              <button
                onClick={() =>
                  sendMessage()
                }
                disabled={
                  !message.trim() ||
                  loading
                }
                className="rounded-xl bg-amber-500 p-3 text-black hover:bg-amber-400 disabled:opacity-30"
              >

                <Send size={19} />

              </button>

            </div>

          </section>


          {/* Profile sidebar */}

          <aside>

            <div className="sticky top-6 rounded-3xl border border-white/10 bg-white/[0.025] p-5">

              <div className="mb-5 flex items-center justify-between">

                <div>

                  <p className="text-xs uppercase tracking-widest text-gray-500">
                    Personalization
                  </p>

                  <h3 className="mt-1 text-xl font-bold">
                    About you
                  </h3>

                </div>


                <button
                  onClick={onProfile}
                  className="text-sm text-amber-400 hover:text-amber-300"
                >
                  View
                </button>

              </div>


              {/* Interests */}

              <div>

                <p className="mb-3 text-sm text-gray-500">
                  Your interests
                </p>

                <div className="space-y-3">

                  {interests.length ? (

                    interests
                      .slice(0, 5)
                      .map(
                        (
                          interest,
                          index
                        ) => (

                          <div
                            key={index}
                          >

                            <div className="mb-1 flex justify-between text-sm">

                              <span className="text-gray-300">
                                {
                                  interest.name
                                }
                              </span>

                              <span className="text-gray-600">
                                {Math.round(
                                  (
                                    interest.strength ||
                                    0
                                  ) * 100
                                )}%
                              </span>

                            </div>

                            <div className="h-1.5 rounded-full bg-white/10">

                              <div
                                className="h-full rounded-full bg-amber-500"
                                style={{
                                  width: `${(
                                    interest.strength ||
                                    0
                                  ) * 100}%`,
                                }}
                              />

                            </div>

                          </div>

                        )
                      )

                  ) : (

                    <p className="text-sm text-gray-600">
                      Complete your profile
                      discovery first.
                    </p>

                  )}

                </div>

              </div>


              {/* Preferences */}

              <div className="mt-6">

                <p className="mb-3 text-sm text-gray-500">
                  You prefer
                </p>

                <div className="flex flex-wrap gap-2">

                  {(
                    profile
                      ?.experience_preferences ||
                    []
                  ).map(
                    (item, index) => (

                      <span
                        key={index}
                        className="rounded-full bg-white/5 px-3 py-1.5 text-xs text-gray-400"
                      >
                        {item}
                      </span>

                    )
                  )}

                </div>

              </div>


              {/* Time */}

              <div className="mt-6 border-t border-white/10 pt-5">

                <div className="flex items-center gap-2 text-sm text-gray-400">

                  <Clock size={15} />

                  Typical time

                </div>

                <p className="mt-1 text-gray-200">

                  {
                    profile?.typical_free_time ||
                    "Not set"
                  }

                </p>

              </div>


              {/* Location */}

              <div className="mt-5 border-t border-white/10 pt-5">

                <div className="flex items-center gap-2 text-sm">

                  <MapPin
                    size={15}
                    className={
                      location
                        ? "text-green-400"
                        : "text-gray-600"
                    }
                  />

                  <span className="text-gray-400">

                    {location
                      ? "Location available"
                      : "Location not shared"}

                  </span>

                </div>

              </div>

            </div>

          </aside>

        </div>

      </main>

    </div>
  );
}