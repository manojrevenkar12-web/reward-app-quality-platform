import { useEffect, useState } from "react";

export type View = "players" | "release" | "production" | "plan" | "tickets";
export const VIEWS: View[] = ["players", "release", "production", "plan", "tickets"];

function read(): View {
  const [, v] = window.location.hash.split("/");
  return VIEWS.includes(v as View) ? (v as View) : "players";
}

export function useRoute(): View {
  const [r, setR] = useState(read);
  useEffect(() => {
    const on = () => setR(read());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return r;
}

export const go = (view: View) => {
  window.location.hash = `/${view}`;
};
