import { lazy, Suspense } from "react";
import { Outlet, Route, Routes } from "react-router-dom";
import AdminRoute from "./components/AdminRoute";
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
const Dashboard = lazy(() => pageLoaders.dashboard().then((m) => ({ default: m.Dashboard })));
const AdminOverview = lazy(() => pageLoaders.adminOverview().then((m) => ({ default: m.AdminOverview })));
const AdminLoans = lazy(() => pageLoaders.adminLoans().then((m) => ({ default: m.AdminLoans })));
const AdminUsers = lazy(() => pageLoaders.adminUsers().then((m) => ({ default: m.AdminUsers })));
const AdminHardware = lazy(() => pageLoaders.adminHardware().then((m) => ({ default: m.AdminHardware })));
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
        {/* Everything inside the app is for signed-in members; /admin pages are
            for admins only on top of that. */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/projects" element={<ProjectsList />} />
          <Route path="/projects/new" element={<NewProject />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/projects/:id/edit" element={<EditProject />} />
          <Route path="/hardware" element={<HardwareList />} />
          <Route path="/loans" element={<MyLoans />} />
          <Route path="/profile" element={<Profile />} />
          <Route
            element={
              <AdminRoute>
                <Outlet />
              </AdminRoute>
            }
          >
            <Route path="/admin" element={<AdminOverview />} />
            <Route path="/admin/loans" element={<AdminLoans />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/hardware" element={<AdminHardware />} />
          </Route>
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
