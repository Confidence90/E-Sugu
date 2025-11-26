import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ArrowLeft, Home, Cable, Tv, Heater, MapPin, Bed, 
  Warehouse, Battery, Star, Heart, Search, ChevronRight, 
  TabletSmartphone, Laptop, Gamepad2, Fence, Camera, Watch,
  Ruler, Bath
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { Skeleton } from '../components/ui/skeleton';

const Alimentation = () => {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedType, setSelectedType] = useState("Tous");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [category, setCategory] = useState(null);
  const [properties, setProperties] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const propertiesPerPage = 8;

  // Récupérer la catégorie Alimentation et ses sous-catégories
  useEffect(() => {
    const fetchCategoryData = async () => {
      try {
        const [categoryRes, propertiesRes] = await Promise.all([
          axios.get('http://localhost:8000/api/categories/categories/Alimentation/'),
          axios.get('http://localhost:8000/api/listings/?category=Alimentation'),
        axios.get('http://localhost:8000/api/listings/', {
            params: {
              category: 'Alimentation',
              status: 'active'  // Ajoutez ce paramètre si nécessaire
            }
      })
        ]);

        console.log("Données de l'API - Catégorie:", categoryRes.data);
        console.log("Données de l'API - Propriétés:", propertiesRes.data);
        setCategory(categoryRes.data);
        setSubcategories(categoryRes.data.subcategories);
        
        // Transformer les données de l'API pour correspondre à notre structure
        const transformedProperties = propertiesRes.data.results.map(item => ({
            
          id: item.id,
          title: item.title,
          description: item.description,
          price: parseFloat(item.price),
          type: item.category_name ? item.subcategory.name : 'Alimentation',
          subcategory: item.category.parent ? item.category.name : null,
          image: item.images?.[0]?.image || 'https://source.unsplash.com/random/600x400/?property',
          location: item.location,
          isFeatured: item.is_featured,
          bedrooms: item.bedrooms || 0,
          bathrooms: item.bathrooms || 0,
          area: item.area ? `${item.area}m²` : '0m²'
        }));
        console.log("Propriétés transformées:", transformedProperties);
        setProperties(transformedProperties);
        setLoading(false);
      } catch (err) {
        console.error('Erreur:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchCategoryData();
  }, []);

  // Filtrage par type
  const filteredProperties = properties.filter(
    (property) =>
      selectedType === "Tous" ||
      (property.type && property.type.toLowerCase() === selectedType.toLowerCase())
      (property.subcategory && property.subcategory.toLowerCase() === selectedType.toLowerCase())
  );

  // Pagination
  const indexOfLastProperty = currentPage * propertiesPerPage;
  const indexOfFirstProperty = indexOfLastProperty - propertiesPerPage;
  const currentProperties = filteredProperties.slice(
    indexOfFirstProperty,
    indexOfLastProperty
  );
  const totalPages = Math.ceil(filteredProperties.length / propertiesPerPage);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Générer les catégories pour la grille à partir des sous-catégories de l'API
  const alimentationCategories = subcategories.map(sub => ({
    name: sub.name,
    icon: getIconForSubcategory(sub.name),
    count: properties.filter(p => p.type === sub.name).length.toString(),
    color: getColorForSubcategory(sub.name)
  }));

  // Helper functions pour les icônes et couleurs
  function getIconForSubcategory(name) {
    const icons = {
      'Téléphones & Tablettes': TabletSmartphone,
      'Ordinateurs': Laptop,
      'Accessoires Informatiques': Cable,
      'Jeux & Vidéo': Gamepad2,
      'Tv, box & vidéo projecteurs': Tv,
      'Appareils photos et Cameras': Camera,
      'Montres': Watch,
      'Autres électronique': Heater,
      'Accessoires Téléphoniques': Battery
    };
    return icons[name] || Fence;
  }

  function getColorForSubcategory(name) {
    const colors = {
      'Téléphones & Tablettes': 'bg-blue-100 text-blue-600',
      'Ordinateurs': 'bg-purple-100 text-purple-600',
      'Accessoires Informatiques': 'bg-green-100 text-green-600',
      'Jeux & Vidéo': 'bg-indigo-100 text-indigo-600',
      'Tv, box & vidéo projecteurs': 'bg-orange-100 text-orange-600',
      'Appareils photos et Cameras': 'bg-pink-100 text-pink-600',
      'Montres': 'bg-yellow-100 text-yellow-600',
      'Autres électronique': 'bg-red-100 text-red-600'
    };
    return colors[name] || 'bg-gray-100 text-gray-600';
  }

  // Composant PropertyCard
  const PropertyCard = ({ property }) => {
    return (
      <div 
        className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 cursor-pointer"
        onClick={() => navigate(`/property/${property.id}`)}
      >
        <div className="relative h-60 overflow-hidden">
          <img 
            src={property.image} 
            alt={property.title} 
            className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
            onError={(e) => {
              e.target.src = 'https://source.unsplash.com/random/600x400/?property';
            }}
          />
          {property.isFeatured && (
            <div className="absolute top-3 left-3 bg-gradient-to-r from-blue-600 to-blue-800 text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center shadow-md">
              <Star className="h-3 w-3 mr-1 fill-current" />
              Vedette
            </div>
          )}
          <button 
            className="absolute top-3 right-3 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md hover:bg-white transition-colors group"
            onClick={(e) => {
              e.stopPropagation();
              // Ajouter aux favoris
            }}
          >
            <Heart className="h-5 w-5 text-gray-600 group-hover:text-red-500 transition-colors" />
          </button>
        </div>
        
        <div className="p-5">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-bold text-xl text-gray-900 line-clamp-1">{property.title}</h3>
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
              {property.type}
            </span>
          </div>
          
          <div className="flex items-center text-gray-600 mb-3">
            <MapPin className="h-4 w-4 mr-1 text-blue-500" />
            <span className="text-sm">{property.location}</span>
          </div>
          
          <p className="text-gray-500 text-sm mb-4 line-clamp-2 h-12">
            {property.description}
          </p>
          
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="flex flex-col items-center bg-gray-50 p-2 rounded-lg">
              <Bed className="h-5 w-5 text-blue-600 mb-1" />
              <span className="text-xs font-medium">{property.bedrooms} {property.bedrooms > 1 ? 'ch.' : 'ch.'}</span>
            </div>
            <div className="flex flex-col items-center bg-gray-50 p-2 rounded-lg">
              <Bath className="h-5 w-5 text-blue-600 mb-1" />
              <span className="text-xs font-medium">{property.bathrooms} {property.bathrooms > 1 ? 's.b.' : 's.b.'}</span>
            </div>
            <div className="flex flex-col items-center bg-gray-50 p-2 rounded-lg">
              <Ruler className="h-5 w-5 text-blue-600 mb-1" />
              <span className="text-xs font-medium">{property.area}</span>
            </div>
          </div>
          
          <div className="flex justify-between items-center pt-3 border-t border-gray-100">
            <span className="font-bold text-xl text-blue-600">
              {property.price.toLocaleString()} FCFA
            </span>
            <button 
              className="text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/property/${property.id}`);
              }}
            >
              Voir détail
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Composant SkeletonCard
  const SkeletonCard = () => {
    return (
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <Skeleton className="h-60 w-full" />
        <div className="p-5 space-y-3">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <div className="grid grid-cols-3 gap-2">
            <Skeleton className="h-12 rounded-lg" />
            <Skeleton className="h-12 rounded-lg" />
            <Skeleton className="h-12 rounded-lg" />
          </div>
          <div className="flex justify-between pt-3">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-8 w-20" />
          </div>
        </div>
      </div>
    );
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded max-w-md mx-auto text-center">
            <p>Erreur lors du chargement des données</p>
            <p className="text-sm">{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-2 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Réessayer
            </button>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-2 mb-8">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-500 hover:text-blue-600 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Retour à l'accueil</span>
          </button>
          <span className="text-gray-300">/</span>
          <span className="text-gray-700 font-medium">{category?.name || 'Alimentation'}</span>
        </div>

        {/* Hero Section */}
        <div className="relative bg-gradient-to-r from-blue-600 to-blue-800 rounded-xl p-8 mb-12 text-white overflow-hidden">
          <div className="absolute right-0 top-0 opacity-10">
            <Home className="h-64 w-64" />
          </div>
          <div className="relative z-10 max-w-2xl mx-auto text-center">
            <div className="w-20 h-20 rounded-full bg-white bg-opacity-20 mx-auto mb-6 flex items-center justify-center">
              <Home className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold mb-4 font-serif">{category?.name || 'Alimentation'}</h1>
            <p className="text-lg text-blue-100 mb-6">
              {category?.description || 'Découvrez notre sélection exclusive de Alimentation'}
            </p>
            
            {/* Search Bar */}
            <div className="relative max-w-xl mx-auto">
              <input
                type="text"
                placeholder="Rechercher des Style à la Une..."
                className="w-full pl-12 pr-4 py-3 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <button className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded-md">
                Rechercher
              </button>
            </div>
          </div>
        </div>

        {/* Categories Grid */}
        {alimentationCategories.length > 0 && (
          <section className="mb-16">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800 font-serif">Nos catégories Style à la Une</h2>
              <button 
                onClick={() => navigate('/alimentation/toutes-categories')}
                className="text-blue-600 hover:text-blue-800 flex items-center"
              >
                Tout voir <ChevronRight className="h-4 w-4 ml-1" />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 gap-6">
              {alimentationCategories.map((category) => {
                const IconComponent = category.icon;
                return (
                  <div 
                    key={category.name}
                    onClick={() => navigate(`/alimentation/categorie/${category.name.toLowerCase()}`)}
                    className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 cursor-pointer"
                  >
                    <div className="p-6 text-center">
                      <div className={`w-16 h-16 rounded-full ${category.color} mx-auto mb-4 flex items-center justify-center transition-transform hover:scale-110`}>
                        <IconComponent className="h-8 w-8" />
                      </div>
                      <h3 className="font-bold text-lg text-gray-800 mb-1">
                        {category.name}
                      </h3>
                      <div className="flex items-center justify-center">
                        <p className="text-sm text-gray-500 mr-1">{category.count} annonces</p>
                        <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-blue-500 transition-colors" />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Filtres */}
        {subcategories.length > 0 && (
          <div className="flex justify-center mb-12">
            <div className="inline-flex bg-white rounded-full shadow-sm p-1 border border-gray-200">
              <button
                onClick={() => {
                  setSelectedType("Tous");
                  setCurrentPage(1);
                }}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  selectedType === "Tous"
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                Tous
              </button>
              {subcategories.map((sub) => (
                <button
                  key={sub.id}
                  onClick={() => {
                    setSelectedType(sub.name);
                    setCurrentPage(1);
                  }}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    selectedType === sub.name
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  {sub.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Featured Properties */}
        <section className="mb-16">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl font-bold text-gray-800 font-serif">
              {selectedType === "Tous" ? "Tout pour votre look" : selectedType}
            </h2>
            <button 
              onClick={() => navigate('/alimentation/toutes-les-annonces')}
              className="text-blue-600 hover:text-blue-800 flex items-center"
            >
              Tout voir <ChevronRight className="h-4 w-4 ml-1" />
            </button>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {[...Array(8)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : properties.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl shadow">
              <p className="text-gray-500">Aucune annonce disponible pour le moment</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                {currentProperties.map((property) => (
                  <PropertyCard key={property.id} property={property} />
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
            </>
          )}
        </section>

        {/* Call to Action */}
        <section className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-xl p-8 text-center text-white mb-12">
          <h2 className="text-2xl font-bold mb-4 font-serif">Vous avez un bien à vendre ou louer ?</h2>
          <p className="mb-6 max-w-2xl mx-auto">
            Publiez votre annonce gratuitement et touchez des milliers de clients potentiels
          </p>
          <button 
            onClick={() => navigate('/publier')}
            className="bg-white text-blue-600 hover:bg-gray-100 px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Publier une annonce
          </button>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Alimentation;