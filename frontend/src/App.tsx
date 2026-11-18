import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import GuestRoute from "./components/GuestRoute";
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
const AppLayout = lazy(() => pageLoaders.appLayout().then((m) => ({ default: m.AppLayout })));
const Profile = lazy(() => pageLoaders.profile().then((m) => ({ default: m.Profile })));
const ProjectsList = lazy(() => pageLoaders.projectsList().then((m) => ({ default: m.ProjectsList })));
const ProjectDetail = lazy(() => pageLoaders.projectDetail().then((m) => ({ default: m.ProjectDetail })));
const NewProject = lazy(() => pageLoaders.newProject().then((m) => ({ default: m.NewProject })));
const EditProject = lazy(() => pageLoaders.editProject().then((m) => ({ default: m.EditProject })));
const HardwareList = lazy(() => pageLoaders.hardwareList().then((m) => ({ default: m.HardwareList })));
const MyLoans = lazy(() => pageLoaders.myLoans().then((m) => ({ default: m.MyLoans })));
const ComponentsPreview = lazy(() =>
  import("./pages/dev/ComponentsPreview").then((m) => ({ default: m.ComponentsPreview })),
);
const ImageGeneratorPreview = lazy(() =>
  import("./pages/dev/ImageGeneratorPreview").then((m) => ({ default: m.ImageGeneratorPreview })),
);

function App() {
  return (
    // No visible fallback: the dark page background is already painted, so a
    // spinner would only flash for the few milliseconds a small chunk takes.
    <Suspense fallback={null}>
      <Routes>
        {/* Visitors only: signed-in members are taken into the app. */}
        <Route
          path="/"
          element={
            <GuestRoute>
              <Landing />
            </GuestRoute>
          }
        />
        <Route
          path="/login"
          element={
            <GuestRoute>
              <Login />
            </GuestRoute>
          }
        />
        <Route
          path="/register"
          element={
            <GuestRoute>
              <Register />
            </GuestRoute>
          }
        />
        {/* Everything inside the app is for signed-in members. Admin-only pages will additionally be
            wrapped in AdminRoute (Phase 3). */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/projects" element={<ProjectsList />} />
          <Route path="/projects/new" element={<NewProject />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/projects/:id/edit" element={<EditProject />} />
          <Route path="/hardware" element={<HardwareList />} />
          <Route path="/loans" element={<MyLoans />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
        {import.meta.env.DEV && <Route path="/dev/components" element={<ComponentsPreview />} />}
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
