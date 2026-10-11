import {
  Camera,
  Compass,
  Heart,
  BookOpen,
  Sparkles,
  Clock,
  Ban,
  Lightbulb,
} from "lucide-react";


function Section({
  icon: Icon,
  title,
  children,
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">

      <div className="mb-4 flex items-center gap-2">

        <Icon
          size={18}
          className="text-amber-400"
        />

        <h3 className="font-semibold text-white">
          {title}
        </h3>

      </div>

      {children}

    </div>
  );
}


function Tags({ items }) {

  if (!items?.length) {
    return (
      <p className="text-sm text-gray-500">
        Nothing added yet.
      </p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">

      {items.map((item, index) => (

        <span
          key={index}
          className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-300"
        >
          {item}
        </span>

      ))}

    </div>
  );
}


export default function ProfilePanel({
  profile,
}) {

  if (!profile) {
    return (
      <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8">

        <p className="text-gray-400">
          Your profile hasn't been created yet.
        </p>

      </div>
    );
  }


  return (
    <div className="space-y-5">

      {/* Interests */}

      <Section
        icon={Heart}
        title="What you enjoy"
      >

        {profile.interests?.length ? (

          <div className="space-y-4">

            {profile.interests.map(
              (interest, index) => {

                const strength =
                  Math.round(
                    (interest.strength || 0) *
                      100
                  );

                return (
                  <div key={index}>

                    <div className="mb-1 flex justify-between">

                      <span className="text-gray-200">
                        {interest.name}
                      </span>

                      <span className="text-sm text-amber-400">
                        {strength}%
                      </span>

                    </div>

                    <div className="h-2 overflow-hidden rounded-full bg-white/10">

                      <div
                        className="h-full rounded-full bg-amber-500"
                        style={{
                          width: `${strength}%`,
                        }}
                      />

                    </div>

                  </div>
                );
              }
            )}

          </div>

        ) : (
          <p className="text-gray-500">
            No interests yet.
          </p>
        )}

      </Section>


      {/* Wants more */}

      <Section
        icon={Compass}
        title="I want more of"
      >

        <Tags
          items={profile.wants_more_of}
        />

      </Section>


      {/* Curiosity */}

      <Section
        icon={Lightbulb}
        title="I'm curious about"
      >

        <Tags
          items={profile.curiosity}
        />

      </Section>


      {/* Experience */}

      <Section
        icon={Sparkles}
        title="I enjoy experiences that..."
      >

        <Tags
          items={
            profile.experience_preferences
          }
        />

      </Section>


      {/* Dislikes */}

      <Section
        icon={Ban}
        title="Things to avoid"
      >

        <Tags
          items={profile.dislikes}
        />

      </Section>


      {/* Constraints */}

      <Section
        icon={BookOpen}
        title="Constraints"
      >

        <Tags
          items={profile.constraints}
        />

      </Section>


      {/* Time */}

      <Section
        icon={Clock}
        title="Typical free time"
      >

        <p className="text-gray-200">

          {profile.typical_free_time ||
            "Not specified"}

        </p>

      </Section>

    </div>
  );
}