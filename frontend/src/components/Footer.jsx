import { Button } from './ui/button';
import { Input } from './ui/input';
import { 
  Facebook, 
  Twitter, 
  Instagram, 
  Youtube,
  Mail,
  Phone,
  MapPin,
  ShoppingCart
} from 'lucide-react';

function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      {/* Main Footer */}
      <div className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-blue-600 p-2 rounded-lg">
                <ShoppingCart className="h-8 w-8 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold">MarketPlace</h3>
                <p className="text-sm text-gray-400">Mali</p>
              </div>
            </div>
            <p className="text-gray-300 leading-relaxed">
              La plateforme de commerce électronique de référence au Mali. 
              Achetez et vendez en toute sécurité avec des milliers d'utilisateurs.
            </p>
            <div className="flex space-x-4">
              <button className="p-2 text-gray-400 hover:bg-blue-600 hover:text-white rounded-full transition-colors">
                <Facebook className="h-5 w-5" />
              </button>
              <button className="p-2 text-gray-400 hover:bg-blue-600 hover:text-white rounded-full transition-colors">
                <Twitter className="h-5 w-5" />
              </button>
              <button className="p-2 text-gray-400 hover:bg-blue-600 hover:text-white rounded-full transition-colors">
                <Instagram className="h-5 w-5" />
              </button>
              <button className="p-2 text-gray-400 hover:bg-blue-600 hover:text-white rounded-full transition-colors">
                <Youtube className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Categories */}
          <div>
            <h4 className="text-lg font-semibold mb-6">Catégories populaires</h4>
            <ul className="space-y-3">
              {['Véhicules', 'Immobilier', 'Électronique', 'Mode & Beauté', 'Maison & Jardin', 'Services'].map((item) => (
                <li key={item}>
                  <a href="#" className="text-gray-400 hover:text-white transition-colors">{item}</a>
                </li>
              ))}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-lg font-semibold mb-6">Support</h4>
            <ul className="space-y-3">
              {['Centre d\'aide', 'Comment ça marche', 'Règles de sécurité', 'Signaler un problème', 'Conditions d\'utilisation', 'Politique de confidentialité'].map((item) => (
                <li key={item}>
                  <a href="#" className="text-gray-400 hover:text-white transition-colors">{item}</a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact & Newsletter */}
          <div>
            <h4 className="text-lg font-semibold mb-6">Restons en contact</h4>
            <div className="space-y-4 mb-6">
              <div className="flex items-center space-x-3">
                <MapPin className="h-5 w-5 text-blue-600" />
                <span className="text-gray-400">Bamako, Mali</span>
              </div>
              <div className="flex items-center space-x-3">
                <Phone className="h-5 w-5 text-blue-600" />
                <span className="text-gray-400">+223 XX XX XX XX</span>
              </div>
              <div className="flex items-center space-x-3">
                <Mail className="h-5 w-5 text-blue-600" />
                <span className="text-gray-400">esugu2025@gmail.com</span>
              </div>
            </div>
            
            <div>
              <h5 className="font-medium mb-3">Newsletter</h5>
              <p className="text-gray-400 text-sm mb-4">
                Recevez nos dernières offres et actualités
              </p>
              <div className="flex space-x-2">
                <input 
                  type="email" 
                  placeholder="Votre email"
                  className="bg-gray-800 border border-gray-700 text-white px-3 py-2 rounded-md w-full focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
                <button className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-md">
                  <Mail className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-800 py-6">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-gray-400 text-sm">
              © {new Date().getFullYear()} MarketPlace Mali. Tous droits réservés.
            </div>
            <div className="flex items-center space-x-6 text-sm">
              {['Conditions générales', 'Confidentialité', 'Cookies'].map((item) => (
                <a key={item} href="#" className="text-gray-400 hover:text-white transition-colors">
                  {item}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;