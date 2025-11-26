import { Link, NavLink } from "react-router-dom";
import { Home, Package, Folder, Percent, Megaphone, FileText } from "lucide-react";

export default function Sidebar() {
  const menuItems = [
    { name: "Dashboard", path: "/", icon: <Home size={18} /> },
    { name: "Commandes", path: "/commandes", icon: <Package size={18} /> },
    { name: "Produits", path: "/produits", icon: <Folder size={18} /> },
    { name: "Promotions", path: "/promotions", icon: <Percent size={18} /> },
    { name: "Promouvoir", path: "/promouvoir", icon: <Megaphone size={18} /> },
    { name: "Relevés de compte", path: "/releves", icon: <FileText size={18} /> },
  ];

  return (
    <aside className="w-64 bg-white border-r h-screen fixed left-0 top-0 flex flex-col">
      <div className="p-4 flex items-center gap-2 border-b">
        <span className="text-orange-500 font-bold text-xl">VC</span>
        <span className="font-semibold">Vendor Center</span>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 rounded-md transition ${
                    isActive
                      ? "bg-orange-100 text-orange-600 font-semibold"
                      : "hover:bg-gray-100 text-gray-700"
                  }`
                }
              >
                {item.icon}
                {item.name}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t">
        <button className="w-full bg-orange-500 text-white py-2 rounded-md font-medium">
          Choisir une boutique 🏪
        </button>
      </div>
    </aside>
  );
}
