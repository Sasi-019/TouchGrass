import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const questions = [
  {
    id: "interests",
    type: "text",
    title: "What do you enjoy doing when you have free time?",
    subtitle:
      "Tell us naturally. You can mention multiple things — there are no wrong answers.",
    placeholder:
      "For example: photography, reading, coding, music, walking...",
  },
  {
    id: "wants_more_of",
    type: "text",
    title: "What do you wish you did more often?",
    subtitle:
      "Think about things you would like to make more time for.",
    placeholder:
      "For example: exercise, spending time outdoors, learning...",
  },
  {
    id: "curiosity",
    type: "text",
    title: "What have you always wanted to try?",
    subtitle:
      "It can be something completely new or something you've been curious about.",
    placeholder:
      "For example: painting, gardening, photography walks...",
  },
  {
    id: "experience_preferences",
    type: "multi",
    title: "What kind of experiences sound good to you?",
    subtitle: "Choose as many as you like.",
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
    id: "typical_free_time",
    type: "single",
    title: "How much free time do you usually have?",
    subtitle:
      "This helps TouchGrass suggest challenges you can realistically complete.",
    options: [
      "10–20 minutes",
      "20–40 minutes",
      "40–60 minutes",
      "1+ hour",
    ],
  },
  {
    id: "dislikes",
    type: "text",
    title: "Is there anything you dislike or want us to avoid?",
    subtitle:
      "Tell us about activities, environments, or situations you would rather avoid.",
    placeholder:
      "For example: crowded places, long travel, noisy environments...",
  },
];

