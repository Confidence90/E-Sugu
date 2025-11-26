import axios from 'axios';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Home, Building, Star, Heart, MapPin, Ruler, Bed, Bath
} from 'lucide-react';
import { Skeleton } from './ui/skeleton';

// Hook personnalisé pour les favoris (déplacé à l'extérieur du composant)
const useFavorites = () => {
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    const fetchFavorites = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) return;
      try {
        const res = await axios.get("http://localhost:8000/api/favorites/listings/", {
          headers: { Authorization: `Bearer ${token}` }
        });
        setFavorites(res.data.results.map(fav => fav.listing.id));
      } catch (e) { 
        console.error("Erreur lors du chargement des favoris:", e);
      }
    };
    fetchFavorites();
  }, []);

  return [favorites, setFavorites];
};

// Composant Skeleton pour le chargement
const SkeletonCard = () => {
  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      <Skeleton className="h-60 w-full" />
      <div className="p-5 space-y-3">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <div className="flex justify-between">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-20" />
        </div>
      </div>
    </div>
  );
};

function ProductsSection() {
  const [activeTab, setActiveTab] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const propertiesPerPage = 40;
  const [favorites, setFavorites] = useFavorites();

  // Fetch data from API
  useEffect(() => {
    const fetchProperties = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/listings/');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        
        // Transform the data to match our needs
        const transformedProperties = data.results.map(item => ({
          id: item.id,
          title: item.title,
          description: item.description,
          price: parseFloat(item.price),
          type: item.type === 'sale' ? 'À vendre' : 'À louer',
          condition: item.condition,
          image: item.images?.[0]?.image || 'https://source.unsplash.com/random/600x400/?property,house',
          location: item.location,
          isFeatured: item.is_featured,
          category: item.category_name,
          bedrooms: Math.floor(Math.random() * 5) + 1,
          bathrooms: Math.floor(Math.random() * 3) + 1,
          area: `${Math.floor(Math.random() * 200) + 50}m²`
        }));
        
        setProperties(transformedProperties);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchProperties();
  }, []);

  // Filter properties based on active tab avec useMemo
  const filteredProperties = useMemo(() => {
    return {
      all: [...properties].sort(() => 0.5 - Math.random()),
      featured: properties.filter(p => p.isFeatured),
      sale: properties.filter(p => p.type === 'À vendre'),
      rent: properties.filter(p => p.type === 'À louer'),
    };
  }, [properties]);

  // Pagination logic
  const indexOfLastProperty = currentPage * propertiesPerPage;
  const indexOfFirstProperty = indexOfLastProperty - propertiesPerPage;
  const currentProperties = filteredProperties[activeTab].slice(indexOfFirstProperty, indexOfLastProperty);
  const totalPages = Math.ceil(filteredProperties[activeTab].length / propertiesPerPage);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  const propertyCategories = useMemo(() => [
    { name: 'Tous', value: 'all', icon: Home, count: properties.length },
    { name: 'Vedettes', value: 'featured', icon: Star, count: properties.filter(p => p.isFeatured).length },
    { name: 'À vendre', value: 'sale', icon: Building, count: properties.filter(p => p.type === 'À vendre').length },
    { name: 'À louer', value: 'rent', icon: Home, count: properties.filter(p => p.type === 'À louer').length }
  ], [properties]);

  if (loading) return (
    <div className="container mx-auto px-4 py-16">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </div>
  );

  if (error) return (
    <div className="text-center py-16">
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded max-w-md mx-auto">
        <p>Erreur lors du chargement des annonces</p>
        <p className="text-sm">{error}</p>
      </div>
    </div>
  );

  return (
    <section className="py-16 bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4 font-serif">Nos propriétés exclusives</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Découvrez des biens immobiliers exceptionnels adaptés à vos besoins
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-12">
          <div className="inline-flex bg-white rounded-full shadow-sm p-1 border border-gray-200">
            {propertyCategories.map((tab) => {
              const IconComponent = tab.icon;
              return (
                <button
                  key={tab.value}
                  onClick={() => {
                    setActiveTab(tab.value);
                    setCurrentPage(1);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className={`px-6 py-2 rounded-full text-sm font-medium transition-all flex items-center ${
                    activeTab === tab.value 
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  <IconComponent className="h-4 w-4 mr-2" />
                  {tab.name} 
                  <span className="ml-1 bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">
                    {tab.count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Property Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {currentProperties.map((property) => (
            <PropertyCard 
              key={property.id} 
              property={property} 
              isFavorite={favorites.includes(property.id)}
              setFavorites={setFavorites}
            />
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center mt-12">
            <nav className="flex items-center space-x-2">
              <button 
                onClick={() => paginate(1)}
                disabled={currentPage === 1}
                className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-50 transition"
              >
                « Début
              </button>
              <button
                onClick={() => paginate(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-50 transition"
              >
                Précédent
              </button>
              
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const page = currentPage <= 3 
                  ? i + 1 
                  : currentPage >= totalPages - 2 
                    ? totalPages - 4 + i 
                    : currentPage - 2 + i;
                return (
                  <button
                    key={page}
                    onClick={() => paginate(page)}
                    className={`px-4 py-2 rounded-lg ${
                      currentPage === page 
                        ? 'bg-blue-600 text-white shadow-md' 
                        : 'border border-gray-300 hover:bg-gray-100'
                    } transition`}
                  >
                    {page}
                  </button>
                );
              })}
              
              <button
                onClick={() => paginate(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-50 transition"
              >
                Suivant
              </button>
              <button 
                onClick={() => paginate(totalPages)}
                disabled={currentPage === totalPages}
                className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 disabled:opacity-50 transition"
              >
                Fin »
              </button>
            </nav>
          </div>
        )}
      </div>
    </section>
  );
}

// Composant PropertyCard séparé pour une meilleure lisibilité
const PropertyCard = ({ property, isFavorite: initialIsFavorite, setFavorites }) => {
  const navigate = useNavigate();
  const [isFavorite, setIsFavorite] = useState(initialIsFavorite);
  const [isLoading, setIsLoading] = useState(false);

  // Mise à jour de l'état si la prop initialIsFavorite change
  useEffect(() => {
    setIsFavorite(initialIsFavorite);
  }, [initialIsFavorite]);

  const handleFavoriteClick = async (e) => {
    e.stopPropagation(); 
    e.preventDefault();
    
    if (isLoading) return;
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Veuillez vous connecter pour ajouter aux favoris');
      navigate('/login');
      return;
    }

    setIsLoading(true);
    
    try {
      if (isFavorite) {
        // Supprimer des favoris
        await axios.delete(`http://localhost:8000/api/favorites/listings/remove/${property.id}/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setIsFavorite(false);
        setFavorites(prev => prev.filter(id => id !== property.id));
        toast.success('Annonce retirée des favoris');
      } else {
        // Ajouter aux favoris
        await axios.post('http://localhost:8000/api/favorites/listings/add/', 
          { listing_id: property.id },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setIsFavorite(true);
        setFavorites(prev => [...prev, property.id]);
        toast.success('Annonce ajoutée aux favoris');
      }
    } catch (error) {
      console.error('Erreur mise à jour favoris:', error);
      if (error.response?.status === 401) {
        toast.error('Session expirée, veuillez vous reconnecter');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        navigate('/login');
      } else {
        toast.error('Erreur lors de la mise à jour des favoris');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100">
      <div className="relative h-60 overflow-hidden">
        <img 
          src={property.image} 
          alt={property.title} 
          onClick={() => navigate(`/details/${property.id}`)}
          className="cursor-pointer w-full h-full object-cover transition-transform duration-500 hover:scale-105"
          loading="lazy"
          onError={(e) => {
            e.target.src = 'https://source.unsplash.com/random/600x400/?property,house';
          }}
        />
        {property.isFeatured && (
          <div className="absolute top-3 left-3 bg-gradient-to-r from-blue-600 to-blue-800 text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center shadow-md">
            <Star className="h-3 w-3 mr-1 fill-current" />
            Vedette
          </div>
        )}
        <button 
          onClick={handleFavoriteClick}
          disabled={isLoading}
          className={`absolute top-3 right-3 p-2 rounded-full shadow-md transition-colors ${
            isFavorite 
              ? 'bg-red-500 text-white' 
              : 'bg-white/90 backdrop-blur-sm hover:bg-white'
          } ${isLoading ? 'animate-pulse' : ''}`}
        >
          <Heart className={`h-5 w-5 ${isFavorite ? 'fill-current' : ''}`} />
        </button>
      </div>
      
      <div className="p-5">
        <div className="flex justify-between items-start mb-2">
          <h3 onClick={() => navigate(`/details/${property.id}`)}
          className="cursor-pointer font-bold text-xl text-gray-900 line-clamp-1">{property.title}</h3>
          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
            {property.type}
          </span>
        </div>
        
        
        
        
        <p className="text-gray-700 text-xxl mb-2 line-clamp-2 h-12">
          {property.description}
        </p>

        {/* Footer avec prix + boutons */}
        <div className="flex justify-between items-center pt-3 border-t border-gray-100">
          <span className="font-bold text-xxl text-gray-700">
            {property.price.toLocaleString()} FCFA
          </span>
          
          
        </div>
      </div>
      
    </div>
  );
};
export default ProductsSection;