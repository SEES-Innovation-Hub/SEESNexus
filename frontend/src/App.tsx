import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { Landing } from "./pages/landing/Landing";
import { NotFound } from "./pages/notfound/NotFound";
import { pageLoaders } from "./routes/pageLoaders";

// Only Landing (the entry page) ships in the main bundle; every other page is
// fetched when its route is first visited, so visitors never download code
// for screens they don't open. The pages use named exports, hence the .then().
// (The loaders live in routes/pageLoaders so links can prefetch the same code.)
const Login = lazy(() => pageLoaders.login().then((m) => ({ default: m.Login })));
const Register = lazy(() => pageLoaders.register().then((m) => ({ default: m.Register })));
const Profile = lazy(() => pageLoaders.profile().then((m) => ({ default: m.Profile })));
const ImageGeneratorPreview = lazy(() =>
  import("./pages/dev/ImageGeneratorPreview").then((m) => ({ default: m.ImageGeneratorPreview })),
);

function App() {
  return (
    // No visible fallback: the dark page background is already painted, so a
    // spinner would only flash for the few milliseconds a small chunk takes.
    <Suspense fallback={null}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        {import.meta.env.DEV && (
          <Route
            path="/dev/image-generator"
            element={
              <ProtectedRoute>
                <ImageGeneratorPreview />
              </ProtectedRoute>
            }
          />
        )}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

export default App;
