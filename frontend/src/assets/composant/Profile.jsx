import React, { useEffect, useState, useRef  } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import Modal from 'react-modal';

import { useNavigate, useSearchParams } from 'react-router-dom';

Modal.setAppElement('#root');

const Profile = () => {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ full_name: '', first_name:'', last_name:'', avatar: '', email: '', phone: '' });
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [discussions, setDiscussions] = useState([]);
  const [selectedDiscussion, setSelectedDiscussion] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isLoadingDiscussions, setIsLoadingDiscussions] = useState(false);
  const [favoriteListings, setFavoriteListings] = useState([]);
  const [isLoadingFavorites, setIsLoadingFavorites] = useState(false);
  const messagesEndRef = useRef(null);

  const fetchDiscussions = async () => {
    setIsLoadingDiscussions(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get('http://localhost:8000/api/discussion/discussions/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDiscussions(response.data.results || []);
    } catch (error) {
      console.error('Erreur lors du chargement des discussions:', error);
      if (error.response?.status !== 401) {
        toast.error('Erreur lors du chargement des discussions');
      }
    } finally {
      setIsLoadingDiscussions(false);
    }
  };

const fetchMessages = async (discussionId) => {
  setIsLoadingMessages(true);
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Token d\'authentification manquant');
      return;
    }

    const response = await axios.get(`http://localhost:8000/api/discussion/discussions/${discussionId}/`, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.data && response.data.messages) {
      setMessages(response.data.messages);
      setSelectedDiscussion(response.data);
    }
  } catch (error) {
    console.error('Erreur détaillée:', error.response?.data);
    if (error.response?.status !== 401) {
      toast.error('Erreur lors du chargement des messages');
    }
  } finally {
    setIsLoadingMessages(false);
  }
};

