import {
  useEffect,
  useState,
} from "react";

import {
  ArrowLeft,
  Sparkles,
} from "lucide-react";

import {
  getProfile,
  normalizeProfile,
} from "../services/api";

import ProfilePanel from "../components/ProfilePanel";


export default function Profile({
  onBack,
}) {

  const [profile, setProfile] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [normalizing, setNormalizing] =
    useState(false);

  const loadProfile = async () => {

    try {

      const data =
        await getProfile();

      setProfile(data);

    } catch (error) {

      console.error(
        "Failed to load profile:",
        error
      );

    } finally {

      setLoading(false);
    }
  };


  useEffect(() => {
    loadProfile();
  }, []);


  const handleNormalize = async () => {

    setNormalizing(true);

    try {

      const data =
        await normalizeProfile();

      setProfile(data);

    } catch (error) {

      console.error(
        "Profile normalization failed:",
        error
      );

      alert(
        "Could not understand the profile."
      );

    } finally {

      setNormalizing(false);
    }
  };


  return (
    <div className="min-h-screen bg-[#090706] text-white">

      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">

        <button
          onClick={onBack}
          className="mb-8 flex items-center gap-2 text-sm text-gray-400 transition hover:text-white"
        >
          <ArrowLeft size={17} />
          Back to Assistant
        </button>


        <div className="mb-8">

          <div className="mb-3 flex items-center gap-2 text-amber-400">

            <Sparkles size={20} />

            <span className="text-sm font-semibold uppercase tracking-[0.25em]">
              Your TouchGrass profile
            </span>

          </div>

          <h1 className="text-4xl font-bold">
            This is what I know about you.
          </h1>

          <p className="mt-3 max-w-2xl text-gray-400">
            Your profile is built from your
            natural answers. TouchGrass uses
            it to make better real-world
            recommendations over time.
          </p>

        </div>


        {loading ? (

          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 text-gray-400">
            Loading your profile...
          </div>

        ) : (

          <>

            <ProfilePanel
              profile={profile}
            />

            <button
              onClick={handleNormalize}
              disabled={normalizing}
              className="mt-6 rounded-xl bg-amber-500 px-5 py-3 font-semibold text-black transition hover:bg-amber-400 disabled:opacity-50"
            >

              {normalizing
                ? "Understanding..."
                : "Refresh AI understanding"}

            </button>

          </>
        )}

      </div>

    </div>
  );
}