import { NavLink } from "react-router-dom";
import { Home, Package, Folder, Menu } from "lucide-react";

export default function BottomBar() {
  const items = [
    { name: "Home", path: "/", icon: <Home size={20} /> },
    { name: "Commandes", path: "/commandes", icon: <Package size={20} /> },
    { name: "Produits", path: "/produits", icon: <Folder size={20} /> },
    { name: "Menu", path: "/menu", icon: <Menu size={20} /> },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-md flex justify-around py-2 lg:hidden">
      {items.map((item) => (
        <NavLink
          key={item.name}
          to={item.path}
          className={({ isActive }) =>
            `flex flex-col items-center text-sm ${
              isActive ? "text-orange-500 font-semibold" : "text-gray-600"
            }`
          }
        >
          {item.icon}
          <span>{item.name}</span>
        </NavLink>
      ))}
    </nav>
  );
}
