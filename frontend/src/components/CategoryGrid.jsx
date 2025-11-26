import { Card } from './ui/card';
import { useNavigate } from 'react-router-dom';
import { 
  TabletSmartphone, 
  Car, 
  Home, 
  Shirt, 
  Volleyball, 
  Baby, 
  Heart, 
  Briefcase,
  Apple,
  Handshake,
  Music,
  PawPrint,
  ChevronRight,
  GraduationCap
} from 'lucide-react';

function CategoryGrid() {
  const navigate = useNavigate();

  const categories = [
    { name: 'Electronique', icon: TabletSmartphone, count: '2,341', color: 'bg-blue-100 text-blue-600' },
    { name: 'Véhicules', icon: Car, count: '1,567', color: 'bg-red-100 text-red-600' },
    { name: 'Immobilier', icon: Home, count: '892', color: 'bg-green-100 text-green-600' },
    { name: 'Mode', icon: Shirt, count: '3,456', color: 'bg-purple-100 text-purple-600' },
    { name: 'Sports & Loisirs', icon: Volleyball, count: '1,234', color: 'bg-indigo-100 text-indigo-600' },
    { name: 'Enfants', icon: Baby, count: '687', color: 'bg-pink-100 text-pink-600' },
    { name: 'Santé & Beauté', icon: Heart, count: '543', color: 'bg-rose-100 text-rose-600' },
    { name: 'Emplois', icon: Briefcase, count: '321', color: 'bg-yellow-100 text-yellow-600' },
    { name: 'Apprentissage', icon: GraduationCap, count: '789', color: 'bg-cyan-100 text-cyan-600' },
    { name: 'Service', icon: Handshake, count: '456', color: 'bg-orange-100 text-orange-600' },
    { name: 'Alimentation', icon: Apple, count: '234', color: 'bg-teal-100 text-teal-600' },
    { name: 'Animaux', icon: PawPrint, count: '345', color: 'bg-gray-100 text-gray-600' },
  ];

  const handleCategoryClick = (categoryName) => {
    if (categoryName === 'Immobilier') {
      navigate('/immobilier');
    } 
     if (categoryName === 'Electronique') {
      navigate('/electronique') ;
    } 
    if (categoryName === 'Véhicules') {
      navigate('/vehicules') ;
    } 
    if (categoryName === 'Mode') {
      navigate('/mode') ;
    } 
    if (categoryName === 'Sports & Loisirs') {
      navigate('/sports') ;
    }
    if (categoryName === 'Enfants') {
      navigate('/enfants') ;
    }  
    if (categoryName === 'Santé & Beauté') {
      navigate('/sante') ;
    }
    if (categoryName === 'Emplois') {
      navigate('/emplois') ;
    }
    if (categoryName === 'Apprentissage') {
      navigate('/apprentissage') ;
    }
    if (categoryName === 'Service') {
      navigate('/service') ;
    }
    if (categoryName === 'Alimentation') {
      navigate('/alimentation') ;
    }
    if (categoryName === 'Animaux') {
      navigate('/animaux') ;
    }
    
  };

  return (
    <section className="py-12 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">Explorez nos catégories</h2>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Découvrez des milliers d'annonces dans nos différentes catégories
          </p>
        </div>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-5">
          {categories.map((category) => {
            const IconComponent = category.icon;
            return (
              <Card 
                key={category.name}
                onClick={() => handleCategoryClick(category.name)}
                className="p-5 text-center hover:shadow-lg transition-all duration-300 cursor-pointer group border border-gray-100 hover:border-blue-200"
              >
                <div className={`w-14 h-14 rounded-full ${category.color} mx-auto mb-4 flex items-center justify-center group-hover:scale-110 transition-transform`}>
                  <IconComponent className="h-6 w-6" />
                </div>
                <h3 className="font-semibold text-sm mb-1 text-gray-800 group-hover:text-blue-600 transition-colors">
                  {category.name}
                </h3>
                <div className="flex items-center justify-center">
                  <p className="text-xs text-gray-500 mr-1">{category.count} annonces</p>
                  <ChevronRight className="h-3 w-3 text-gray-400 group-hover:text-blue-500 transition-colors" />
                </div>
              </Card>
            );
          })}
        </div>

        <div className="text-center mt-10">
          <button 
            className="px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors duration-300 inline-flex items-center"
            onClick={() => navigate('/categories')}
          >
            Voir toutes les catégories
            <ChevronRight className="h-4 w-4 ml-1" />
          </button>
        </div>
      </div>
    </section>
  );
}

export default CategoryGrid;