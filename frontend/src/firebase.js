// Firebase Authentication (optional).
// If the VITE_FIREBASE_* env vars are not set, sign-in with Google is hidden
// and the app falls back to email/password auth against our own backend.
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const firebaseConfigured = Boolean(config.apiKey && config.projectId);

let auth = null;
if (firebaseConfigured) {
  try {
    const app = initializeApp(config);
    auth = getAuth(app);
  } catch (e) {
    console.warn("Firebase init failed:", e);
  }
}

// Sign in with Google and return the Firebase ID token (to exchange with backend).
export async function googleSignIn() {
  if (!auth) throw new Error("Firebase sign-in is not configured.");
  const provider = new GoogleAuthProvider();
  const result = await signInWithPopup(auth, provider);
  return await result.user.getIdToken();
}
