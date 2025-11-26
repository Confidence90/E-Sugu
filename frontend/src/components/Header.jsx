import { Search, Heart, ShoppingCart, Menu, Bell, User, Plus } from 'lucide-react';
import { Button } from './ui/button';
import axios from 'axios';
import logo from '../assets/logo.jpg';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Input } from './ui/input';

function Header() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        setUser(null);
        return;
      }

      const response = await axios.get('http://localhost:8000/api/users/profile/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUser(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération du profil:', error);
      localStorage.removeItem('access_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleAuthChange = () => fetchUser();

    fetchUser();
    window.addEventListener('authChange', handleAuthChange);
    
    return () => {
      window.removeEventListener('authChange', handleAuthChange);
    };
  }, []);

  const handleLogout = async () => {
    try {
      await axios.post('http://localhost:8000/api/users/logout/', {}, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    } finally {
      localStorage.removeItem('access_token');
      setUser(null);
      navigate('/');
      window.dispatchEvent(new Event('authChange'));
    }
  };
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg sticky top-0 z-50">
  {/* Top Bar */}
  <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-12">
    <div className="flex flex-col sm:flex-row justify-between items-center py-2 text-sm border-b border-white/20 gap-2">
      <div className="flex items-center space-x-4">
        <span>🇫🇷 Français</span>
        <span>📍 Bamako, Mali</span>
      </div>
      <div className="flex flex-wrap items-center justify-center sm:justify-end gap-2 sm:gap-4">
        <span>📞 +223 90 11 70 51 / +223 73 01 68 99</span>
        <span>✉️ esugu2025@gmail.com</span>
      </div>
    </div>

    {/* Main Header */}
    <div className="flex flex-wrap items-center justify-between py-4 gap-4">
      {/* Logo */}
      <Link to="/" className="flex items-center space-x-3">
        <div className="bg-white/10 p-2 rounded-lg">
          <img src={logo} alt="E-sugu logo" className="h-10 w-10 object-contain rounded-xl" />
        </div>
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold flex items-center">
            <span className="text-green-400">E</span>
            <span className="text-yellow-300">-</span>
            <span className="text-red-500">Sugu</span>
          </h1>
          <p className="text-xs sm:text-sm text-yellow-300">Achetez & Vendez facilement</p>
        </div>
      </Link>

      {/* Search Bar */}
      <div className="flex-1 w-full sm:max-w-2xl">
        <div className="relative">
          <Input
            placeholder="Rechercher des produits, services..."
            className="pl-12 pr-24 py-3 text-base sm:text-lg bg-white text-gray-900 rounded-md focus:ring-2 focus:ring-blue-500"
          />
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <Button className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-500 hover:bg-blue-600 text-white">
            Rechercher
          </Button>
        </div>
      </div>

      {/* User Actions */}
      <div className="flex items-center space-x-2 sm:space-x-4">
        <button className="p-2 hover:bg-white/20 rounded-full">
          <Bell className="h-5 w-5" />
        </button>
        <button onClick={() => navigate('/profile?tab=wishlist')}
          className="p-2 hover:bg-white/20 rounded-full hidden sm:flex items-center">
          <Heart className="h-5 w-5" />
          <span className="ml-2">Mes Favoris</span>
        </button>
        <button className="p-2 hover:bg-white/20 rounded-full flex items-center relative">
          <ShoppingCart className="h-5 w-5" />
          <span className="ml-2 hidden sm:inline">Panier</span>
          <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            3
          </span>
        </button>

         {/* Connexion / Profil */}
      {isLoading ? (
        <div className="h-10 w-24 bg-white/20 rounded-md animate-pulse" />
      ) : user ? (
        <div className="relative group">
          <button className="flex items-center space-x-2">
            <img
              src={user.avatar ? `http://localhost:8000${user.avatar}` : 'https://i.pravatar.cc/300'}
              alt="User avatar"
              className="h-10 w-10 rounded-full object-cover border-2 border-white"
              onError={(e) => (e.target.src = 'https://i.pravatar.cc/300')}
            />
            <span className="hidden sm:inline">{user.first_name || user.username}</span>
          </button>

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl py-2 z-50 hidden group-hover:block">
            <Link
              to="/profile"
              className="block px-4 py-2 text-gray-800 hover:bg-blue-50"
            >
              Mon profil
            </Link>
            <Link
              to="/mes-annonces"
              className="block px-4 py-2 text-gray-800 hover:bg-blue-50"
            >
              Mes annonces
            </Link>
            <Link
              to="/parametres"
              className="block px-4 py-2 text-gray-800 hover:bg-blue-50"
            >
              Paramètres
            </Link>
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-gray-800 hover:bg-blue-50 border-t border-gray-100"
            >
              Déconnexion
            </button>
          </div>
        </div>
      ) : (
        <Link
          to="/login"
          className="border border-white px-4 py-2 rounded-lg flex items-center hover:bg-white hover:text-blue-600 transition-colors"
        >
          <User className="h-5 w-5 mr-2" />
          <span className="hidden sm:inline">Se connecter</span>
        </Link>
      )}
        {/* Mobile menu icon */}
        <button className="sm:hidden text-white p-2">
          <Menu className="h-5 w-5" />
        </button>
      </div>
    </div>

    {/* Navigation */}
    <nav className="overflow-x-auto pb-4">
      <div className="flex items-center justify-between">
        <div className="flex space-x-6 whitespace-nowrap text-sm font-medium">
           {[
        { name: 'Accueil', path: '/' },
        { name: 'Catégories', path: '/categories' },
        { name: 'Nouveautés', path: '/#' },
        { name: 'Promotions', path: '/#' },
        { name: 'Services', path: '/#' }
      ].map((item) => (
        <a 
          key={item.name} 
          href={item.path} 
          className="hover:text-white/80"
          // Optionnel: ajouter un style pour le lien actif
          // className={`hover:text-white/80 ${currentPath === item.path ? 'text-white font-bold' : ''}`}
        >
          {item.name}
        </a>
      ))}
        </div>
        <a href="/publier">
          <button className="border border-white text-white px-4 py-2 rounded-lg flex items-center hover:bg-white text-base hover:text-blue-600 transition-colors">
            <Plus className="h-5 w-5 mr-2" />
            <span className="hidden sm:inline">Publier une annonce</span>
          </button>
        </a>
      </div>
    </nav>
  </div>
</header>
  );
}

export default Header;