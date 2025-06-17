import { useNewsSelection } from "./useNewsSelection";

/**
 * Orchestrates the scoring submission flow:
 *  - snapshot the IDs at click time (UD §2.3.9)
 *  - prevent duplicate submissions (UD §2.3.8)
 *  - on success clear processed selections (UD §2.5.4)
 */
export const useNewsScoring = () => {
  const selection = useNewsSelection();

  return {
    selection,
  }
}