const sendMessage = async () => {
  if (!newMessage.trim() || !selectedDiscussion) return;

  try {
    console.log("DEBUG selectedDiscussion:", selectedDiscussion);
    console.log("DEBUG listing:", selectedDiscussion.listing);
    console.log("DEBUG listing_id:", selectedDiscussion.listing?.id);

    const token = localStorage.getItem('access_token');

    const payload = {
      listing_id: selectedDiscussion.listing_id, // Champ maintenant disponible
      content: newMessage
    };console.log("Payload envoyé:", payload);

    const response = await axios.post(
      'http://localhost:8000/api/discussion/messages/',
      payload,
      {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    setMessages([...messages, response.data]);
    setNewMessage('');
    toast.success('Message envoyé');
  } catch (error) {
    console.error('Erreur détaillée:', error.response?.data);

    if (error.response?.status === 404) {
      toast.error('Annonce non trouvée');
    } else if (error.response?.status === 400) {
      toast.error('Données invalides');
    } else {
      toast.error('Erreur lors de l\'envoi du message');
    }
  }
};


// Dans le composant Profile
useEffect(() => {
  let intervalId;
  
  if (activeTab === 'messages' && selectedDiscussion) {
    intervalId = setInterval(() => {
      fetchMessages(selectedDiscussion.id);
    }, 5000); // Vérifier toutes les 5 secondes
  }
  
  return () => {
    if (intervalId) clearInterval(intervalId);
  };
}, [activeTab, selectedDiscussion]);


  useEffect(() => {
    if (activeTab === 'messages') {
      fetchDiscussions();
    }
  }, [activeTab]);

  useEffect(() => {
  if (messagesEndRef.current && activeTab === 'messages') {
    messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  }
}, [messages, activeTab]);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && ['profile', 'orders', 'wishlist', 'settings', 'addresses', 'payments', 'messages'].includes(tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);


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

  // Configuration de l'intercepteur axios
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
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

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [navigate]);

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
        country_code: res.data.country_code || '+223',
        location: res.data.location || ''
      });
      if (!res.data.first_name && !res.data.last_name) {
        toast.warn('Veuillez compléter votre prénom et nom dans le profil');
      }
    } catch (err) {
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

  // Fonction pour récupérer les favoris
  const fetchFavoriteListings = async () => {
    setIsLoadingFavorites(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get('http://localhost:8000/api/favorites/listings/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Accéder aux résultats via response.data.results
      setFavoriteListings(response.data.results || []);
    } catch (error) {
      console.error('Erreur lors du chargement des favoris:', error);
      if (error.response?.status !== 401) {
        toast.error('Erreur lors du chargement des favoris');
      }
    } finally {
      setIsLoadingFavorites(false);
    }
  };

  // Fonction pour retirer des favoris
  const handleRemoveFavorite = async (listingId) => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`http://localhost:8000/api/favorites/listings/remove/${listingId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Mettre à jour la liste localement
      setFavoriteListings(prev => prev.filter(fav => fav.listing.id !== listingId));
      toast.success('Annonce retirée des favoris');
    } catch (error) {
      console.error('Erreur lors de la suppression des favoris:', error);
      if (error.response?.status !== 401) {
        toast.error('Erreur lors de la suppression des favoris');
      }
    }
  };
//Enlever code de test avant déploiement
/*const testEndpoints = async () => {
  const token = localStorage.getItem('access_token');
  const testData = [
    { listing_id: parseInt(selectedDiscussion.listing.id), content: "TEST" },  // Format correct - entier simple
    { listing_id: [parseInt(selectedDiscussion.listing.id)], content: "TEST" }, // Format incorrect - tableau (pour comparaison)
  ];

  for (let i = 0; i < testData.length; i++) {
    try {
      const response = await axios.post(
        'http://localhost:8000/api/discussion/messages/',
        testData[i],
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      console.log(`Format ${i+1} réussi:`, response.data);
      toast.success(`Format ${i+1} fonctionne`);
      return i + 1;
    } catch (error) {
      console.log(`Format ${i+1} échoué:`, error.response?.data);
    }
  }
  toast.error('Aucun format ne fonctionne');
  return 0;
};
//Enlever code de test avant déploiement
  useEffect(() => {
  // Exécuter le test automatiquement quand une discussion est sélectionnée
  if (selectedDiscussion && process.env.NODE_ENV === 'development') {
    const runTest = async () => {
      console.log("Exécution automatique du test des endpoints...");
      await testEndpoints();
    };
    runTest();
  }
}, [selectedDiscussion]);*/

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

  // Charger les favoris quand l'onglet est activé
  useEffect(() => {
    if (activeTab === 'wishlist') {
      fetchFavoriteListings();
    }
  }, [activeTab]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const token = localStorage.getItem('access_token');
    const form = new FormData();
    form.append('first_name', formData.first_name);
    form.append('last_name', formData.last_name);
    if (file) form.append('avatar', file);
    if (formData.phone) form.append('phone', formData.phone);
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

  // Liste des indicatifs téléphoniques
  const COUNTRY_CHOICES = [
    // ... (votre liste de pays existante)
  ];

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
            <a href="/" className="hover:text-gray-200">Accueil</a>
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
                      onClick={() => {
                        setActiveTab('messages');
                        setSearchParams({ tab: 'messages' });
                      }}
                      className={`flex items-center justify-between w-full ${activeTab === 'messages' ? 'text-purple-600 font-medium' : 'text-gray-600 hover:text-purple-600'}`}
                    >
                      <div className="flex items-center space-x-3">
                        <i className="fas fa-comments w-6"></i>
                        <span>Messages</span>
                      </div>
                      {discussions.some(d => 
                        d.messages && d.messages.some(m => !m.is_read && m.sender.id !== user?.id)
                      ) && (
                        <span className="bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                          {discussions.reduce((total, d) => {
                            if (d.messages) {
                              return total + d.messages.filter(m => !m.is_read && m.sender.id !== user?.id).length;
                            }
                            return total;
                          }, 0)}
                        </span>
                      )}
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
                      <p className="font-bold text-xl">{favoriteListings.length}</p>
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
                          : '0.00 FCFA'}
                      </p>
                    </div>
                    <div className="bg-green-100 p-3 rounded-full">
                      <i className="fas fa-euro-sign text-green-600"></i>
                    </div>
                  </div>
                </div>
                <div className="bg-indigo-50 rounded-lg p-4 hover:-translate-y-1 transition-transform">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-gray-500 text-sm">Messages</p>
                      <p className="font-bold text-xl">
                        {discussions.reduce((total, d) => total + (d.messages?.length || 0), 0)}
                      </p>
                    </div>
                    <div className="bg-indigo-100 p-3 rounded-full">
                      <i className="fas fa-comments text-indigo-600"></i>
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
                    onClick={() => {
                      setActiveTab('messages');
                      setSearchParams({ tab: 'messages' });
                    }}
                    className={`py-4 px-1 ${activeTab === 'messages' ? 'border-b-3 border-purple-600 text-purple-600 font-semibold' : 'text-gray-500 hover:text-purple-600'}`}
                  >
                    Messages
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

                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                        <input 
                          type="email" 
                          value={formData.email || 'Non défini'} 
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                          readOnly
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                        <input 
                          type="text" 
                          value={`${formData.country_code || ''} ${formData.phone || 'Non renseigné'}`} 
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                          readOnly
                        />
                      </div>
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
                              <span className="font-bold">{order.total_amount.toFixed(2)} FCFA</span>
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
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold">Mes Favoris</h3>
                    <button 
                      onClick={fetchFavoriteListings}
                      className="text-purple-600 hover:text-purple-800 text-sm font-medium flex items-center"
                    >
                      <i className="fas fa-sync-alt mr-1"></i> Actualiser
                    </button>
                  </div>
                  
                  {isLoadingFavorites ? (
                    <div className="text-center py-8">
                      <i className="fas fa-spinner fa-spin text-4xl text-purple-600 mb-4"></i>
                      <p className="text-gray-500">Chargement des favoris...</p>
                    </div>
                  ) : favoriteListings.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {favoriteListings.map((favorite) => {
                        // Prendre la première image disponible ou une image par défaut
                        const firstImage = favorite.listing.images && favorite.listing.images.length > 0 
                          ? favorite.listing.images[0].image 
                          : 'https://via.placeholder.com/300';
                        
                        return (
                          <div key={favorite.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                            <img 
                              src={firstImage}
                              alt={favorite.listing.title}
                              className="w-full h-48 object-cover"
                              onError={(e) => {
                                e.target.src = 'https://via.placeholder.com/300';
                              }}
                            />
                            <div className="p-4">
                              <h4 className="font-medium mb-2 line-clamp-1">{favorite.listing.title}</h4>
                              <p className="text-gray-600 text-sm mb-2 line-clamp-2">{favorite.listing.description}</p>
                              <div className="flex justify-between items-center">
                                <p className="text-purple-600 font-bold">{parseFloat(favorite.listing.price).toLocaleString()} FCFA</p>
                                <span className="text-xs bg-gray-100 px-2 py-1 rounded capitalize">
                                  {favorite.listing.condition === 'used' ? 'Occasion' : 'Neuf'}
                                </span>
                              </div>
                              <div className="flex justify-between items-center mt-4">
                                <button 
                                  onClick={() => navigate(`/listing/${favorite.listing.id}`)}
                                  className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                                >
                                  Voir détails
                                </button>
                                <button 
                                  onClick={() => handleRemoveFavorite(favorite.listing.id)}
                                  className="text-red-500 hover:text-red-700"
                                  title="Retirer des favoris"
                                >
                                  <i className="fas fa-trash"></i>
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
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
                  )}
                </div>
              )}
              {activeTab === 'messages' && (
                <div className="p-6">
                  <h3 className="text-xl font-bold mb-6">Mes Messages</h3>
                  
                  {isLoadingDiscussions ? (
                    <div className="text-center py-8">
                      <i className="fas fa-spinner fa-spin text-4xl text-purple-600 mb-4"></i>
                      <p className="text-gray-500">Chargement des discussions...</p>
                    </div>
                  ) : selectedDiscussion ? (
                    <div>
                      {/* Header de la discussion */}
                      <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center">
                          <button 
                            onClick={() => setSelectedDiscussion(null)}
                            className="mr-4 text-purple-600 hover:text-purple-800"
                          >
                            <i className="fas fa-arrow-left"></i>
                          </button>
                          <div>
                            <h4 className="font-bold">{selectedDiscussion.listing_title}</h4>
                            <p className="text-gray-600 text-sm">
                              Discussion avec {user.id === selectedDiscussion.buyer.id ? 
                              selectedDiscussion.seller.username : selectedDiscussion.buyer.username}
                            </p>
                          </div>
                        </div>
                        <img 
                          src={selectedDiscussion.listing_images?.[0]?.image || 'https://via.placeholder.com/150'} 
                          alt={selectedDiscussion.listing_title}
                          className="w-16 h-16 object-cover rounded"
                          onError={(e) => {
                            e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI0VFRUVFRSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkeT0iLjM1ZW0iIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5OTk5OTkiPjE1MHgxNTA8L3RleHQ+PC9zdmc+';
                          }}
                        />
                      </div>
                      
                      {/* Messages */}
                      <div className="border rounded-lg p-4 mb-4 h-96 overflow-y-auto">
                        {isLoadingMessages ? (
                          <div className="text-center py-8">
                            <i className="fas fa-spinner fa-spin text-purple-600"></i>
                          </div>
                        ) : messages.length > 0 ? (
                          messages.map((message) => {
                            const isOwn = message.sender.id === user?.id;
                            return (
                                <div 
                                  key={message.id} 
                                  className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-4`}
                                >
                                  <div className="flex items-end space-x-2 max-w-xs lg:max-w-md">
                                    {!isOwn && (
                                      <div className="h-6 w-6 rounded-full overflow-hidden bg-gray-200 flex-shrink-0">
                                       <img 
                                            src={selectedDiscussion.buyer.id === user?.id ? 
                                              (selectedDiscussion.seller.avatar ? 
                                                `http://localhost:8000${selectedDiscussion.seller.avatar}` : 
                                                'https://i.pravatar.cc/150?img=3') : 
                                              (selectedDiscussion.buyer.avatar ? 
                                                `http://localhost:8000${selectedDiscussion.buyer.avatar}` : 
                                                'https://i.pravatar.cc/150?img=4')} 
                                            alt="Avatar"
                                            className="h-full w-full object-cover"
                                            onError={(e) => {
                                              e.target.src = 'https://i.pravatar.cc/150?img=5';
                                            }}
                                          />
                                      </div>
                                    )}
                                    
                                    <div className={`rounded-2xl px-4 py-2 ${
                                      isOwn 
                                        ? 'bg-blue-600 text-white' 
                                        : 'bg-gray-100 text-gray-900'
                                    }`}>
                                      <p className="text-sm">{message.content}</p>
                                      <p className={`text-xs mt-1 ${
                                        isOwn ? 'text-blue-100' : 'text-gray-500'
                                      }`}>
                                        {new Date(message.created_at).toLocaleTimeString('fr-FR', { 
                                          hour: '2-digit', 
                                          minute: '2-digit' 
                                        })}
                                      </p>
                                    </div>

                                    {isOwn && (
                                      <div className="h-6 w-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                                        <i className="fas fa-user text-gray-600 text-xs"></i>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })
                          ) : (
                            <div className="text-center text-gray-500 py-8">
                              Aucun message dans cette conversation
                            </div>
                          )}
                          <div ref={messagesEndRef} />
                        </div>

                        {/* Input pour envoyer un message - REMPLACEZ AUSSI CETTE PARTIE */}
                        <div className="flex items-center space-x-2">
                          <input
                            type="text"
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            placeholder="Tapez votre message..."
                            className="flex-1 rounded-full bg-gray-100 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-600"
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                sendMessage();
                              }
                            }}
                          />
                          <button
                            onClick={sendMessage}
                            disabled={!newMessage.trim() || !selectedDiscussion}
                            className="rounded-full bg-gradient-to-r from-purple-600 to-indigo-700 p-2 text-white hover:opacity-90 transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <i className="fas fa-paper-plane"></i>
                          </button>
                        </div>
                        {/* AJOUTEZ ICI LE BOUTON DE TEST */}

                    </div>
                  ) : (
                    <div>
                      {discussions.length > 0 ? (
                        <div className="space-y-4">
                          {discussions.map((discussion) => (
                            <div 
                              key={discussion.id} 
                              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                              onClick={() => fetchMessages(discussion.id)}
                            >
                              <div className="flex justify-between items-start">
                                <div className="flex-1">
                                  <h4 className="font-medium">{discussion.listing_title}</h4>


                                  <p className="text-gray-600 text-sm">
                                    Avec {user.id === discussion.buyer.id ? 
                                    discussion.seller.username : discussion.buyer.username}
                                  </p>
                                  {discussion.messages && discussion.messages.length > 0 && (
                                    <p className="text-gray-500 text-sm mt-2 truncate">
                                      {discussion.messages[discussion.messages.length - 1].content}
                                    </p>
                                  )}
                                </div>
                                <div className="text-right">
                                  <p className="text-xs text-gray-500">
                                    {new Date(discussion.created_at).toLocaleDateString()}
                                  </p>
                                  {discussion.messages && discussion.messages.some(m => !m.is_read && m.sender !== user.id) && (
                                    <span className="inline-block mt-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                                      {discussion.messages.filter(m => !m.is_read && m.sender !== user.id).length}
                                    </span>
                                  )}s
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <i className="fas fa-comments text-4xl text-gray-300 mb-4"></i>
                          <p className="text-gray-500">Vous n'avez aucune conversation</p>
                        </div>
                      )}
                    </div>
                  )}
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

      {/* Styles CSS pour line-clamp */}
      <style>
        {`
          .line-clamp-1 {
            overflow: hidden;
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 1;
          }
          .line-clamp-2 {
            overflow: hidden;
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
          }
        `}
      </style>
    </div>
  );
};

export default Profile;