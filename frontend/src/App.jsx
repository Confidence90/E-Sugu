import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import 'react-toastify/dist/ReactToastify.css';
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PrivateRoute from './assets/composant/PrivateRoute';

// Imports des composants
import Index from "./pages/Index";
import Immobilier from "./pages/Immobilier";
import SetupBoutique from './pages/SetupBoutique';
import Electronique from "./pages/Electronique";
import CategoryGrid from './components/CategoryGrid';
import Véhicule from "./pages/Véhicule";
import Mode from "./pages/Mode";
import Sports from "./pages/Sports";
import NotFound from "./pages/NotFound";
import Discussion from './pages/Discussion';
import Profile from './assets/composant/Profile';
import Signup from './assets/composant/Signup';
import Login from './assets/composant/Login';
import Enfants from './pages/Enfants';
import Sante from './pages/Sante';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from "./pages/Dashboard";
import Produits from "./pages/Produits";
import Commandes from "./pages/Commandes";
import Emplois from './pages/Emplois';
import Apprentissage from './pages/Apprentissage';
import Service from './pages/Service';
import Alimentation from './pages/Alimentation';
import PropertyDetails from './pages/PropertyDetails';
import Animaux from './pages/Animaux';
import VerifyEmail from './assets/composant/VerifyEmail';
import PasswordResetRequest from './assets/composant/PasswordResetRequest';
import ResetPassword from './assets/composant/ResetPassword';
import PublierAnnonce from './pages/PublierAnnonce';

const queryClient = new QueryClient();

function App() {
  return (

    <QueryClientProvider client={queryClient}>
      <div className='App'>
        <Router>
          <ToastContainer 
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
          />
          
          <Routes>
            {/* Routes publiques */}
            <Route path="/" element={<Index />} />
            <Route path="/register" element={<Signup />} />
            <Route path="/login" element={<Login />} />
            <Route path="/otp/verify" element={<VerifyEmail />} />
            <Route path="/forget-password" element={<PasswordResetRequest />} />
            <Route path="/password-reset-confirm/:uid/:token" element={<ResetPassword />} />
            <Route path="/auth/callback" element={<Signup />} />
            <Route path="/auth/callback/:provider" element={<Signup />} />
            <Route path="/immobilier" element={<Immobilier />} />
            <Route path="/electronique" element={<Electronique />} />
            <Route path="/vehicules" element={<Véhicule />} />
            <Route path="/mode" element={<Mode />} />
            <Route path="/alimentation" element={<Alimentation />} />
            <Route path="/details/:id" element={<PropertyDetails />} />
            <Route path="/animaux" element={<Animaux />} />
            <Route path="/sports" element={<Sports />} />
            <Route path="/enfants" element={<Enfants />} />
            <Route path="/discussion/:propertyId" element={<Discussion />} />
            <Route path="/sante" element={<Sante />} />
            <Route path="/emplois" element={<Emplois />} />
            <Route path="/apprentissage" element={<Apprentissage />} />
            <Route path="/service" element={<Service />} />
            <Route path="/publier" element={<PublierAnnonce />} />
            <Route path="/categories" element={<CategoryGrid />} />

            {/* Route protégée */}
            <Route path="/profile" element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            } />

            {/* Routes avec layout Dashboard */}
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/produits" element={<Produits />} />
              <Route path="/commandes" element={<Commandes />} />
              <Route path="/setup" element={<SetupBoutique />} />
            </Route>

            {/* Gestion des erreurs 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
      </div>
    </QueryClientProvider>

  );
}

export default App;