function ProfileDiscovery() {
  const navigate = useNavigate();

  const [currentQuestion, setCurrentQuestion] = useState(0);

  const [answers, setAnswers] = useState({
    interests: "",
    wants_more_of: "",
    curiosity: "",
    experience_preferences: [],
    typical_free_time: "",
    dislikes: "",
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const question = questions[currentQuestion];

  const progress =
    ((currentQuestion + 1) / questions.length) * 100;

  const handleTextChange = (value) => {
    setAnswers((previous) => ({
      ...previous,
      [question.id]: value,
    }));
  };

  const togglePreference = (option) => {
    setAnswers((previous) => {
      const current = previous.experience_preferences;

      if (current.includes(option)) {
        return {
          ...previous,
          experience_preferences: current.filter(
            (item) => item !== option
          ),
        };
      }

      return {
        ...previous,
        experience_preferences: [...current, option],
      };
    });
  };

  const selectTime = (option) => {
    setAnswers((previous) => ({
      ...previous,
      typical_free_time: option,
    }));
  };

  const canContinue = () => {
    if (question.type === "multi") {
      return answers.experience_preferences.length > 0;
    }

    if (question.type === "single") {
      return answers.typical_free_time !== "";
    }

    return answers[question.id].trim() !== "";
  };

  const saveProfile = async () => {
    setSaving(true);
    setError("");

    try {
      const profilePayload = {
        /*
         * For now we preserve the user's natural-language answer.
         * Qwen will normalize this later.
         */
        interests: answers.interests.trim()
          ? [{ raw: answers.interests.trim() }]
          : [],

        wants_more_of: answers.wants_more_of.trim()
          ? [answers.wants_more_of.trim()]
          : [],

        curiosity: answers.curiosity.trim()
          ? [answers.curiosity.trim()]
          : [],

        experience_preferences:
          answers.experience_preferences,

        dislikes: answers.dislikes.trim()
          ? [answers.dislikes.trim()]
          : [],

        constraints: [],

        typical_free_time:
          answers.typical_free_time,
      };

      await api.post("/profile", profilePayload);

      navigate("/home");
    } catch (err) {
      console.error(err);

      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError(
          "We couldn't save your profile. Please try again."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    if (!canContinue()) return;

    if (currentQuestion === questions.length - 1) {
      await saveProfile();
      return;
    }

    setCurrentQuestion((previous) => previous + 1);
  };

  const handleBack = () => {
    if (currentQuestion === 0) {
      navigate("/home");
      return;
    }

    setCurrentQuestion((previous) => previous - 1);
    setError("");
  };

  return (
    <div className="min-h-screen bg-[#f3f7f0] px-5 py-8 text-[#1b4332]">
      <div className="mx-auto flex min-h-[90vh] max-w-3xl flex-col">

        {/* Header */}
        <header className="mb-10 flex items-center justify-between">
          <button
            onClick={() => navigate("/home")}
            className="text-sm font-medium text-[#52796f] transition hover:text-[#1b4332]"
          >
            ← Back
          </button>

          <div className="text-sm font-semibold text-[#52796f]">
            TouchGrass
          </div>
        </header>

        {/* Progress */}
        <div className="mb-10">
          <div className="mb-3 flex items-center justify-between text-sm">
            <span className="font-medium text-[#52796f]">
              Getting to know you
            </span>

            <span className="text-[#6b7f72]">
              {currentQuestion + 1} / {questions.length}
            </span>
          </div>

          <div className="h-2 overflow-hidden rounded-full bg-[#dce8d7]">
            <div
              className="h-full rounded-full bg-[#52796f] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Main Card */}
        <main className="flex flex-1 items-center justify-center">
          <div className="w-full rounded-3xl border border-[#dce8d7] bg-white p-7 shadow-sm sm:p-10">

            <div className="mb-8">
              <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-[#6a994e]">
                Let's discover your world
              </p>

              <h1 className="text-3xl font-bold leading-tight text-[#1b4332] sm:text-4xl">
                {question.title}
              </h1>

              <p className="mt-4 max-w-2xl text-base leading-7 text-[#52796f]">
                {question.subtitle}
              </p>
            </div>

            {/* Text Question */}
            {question.type === "text" && (
              <textarea
                value={answers[question.id]}
                onChange={(event) =>
                  handleTextChange(event.target.value)
                }
                placeholder={question.placeholder}
                rows={5}
                autoFocus
                className="w-full resize-none rounded-2xl border border-[#cddbc8] bg-[#f8fbf6] p-5 text-base text-[#1b4332] outline-none transition placeholder:text-[#91a496] focus:border-[#52796f] focus:ring-4 focus:ring-[#52796f]/10"
              />
            )}

            {/* Multi Select */}
            {question.type === "multi" && (
              <div className="grid gap-3 sm:grid-cols-2">
                {question.options.map((option) => {
                  const selected =
                    answers.experience_preferences.includes(option);

                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() => togglePreference(option)}
                      className={`rounded-2xl border p-5 text-left font-medium transition ${
                        selected
                          ? "border-[#52796f] bg-[#e3eee0] text-[#1b4332] shadow-sm"
                          : "border-[#d5e1d1] bg-[#f8fbf6] text-[#52796f] hover:border-[#9db39a] hover:bg-[#f0f6ed]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>{option}</span>

                        {selected && (
                          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#52796f] text-sm text-white">
                            ✓
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Single Select */}
            {question.type === "single" && (
              <div className="grid gap-3 sm:grid-cols-2">
                {question.options.map((option) => {
                  const selected =
                    answers.typical_free_time === option;

                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() => selectTime(option)}
                      className={`rounded-2xl border p-5 text-left font-medium transition ${
                        selected
                          ? "border-[#52796f] bg-[#e3eee0] text-[#1b4332] shadow-sm"
                          : "border-[#d5e1d1] bg-[#f8fbf6] text-[#52796f] hover:border-[#9db39a] hover:bg-[#f0f6ed]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>{option}</span>

                        {selected && (
                          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#52796f] text-sm text-white">
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
              <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Navigation */}
            <div className="mt-10 flex items-center justify-between gap-4">
              <button
                type="button"
                onClick={handleBack}
                className="rounded-xl px-5 py-3 font-medium text-[#52796f] transition hover:bg-[#f0f6ed]"
              >
                Back
              </button>

              <button
                type="button"
                onClick={handleNext}
                disabled={!canContinue() || saving}
                className={`rounded-xl px-7 py-3 font-semibold text-white transition ${
                  canContinue() && !saving
                    ? "bg-[#31572c] shadow-sm hover:bg-[#1b4332]"
                    : "cursor-not-allowed bg-[#a9b9a5]"
                }`}
              >
                {saving
                  ? "Saving..."
                  : currentQuestion === questions.length - 1
                    ? "Create my profile"
                    : "Continue"}
              </button>
            </div>
          </div>
        </main>

        {/* Footer hint */}
        <p className="mt-8 text-center text-sm text-[#7a8f81]">
          There are no right answers. Just tell TouchGrass what feels like you.
        </p>
      </div>
    </div>
  );
}

export default ProfileDiscovery;