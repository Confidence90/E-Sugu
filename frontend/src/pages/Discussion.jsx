import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Send, 
  Phone, 
  Video, 
  MoreVertical,
  MapPin,
  Home,
  User
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Discussion = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);

  // Configuration d'Axios pour inclure le token d'authentification
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  // Charger les données de la propriété et les messages
  useEffect(() => {
    const loadPropertyAndMessages = async () => {
      try {
        setLoading(true);
        
        // Charger les données de la propriété
        const propertyResponse = await axios.get(`http://localhost:8000/api/listings/${propertyId}/`);
        const propertyData = propertyResponse.data;
        
        setProperty({
          id: propertyData.id,
          title: propertyData.title,
          price: propertyData.price || 0,
          location: propertyData.location || 'Localisation non spécifiée',
          image: propertyData.images?.[0]?.image || 'https://source.unsplash.com/random/600x400/?property,house',
          seller: {
            name: propertyData.seller?.username || 'Vendeur',
            avatar: propertyData.seller?.profile_picture || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face',
            isOnline: propertyData.seller?.is_online || false
          }
        });

        // Charger les messages de la discussion
        try {
          // Essayer d'abord avec l'endpoint qui fonctionne dans le Profile
          const discussionResponse = await axios.get(`http://localhost:8000/api/discussions/discussions/`);
          
          // Filtrer les discussions pour trouver celle qui correspond à la propriété
          const discussions = discussionResponse.data.results || discussionResponse.data;
          const discussion = discussions.find(d => d.listing.id.toString() === propertyId);
          
          if (discussion) {
            // Vérifier si la discussion a des messages
            if (discussion.messages && Array.isArray(discussion.messages)) {
              const formattedMessages = discussion.messages.map(msg => ({
                id: msg.id.toString(),
                text: msg.content,
                timestamp: new Date(msg.created_at),
                isOwn: msg.sender.id === parseInt(localStorage.getItem('userId') || '0'),
                type: 'text'
              }));
              
              setMessages(formattedMessages);
            }
          } else {
            // Si aucune discussion n'existe, initialiser avec des messages vides
            setMessages([]);
          }
        } catch (discussionError) {
          console.error('Erreur lors du chargement des messages:', discussionError);
          // Initialiser avec des messages vides si l'API n'est pas disponible
          setMessages([]);
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        toast.error("Impossible de charger la discussion");
        setLoading(false);
      }
    };

    if (propertyId) {
      loadPropertyAndMessages();
    }
  }, [propertyId]);

  // Auto-scroll vers le bas
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Envoyer un message
  const sendMessage = async () => {
    if (!newMessage.trim() || !propertyId) return;

    try {
      // Essayer d'abord avec l'endpoint /api/messages/
      const response = await axios.post('http://localhost:8000/api/discussion/messages/', {
        listing_id: parseInt(propertyId),
        content: newMessage
      });

      // Ajouter le message à l'état local
      const messageData = response.data;
      const newMsg = {
        id: messageData.id.toString(),
        text: messageData.content,
        timestamp: new Date(messageData.created_at),
        isOwn: true,
        type: 'text'
      };

      setMessages(prev => [...prev, newMsg]);
      setNewMessage('');
      
      toast.success('Message envoyé');
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      
      // Si le premier endpoint échoue, essayer avec /api/send-message/
      if (error.response?.status === 404) {
        try {
          const response = await axios.post('http://localhost:8000/api/discussion/send-message/', {
            listing_id: parseInt(propertyId),
            content: newMessage
          });
          
          const messageData = response.data;
          const newMsg = {
            id: messageData.id.toString(),
            text: messageData.content,
            timestamp: new Date(messageData.created_at),
            isOwn: true,
            type: 'text'
          };
          
          setMessages(prev => [...prev, newMsg]);
          setNewMessage('');
          toast.success('Message envoyé');
        } catch (secondError) {
          console.error('Erreur avec le second endpoint:', secondError);
          if (secondError.response?.status === 401) {
            toast.error('Veuillez vous connecter pour envoyer un message');
            navigate('/login');
          } else {
            toast.error("Impossible d'envoyer le message");
          }
        }
      } else if (error.response?.status === 401) {
        toast.error('Veuillez vous connecter pour envoyer un message');
        navigate('/login');
      } else {
        toast.error("Impossible d'envoyer le message");
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Chargement de la discussion...</p>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">Propriété non trouvée</p>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(-1)}
              className="text-white p-2 rounded-full hover:bg-blue-700 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="h-10 w-10 rounded-full overflow-hidden bg-gray-200">
                  <img 
                    src={property.seller.avatar} 
                    alt={property.seller.name}
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      e.target.src = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face';
                    }}
                  />
                </div>
                {property.seller.isOnline && (
                  <div className="absolute -bottom-1 -right-1 h-3 w-3 bg-green-500 border-2 border-white rounded-full"></div>
                )}
              </div>
              
              <div>
                <h2 className="font-semibold">{property.seller.name}</h2>
                <p className="text-xs text-blue-100">
                  {property.seller.isOnline ? 'En ligne' : 'Hors ligne'}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button className="text-white p-2 rounded-full hover:bg-blue-700 transition-colors">
              <Phone className="h-5 w-5" />
            </button>
            <button className="text-white p-2 rounded-full hover:bg-blue-700 transition-colors">
              <Video className="h-5 w-5" />
            </button>
            <button className="text-white p-2 rounded-full hover:bg-blue-700 transition-colors">
              <MoreVertical className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Property Card */}
      <div className="max-w-4xl mx-auto w-full p-4">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="flex">
            <img 
              src={property.image} 
              alt={property.title}
              className="w-24 h-24 object-cover"
              onError={(e) => {
                e.target.src = 'https://source.unsplash.com/random/600x400/?property,house';
              }}
            />
            <div className="flex-1 p-4">
              <h3 className="font-semibold text-lg mb-1">{property.title}</h3>
              <p className="text-blue-600 font-bold text-xl mb-2">
                {property.price.toLocaleString()} FCFA
              </p>
              <div className="flex items-center text-sm text-gray-500">
                <MapPin className="h-4 w-4 mr-1" />
                {property.location}
              </div>
            </div>
            <div className="p-4 flex items-center">
              <button 
                onClick={() => navigate(`/details/${property.id}`)}
                className="px-3 py-2 border border-blue-600 text-blue-600 rounded-md text-sm flex items-center hover:bg-blue-50 transition-colors"
              >
                <Home className="h-4 w-4 mr-2" />
                Voir détails
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 max-w-4xl mx-auto w-full px-4 pb-4 overflow-hidden">
        <div className="h-full bg-white rounded-lg shadow-sm flex flex-col">
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isOwn ? 'justify-end' : 'justify-start'}`}
              >
                <div className="flex items-end space-x-2 max-w-xs lg:max-w-md">
                  {!message.isOwn && (
                    <div className="h-6 w-6 rounded-full overflow-hidden bg-gray-200 flex-shrink-0">
                      <img 
                        src={property.seller.avatar} 
                        alt={property.seller.name}
                        className="h-full w-full object-cover"
                        onError={(e) => {
                          e.target.src = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face';
                        }}
                      />
                    </div>
                  )}
                  
                  <div className={`rounded-2xl px-4 py-2 ${
                    message.isOwn 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <p className="text-sm">{message.text}</p>
                    <p className={`text-xs mt-1 ${
                      message.isOwn ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      {formatTime(message.timestamp)}
                    </p>
                  </div>

                  {message.isOwn && (
                    <div className="h-6 w-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                      <User className="h-3 w-3 text-gray-600" />
                    </div>
                  )}
                </div>
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t p-4">
            <div className="flex items-center space-x-2">
              <input
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Tapez votre message..."
                className="flex-1 rounded-full bg-gray-100 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button 
                onClick={sendMessage}
                disabled={!newMessage.trim()}
                className="rounded-full bg-blue-600 p-2 text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Discussion;