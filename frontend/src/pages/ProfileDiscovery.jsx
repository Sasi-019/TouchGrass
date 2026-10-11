import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { normalizeProfile, saveProfile } from "../services/api";

const questions = [
  {
    id: "free_time",
    title: "What do you enjoy doing when you have free time?",
    placeholder:
      "For example: photography, reading, gaming, walking, music...",
    type: "text",
  },
  {
    id: "wants_more",
    title: "What do you wish you did more often?",
    placeholder:
      "For example: exercise more, spend time outside, meet people...",
    type: "text",
  },
  {
    id: "curiosity",
    title: "What have you always wanted to try or learn?",
    placeholder:
      "For example: gardening, cooking, painting, bird watching...",
    type: "text",
  },
  {
    id: "experience_preferences",
    title: "What kind of experiences sound good to you?",
    type: "multi",
    options: [
      "Learn",
      "Create",
      "Explore",
      "Move",
      "Connect",
      "Relax",
    ],
  },
  {
    id: "free_time_duration",
    title: "How much free time do you usually have?",
    type: "single",
    options: [
      "10–20 minutes",
      "20–40 minutes",
      "40–60 minutes",
      "1+ hour",
    ],
  },
  {
    id: "dislikes",
    title: "Is there anything you dislike or want to avoid?",
    placeholder:
      "For example: crowded places, long travel, intense exercise...",
    type: "text",
  },
  {
    id: "adventure_level",
    title: "How adventurous should TouchGrass be?",
    type: "single",
    options: [
      "Keep it comfortable",
      "Moderate",
      "Surprise me",
    ],
  },
];

export default function ProfileDiscovery() {
  const navigate = useNavigate();

  const [currentIndex, setCurrentIndex] = useState(0);

  const [answers, setAnswers] = useState({
    free_time: "",
    wants_more: "",
    curiosity: "",
    experience_preferences: [],
    free_time_duration: "",
    dislikes: "",
    adventure_level: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const question = questions[currentIndex];

  const updateAnswer = (value) => {
    setAnswers((previous) => ({
      ...previous,
      [question.id]: value,
    }));
  };

  const toggleExperience = (option) => {
    setAnswers((previous) => {
      const current = previous.experience_preferences;

      if (current.includes(option.toLowerCase())) {
        return {
          ...previous,
          experience_preferences: current.filter(
            (item) => item !== option.toLowerCase()
          ),
        };
      }

      return {
        ...previous,
        experience_preferences: [
          ...current,
          option.toLowerCase(),
        ],
      };
    });
  };

  const canContinue = () => {
    const value = answers[question.id];

    if (question.type === "multi") {
      return value.length > 0;
    }

    return String(value || "").trim().length > 0;
  };

  const goNext = async () => {
    setError("");

    if (!canContinue()) {
      setError("Please answer this question before continuing.");
      return;
    }

    if (currentIndex < questions.length - 1) {
      setCurrentIndex((index) => index + 1);
      return;
    }

    await finishProfile();
  };

  const goBack = () => {
    setError("");

    if (currentIndex > 0) {
      setCurrentIndex((index) => index - 1);
    }
  };

  const finishProfile = async () => {
    setLoading(true);
    setError("");

    try {
      // Step 1:
      // Send natural-language answers to Groq.
      const normalized = await normalizeProfile(answers);

      console.log("AI normalized profile:", normalized);

      // Step 2:
      // Save the structured profile in PostgreSQL.
      const savedProfile = await saveProfile(normalized);

      console.log("Saved profile:", savedProfile);

      // Step 3:
      // Continue to Home.
      navigate("/home");
    } catch (err) {
      console.error("Profile setup failed:", err);

      const message =
        err.response?.data?.detail ||
        "Something went wrong while creating your profile.";

      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const progress =
    ((currentIndex + 1) / questions.length) * 100;

  return (
    <div className="min-h-screen bg-[#120b08] text-white flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-2xl">

        {/* Header */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span className="text-amber-400 font-semibold tracking-wide">
              TOUCHGRASS
            </span>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold">
            Let's get to know you
          </h1>

          <p className="text-gray-400 mt-3">
            A few simple questions help TouchGrass understand
            what kind of experiences you'll enjoy.
          </p>
        </div>

        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>
              Question {currentIndex + 1} of {questions.length}
            </span>

            <span>
              {Math.round(progress)}%
            </span>
          </div>

          <div className="h-2 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        <div className="rounded-3xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6 md:p-8 shadow-2xl">

          <div className="mb-7">
            <p className="text-amber-400 text-sm font-medium mb-3">
              GETTING TO KNOW YOU
            </p>

            <h2 className="text-2xl md:text-3xl font-semibold leading-tight">
              {question.title}
            </h2>
          </div>

          {/* Text Input */}
          {question.type === "text" && (
            <textarea
              value={answers[question.id]}
              onChange={(event) =>
                updateAnswer(event.target.value)
              }
              placeholder={question.placeholder}
              rows={5}
              className="w-full rounded-2xl border border-white/10 bg-black/20 px-5 py-4 text-white placeholder-gray-500 outline-none resize-none focus:border-amber-500/60 focus:ring-2 focus:ring-amber-500/20 transition"
              autoFocus
            />
          )}

          {/* Multi Select */}
          {question.type === "multi" && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {question.options.map((option) => {
                const selected =
                  answers.experience_preferences.includes(
                    option.toLowerCase()
                  );

                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() => toggleExperience(option)}
                    className={`rounded-2xl border px-4 py-4 text-sm font-medium transition ${
                      selected
                        ? "border-amber-500 bg-amber-500/20 text-amber-300"
                        : "border-white/10 bg-white/[0.03] text-gray-300 hover:bg-white/[0.08]"
                    }`}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          )}

          {/* Single Select */}
          {question.type === "single" && (
            <div className="space-y-3">
              {question.options.map((option) => {
                const selected =
                  answers[question.id] === option;

                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() => updateAnswer(option)}
                    className={`w-full text-left rounded-2xl border px-5 py-4 transition ${
                      selected
                        ? "border-amber-500 bg-amber-500/20 text-amber-300"
                        : "border-white/10 bg-white/[0.03] text-gray-300 hover:bg-white/[0.08]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span>{option}</span>

                      {selected && (
                        <span className="text-amber-400">
                          ✓
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8">

            <button
              type="button"
              onClick={goBack}
              disabled={currentIndex === 0 || loading}
              className="px-5 py-3 rounded-xl text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition"
            >
              ← Back
            </button>

            <button
              type="button"
              onClick={goNext}
              disabled={loading}
              className="px-7 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-black font-semibold hover:from-amber-400 hover:to-orange-400 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg shadow-amber-500/10"
            >
              {loading
                ? "Building your profile..."
                : currentIndex === questions.length - 1
                ? "Create my profile"
                : "Continue →"}
            </button>

          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-500 mt-6">
          Your answers help TouchGrass personalize your
          offline experiences.
        </p>
      </div>
    </div>
  );
}