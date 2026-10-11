import { useCallback, useEffect, useState } from "react";

const OPT_IN_KEY = "touchgrass_location_optin";

/**
 * Optional browser location.
 *
 * Nothing is requested until the user presses "Use my location", and the
 * coordinates live only in memory (never in localStorage). The app works the
 * same whether the status is "idle", "denied" or "unsupported".
 *
 * status: "idle" | "asking" | "granted" | "denied" | "unavailable" | "unsupported"
 */
export default function useBrowserLocation() {
  const [status, setStatus] = useState(
    typeof navigator !== "undefined" && "geolocation" in navigator
      ? "idle"
      : "unsupported"
  );
  const [coords, setCoords] = useState(null);

  const request = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setStatus("unsupported");
      return;
    }

    setStatus("asking");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setStatus("granted");

        try {
          // Remember that the user chose to share, so next visit can reuse
          // the permission they already granted (no new prompt).
          localStorage.setItem(OPT_IN_KEY, "1");
        } catch {
          /* storage unavailable: fine */
        }
      },
      (error) => {
        setCoords(null);
        // 1 = permission denied; anything else = could not get a position.
        setStatus(error.code === 1 ? "denied" : "unavailable");
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 5 * 60 * 1000 }
    );
  }, []);

  const clear = useCallback(() => {
    setCoords(null);
    setStatus("idle");

    try {
      localStorage.removeItem(OPT_IN_KEY);
    } catch {
      /* ignore */
    }
  }, []);

  // Only if the user pressed "Use my location" before AND the browser still
  // says permission is granted: quietly pick it up again. Never prompts.
  useEffect(() => {
    let optedIn = false;

    try {
      optedIn = localStorage.getItem(OPT_IN_KEY) === "1";
    } catch {
      optedIn = false;
    }

    if (!optedIn || !navigator.permissions?.query) {
      return;
    }

    navigator.permissions
      .query({ name: "geolocation" })
      .then((result) => {
        if (result.state === "granted") {
          request();
        }
      })
      .catch(() => {});
  }, [request]);

  return { status, coords, request, clear };
}
