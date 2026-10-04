// The page's sentences (§4.7), verbatim.

export const LOADING = "Opening the Library…";
export const STARTING = "Starting the Library's backend…";
export const BACKEND_FAILED = (detail: string) =>
  `The Library's backend did not start: ${detail}`;
export const NOT_APPROVED =
  "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.";
export const BACKEND_UNSUPPORTED = (detail: string) =>
  `This agent-server cannot run the Library's backend: ${detail}`;
export const NO_FRAMES =
  "This version of Canvas cannot show an App's own pages. Update the app.";
export const TRY_AGAIN = "Try again";
export const STILL_STARTING = "it was still starting after 45 seconds.";
