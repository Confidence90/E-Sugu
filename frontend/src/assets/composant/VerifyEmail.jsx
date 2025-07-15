import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';

const VerifyEmail = () => {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);

  // Récupérer l'email depuis l'URL ou le localStorage
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const emailParam = queryParams.get('email');
    const storedEmail = localStorage.getItem('registrationEmail');
    
    if (emailParam) {
      setEmail(emailParam);
    } else if (storedEmail) {
      setEmail(storedEmail);
    } else {
      toast.error("Email non trouvé, veuillez vous réinscrire");
      navigate('/register');
    }
  }, [location, navigate]);

  useEffect(() => {
    if (!canResend && timer > 0) {
      const countdown = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(countdown);
    } else if (timer === 0) {
      setCanResend(true);
    }
  }, [timer, canResend]);

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    
    if (!otp || otp.length !== 6) {
      toast.error("Veuillez entrer un code OTP valide à 6 chiffres");
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/users/verify-otp/',
        { email, otp },
        { headers: { 'Content-Type': 'application/json' } }
      );

      if (response.status === 200) {
        toast.success(response.data.message || 'Email vérifié avec succès !');
        localStorage.removeItem('registrationEmail');
        navigate('/login');
      }
    } catch (error) {
      console.error('Erreur de vérification:', error.response?.data);
      toast.error(
        error.response?.data?.detail || 
        error.response?.data?.message || 
        "Échec de la vérification du code OTP"
      );
      
      // If OTP is expired, allow resend immediately
      if (error.response?.status === 400 || error.response?.status === 401) {
        setCanResend(true);
        setTimer(0);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      toast.error("Vous devez être connecté pour renvoyer le code.");
      return;
    }

    try {
      const resendRes = await axios.post(
        'http://localhost:8000/api/users/resend-otp/',
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      toast.success(resendRes.data.message || "Un nouveau code OTP a été envoyé !");
      setTimer(60);
      setCanResend(false);
    } catch (resendError) {
      console.error("Échec renvoi OTP:", resendError.response);
      if (resendError.response?.status === 401) {
        toast.error("Session expirée. Veuillez vous reconnecter.");
        navigate('/login');
      } else {
        toast.error(resendError.response?.data?.detail || "Erreur lors du renvoi du code OTP");
      }
    }
  };

  return (
    <div className="gradient-bg min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl p-8 shadow-lg transition-all transform hover:scale-[1.01]">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="fas fa-envelope text-purple-600 text-3xl"></i>
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">Vérification d'Email</h1>
            <p className="text-gray-600">
              Nous avons envoyé un code OTP à <span className="font-medium">{email}</span>
            </p>
          </div>

          <form onSubmit={handleOtpSubmit} className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                Code OTP
              </label>
              <div className="relative">
                <input
                  type="text"
                  id="otp"
                  name="otp"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ''))}
                  required
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Entrez le code à 6 chiffres"
                  maxLength="6"
                  pattern="\d{6}"
                  inputMode="numeric"
                />
                <div className="absolute right-3 top-3 text-gray-400">
                  <i className="fas fa-key"></i>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Veuillez entrer le code de vérification que vous avez reçu
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !email}
              className={`w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-lg transition-all flex items-center justify-center ${
                loading || !email ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? (
                <>
                  Vérification...
                  <i className="fas fa-spinner fa-spin ml-2"></i>
                </>
              ) : (
                'Vérifier'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Vous n'avez pas reçu de code ?{' '}
              <button 
                type="button" 
                onClick={handleResendOtp}
                className={`font-medium focus:outline-none transition-colors ${
                  canResend ? "text-purple-600 hover:text-purple-800" : "text-gray-400 cursor-not-allowed"
                }`}
                disabled={!canResend}
              >
                {canResend ? 'Renvoyer' : `Renvoyer dans ${timer}s`}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;