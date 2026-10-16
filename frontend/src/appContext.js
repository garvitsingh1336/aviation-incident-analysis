import { createContext, useContext } from "react";

/** App-wide helpers made available to every view (e.g. opening a report). */
export const AppContext = createContext({
  openReport: () => {},
  navigate: () => {},
});

export const useApp = () => useContext(AppContext);
