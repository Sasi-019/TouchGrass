import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function Activity() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
<<<<<<< HEAD
  const [memoryNote, setMemoryNote] = useState("");
=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchActivity = async () => {
      try {
<<<<<<< HEAD
        const response = await api.get(`/activities/${id}`);

        setActivity(response.data);
      } catch (err) {
        console.error(err);
        setError(
          err.response?.status === 404
            ? "Activity not found."
            : "Unable to load this activity."
        );
=======
        const response = await api.get("/activities");
        const foundActivity = response.data.find(
          (item) => item.id === Number(id)
        );

        if (!foundActivity) {
          setError("Activity not found.");
          return;
        }

        setActivity(foundActivity);
      } catch (err) {
        console.error(err);
        setError("Unable to load this activity.");
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
      } finally {
        setLoading(false);
      }
    };

    fetchActivity();
  }, [id]);

<<<<<<< HEAD
  const submitFeedback = async (didIt = true) => {
    if (didIt && !completed) {
=======
  const submitFeedback = async () => {
    if (!completed) {
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
      setError("Please mark the activity as completed first.");
      return;
    }

<<<<<<< HEAD
    if (didIt && rating === 0) {
=======
    if (rating === 0) {
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
      setError("Please give the activity a rating.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

<<<<<<< HEAD
      const response = await api.post(`/activities/${id}/feedback`, {
        rating: didIt ? rating : null,
        completed: didIt ? "yes" : "no",
        comment,
      });

      setMemoryNote(response.data?.memory_note || "");
      setSuccess(true);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Unable to save your feedback."
      );
=======
      await api.post(`/activities/${id}/feedback`, {
        rating,
        completed: "yes",
        comment,
      });

      setSuccess(true);
    } catch (err) {
      console.error(err);
      setError("Unable to save your feedback.");
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f3f7f0] flex items-center justify-center">
        <p className="text-lg text-[#31572c]">
          Loading your challenge...
        </p>
      </div>
    );
  }

  if (error && !activity) {
    return (
      <div className="min-h-screen bg-[#f3f7f0] flex items-center justify-center">
        <div className="text-center">
          <p className="mb-5 text-red-600">{error}</p>

          <button
            onClick={() => navigate("/home")}
            className="rounded-xl bg-[#31572c] px-5 py-3 text-white"
          >
            Back to home
          </button>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#f3f7f0] px-6 py-12">
        <div className="mx-auto max-w-2xl text-center">

          <div className="mb-6 text-6xl">🌱</div>

          <h1 className="text-4xl font-bold text-[#1b4332]">
            Nice work.
          </h1>

          <p className="mt-4 text-lg leading-relaxed text-[#52796f]">
            You stepped away from the screen and did something real.
            Your feedback will help TouchGrass understand what you enjoy.
          </p>

<<<<<<< HEAD
          {memoryNote && (
            <p className="mx-auto mt-6 max-w-xl rounded-2xl bg-white p-5 text-left text-[#31572c] shadow-sm">
              <span className="block text-sm font-semibold uppercase tracking-widest text-[#6a994e]">
                What I learned
              </span>
              <span className="mt-2 block">{memoryNote}</span>
            </p>
          )}

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
          <button
            onClick={() => navigate("/home")}
            className="mt-8 rounded-xl bg-[#31572c] px-6 py-3 font-medium text-white hover:bg-[#264523]"
          >
            Back to home
          </button>

        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f3f7f0] px-6 py-10">
      <div className="mx-auto max-w-3xl">

        <button
          onClick={() => navigate("/home")}
          className="mb-8 text-sm font-medium text-[#52796f] hover:text-[#31572c]"
        >
          ← Back to activities
        </button>

        <div className="rounded-3xl bg-white p-8 shadow-sm md:p-10">

          <p className="text-sm font-medium uppercase tracking-widest text-[#6a994e]">
            {activity.category || "Challenge"}
          </p>

          <h1 className="mt-3 text-4xl font-bold text-[#1b4332]">
            {activity.title}
          </h1>

          {activity.duration_minutes && (
            <div className="mt-4 inline-block rounded-full bg-[#edf6e9] px-4 py-2 text-sm text-[#31572c]">
              ⏱ {activity.duration_minutes} minutes
            </div>
          )}

          <div className="mt-8 rounded-2xl bg-[#f3f7f0] p-6">
            <p className="text-lg leading-8 text-[#31572c]">
              {activity.description}
            </p>
          </div>

          <div className="mt-8">
            <label className="flex cursor-pointer items-center gap-3">
              <input
                type="checkbox"
                checked={completed}
                onChange={(e) => setCompleted(e.target.checked)}
                className="h-5 w-5 accent-[#31572c]"
              />

              <span className="text-lg font-medium text-[#1b4332]">
                I completed this challenge
              </span>
            </label>
          </div>

<<<<<<< HEAD
          {!completed && (
            <button
              onClick={() => submitFeedback(false)}
              disabled={submitting}
              className="mt-6 text-sm font-medium text-[#52796f] underline-offset-4 hover:underline disabled:opacity-60"
            >
              I didn't get to this one
            </button>
          )}

          {!completed && error && (
            <p className="mt-4 text-sm text-red-600">{error}</p>
          )}

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
          {completed && (
            <div className="mt-10 border-t border-[#e5eee1] pt-8">

              <h2 className="text-2xl font-bold text-[#1b4332]">
                How was it?
              </h2>

              <p className="mt-2 text-[#52796f]">
                Your feedback helps TouchGrass learn what works for you.
              </p>

              <div className="mt-6">
                <p className="mb-3 font-medium text-[#31572c]">
                  Your rating
                </p>

                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <button
                      key={value}
                      onClick={() => setRating(value)}
                      className={`text-3xl transition ${
                        value <= rating
                          ? "opacity-100"
                          : "opacity-30 hover:opacity-70"
                      }`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-6">
                <label className="mb-2 block font-medium text-[#31572c]">
                  Anything you want to say?
                </label>

                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="How did it feel?"
                  rows={4}
                  className="w-full rounded-2xl border border-[#dbe8d5] bg-[#fbfdf9] p-4 outline-none focus:border-[#6a994e]"
                />
              </div>

              {error && (
                <p className="mt-4 text-sm text-red-600">
                  {error}
                </p>
              )}

              <button
<<<<<<< HEAD
                onClick={() => submitFeedback(true)}
=======
                onClick={submitFeedback}
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
                disabled={submitting}
                className="mt-6 rounded-xl bg-[#31572c] px-6 py-3 font-medium text-white transition hover:bg-[#264523] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? "Saving..." : "Save my feedback"}
              </button>

            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default Activity;