import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import 'react-toastify/dist/ReactToastify.css';
import PrivateRoute from './assets/composant/PrivateRoute';


import Profile from './assets/composant/Profile';
import Signup from './assets/composant/Signup';
import Login from './assets/composant/Login';
import VerifyEmail from './assets/composant/VerifyEmail';
import PasswordResetRequest from './assets/composant/PasswordResetRequest';
import ResetPassword from './assets/composant/ResetPassword';

function App() {
  return (
    <div className='App'>
      <Router>
        <ToastContainer />
        <Routes>
          <Route path='/register' element={<Signup />} />
          <Route path='/login' element={<Login />} />
          <Route path='/otp/verify' element={<VerifyEmail />} />
          <Route path='/forget-password' element={<PasswordResetRequest />} />
          <Route path='/password-reset-confirm/:uid/:token' element={<ResetPassword />} />
           <Route path="/auth/callback" element={<Signup />} />
          {/* ✅ Route protégée */}
          <Route path='/profile' element={
            <PrivateRoute>
              <Profile />
            </PrivateRoute>
          } />

          {/* Redirection si aucune route ne correspond */}
          <Route path='*' element={<Navigate to='/login' />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
