import { useResource } from "./api";
import type { Results } from "./types";

/** Every report view reads the same evaluation. */
export const useResults = () => useResource<Results>("/api/results");
