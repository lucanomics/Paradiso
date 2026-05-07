import { createBrowserRouter } from "react-router";
import Landing from "./Landing";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Landing,
  },
]);
