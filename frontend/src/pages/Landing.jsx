import { Link } from "react-router-dom";

function Landing() {
  return (
    <main className="min-h-screen bg-[#eef6ef] text-[#18352a] flex items-center">
      <div className="max-w-6xl mx-auto px-6 py-20 w-full">

        <div className="max-w-3xl">
          <p className="text-sm font-bold tracking-[0.25em] text-[#527862] mb-6">
            TOUCHGRASS
          </p>

          <h1 className="text-5xl md:text-7xl font-bold leading-[1.05] tracking-tight">
            A reason to
            <span className="block text-[#4f8063]">
              step outside.
            </span>
          </h1>

          <p className="mt-7 text-lg md:text-xl text-[#60766a] max-w-2xl leading-relaxed">
            TouchGrass learns what you enjoy, understands what is possible
            right now, and gives you one meaningful thing to do offline.
          </p>

          <div className="flex flex-wrap gap-4 mt-10">
            <Link
              to="/signup"
              className="px-7 py-3.5 rounded-2xl bg-[#315f47] text-white font-semibold hover:bg-[#264d39] transition shadow-lg"
            >
              Get started
            </Link>

            <Link
              to="/signin"
              className="px-7 py-3.5 rounded-2xl bg-white border border-[#d5e2d8] text-[#315f47] font-semibold hover:bg-[#f7faf7] transition"
            >
              Sign in
            </Link>
          </div>
        </div>

        <div className="mt-20 grid md:grid-cols-3 gap-5">

          <div className="bg-white rounded-3xl p-6 border border-[#dce8df]">
            <div className="text-3xl mb-4">🌱</div>
            <h3 className="font-bold text-lg">Know you</h3>
            <p className="mt-2 text-sm text-[#708277]">
              Your interests, curiosity, preferences and dislikes become
              long-term memory.
            </p>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-[#dce8df]">
            <div className="text-3xl mb-4">☀️</div>
            <h3 className="font-bold text-lg">Understand now</h3>
            <p className="mt-2 text-sm text-[#708277]">
              Time, weather, location and your current situation shape
              today's suggestion.
            </p>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-[#dce8df]">
            <div className="text-3xl mb-4">🌿</div>
            <h3 className="font-bold text-lg">Go offline</h3>
            <p className="mt-2 text-sm text-[#708277]">
              Get one realistic challenge instead of another endless list
              of recommendations.
            </p>
          </div>

        </div>

      </div>
    </main>
  );
}

export default Landing;