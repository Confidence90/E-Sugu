import { useState, useEffect } from 'react';
import { Search, TrendingUp, Users, Shield } from 'lucide-react';
import heroBanner from '../assets/hero-banner.jpg';

function HeroSection() {
  const [categories, setCategories] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState({
    keyword: '',
    category: '',
    location: '',
    minPrice: '',
    maxPrice: ''
  });

  // Récupérer les catégories depuis l'API
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/categories/');
        if (response.ok) {
          const data = await response.json();
          setCategories(data.results || data);
        }
      } catch (error) {
        console.error('Erreur lors du chargement des catégories:', error);
      }
    };

    // Récupérer les localisations depuis l'API
    const fetchLocations = async () => {
      try {
        //const response = await fetch('http://localhost:8000/api/locations/');
        if (response.ok) {
          const data = await response.json();
          setLocations(data.results || data);
        }
      } catch (error) {
        console.error('Erreur lors du chargement des localisations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCategories();
    fetchLocations();
  }, []);

  const handleSearchChange = (e) => {
    const { name, value } = e.target;
    setSearchQuery(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    // Ici vous pouvez rediriger vers la page de résultats de recherche
    // ou déclencher une recherche via API
    console.log('Recherche:', searchQuery);
    
    // Exemple de redirection vers la page de recherche avec les paramètres
    const params = new URLSearchParams();
    if (searchQuery.keyword) params.append('q', searchQuery.keyword);
    if (searchQuery.category) params.append('category', searchQuery.category);
    if (searchQuery.location) params.append('location', searchQuery.location);
    if (searchQuery.minPrice) params.append('min_price', searchQuery.minPrice);
    if (searchQuery.maxPrice) params.append('max_price', searchQuery.maxPrice);
    
    window.location.href = `/recherche?${params.toString()}`;
  };

  return (
    <section className="relative bg-gradient-to-r from-blue-600 to-blue-800 overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0 opacity-50">
        <img 
          src={heroBanner} 
          alt="Hero background" 
          className="w-full h-full object-cover"
        />
      </div>

      {/* Content */}
      <div className="relative max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-12 py-12 sm:py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Content */}
          <div className="text-center lg:text-left">
            <h1 className="text-3xl sm:text-4xl lg:text-6xl font-bold text-white mb-6">
              Achetez facilement,<br />
              <span className="text-yellow-300">Vendez rapidement</span>
            </h1>
            <p className="text-base sm:text-lg lg:text-xl text-white/80 mb-8 max-w-2xl mx-auto lg:mx-0">
              Découvrez la plus grande marketplace du Mali. Des milliers de produits et services 
              vous attendent à des prix imbattables.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row justify-center lg:justify-start gap-4 mb-12">
              <button className="bg-white text-blue-600 hover:bg-gray-100 px-6 py-3 rounded-md text-base sm:text-lg font-medium transition-colors">
                Commencer à acheter
              </button>
              <a href="/publier">
                <button className="border border-white text-white hover:bg-white hover:text-blue-600 px-6 py-3 rounded-md text-base sm:text-lg font-medium transition-colors">
                  Publier une annonce
                </button>
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 pt-8 border-t border-white/20">
              {[
                { icon: TrendingUp, value: '50K+', label: 'Annonces actives' },
                { icon: Users, value: '15K+', label: 'Utilisateurs actifs' },
                { icon: Shield, value: '100%', label: 'Sécurisé' }
              ].map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="flex items-center justify-center mb-2">
                    <stat.icon className="h-6 w-6 text-yellow-300 mr-2" />
                    <span className="text-2xl font-bold text-white">{stat.value}</span>
                  </div>
                  <p className="text-white/80 text-sm sm:text-base">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Content - Search Form */}
          <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 sm:p-8 shadow-2xl">
            <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-6">Recherche avancée</h3>
            <form onSubmit={handleSearchSubmit} className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input 
                  type="text"
                  name="keyword"
                  placeholder="Que recherchez-vous ?"
                  className="w-full pl-10 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery.keyword}
                  onChange={handleSearchChange}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <select 
                  name="category"
                  className="w-full p-3 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery.category}
                  onChange={handleSearchChange}
                >
                  <option value="">Toutes catégories</option>
                  {loading ? (
                    <option disabled>Chargement...</option>
                  ) : (
                    categories.map(category => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))
                  )}
                </select>
                <select 
                  name="location"
                  className="w-full p-3 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery.location}
                  onChange={handleSearchChange}
                >
                  <option value="">Toutes régions</option>
                  {loading ? (
                    <option disabled>Chargement...</option>
                  ) : (
                    locations.map(location => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <input 
                  type="number" 
                  name="minPrice"
                  placeholder="Prix min" 
                  className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery.minPrice}
                  onChange={handleSearchChange}
                />
                <input 
                  type="number" 
                  name="maxPrice"
                  placeholder="Prix max" 
                  className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery.maxPrice}
                  onChange={handleSearchChange}
                />
              </div>

              <button 
                type="submit"
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-md flex items-center justify-center font-medium transition-colors"
              >
                <Search className="h-5 w-5 mr-2" />
                Rechercher
              </button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;