import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Camera,
  Compass,
  Heart,
  Leaf,
  MapPin,
  Mountain,
  Pencil,
  Sparkles,
  Timer,
  WandSparkles,
  BookOpen,
} from "lucide-react";
import { getProfile } from "../services/api";

const interestIcons = {
  photography: Camera,
  nature: Leaf,
  reading: BookOpen,
  exploring: Compass,
  travel: MapPin,
};

function getIconForInterest(name) {
  const normalized = name.toLowerCase();

  for (const key of Object.keys(interestIcons)) {
    if (normalized.includes(key)) {
      return interestIcons[key];
    }
  }

  return Sparkles;
}

export default function Profile() {
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getProfile();

      setProfile(data);
    } catch (err) {
      console.error("Failed to load profile:", err);

      if (err.response?.status === 404) {
        setError("You haven't created your profile yet.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load your profile."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#120b08] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">
            Loading your profile...
          </p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-[#120b08] text-white flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center rounded-3xl border border-white/10 bg-white/[0.04] p-8">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-amber-500/10 flex items-center justify-center mb-5">
            <Sparkles className="w-8 h-8 text-amber-400" />
          </div>

          <h1 className="text-2xl font-bold mb-3">
            Your profile isn't ready yet
          </h1>

          <p className="text-gray-400 mb-7">
            {error ||
              "Tell TouchGrass a little about yourself first."}
          </p>

          <button
            onClick={() => navigate("/profile-discovery")}
            className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-5 py-3 font-semibold text-black hover:from-amber-400 hover:to-orange-400 transition"
          >
            Create my profile
          </button>

          <button
            onClick={() => navigate("/home")}
            className="w-full mt-3 rounded-xl border border-white/10 px-5 py-3 text-gray-300 hover:bg-white/5 transition"
          >
            Back to home
          </button>
        </div>
      </div>
    );
  }

  const interests = Array.isArray(profile.interests)
    ? profile.interests
    : [];

  const wantsMore = Array.isArray(profile.wants_more_of)
    ? profile.wants_more_of
    : [];

  const curiosity = Array.isArray(profile.curiosity)
    ? profile.curiosity
    : [];

  const preferences = Array.isArray(
    profile.experience_preferences
  )
    ? profile.experience_preferences
    : [];

  return (
    <div className="min-h-screen bg-[#120b08] text-white">
      {/* Background decoration */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-orange-600/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-5xl mx-auto px-4 py-8 md:py-12">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate("/home")}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to home</span>
          </button>

          <button
            onClick={() => navigate("/profile-discovery")}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm text-gray-300 hover:bg-white/[0.08] hover:text-white transition"
          >
            <Pencil className="w-4 h-4" />
            Edit profile
          </button>
        </div>

        {/* Hero Card */}
        <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-amber-500/10 via-white/[0.04] to-orange-500/5 p-6 md:p-8 mb-6">
          <div className="flex flex-col md:flex-row md:items-center gap-6">

            {/* Avatar */}
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/10">
              <Sparkles className="w-11 h-11 text-black" />
            </div>

            <div className="flex-1">
              <p className="text-amber-400 text-sm font-semibold uppercase tracking-wider mb-2">
                Your TouchGrass profile
              </p>

              <h1 className="text-3xl md:text-4xl font-bold mb-2">
                Your offline personality
              </h1>

              <p className="text-gray-400 max-w-2xl">
                TouchGrass uses what you enjoy, what you're
                curious about, and how you like to spend your
                time to create better real-world experiences.
              </p>
            </div>
          </div>
        </div>

        {/* Main grid */}
        <div className="grid lg:grid-cols-2 gap-6">

          {/* Interests */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                <Heart className="w-5 h-5 text-amber-400" />
              </div>

              <div>
                <h2 className="font-semibold text-lg">
                  What you enjoy
                </h2>
                <p className="text-sm text-gray-500">
                  Your strongest interests
                </p>
              </div>
            </div>

            {interests.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {interests.map((interest, index) => {
                  const name =
                    typeof interest === "string"
                      ? interest
                      : interest.name;

                  const strength =
                    typeof interest === "object"
                      ? interest.strength
                      : null;

                  const Icon = getIconForInterest(
                    String(name || "")
                  );

                  return (
                    <div
                      key={`${name}-${index}`}
                      className="rounded-2xl border border-white/10 bg-black/10 p-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-amber-500/10 flex items-center justify-center">
                          <Icon className="w-4 h-4 text-amber-400" />
                        </div>

                        <div className="min-w-0">
                          <p className="font-medium capitalize truncate">
                            {name}
                          </p>

                          {typeof strength === "number" && (
                            <p className="text-xs text-gray-500 mt-1">
                              {Math.round(strength * 100)}% interest
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyText text="No interests recorded yet." />
            )}
          </section>

          {/* Wants More */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                <Leaf className="w-5 h-5 text-green-400" />
              </div>

              <div>
                <h2 className="font-semibold text-lg">
                  You want more of
                </h2>
                <p className="text-sm text-gray-500">
                  Things you'd like to do more often
                </p>
              </div>
            </div>

            {wantsMore.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {wantsMore.map((item, index) => (
                  <Tag
                    key={`${item}-${index}`}
                    text={item}
                  />
                ))}
              </div>
            ) : (
              <EmptyText text="Nothing added yet." />
            )}
          </section>

          {/* Curiosity */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <WandSparkles className="w-5 h-5 text-purple-400" />
              </div>

              <div>
                <h2 className="font-semibold text-lg">
                  Curious about
                </h2>
                <p className="text-sm text-gray-500">
                  Things you want to explore
                </p>
              </div>
            </div>

            {curiosity.length > 0 ? (
              <div className="space-y-2">
                {curiosity.map((item, index) => (
                  <div
                    key={`${item}-${index}`}
                    className="flex items-center gap-3 rounded-xl bg-white/[0.03] px-4 py-3"
                  >
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <span className="text-gray-300 capitalize">
                      {item}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyText text="Nothing added yet." />
            )}
          </section>

          {/* Experience Preferences */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <Compass className="w-5 h-5 text-blue-400" />
              </div>

              <div>
                <h2 className="font-semibold text-lg">
                  Experience style
                </h2>
                <p className="text-sm text-gray-500">
                  How you like to spend your time
                </p>
              </div>
            </div>

            {preferences.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {preferences.map((item, index) => (
                  <Tag
                    key={`${item}-${index}`}
                    text={item}
                    blue
                  />
                ))}
              </div>
            ) : (
              <EmptyText text="No preferences recorded yet." />
            )}
          </section>
        </div>

        {/* Preferences summary */}
        <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.04] p-6">
          <h2 className="font-semibold text-lg mb-5">
            Your activity preferences
          </h2>

          <div className="grid md:grid-cols-3 gap-4">

            <InfoCard
              icon={<Timer className="w-5 h-5" />}
              label="Typical free time"
              value={
                profile.typical_free_time ||
                "Not specified"
              }
            />

            <InfoCard
              icon={<Mountain className="w-5 h-5" />}
              label="Adventure level"
              value={
                profile.adventure_level ||
                "Not specified"
              }
            />

            <InfoCard
              icon={<MapPin className="w-5 h-5" />}
              label="Activity style"
              value={
                preferences.length > 0
                  ? preferences
                      .slice(0, 2)
                      .join(" + ")
                  : "Personalized"
              }
            />

          </div>
        </section>

        {/* Bottom CTA */}
        <div className="mt-6 rounded-3xl border border-amber-500/20 bg-amber-500/[0.05] p-6 text-center">
          <Sparkles className="w-7 h-7 text-amber-400 mx-auto mb-3" />

          <h2 className="text-xl font-semibold mb-2">
            Ready to touch some grass?
          </h2>

          <p className="text-gray-400 text-sm mb-5">
            Your profile is ready. Let TouchGrass find
            something meaningful for you to do.
          </p>

          <button
            onClick={() => navigate("/home")}
            className="rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-3 font-semibold text-black hover:from-amber-400 hover:to-orange-400 transition"
          >
            Find something to do
          </button>
        </div>

      </div>
    </div>
  );
}

function Tag({ text, blue = false }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1.5 text-sm capitalize ${
        blue
          ? "border-blue-500/20 bg-blue-500/10 text-blue-300"
          : "border-amber-500/20 bg-amber-500/10 text-amber-300"
      }`}
    >
      {text}
    </span>
  );
}

function EmptyText({ text }) {
  return (
    <p className="text-sm text-gray-500 py-3">
      {text}
    </p>
  );
}

function InfoCard({ icon, label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className="text-amber-400">
          {icon}
        </div>

        <span className="text-sm text-gray-500">
          {label}
        </span>
      </div>

      <p className="text-gray-200 capitalize font-medium">
        {value}
      </p>
    </div>
  );
}