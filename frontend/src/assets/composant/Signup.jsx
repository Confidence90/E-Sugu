import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from "react-router-dom";
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import { FaEye, FaEyeSlash, FaCheck, FaShoppingBag, FaArrowRight, FaSpinner, FaCheckCircle, FaGoogle, FaFacebookF, FaApple } from 'react-icons/fa';

const Signup = () => {
  const navigate = useNavigate();
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const [fieldErrors, setFieldErrors] = useState({});
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    password2: '',
    country_code: '+223', // Valeur par défaut pour la Côte d'Ivoire
    phone: '',
    location: '',
    is_seller: false
  });

  const [passwordStrength, setPasswordStrength] = useState({
    width: '0%',
    color: 'bg-gray-200',
    requirements: {
      length: false,
      number: false,
      special: false,
      uppercase: false
    }
  });

  const [showPassword, setShowPassword] = useState({
    password: false,
    password2: false
  });

  const [termsAccepted, setTermsAccepted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { first_name, last_name, email, password, password2, country_code, phone, location } = formData;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFieldErrors(prev => ({ ...prev, [name]: undefined }));
    setError("");
    
    setFormData({ ...formData, [name]: value });

    if (name === 'password') {
      checkPasswordStrength(value);
    }
  };

  const checkPasswordStrength = (password) => {
    let strength = 0;
    const requirements = {
      length: password.length >= 8,
      number: /[0-9]/.test(password),
      special: /[!@#$%^&*]/.test(password),
      uppercase: /[A-Z]/.test(password) && /[a-z]/.test(password)
    };

    if (requirements.length) strength += 25;
    if (requirements.number) strength += 25;
    if (requirements.special) strength += 25;
    if (requirements.uppercase) strength += 25;

    let color;
    if (strength <= 25) {
      color = 'bg-red-500';
    } else if (strength <= 50) {
      color = 'bg-yellow-500';
    } else if (strength <= 75) {
      color = 'bg-blue-500';
    } else {
      color = 'bg-green-500';
    }

    setPasswordStrength({
      width: `${strength}%`,
      color,
      requirements
    });
  };

  const togglePasswordVisibility = (field) => {
    setShowPassword({
      ...showPassword,
      [field]: !showPassword[field]
    });
  };

  const handleSigninWithGoogle = async (response) => {
    try {
      const payload = response.credential;
      const server_res = await axios.post(
        'http://localhost:8000/api/users/google/',
        { access_token: payload }
      );
      console.log(server_res.data);
      navigate('/dashboard');
      toast.success("Connexion réussie avec Google");
    } catch (error) {
      toast.error("Erreur lors de la connexion Google");
    }
  };

  useEffect(() => {
    const loadGoogleScript = () => {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        if (window.google && clientId) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleSigninWithGoogle,
          });

          window.google.accounts.id.renderButton(
            document.getElementById('googleSignIn'),
            {
              theme: 'outline',
              size: 'large',
              text: 'signnp_with',
              shape: 'rectangular',
              width: 100,
            }
          );
        } else {
          console.error("Google API ou clientId introuvable.");
        }
      };
      document.body.appendChild(script);
    };

    loadGoogleScript();
  }, []);

  const [error, setError] = useState("");
  const handleSocialLogin = (provider) => {
    toast.info(`Connexion avec ${provider} en cours...`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Réinitialiser les erreurs
    setFieldErrors({});
    setError("");
    // Validation des champs obligatoires
    if (!termsAccepted) {
      toast.error("Veuillez accepter les conditions générales");
      return;
    }
    // Validation des mots de passe
    if (password !== password2) {
      setFieldErrors({ password2: "Les mots de passe ne correspondent pas" });
      return;
    }
    // Validation des champs requis
    if (!email || !first_name || !last_name || !password || !password2 || !phone) {
      setError("Tous les champs obligatoires doivent être remplis !");
      return;
    }
    // Validation du téléphone
    if (!/^\d{8,}$/.test(phone)) {
    setFieldErrors({ phone: "Le numéro doit contenir au moins 8 chiffres" });
    return;
  }

    setIsSubmitting(true);
    
    try {
    
      const response = await axios.post(
        'http://localhost:8000/api/users/register/',
        {
          first_name: first_name.trim(),
          last_name: last_name.trim(),
          email: email.trim(),
          password: password,
          password2: password2,
          country_code: country_code,
          phone: phone.trim(),
          location: location.trim(),
          is_seller_pending: false
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        }
      );
      if (process.env.NODE_ENV === 'development') {
        console.log('API Response:', response); 
      }
      
      
    
      if (response.status === 201) {
  // ✅ Stocker l’email dans localStorage
      localStorage.setItem("registrationEmail", email);

  // ✅ Naviguer vers la page de vérification avec l’email dans l’URL
      navigate(`/otp/verify?email=${encodeURIComponent(email)}`);

  // ✅ Optionnel : message de confirmation
    toast.success(response.data.message || 'Compte créé avec succès');
    }

    } catch (err) {
      console.error('Erreur détaillée:', err.response?.data);
      
      if (err.response) {
      // Erreurs de validation
      if (err.response.status === 400) {
        const { data } = err.response;
        
        // Gestion des erreurs de champ
        if (data.errors) {
          setFieldErrors(data.errors);
        } 
        // Email déjà existant
        else if (data.email) {
          setError("Cet email est déjà utilisé");
          setFieldErrors({ email: data.email });
        }
        // Erreur de téléphone
        else if (data.phone) {
          setError("Numéro de téléphone invalide");
          setFieldErrors({ phone: data.phone });
        }
        // Message général
        else if (data.message) {
          setError(data.message);
        } else {
          setError("Veuillez vérifier les informations saisies");
        }
      }
      // Erreur serveur
      else if (err.response.status === 500) {
        setError("Erreur serveur. Veuillez réessayer plus tard.");
      } else {
        setError(err.response.data?.message || 'Erreur lors de la création du compte.');
      }
    } 
        // Erreur de connexion
    else if (err.request) {
      setError("Le serveur ne répond pas. Vérifiez votre connexion.");
    } 
    // Erreur inattendue
    else {
      setError("Une erreur inattendue est survenue");
    }
  } finally {
    setIsSubmitting(false);
  }
  };   
    

  // Liste des indicatifs téléphoniques
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

  return (
    <div className="bg-gray-50 min-h-screen flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col md:flex-row transform hover:shadow-2xl transition duration-500">
        {/* Illustration Section */}
        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 text-white p-8 md:w-1/2 flex flex-col justify-center items-center text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full opacity-10">
            <div className="absolute top-20 left-20 w-32 h-32 rounded-full bg-white"></div>
            <div className="absolute bottom-10 right-10 w-40 h-40 rounded-full bg-white"></div>
            <div className="absolute top-1/3 right-20 w-24 h-24 rounded-full bg-white"></div>
          </div>
          
          <div className="relative z-10 mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-indigo-600 to-purple-700 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg animate-pulse">
              <FaShoppingBag className="text-3xl" />
            </div>
            <h1 className="text-3xl font-bold mb-2">Rejoignez notre communauté</h1>
            <p className="opacity-90 max-w-md">Créez votre compte et bénéficiez de 10% de réduction sur votre première commande + un cadeau surprise !</p>
          </div>
          
          <div className="relative z-10 w-full max-w-xs animate-float">
            <img 
              src="https://cdn.dribbble.com/users/1787505/screenshots/11300794/media/3b5b1e9d0b3d3e68c7a7d9b9f5a5a5e9.png" 
              alt="Shopping illustration" 
              className="w-full h-auto"
            />
          </div>
          
          <div className="relative z-10 mt-8 flex space-x-4">
            <div className="w-3 h-3 bg-white rounded-full opacity-60"></div>
            <div className="w-3 h-3 bg-white rounded-full opacity-30"></div>
            <div className="w-3 h-3 bg-white rounded-full opacity-10"></div>
          </div>
          
          <p className="relative z-10 mt-6 text-sm opacity-80">
            Déjà membre? <Link to="/login" className="font-semibold underline hover:opacity-90 transition">Connectez-vous</Link>
          </p>
        </div>
        
        {/* Form Section */}
        <div className="p-8 md:w-1/2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Créer un compte</h2>
            <div className="flex space-x-2">
              <div className="w-2 h-2 bg-indigo-400 rounded-full"></div>
              <div className="w-2 h-2 bg-indigo-300 rounded-full"></div>
              <div className="w-2 h-2 bg-indigo-200 rounded-full"></div>
            </div>
          </div>
          {/* Message d'erreur général plus visible */}
          {(error || Object.keys(fieldErrors).length > 0) && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg">
              {error && <p className="font-medium">{error}</p>}
              {Object.entries(fieldErrors).map(([field, message]) => (
                field !== 'password2' && <p key={field}>{message}</p>
              ))}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex space-x-4">
              <div className="w-1/2 relative">
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                <input 
                  type="text" 
                  id="first_name" 
                  name="first_name" 
                  required
                  value={first_name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200"
                  placeholder="Votre prénom"
                />
                <div className={`absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none transition duration-200 ${first_name ? 'opacity-100' : 'opacity-0'}`}>
                  <FaCheck className="text-green-500" />
                </div>
              </div>
              <div className="w-1/2 relative">
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                <input 
                  type="text" 
                  id="last_name" 
                  name="last_name" 
                  required
                  value={last_name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200"
                  placeholder="Votre nom"
                />
                <div className={`absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none transition duration-200 ${last_name ? 'opacity-100' : 'opacity-0'}`}>
                  <FaCheck className="text-green-500" />
                </div>
              </div>
            </div>
            
            {/* Pour l'email */}
            <div className="relative">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input 
                type="email" 
                id="email" 
                name="email" 
                required
                value={email}
                onChange={handleChange}
                className={`w-full px-4 py-3 border ${fieldErrors.email ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200`}
                placeholder="exemple@domaine.com"
              />
              {fieldErrors.email && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p>
              )}
              <div className={`absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none transition duration-200 ${email ? 'opacity-100' : 'opacity-0'}`}>
                <FaCheck className="text-green-500" />
              </div>
            </div>

            {/* Nouveaux champs ajoutés */}
            <div className="flex space-x-4">
              <div className="w-1/3 relative">
                <label htmlFor="country_code" className="block text-sm font-medium text-gray-700 mb-1">Indicatif</label>
                <select
                  id="country_code"
                  name="country_code"
                  value={country_code}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200"
                >
                  {COUNTRY_CHOICES.map((country) => (
                    <option key={country.code} value={country.code}>
                      {country.name} ({country.code})
                    </option>
                  ))}
                </select>
              </div>
              <div className="w-2/3 relative">
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                <input 
                  type="tel" 
                  id="phone" 
                  name="phone" 
                  required
                  value={phone}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200"
                  placeholder="77777777"
                />
                 {fieldErrors.phone && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.phone}</p>
                  )}
                <div className={`absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none transition duration-200 ${phone ? 'opacity-100' : 'opacity-0'}`}>
                  <FaCheck className="text-green-500" />
                </div>
              </div>
            </div>

            <div className="relative">
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">Localisation (Ville)</label>
              <input 
                type="text" 
                id="location" 
                name="location" 
                value={location}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200"
                placeholder="Bamako"
              />
              <div className={`absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none transition duration-200 ${location ? 'opacity-100' : 'opacity-0'}`}>
                <FaCheck className="text-green-500" />
              </div>
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
              <div className="relative">
                <input 
                  type={showPassword.password ? "text" : "password"} 
                  id="password" 
                  name="password" 
                  required
                  value={password}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200"
                  placeholder="••••••••"
                />
                <button 
                  type="button" 
                  className="absolute right-3 top-3 text-gray-500 hover:text-gray-700 transition"
                  onClick={() => togglePasswordVisibility('password')}
                >
                  {showPassword.password ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
              )}
              <div className="mt-2">
                <div className="flex mb-1">
                  <div className="w-full bg-gray-200 rounded-full h-1">
                    <div 
                      className={`h-full rounded-full ${passwordStrength.color}`} 
                      style={{ width: passwordStrength.width }}
                    ></div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 flex flex-wrap gap-1">
                  <span className="inline-flex items-center">
                    {passwordStrength.requirements.length ? (
                      <FaCheck className="text-green-500 mr-1 text-xs" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-gray-300 mr-1"></span>
                    )}
                    8 caractères
                  </span>
                  <span className="inline-flex items-center">
                    {passwordStrength.requirements.number ? (
                      <FaCheck className="text-green-500 mr-1 text-xs" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-gray-300 mr-1"></span>
                    )}
                    1 chiffre
                  </span>
                  <span className="inline-flex items-center">
                    {passwordStrength.requirements.special ? (
                      <FaCheck className="text-green-500 mr-1 text-xs" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-gray-300 mr-1"></span>
                    )}
                    1 spécial
                  </span>
                </div>
              </div>
            </div>
            
            <div className="relative">
              <label htmlFor="password2" className="block text-sm font-medium text-gray-700 mb-1">Confirmer le mot de passe</label>
              <div className="relative">
                <input 
                  type={showPassword.password2 ? "text" : "password"} 
                  id="password2" 
                  name="password2" 
                  required
                  value={password2}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200"
                  placeholder="••••••••"
                />
                <button 
                  type="button" 
                  className="absolute right-3 top-3 text-gray-500 hover:text-gray-700 transition"
                  onClick={() => togglePasswordVisibility('password2')}
                >
                  {showPassword.password2 ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
              {fieldErrors.password2 && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.password2}</p>
              )}
              <div className={`absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none transition duration-200 ${password2 && password === password2 ? 'opacity-100' : 'opacity-0'}`}>
                <FaCheck className="text-green-500" />
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input 
                  type="checkbox" 
                  id="terms" 
                  name="terms" 
                  required
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="terms" className="text-gray-700">
                  J'accepte les <a href="#" className="text-indigo-600 hover:underline font-medium">conditions générales</a> et la <a href="#" className="text-indigo-600 hover:underline font-medium">politique de confidentialité</a>
                </label>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input 
                  type="checkbox" 
                  id="is_seller" 
                  name="is_seller"
                  checked={formData.is_seller}
                  onChange={(e) => setFormData({...formData, is_seller: e.target.checked})}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="is_seller" className="text-gray-700">
                  Je souhaite m'inscrire en tant que vendeur
                </label>
              </div>
            </div>
            
            <button 
              type="submit" 
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-700 text-white py-3 px-4 rounded-lg font-medium hover:opacity-90 transition duration-200 flex items-center justify-center shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-70"
            >
              {isSubmitting ? (
                <>
                  <FaSpinner className="animate-spin mr-2" />
                  <span>Création du compte...</span>
                </>
              ) : (
                <>
                  <span>S'inscrire gratuitement</span>
                  <FaArrowRight className="ml-2" />
                </>
              )}
            </button>
            
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Ou s'inscrire avec</span>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              <button 
                type="button" 
                id="googleSignIn"
                className="social-btn flex items-center justify-center py-2 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <FaGoogle className="text-red-500 mr-2" />
                <span className="text-sm font-medium text-gray-700">Google</span>
              </button>
              <button 
                type="button" 
                className="social-btn flex items-center justify-center py-2 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition transform hover:-translate-y-0.5 active:translate-y-0"
                onClick={() => handleSocialLogin('facebook')}
              >
                <FaFacebookF className="text-blue-600 mr-2" />
                <span className="text-sm font-medium text-gray-700">Facebook</span>
              </button>
              <button 
                type="button" 
                className="social-btn flex items-center justify-center py-2 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition transform hover:-translate-y-0.5 active:translate-y-0"
                onClick={() => handleSocialLogin('apple')}
              >
                <FaApple className="text-gray-800 mr-2" />
                <span className="text-sm font-medium text-gray-700">Apple</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Signup;