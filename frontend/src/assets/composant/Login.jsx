import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import { FaGithub, FaGoogle, FaSpinner, FaArrowRight } from 'react-icons/fa';
import axios from 'axios';


const Login = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [lastRequestTime, setLastRequestTime] = useState(0);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const handleOnChange = (e) => {
    const { name, value } = e.target;
    setLoginData((prev) => ({ ...prev, [name]: value }));
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    setError('');
  };

  const handleLoginWithGithub = () => {
    const githubClientId = import.meta.env.VITE_GITHUB_CLIENT_ID;
    if (!githubClientId) {
      toast.error('Configuration GitHub manquante');
      return;
    }
    window.location.assign(
      `https://github.com/login/oauth/authorize?client_id=${githubClientId}&scope=user:email`
    );
  };

  const handleLoginWithGoogle = async (response) => {
    try {
      const res = await axios.post('http://localhost:8000/api/users/google-login/', {
        id_token: response.credential,
      });
      if (res.status === 200) {
        localStorage.setItem('token', res.data.token);
        localStorage.setItem(
          'user',
          JSON.stringify({
            id: res.data.id,
            email: res.data.email,
            names: res.data.full_name || `${res.data.first_name} ${res.data.last_name}`,

          })
        );
        toast.success('Connexion avec Google réussie !');
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error('Échec de la connexion avec Google');
      console.error('Erreur Google:', error);
    }
  };

  const sendGithubCodeToServer = async () => {
    const code = searchParams.get('code');
    if (!code) return;

    try {
      setIsLoading(true);
      const res = await axios.post('http://localhost:8000/api/users/github-login/', { code });
      if (res.status === 200) {
        localStorage.setItem('token', res.data.token);
        localStorage.setItem(
          'user',
          JSON.stringify({
            id: res.data.id,
            email: res.data.email,
            names: res.data.full_name,
          })
        );
        toast.success('Connexion avec GitHub réussie !');
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error('Échec de la connexion avec GitHub');
      console.error('Erreur GitHub:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    sendGithubCodeToServer();
  }, [searchParams]);

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (window.google && clientId) {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleLoginWithGoogle,
      });
      window.google.accounts.id.renderButton(
        document.getElementById('signInDiv'),
        { theme: 'outline', size: 'large', text: 'signin', width: 190 }
      );
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const now = Date.now();
    if (now - lastRequestTime < 2000) {
    setError('Veuillez patienter avant de réessayer');
    return;
    }
    setLastRequestTime(now);

    
   const { email, password } = loginData;
  
    // Validation des champs
    if (!email || !password) {
      setError('Veuillez remplir tous les champs obligatoires');
    return;
    }

    

    
    
    

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setFieldErrors((prev) => ({ ...prev, email: 'Email invalide' }));
      return;
    }
  // Validation du mot de passe

    if (password.length < 8) {
      setFieldErrors({ password: 'Le mot de passe doit contenir au moins 8 caractères' });
      return;
    }

    setIsSubmitting(true);
    setError('');
    setFieldErrors({});

    try {
      const res = await axios.post(
       'http://localhost:8000/api/users/login/',
         loginData, // 🟢 les données de connexion
     {
        headers: {
        'Content-Type': 'application/json'
    }
    }
    );

      const user = {
      id: res.data.id,
      email: res.data.email,
      full_name: res.data.full_name,
    };

     const storage = rememberMe ? localStorage : sessionStorage;

      
      storage.setItem('access_token', res.data.access);
      storage.setItem('refresh_token', res.data.refresh);
      storage.setItem('user', JSON.stringify(user));

      toast.success('Connexion réussie');
      console.log("Navigation vers profile");
      navigate('/profile');
    } catch (error) {
      if (error.response) {
        const { status, data } = error.response;
        if (status === 400) {
          if (data.errors) {
            setFieldErrors(data.errors);
          } else if (typeof data === 'string' && data.includes('Email ou mot de passe incorrect')) {
          setError('Email ou mot de passe incorrect');
          } else if (data.password) {
            setFieldErrors((prev) => ({ ...prev, password: data.password }));
          } else if (data.message) {
            setError(data.message);
          } else {
            setError('Identifiants incorrects');
          }
        } else if (status === 401) {
          setError('Email ou mot de passe incorrect');
        } else if (status === 403) {
          setError('Compte non activé. Vérifiez vos emails.');
        } else if (status === 429) {
           setError('Trop de tentatives. Veuillez patienter.');
        }
        else {
          setError('Une erreur est survenue lors de la connexion.');
        }
      } else if (error.request) {
        setError('Le serveur ne répond pas. Veuillez réessayer plus tard.');
      } else {
      console.error('Erreur inattendue :', error); // Ajoute ceci
      setError('Une erreur inattendue est survenue');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-gray-50 min-h-screen flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col md:flex-row">
        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 text-white p-8 md:w-1/2 flex flex-col justify-center items-center text-center">
          <h1 className="text-3xl font-bold mb-2">Content de vous revoir</h1>
          <p className="opacity-90 max-w-md">
            Connectez-vous pour continuer votre shopping et profiter de nos offres !
          </p>
          <img
            src="https://cdn.dribbble.com/users/1787505/screenshots/11300794/media/3b5b1e9d0b3d3e68c7a7d9b9f5a5a5e9.png"
            alt="Shopping illustration"
            className="mt-8 w-full max-w-xs"
          />
        </div>

        <div className="p-8 md:w-1/2">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Connexion</h2>
          {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                name="email"
                value={loginData.email}
                onChange={handleOnChange}
                className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-200 ${
                  fieldErrors.email ? 'border-red-500' : ''
                }`}
                placeholder="exemple@domaine.com"
              />
              {fieldErrors.email && <p className="text-red-500 text-sm">{fieldErrors.email}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
              <input
                type="password"
                name="password"
                value={loginData.password}
                onChange={handleOnChange}
                className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-200 ${
                  fieldErrors.password ? 'border-red-500' : ''
                }`}
                placeholder="••••••••"
              />
              {fieldErrors.password && <p className="text-red-500 text-sm">{fieldErrors.password}</p>}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={() => setRememberMe(!rememberMe)}
                  className="form-checkbox h-4 w-4 text-purple-600"
                />
                <span className="text-sm text-gray-600">Se souvenir de moi</span>
              </label>
              <Link to="/password-reset" className="text-sm text-indigo-600 hover:underline">
                Mot de passe oublié ?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || isLoading}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-700 text-white py-3 px-4 rounded-lg font-medium hover:opacity-90 transition duration-200 flex items-center justify-center disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <FaSpinner className="animate-spin mr-2" />
                  Connexion...
                </>
              ) : (
                <>
                  <span>Se connecter</span>
                  <FaArrowRight className="ml-2" />
                </>
              )}
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Ou continuer avec</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={handleLoginWithGithub}
              type="button"
              disabled={isLoading}
              className="flex items-center justify-center py-2 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
            >
              <FaGithub className="text-gray-800 mr-2" />
              <span className="text-sm font-medium text-gray-700">GitHub</span>
            </button>
            <div id="signInDiv" className="flex items-center justify-center" />
          </div>

          <p className="text-sm text-center mt-6 text-gray-600">
            Pas encore de compte ?{' '}
            <Link to="/signup" className="text-indigo-600 hover:underline font-medium">
              Créer un compte
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
