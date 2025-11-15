import { Refine } from "@refinedev/core";
import {
  ThemedLayoutV2,
  RefineSnackbarProvider,
  notificationProvider,
  ErrorComponent,
} from "@refinedev/mui";
import CssBaseline from "@mui/material/CssBaseline";
import GlobalStyles from "@mui/material/GlobalStyles";
import routerBindings, {
  DocumentTitleHandler,
  UnsavedChangesNotifier,
} from "@refinedev/react-router-v6";
import dataProvider from "@refinedev/simple-rest";
import { BrowserRouter, Route, Routes, Outlet } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <CssBaseline />
      <GlobalStyles styles={{ html: { WebkitFontSmoothing: "auto" } }} />
      <RefineSnackbarProvider>
        <Refine
          dataProvider={dataProvider("http://localhost:8000/api")}
          notificationProvider={notificationProvider}
          routerProvider={routerBindings}
          resources={[
            {
              name: "projects",
              list: "/projects",
            },
          ]}
          options={{
            syncWithLocation: true,
            warnWhenUnsavedChanges: true,
          }}
        >
          <Routes>
            <Route
              element={
                <ThemedLayoutV2>
                  <Outlet />
                </ThemedLayoutV2>
              }
            >
              <Route
                index
                element={
                  <div style={{ padding: "24px" }}>
                    <h1>Welcome to Borg Tools Scanner</h1>
                    <p>Frontend is working! Now we'll add project list component.</p>
                  </div>
                }
              />
              <Route path="*" element={<ErrorComponent />} />
            </Route>
          </Routes>
          <UnsavedChangesNotifier />
          <DocumentTitleHandler />
        </Refine>
      </RefineSnackbarProvider>
    </BrowserRouter>
  );
}

export default App;
