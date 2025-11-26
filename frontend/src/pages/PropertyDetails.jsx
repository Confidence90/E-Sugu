import { useState, useEffect } from 'react';
import { 
  ArrowLeft, Heart, Share2, MapPin, Calendar, Eye, Star, 
  Wifi, Shield, Camera, MessageCircle, ChevronLeft, ChevronRight, Play,
  CheckCircle, Calculator, User, Award, Verified, CreditCard,
  Lock, Headphones, Store, Package
} from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';

function PropertyDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isLiked, setIsLiked] = useState(false);
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('description');
  const [showContactModal, setShowContactModal] = useState(false);
  
  // Fetch property data from API
  useEffect(() => {
  const fetchProperty = async () => {
    try {
      setLoading(true);
      // Utiliser l'URL sans paramètres pour récupérer une propriété spécifique
      const response = await fetch(`http://localhost:8000/api/listings/${id}/`);
    
      if (!response.ok) {
        throw new Error('Propriété non trouvée');
      }
      
      const data = await response.json();
      
      // Transformation des données pour correspondre à la structure attendue
      const propertyData = {
        id: data.id,
        title: data.title,
        description: data.description,
        price: parseFloat(data.price),
        type: data.type === 'sale' ? 'À vendre' : 'À louer',
        condition: data.condition,
        location: data.location,
        isFeatured: data.is_featured,
        images: data.images.map(img => img.image),
        // Suppression des caractéristiques spécifiques
        amenities: data.amenities || [
          "Cuisine équipée moderne",
          "Climatisation dans toutes les pièces", 
          "Système de sécurité 24h/24",
          "Connexion fibre optique"
        ],
        // Supprimer les informations personnelles du vendeur
        seller: {
          rating: 4.8,
          reviews: 127,
          verified: true,
          memberSince: data.created_at ? data.created_at.split('-')[0] : "2019"
        },
        stats: {
          views: 1247, // Valeur par défaut
          likes: 89,   // Valeur par défaut
          published: data.created_at ? `Publié le ${new Date(data.created_at).toLocaleDateString()}` : "Il y a 3 jours"
        },
        coordinates: {
          lat: 12.6392, // Valeur par défaut
          lng: -8.0029  // Valeur par défaut
        }
      };
      
      setProperty(propertyData);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  fetchProperty();
}, [id]);

  const nextImage = () => {
    if (!property) return;
    setCurrentImageIndex((prev) => 
      prev === property.images.length - 1 ? 0 : prev + 1
    );
  };

  const prevImage = () => {
    if (!property) return;
    setCurrentImageIndex((prev) => 
      prev === 0 ? property.images.length - 1 : prev - 1
    );
  };

  const handleContact = () => {
    // Ouvrir le modal de contact au lieu de montrer les infos du vendeur
    setShowContactModal(true);
  };

  const handlePurchase = () => {
    // Rediriger vers la page de processus d'achat
    navigate(`/checkout/${id}`);
  };

  if (loading) {
    return <PropertyDetailsSkeleton />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded max-w-md mx-auto">
            <p>Erreur lors du chargement de la propriété</p>
            <p className="text-sm">{error}</p>
          </div>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p>Propriété non trouvée</p>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50">
      {/* Header avec navigation */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <button 
              onClick={() => navigate(-1)}
              className="flex items-center text-gray-600 hover:text-primary transition-colors group"
            >
              <ArrowLeft className="h-5 w-5 mr-2 group-hover:-translate-x-1 transition-transform" />
              <span className="font-medium">Retour aux annonces</span>
            </button>
            
            <div className="flex items-center space-x-3">
              <button 
                onClick={() => setIsLiked(!isLiked)}
                className={`p-3 rounded-full border-2 transition-all ${
                  isLiked 
                    ? 'bg-red-50 border-red-200 text-red-600' 
                    : 'bg-white border-gray-200 text-gray-600 hover:border-red-200 hover:text-red-600'
                }`}
              >
                <Heart className={`h-5 w-5 ${isLiked ? 'fill-current' : ''}`} />
              </button>
              
              <button className="p-3 rounded-full border-2 border-gray-200 text-gray-600 hover:border-blue-200 hover:text-blue-600 transition-all">
                <Share2 className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Colonne principale */}
          <div className="lg:col-span-2 space-y-8">
            {/* Galerie d'images */}
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="relative h-96 md:h-[500px]">
                <img
                  src={property.images[currentImageIndex]}
                  alt={property.title}
                  className="w-full h-full object-cover"
                />
                
                {/* Navigation images */}
                <button
                  onClick={prevImage}
                  className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-black/50 text-white rounded-full hover:bg-black/70 transition-colors"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                
                <button
                  onClick={nextImage}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-black/50 text-white rounded-full hover:bg-black/70 transition-colors"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>

                {/* Indicateurs */}
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-2">
                  {property.images.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`w-2 h-2 rounded-full transition-all ${
                        index === currentImageIndex ? 'bg-white w-6' : 'bg-white/60'
                      }`}
                    />
                  ))}
                </div>

                {/* Badges */}
                <div className="absolute top-4 left-4 flex flex-col space-y-2">
                  <span className="bg-gradient-to-r from-emerald-500 to-emerald-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                    {property.type}
                  </span>
                  <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                    {property.condition}
                  </span>
                </div>

                {/* Play button pour visite virtuelle */}
                <button className="absolute top-4 right-4 p-3 bg-white/90 backdrop-blur-sm rounded-full shadow-lg hover:bg-white transition-colors group">
                  <Play className="h-5 w-5 text-blue-600 group-hover:scale-110 transition-transform fill-current" />
                </button>
              </div>

              {/* Miniatures */}
              <div className="p-4 bg-gray-50">
                <div className="flex space-x-2 overflow-x-auto">
                  {property.images.map((image, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`flex-shrink-0 w-20 h-16 rounded-lg overflow-hidden border-2 transition-all ${
                        index === currentImageIndex 
                          ? 'border-blue-500 ring-2 ring-blue-200' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <img
                        src={image}
                        alt={`Vue ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Informations principales */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-6">
                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">{property.title}</h1>
                  <div className="flex items-center text-gray-600 mb-4">
                    <MapPin className="h-5 w-5 mr-2 text-blue-500" />
                    <span className="text-lg">{property.location}</span>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-blue-600">
                    {property.price.toLocaleString()} FCFA
                  </div>
                </div>
              </div>

              {/* Statistiques */}
              <div className="flex flex-wrap items-center gap-6 pt-4 border-t border-gray-100">
                <div className="flex items-center text-gray-500">
                  <Eye className="h-4 w-4 mr-2" />
                  <span className="text-sm">{property.stats.views} vues</span>
                </div>
                <div className="flex items-center text-gray-500">
                  <Heart className="h-4 w-4 mr-2" />
                  <span className="text-sm">{property.stats.likes} favoris</span>
                </div>
                <div className="flex items-center text-gray-500">
                  <Calendar className="h-4 w-4 mr-2" />
                  <span className="text-sm">Publié {property.stats.published}</span>
                </div>
              </div>
            </div>

            {/* Onglets de contenu */}
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="border-b border-gray-100">
                <nav className="flex space-x-8 px-6">
                  {[
                    { id: 'description', label: 'Description', icon: User },
                    { id: 'amenities', label: 'Équipements', icon: CheckCircle },
                    { id: 'location', label: 'Localisation', icon: MapPin }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <tab.icon className="h-4 w-4 mr-2" />
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'description' && (
                  <div className="space-y-4">
                    <p className="text-gray-700 leading-relaxed text-lg">
                      {property.description}
                    </p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-1 gap-4 mt-6">
                      
                    </div>
                  </div>
                )}

                {activeTab === 'amenities' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {property.amenities.map((amenity, index) => (
                      <div key={index} className="flex items-center p-3 bg-green-50 rounded-lg border border-green-100">
                        <CheckCircle className="h-5 w-5 text-green-600 mr-3 flex-shrink-0" />
                        <span className="text-gray-700">{amenity}</span>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'location' && (
                  <div className="space-y-4">
                    <div className="bg-gray-100 rounded-xl h-64 flex items-center justify-center">
                      <div className="text-center text-gray-500">
                        <MapPin className="h-12 w-12 mx-auto mb-2" />
                        <p>Carte interactive</p>
                        <p className="text-sm">{property.location}</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-blue-50 rounded-xl">
                        <div className="font-semibold text-blue-900">École primaire</div>
                        <div className="text-sm text-blue-600">À 500m</div>
                      </div>
                      <div className="text-center p-4 bg-green-50 rounded-xl">
                        <div className="font-semibold text-green-900">Centre commercial</div>
                        <div className="text-sm text-green-600">À 2km</div>
                      </div>
                      <div className="text-center p-4 bg-purple-50 rounded-xl">
                        <div className="font-semibold text-purple-900">Hôpital</div>
                        <div className="text-sm text-purple-600">À 3km</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Carte d'achat sécurisé */}
            <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-8">
              <div className="text-center mb-6">
                <div className="bg-blue-100 p-3 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Store className="h-8 w-8 text-blue-600" />
                </div>
                
                <h3 className="font-semibold text-xl text-gray-900 mt-2">Achat sécurisé E-Sugu</h3>
                <div className="flex items-center justify-center mt-2">
                  <div className="flex items-center text-yellow-500 mr-2">
                    <Star className="h-4 w-4 fill-current" />
                    <span className="ml-1 font-medium">{property.seller.rating}</span>
                  </div>
                  <span className="text-gray-500 text-sm">({property.seller.reviews} avis)</span>
                </div>
                <div className="flex items-center justify-center mt-2 text-green-600">
                  <Verified className="h-4 w-4 mr-1" />
                  <span className="text-sm">Vendeur vérifié</span>
                </div>
              </div>

              <div className="space-y-3">
                <button 
                  onClick={handlePurchase}
                  className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white font-semibold py-3 px-4 rounded-xl transition-all transform hover:scale-105 flex items-center justify-center"
                >
                  <CreditCard className="h-5 w-5 mr-2" />
                  Acheter maintenant
                </button>
                
                <button 
                  onClick={() => setIsLiked(!isLiked)}
                  className="w-full bg-white border-2 border-emerald-600 hover:bg-emerald-50 text-emerald-700 font-semibold py-3 px-4 rounded-xl transition-all flex items-center justify-center"
                >
                  <Heart className={`h-5 w-5 mr-2 ${isLiked ? 'fill-current' : ''}`} />
                  {isLiked ? 'Retirer des favoris' : 'Ajouter aux favoris'}
                </button>
                
                <button 
                  onClick={handleContact}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-xl transition-all flex items-center justify-center"
                >
                  <MessageCircle className="h-5 w-5 mr-2" />
                  Contacter via E-Sugu
                </button>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-100 space-y-3">
                <div className="flex items-center text-gray-500 text-sm">
                  <Shield className="h-4 w-4 mr-2 text-green-500" />
                  <span>Transaction sécurisée</span>
                </div>
                <div className="flex items-center text-gray-500 text-sm">
                  <Package className="h-4 w-4 mr-2 text-blue-500" />
                  <span>Garantie de remboursement</span>
                </div>
                <div className="flex items-center text-gray-500 text-sm">
                  <Headphones className="h-4 w-4 mr-2 text-purple-500" />
                  <span>Support client 7j/7</span>
                </div>
              </div>
            </div>

            {/* Garanties E-Sugu */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6">
              <div className="flex items-center mb-4">
                <Shield className="h-6 w-6 text-blue-600 mr-2" />
                <h3 className="font-semibold text-blue-900">Garanties E-Sugu</h3>
              </div>
              <ul className="space-y-3 text-sm text-blue-800">
                <li className="flex items-start">
                  <Lock className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Paiement sécurisé via notre plateforme</span>
                </li>
                <li className="flex items-start">
                  <Package className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Vérification de la propriété avant transaction</span>
                </li>
                <li className="flex items-start">
                  <CreditCard className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Remboursement sous 15 jours si non satisfait</span>
                </li>
                <li className="flex items-start">
                  <Headphones className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Support client dédié pour tout problème</span>
                </li>
              </ul>
            </div>

            {/* Calcul de crédit */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Calculator className="h-5 w-5 mr-2 text-blue-600" />
                Simulateur de crédit
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Apport initial (FCFA)
                  </label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="10 000 000"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Durée (années)
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option>10 ans</option>
                    <option>15 ans</option>
                    <option>20 ans</option>
                    <option>25 ans</option>
                  </select>
                </div>
                
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors">
                  Calculer
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Annonces similaires */}
        <div className="mt-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Propriétés similaires</h2>
          <SimilarProperties currentId={property.id} />
        </div>
      </div>

      {/* Modal de contact */}
      {showContactModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Contacter via E-Sugu</h3>
            <p className="text-gray-600 mb-6">
              Tous les messages passent par notre plateforme sécurisée. Nous protégeons vos informations personnelles.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Votre message
                </label>
                <textarea 
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="4"
                  placeholder="Bonjour, je suis intéressé par cette propriété..."
                ></textarea>
              </div>
              
              <div className="flex space-x-3 pt-2">
                <button 
                  onClick={() => setShowContactModal(false)}
                  className="flex-1 border-2 border-gray-300 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Annuler
                </button>
                <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors">
                  Envoyer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Composant pour les annonces similaires
const SimilarProperties = ({ currentId }) => {
  const [similarProperties, setSimilarProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchSimilarProperties = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/listings/');
        if (!response.ok) {
          throw new Error('Erreur réseau');
        }
        const data = await response.json();
        
        // Transform data
        const transformed = data.results
          .filter(item => item.id !== currentId)
          .slice(0, 3)
          .map(item => ({
            id: item.id,
            title: item.title,
            price: parseFloat(item.price),
            location: item.location,
            image: item.images?.[0]?.image || 'https://source.unsplash.com/random/600x400/?property,house',
          }));
        
        setSimilarProperties(transformed);
        setLoading(false);
      } catch (err) {
        console.error('Erreur lors du chargement des propriétés similaires:', err);
        setLoading(false);
      }
    };
    
    fetchSimilarProperties();
  }, [currentId]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="h-48 bg-gray-200 animate-pulse"></div>
            <div className="p-5">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-full"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {similarProperties.map((property) => (
        <div key={property.id} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
          <div className="relative h-48 overflow-hidden">
            <img
              src={property.image}
              alt={property.title}
              className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
            />
            <button className="absolute top-3 right-3 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md hover:bg-white transition-colors">
              <Heart className="h-4 w-4 text-gray-600 hover:text-red-500 transition-colors" />
            </button>
          </div>
          
          <div className="p-5">
            <h3 className="font-bold text-lg text-gray-900 mb-2 line-clamp-1">{property.title}</h3>
            
            <div className="flex items-center text-gray-600 mb-3">
              <MapPin className="h-4 w-4 mr-1 text-blue-500" />
              <span className="text-sm">{property.location}</span>
            </div>
            
            <div className="flex justify-between items-center pt-3 border-t border-gray-100">
              <span className="font-bold text-lg text-blue-600">
                {property.price.toLocaleString()} FCFA
              </span>
              <button className="text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg transition-colors">
                Voir
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Skeleton de chargement
const PropertyDetailsSkeleton = () => {
  return (
    <div className="min-h-screen bg-gray-50 animate-pulse">
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="h-6 bg-gray-300 rounded w-40"></div>
            <div className="flex space-x-3">
              <div className="h-10 w-10 bg-gray-300 rounded-full"></div>
              <div className="h-10 w-10 bg-gray-300 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="h-[500px] bg-gray-300"></div>
            </div>
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="h-8 bg-gray-300 rounded w-3/4 mb-4"></div>
              <div className="h-6 bg-gray-300 rounded w-1/2 mb-6"></div>
            </div>
          </div>
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="h-20 w-20 bg-gray-300 rounded-full mx-auto mb-4"></div>
              <div className="h-6 bg-gray-300 rounded w-3/4 mx-auto mb-2"></div>
              <div className="h-4 bg-gray-300 rounded w-1/2 mx-auto mb-6"></div>
              <div className="space-y-3">
                <div className="h-12 bg-gray-300 rounded-xl"></div>
                <div className="h-12 bg-gray-300 rounded-xl"></div>
                <div className="h-12 bg-gray-300 rounded-xl"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyDetails;