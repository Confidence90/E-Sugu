// Dans App.jsx ou un fichier de routage
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';

function GoogleCallback() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const access_token = params.get('access_token');
    const refresh_token = params.get('refresh_token');

    if (access_token && refresh_token) {
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      navigate('/profile');
      toast.success('Connexion Google réussie');
    } else {
      toast.error('Échec de la connexion Google');
      navigate('/signup');
    }
  }, [navigate, location]);

  return <div>Redirection...</div>;
}

export default GoogleCallback;