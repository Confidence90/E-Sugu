import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import Modal from 'react-modal';
import { useNavigate } from 'react-router-dom';

Modal.setAppElement('#root');

const Profile = () => {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ full_name: '', avatar: '', email: '', phone: ''/*, birthday: ''*/ });
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const navigate = useNavigate();

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (!refresh) {
        toast.error('Session expirée, veuillez vous reconnecter');
        navigate('/login');
        return null;
      }
      const response = await axios.post('http://localhost:8000/api/users/refresh-token/', { refresh });
      localStorage.setItem('access_token', response.data.access);
      return response.data.access;
    } catch (error) {
      console.error('Erreur rafraîchissement token:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
      return null;
    }
  };

  axios.interceptors.response.use(
    response => response,
    async error => {
      const originalRequest = error.config;
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        const newToken = await refreshToken();
        if (newToken) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
          originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          return axios(originalRequest);
        }
      }
      if (error.response?.status === 401) {
        toast.error('Session expirée, veuillez vous reconnecter');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        navigate('/login');
      }
      return Promise.reject(error);
    }
  );

  const fetchProfile = async () => {
  setIsLoading(true);
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Veuillez vous connecter');
      navigate('/login');
      return;
    }

    const res = await axios.get('http://localhost:8000/api/users/profile/', {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    setUser(res.data);
    setFormData({
      full_name: `${res.data.first_name || ''} ${res.data.last_name || ''}`.trim(),
      first_name: res.data.first_name || '',
      last_name: res.data.last_name || '',
      avatar: res.data.avatar || '',
      email: res.data.email || '',
      phone: res.data.phone || '',
      //birthday: res.data.birthday || '',
      country_code: res.data.country_code || '+223',
      location: res.data.location || ''
    });
  } catch (err) {
    console.error('Erreur profile:', err.response?.data || err.message);
    if (err.response?.status !== 401) {
      toast.error('Erreur lors du chargement du profil');
    }
  } finally {
    setIsLoading(false);
  }
};

  const fetchOrders = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await axios.get('http://localhost:8000/api/commandes/mes-commandes/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrders(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Erreur commandes:', err.response?.data || err.message);
      setOrders([]);
      if (err.response?.status !== 401) {
        toast.error('Impossible de charger les commandes');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const checkAuthAndFetch = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        navigate('/login');
        return;
      }
      await fetchProfile();
      await fetchOrders();
    };

    checkAuthAndFetch();
  }, [navigate]);

  const handleUpdate = async (e) => {
  e.preventDefault();
  setIsLoading(true);

  const token = localStorage.getItem('access_token');
  const form = new FormData();
  form.append('first_name', formData.first_name);
  form.append('last_name', formData.last_name);
  if (file) form.append('avatar', file);
  if (formData.phone) form.append('phone', formData.phone);
  //if (formData.birthday) form.append('birthday', formData.birthday);
  if (formData.country_code) form.append('country_code', formData.country_code);
  if (formData.location) form.append('location', formData.location);

  try {
    await axios.put('http://localhost:8000/api/users/profile/', form, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    toast.success("Profil mis à jour avec succès");
    setIsModalOpen(false);
    await fetchProfile();
    setFile(null);
  } catch (error) {
    console.error('Erreur mise à jour:', error.response?.data || error.message);
    toast.error(error.response?.data?.message || "Erreur lors de la mise à jour du profil");
  } finally {
    setIsLoading(false);
  }
};

  if (isLoading && !user) {
    return <div className="flex justify-center items-center h-screen">Chargement...</div>;
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'shipped':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  // Ajoutez cette fonction utilitaire quelque part dans votre code
const safeReduce = (array, callback, initialValue) => {
  if (!Array.isArray(array)) return initialValue;
  try {
    return array.reduce(callback, initialValue);
  } catch (error) {
    console.error('Reduce error:', error);
    return initialValue;
  }
};
const COUNTRY_CHOICES = [
  // Afrique
  { code: '+213', name: 'Algérie (+213)' }, { code: '+229', name: 'Bénin (+229)' }, 
  { code: '+226', name: 'Burkina Faso (+226)' }, { code: '+237', name: 'Cameroun (+237)' },
  { code: '+238', name: 'Cap-Vert (+238)' }, { code: '+236', name: 'Centrafrique (+236)' },
  { code: '+235', name: 'Tchad (+235)' }, { code: '+269', name: 'Comores (+269)' },
  { code: '+242', name: 'Congo-Brazzaville (+242)' }, { code: '+243', name: 'RD Congo (+243)' },
  { code: '+225', name: 'Côte d’Ivoire (+225)' }, { code: '+240', name: 'Guinée équatoriale (+240)' },
  { code: '+241', name: 'Gabon (+241)' }, { code: '+220', name: 'Gambie (+220)' },
  { code: '+233', name: 'Ghana (+233)' }, { code: '+224', name: 'Guinée (+224)' },
  { code: '+245', name: 'Guinée-Bissau (+245)' }, { code: '+254', name: 'Kenya (+254)' },
  { code: '+266', name: 'Lesotho (+266)' }, { code: '+231', name: 'Libéria (+231)' },
  { code: '+218', name: 'Libye (+218)' }, { code: '+261', name: 'Madagascar (+261)' },
  { code: '+265', name: 'Malawi (+265)' }, { code: '+223', name: 'Mali (+223)' },
  { code: '+222', name: 'Mauritanie (+222)' }, { code: '+230', name: 'Maurice (+230)' },
  { code: '+262', name: 'Mayotte (+262)' }, { code: '+212', name: 'Maroc (+212)' },
  { code: '+258', name: 'Mozambique (+258)' }, { code: '+264', name: 'Namibie (+264)' },
  { code: '+227', name: 'Niger (+227)' }, { code: '+234', name: 'Nigéria (+234)' },
  { code: '+250', name: 'Rwanda (+250)' }, { code: '+239', name: 'Sao Tomé-et-Principe (+239)' },
  { code: '+221', name: 'Sénégal (+221)' }, { code: '+248', name: 'Seychelles (+248)' },
  { code: '+232', name: 'Sierra Leone (+232)' }, { code: '+252', name: 'Somalie (+252)' },
  { code: '+27', name: 'Afrique du Sud (+27)' }, { code: '+211', name: 'Soudan du Sud (+211)' },
  { code: '+249', name: 'Soudan (+249)' }, { code: '+255', name: 'Tanzanie (+255)' },
  { code: '+228', name: 'Togo (+228)' }, { code: '+216', name: 'Tunisie (+216)' },
  { code: '+256', name: 'Ouganda (+256)' }, { code: '+260', name: 'Zambie (+260)' },
  { code: '+263', name: 'Zimbabwe (+263)' },

  // Europe
  { code: '+43', name: 'Autriche (+43)' }, { code: '+32', name: 'Belgique (+32)' },
  { code: '+359', name: 'Bulgarie (+359)' }, { code: '+385', name: 'Croatie (+385)' },
  { code: '+357', name: 'Chypre (+357)' }, { code: '+420', name: 'République Tchèque (+420)' },
  { code: '+45', name: 'Danemark (+45)' }, { code: '+372', name: 'Estonie (+372)' },
  { code: '+358', name: 'Finlande (+358)' }, { code: '+33', name: 'France (+33)' },
  { code: '+49', name: 'Allemagne (+49)' }, { code: '+30', name: 'Grèce (+30)' },
  { code: '+36', name: 'Hongrie (+36)' }, { code: '+353', name: 'Irlande (+353)' },
  { code: '+39', name: 'Italie (+39)' }, { code: '+371', name: 'Lettonie (+371)' },
  { code: '+370', name: 'Lituanie (+370)' }, { code: '+352', name: 'Luxembourg (+352)' },
  { code: '+31', name: 'Pays-Bas (+31)' }, { code: '+48', name: 'Pologne (+48)' },
  { code: '+351', name: 'Portugal (+351)' }, { code: '+40', name: 'Roumanie (+40)' },
  { code: '+421', name: 'Slovaquie (+421)' }, { code: '+386', name: 'Slovénie (+386)' },
  { code: '+34', name: 'Espagne (+34)' }, { code: '+46', name: 'Suède (+46)' },
  { code: '+41', name: 'Suisse (+41)' }, { code: '+44', name: 'Royaume-Uni (+44)' },

  // Asie
  { code: '+93', name: 'Afghanistan (+93)' }, { code: '+880', name: 'Bangladesh (+880)' },
  { code: '+86', name: 'Chine (+86)' }, { code: '+91', name: 'Inde (+91)' },
  { code: '+62', name: 'Indonésie (+62)' }, { code: '+81', name: 'Japon (+81)' },
  { code: '+82', name: 'Corée du Sud (+82)' }, { code: '+60', name: 'Malaisie (+60)' },
  { code: '+95', name: 'Myanmar (+95)' }, { code: '+92', name: 'Pakistan (+92)' },
  { code: '+63', name: 'Philippines (+63)' }, { code: '+65', name: 'Singapour (+65)' },
  { code: '+66', name: 'Thaïlande (+66)' }, { code: '+84', name: 'Vietnam (+84)' },

  // Amériques
  { code: '+54', name: 'Argentine (+54)' }, { code: '+55', name: 'Brésil (+55)' },
  { code: '+56', name: 'Chili (+56)' }, { code: '+57', name: 'Colombie (+57)' },
  { code: '+53', name: 'Cuba (+53)' }, { code: '+593', name: 'Équateur (+593)' },
  { code: '+502', name: 'Guatemala (+502)' }, { code: '+504', name: 'Honduras (+504)' },
  { code: '+52', name: 'Mexique (+52)' }, { code: '+1', name: 'États-Unis (+1)' },
  { code: '+598', name: 'Uruguay (+598)' }, { code: '+58', name: 'Venezuela (+58)' },

  // Océanie
  { code: '+61', name: 'Australie (+61)' }, { code: '+64', name: 'Nouvelle-Zélande (+64)' },
  { code: '+675', name: 'Papouasie-Nouvelle-Guinée (+675)' }
];

/*<div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Date de naissance</label>
                      <input 
                        type="text" 
                        value={formData.birthday ? new Date(formData.birthday).toLocaleDateString() : 'Non renseignée'} 
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                        readOnly
                      />
                    </div>*/

// Utilisation :
safeReduce(orders, (total, order) => total + (order.total_amount || 0), 0).toFixed(2) + ' €'

  return (
    <div className="bg-gray-50 min-h-screen font-sans">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 to-indigo-700 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <i className="fas fa-shopping-bag text-2xl"></i>
            <span className="text-xl font-bold">E-Sugu</span>
          </div>
          <nav className="hidden md:flex space-x-6">
            <a href="#" className="hover:text-gray-200">Accueil</a>
            <a href="#" className="hover:text-gray-200">Boutique</a>
            <a href="#" className="hover:text-gray-200">Nouveautés</a>
            <a href="#" className="hover:text-gray-200">Contact</a>
          </nav>
          <div className="flex items-center space-x-4">
            <button className="hover:text-gray-200">
              <i className="fas fa-search"></i>
            </button>
            <button className="hover:text-gray-200">
              <i className="fas fa-heart"></i>
            </button>
            <button className="hover:text-gray-200 relative">
              <i className="fas fa-shopping-cart"></i>
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">3</span>
            </button>
            <button className="md:hidden">
              <i className="fas fa-bars"></i>
            </button>
          </div>
        </div>
      </header>

      {/* Profile Section */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Sidebar */}
          <div className="w-full md:w-1/4">
            <div className="bg-white rounded-xl shadow-md overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-indigo-700 py-6 flex flex-col items-center">
               <div className="relative">
                <img 
                  src={user?.avatar ? `http://localhost:8000${user.avatar}` : 'https://i.pravatar.cc/300'} 
                  alt="Profile" 
                  className="border-4 border-white rounded-full h-24 w-24 object-cover shadow-lg"
                  onError={(e) => {
                    e.target.src = 'https://i.pravatar.cc/300';
                  }}
                />
                <button 
                  className="absolute bottom-0 right-0 bg-white rounded-full p-2 shadow-md"
                  onClick={() => setIsModalOpen(true)}
                >
                  <i className="fas fa-camera text-purple-600"></i>
                </button>
              </div>
                <h2 className="text-white font-bold text-xl mt-4">{user?.full_name || user?.username}</h2>
                <p className="text-purple-200">Membre depuis {new Date(user?.date_joined).getFullYear() || '2023'}</p>
              </div>
              <div className="p-6">
                <ul className="space-y-3">
                  <li>
                    <button 
                      onClick={() => setActiveTab('profile')}
                      className={`flex items-center space-x-3 w-full ${activeTab === 'profile' ? 'text-purple-600 font-medium' : 'text-gray-600 hover:text-purple-600'}`}
                    >
                      <i className="fas fa-user-circle w-6"></i>
                      <span>Mon Profil</span>
                    </button>
                  </li>
                  <li>
                    <button 
                      onClick={() => setActiveTab('orders')}
                      className={`flex items-center space-x-3 w-full ${activeTab === 'orders' ? 'text-purple-600 font-medium' : 'text-gray-600 hover:text-purple-600'}`}
                    >
                      <i className="fas fa-shopping-bag w-6"></i>
                      <span>Mes Commandes</span>
                    </button>
                  </li>
                  <li>
                    <button 
                      onClick={() => setActiveTab('wishlist')}
                      className={`flex items-center space-x-3 w-full ${activeTab === 'wishlist' ? 'text-purple-600 font-medium' : 'text-gray-600 hover:text-purple-600'}`}
                    >
                      <i className="fas fa-heart w-6"></i>
                      <span>Mes Favoris</span>
                    </button>
                  </li>
                  <li>
                    <button 
                      onClick={() => setActiveTab('addresses')}
                      className={`flex items-center space-x-3 w-full ${activeTab === 'addresses' ? 'text-purple-600 font-medium' : 'text-gray-600 hover:text-purple-600'}`}
                    >
                      <i className="fas fa-map-marker-alt w-6"></i>
                      <span>Adresses</span>
                    </button>
                  </li>
                  <li>
                    <button 
                      onClick={() => setActiveTab('payments')}
                      className={`flex items-center space-x-3 w-full ${activeTab === 'payments' ? 'text-purple-600 font-medium' : 'text-gray-600 hover:text-purple-600'}`}
                    >
                      <i className="fas fa-credit-card w-6"></i>
                      <span>Moyens de Paiement</span>
                    </button>
                  </li>
                  <li>
                    <button 
                      onClick={() => setActiveTab('settings')}
                      className={`flex items-center space-x-3 w-full ${activeTab === 'settings' ? 'text-purple-600 font-medium' : 'text-gray-600 hover:text-purple-600'}`}
                    >
                      <i className="fas fa-cog w-6"></i>
                      <span>Paramètres</span>
                    </button>
                  </li>
                  <li className="pt-4 border-t">
                    <button 
                      onClick={() => {
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        navigate('/login');
                      }}
                      className="flex items-center space-x-3 text-red-500 hover:text-red-600 w-full"
                    >
                      <i className="fas fa-sign-out-alt w-6"></i>
                      <span>Déconnexion</span>
                    </button>
                  </li>
                </ul>
              </div>
            </div>

            {/* Stats */}
            <div className="bg-white rounded-xl shadow-md mt-6 p-6">
              <h3 className="font-bold text-lg mb-4">Statistiques</h3>
              <div className="space-y-4">
                <div className="bg-purple-50 rounded-lg p-4 hover:-translate-y-1 transition-transform">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-gray-500 text-sm">Commandes</p>
                      <p className="font-bold text-xl">{orders.length}</p>
                    </div>
                    <div className="bg-purple-100 p-3 rounded-full">
                      <i className="fas fa-shopping-bag text-purple-600"></i>
                    </div>
                  </div>
                </div>
                <div className="bg-blue-50 rounded-lg p-4 hover:-translate-y-1 transition-transform">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-gray-500 text-sm">Favoris</p>
                      <p className="font-bold text-xl">8</p>
                    </div>
                    <div className="bg-blue-100 p-3 rounded-full">
                      <i className="fas fa-heart text-blue-600"></i>
                    </div>
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4 hover:-translate-y-1 transition-transform">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-gray-500 text-sm">Dépenses</p>
                    <p className="font-bold text-xl">
                      {orders && Array.isArray(orders) 
                        ? orders.reduce((total, order) => total + (order.total_amount || 0), 0).toFixed(2) + ' FCFA'
                        : '0.00 €'}
                    </p>
                  </div>
                  <div className="bg-green-100 p-3 rounded-full">
                    <i className="fas fa-euro-sign text-green-600"></i>
                  </div>
                </div>
              </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="w-full md:w-3/4">
            <div className="bg-white rounded-xl shadow-md overflow-hidden">
              {/* Tabs */}
              <div className="border-b border-gray-200">
                <div className="flex space-x-8 px-6">
                  <button 
                    onClick={() => setActiveTab('profile')}
                    className={`py-4 px-1 ${activeTab === 'profile' ? 'border-b-3 border-purple-600 text-purple-600 font-semibold' : 'text-gray-500 hover:text-purple-600'}`}
                  >
                    Profil
                  </button>
                  <button 
                    onClick={() => setActiveTab('orders')}
                    className={`py-4 px-1 ${activeTab === 'orders' ? 'border-b-3 border-purple-600 text-purple-600 font-semibold' : 'text-gray-500 hover:text-purple-600'}`}
                  >
                    Commandes
                  </button>
                  <button 
                    onClick={() => setActiveTab('wishlist')}
                    className={`py-4 px-1 ${activeTab === 'wishlist' ? 'border-b-3 border-purple-600 text-purple-600 font-semibold' : 'text-gray-500 hover:text-purple-600'}`}
                  >
                    Favoris
                  </button>
                  <button 
                    onClick={() => setActiveTab('settings')}
                    className={`py-4 px-1 ${activeTab === 'settings' ? 'border-b-3 border-purple-600 text-purple-600 font-semibold' : 'text-gray-500 hover:text-purple-600'}`}
                  >
                    Paramètres
                  </button>
                </div>
              </div>

              {activeTab === 'profile' && (
  <div className="p-6">
    <h3 className="text-xl font-bold mb-6">Informations Personnelles</h3>
    
    <form className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
          <input 
            type="text" 
            value={formData.first_name || ''} 
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
            readOnly
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
          <input 
            type="text" 
            value={formData.last_name || ''} 
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
            readOnly
          />
        </div>
      </div>
      
      {/* ... autres champs ... */}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
          <input 
            type="text" 
            value={`${formData.country_code || ''} ${formData.phone || 'Non renseigné'}`} 
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
            readOnly
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Localisation</label>
          <input 
            type="text" 
            value={formData.location || 'Non renseignée'} 
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
            readOnly
          />
        </div>
      </div>
                    
                    






                    <div className="pt-4">
                      <button 
                        type="button"
                        onClick={() => setIsModalOpen(true)}
                        className="bg-gradient-to-r from-purple-600 to-indigo-700 text-white px-6 py-2 rounded-lg hover:opacity-90 transition duration-300 font-medium"
                      >
                        Modifier les informations
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Orders */}
              {activeTab === 'orders' && (
                <div className="p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold">Mes Commandes</h3>
                    <button className="text-purple-600 hover:text-purple-800 text-sm font-medium">
                      Voir tout
                    </button>
                  </div>
                  
                  {orders.length > 0 ? (
                    <div className="space-y-4">
                      {orders.slice(0, 3).map((order) => (
                        <div key={order.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                            <div className="flex items-center space-x-4 mb-4 md:mb-0">
                              {order.items?.[0]?.product_image ? (
                                <img 
                                  src={order.items[0].product_image} 
                                  alt="Product" 
                                  className="w-16 h-16 object-cover rounded"
                                />
                              ) : (
                                <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                                  <i className="fas fa-box-open text-gray-400"></i>
                                </div>
                              )}
                              <div>
                                <h4 className="font-medium">
                                  {order.items?.[0]?.product_name || 'Commande'} {order.items.length > 1 ? `+ ${order.items.length - 1} autres` : ''}
                                </h4>
                                <p className="text-gray-500 text-sm">Commande #{order.id}</p>
                                <p className="text-gray-500 text-sm">
                                  {new Date(order.date).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex flex-col md:items-end">
                              <span className="font-bold">{order.total_amount.toFixed(2)} €</span>
                              <span className={`inline-block px-2 py-1 text-xs rounded-full ${getStatusColor(order.status)} mt-1 capitalize`}>
                                {order.status}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <i className="fas fa-shopping-bag text-4xl text-gray-300 mb-4"></i>
                      <p className="text-gray-500">Vous n'avez pas encore passé de commande</p>
                      <button 
                        onClick={() => navigate('/shop')}
                        className="mt-4 bg-gradient-to-r from-purple-600 to-indigo-700 text-white px-6 py-2 rounded-lg hover:opacity-90 transition duration-300 font-medium"
                      >
                        Découvrir la boutique
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Wishlist */}
              {activeTab === 'wishlist' && (
                <div className="p-6">
                  <h3 className="text-xl font-bold mb-6">Mes Favoris</h3>
                  <div className="text-center py-8">
                    <i className="fas fa-heart text-4xl text-gray-300 mb-4"></i>
                    <p className="text-gray-500">Votre liste de favoris est vide</p>
                    <button 
                      onClick={() => navigate('/shop')}
                      className="mt-4 bg-gradient-to-r from-purple-600 to-indigo-700 text-white px-6 py-2 rounded-lg hover:opacity-90 transition duration-300 font-medium"
                    >
                      Parcourir les produits
                    </button>
                  </div>
                </div>
              )}

              {/* Settings */}
              {activeTab === 'settings' && (
                <div className="p-6">
                  <h3 className="text-xl font-bold mb-6">Paramètres du compte</h3>
                  <div className="space-y-6">
                    <div className="p-4 border border-gray-200 rounded-lg">
                      <h4 className="font-bold mb-2">Sécurité</h4>
                      <p className="text-gray-600 mb-4">Gérez votre mot de passe et la sécurité de votre compte</p>
                      <button 
                        onClick={() => navigate('/change-password')}
                        className="bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-lg transition"
                      >
                        Changer le mot de passe
                      </button>
                    </div>
                    
                    <div className="p-4 border border-gray-200 rounded-lg">
                      <h4 className="font-bold mb-2">Notifications</h4>
                      <p className="text-gray-600 mb-4">Configurez vos préférences de notification</p>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span>Notifications email</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" defaultChecked />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Notifications SMS</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                      </div>
                    </div>
                    
                    <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                      <h4 className="font-bold mb-2 text-red-700">Zone dangereuse</h4>
                      <p className="text-red-600 mb-4">Ces actions sont irréversibles. Soyez certain de votre choix.</p>
                      <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition">
                        Supprimer mon compte
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-12 mt-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4">E-Sugu</h3>
              <p className="text-gray-400">Votre boutique en ligne préférée pour les dernières tendances et produits de qualité.</p>
              <div className="flex space-x-4 mt-4">
                <a href="#" className="text-gray-400 hover:text-white"><i className="fab fa-facebook-f"></i></a>
                <a href="#" className="text-gray-400 hover:text-white"><i className="fab fa-twitter"></i></a>
                <a href="#" className="text-gray-400 hover:text-white"><i className="fab fa-instagram"></i></a>
                <a href="#" className="text-gray-400 hover:text-white"><i className="fab fa-pinterest"></i></a>
              </div>
            </div>
            <div>
              <h4 className="font-bold mb-4">Boutique</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-gray-400 hover:text-white">Nouveautés</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Meilleures ventes</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Soldes</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Collections</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Cadeaux</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Aide</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-gray-400 hover:text-white">FAQ</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Livraison</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Retours</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Paiement sécurisé</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Contactez-nous</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Newsletter</h4>
              <p className="text-gray-400 mb-4">Abonnez-vous pour recevoir nos offres spéciales et actualités.</p>
              <form className="flex">
                <input type="email" placeholder="Votre email" className="px-4 py-2 rounded-l-lg focus:outline-none text-gray-800 w-full" />
                <button type="submit" className="bg-gradient-to-r from-purple-600 to-indigo-700 px-4 py-2 rounded-r-lg font-medium">
                  <i className="fas fa-paper-plane"></i>
                </button>
              </form>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
            <p>© {new Date().getFullYear()} E-Sugu. Tous droits réservés.</p>
          </div>
        </div>
      </footer>

      {/* MODALE D'ÉDITION */}
      <Modal
        isOpen={isModalOpen}
        onRequestClose={() => !isLoading && setIsModalOpen(false)}
        className="bg-white p-6 max-w-lg mx-auto mt-20 rounded-xl shadow-xl outline-none"
        overlayClassName="fixed inset-0 bg-black bg-opacity-30 flex justify-center items-start z-50"
      >
        <h2 className="text-xl font-bold mb-4">Modifier le profil</h2>
        <form onSubmit={handleUpdate} className="space-y-4">
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
      <input
        type="text"
        value={formData.first_name || ''}
        onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
        disabled={isLoading}
      />
    </div>
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
      <input
        type="text"
        value={formData.last_name || ''}
        onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
        disabled={isLoading}
      />
    </div>
  </div>
  
  {/* ... autres champs ... */}
  
  <div className="flex space-x-4">
    <div className="w-1/3 relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">Indicatif</label>
      <select
        value={formData.country_code || '+223'}
        onChange={(e) => setFormData({ ...formData, country_code: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
        disabled={isLoading}
      >
        {COUNTRY_CHOICES.map((country) => (
          <option key={country.code} value={country.code}>
            {country.name}
          </option>
        ))}
      </select>
    </div>
    <div className="w-2/3 relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
      <input
        type="tel"
        value={formData.phone || ''}
        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
        disabled={isLoading}
      />
    </div>
  </div>
  
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">Localisation</label>
    <input
      type="text"
      value={formData.location || ''}
      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
      disabled={isLoading}
    />
  </div>
          
          <div>
  <label className="block text-sm font-medium text-gray-700 mb-1">Photo de profil</label>
  {file ? (
    <div className="mb-2 flex flex-col items-center">
      <img 
        src={URL.createObjectURL(file)} 
        alt="Preview" 
        className="w-20 h-20 rounded-full object-cover mb-2"
      />
      <button
        type="button"
        onClick={() => setFile(null)}
        className="text-sm text-red-600 hover:text-red-800"
      >
        Supprimer
      </button>
    </div>
  ) : (
    <div className="mb-2 flex justify-center">
      <img 
        src={user?.avatar ? `http://localhost:8000${user.avatar}` : 'https://i.pravatar.cc/300'} 
        alt="Current" 
        className="w-20 h-20 rounded-full object-cover"
        onError={(e) => {
          e.target.src = 'https://i.pravatar.cc/300';
        }}
      />
    </div>
  )}
  <input
    type="file"
    accept="image/*"
    onChange={(e) => {
      if (e.target.files && e.target.files[0]) {
        setFile(e.target.files[0]);
      }
    }}
    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent mt-2"
    disabled={isLoading}
  />
  <p className="text-xs text-gray-500 mt-1">Formats acceptés: JPG, PNG (max 2MB)</p>
</div>
          
          <div className="flex justify-end pt-4 space-x-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
              disabled={isLoading}
            >
              Annuler
            </button>
            <button
              type="submit"
              className="bg-gradient-to-r from-purple-600 to-indigo-700 text-white px-4 py-2 rounded-lg hover:opacity-90 transition disabled:opacity-50"
              disabled={isLoading}
            >
              {isLoading ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Profile;