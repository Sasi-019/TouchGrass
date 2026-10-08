import {
  MapPin,
  Clock,
  Sparkles,
} from "lucide-react";


export default function ActivityCard({
  activity,
}) {

  if (!activity) {
    return null;
  }

  const place =
    activity.place;


  return (
    <div className="rounded-3xl border border-amber-500/20 bg-gradient-to-br from-amber-500/10 to-white/[0.03] p-6 shadow-xl">

      <div className="mb-4 flex items-center gap-2 text-amber-400">
        <Sparkles size={18} />

        <span className="text-sm font-medium">
          Your TouchGrass challenge
        </span>
      </div>


      <h2 className="text-2xl font-bold text-white">
        {activity.title}
      </h2>


      <p className="mt-4 leading-7 text-gray-300">
        {activity.description}
      </p>


      <div className="mt-5 flex flex-wrap gap-3">

        {activity.duration_minutes && (
          <div className="flex items-center gap-2 rounded-full bg-white/5 px-3 py-2 text-sm text-gray-300">
            <Clock size={15} />

            {activity.duration_minutes} min
          </div>
        )}


        {place?.name && (
          <div className="flex items-center gap-2 rounded-full bg-white/5 px-3 py-2 text-sm text-gray-300">
            <MapPin size={15} />

            {place.name}
          </div>
        )}

      </div>


      {activity.reason && (
        <div className="mt-5 border-t border-white/10 pt-4 text-sm text-gray-400">
          {activity.reason}
        </div>
      )}

    </div>
  );
}