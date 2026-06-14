import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import PrismBackdrop from "@/components/landing/PrismBackdrop";

export default function Layout() {
  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Subtle ambient prism behind the app chrome — kept low-opacity for readability. */}
      <PrismBackdrop className="prism-ambient" />
      <Navbar />
      <main className="relative z-10 flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
