import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import BottomBar from "../components/BottomBar";
import { Outlet } from "react-router-dom";

export default function DashboardLayout() {
 return (
    <div className="flex">
      {/* Sidebar visible seulement sur desktop */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <div className="lg:ml-64 flex-1">
        
        <main className="pt-20 pb-16 px-6"> {/* pb-16 = espace pour la BottomBar */}
          <Outlet />
        </main>
      </div>

      {/* BottomBar visible uniquement sur mobile */}
      <BottomBar />
    </div>
  );
}
