import { Heart, MapPin, Eye, Star } from 'lucide-react';

function ProductCard({ 
  title, 
  price, 
  location, 
  image, 
  isNew, 
  isFeatured, 
  views,
  rating = 4.5 
}) {
  return (
    <div className="group cursor-pointer hover:shadow-lg transition-all duration-300 overflow-hidden border border-gray-200 rounded-lg">
      <div className="relative">
        <img 
          src={image} 
          alt={title}
          className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
        />
        <div className="absolute top-3 left-3 flex gap-2">
          {isNew && (
            <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
              Nouveau
            </span>
          )}
          {isFeatured && (
            <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
              Vedette
            </span>
          )}
        </div>
        <button
          className="absolute top-3 right-3 bg-white/90 hover:bg-white text-gray-600 hover:text-red-500 p-2 rounded-full"
        >
          <Heart className="h-4 w-4" />
        </button>
        <div className="absolute bottom-3 left-3 flex items-center gap-2 text-white text-xs bg-black/50 px-2 py-1 rounded">
          <Eye className="h-3 w-3" />
          <span>{views || 0}</span>
        </div>
      </div>
      
      <div className="p-4">
        <h3 className="font-semibold text-sm mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
          {title}
        </h3>
        
        <div className="flex items-center gap-1 mb-2">
          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
          <span className="text-xs text-gray-500">{rating}</span>
        </div>
        
        <div className="flex items-center justify-between mb-3">
          <span className="text-lg font-bold text-blue-600">{price}</span>
          <div className="flex items-center text-xs text-gray-500">
            <MapPin className="h-3 w-3 mr-1" />
            <span>{location}</span>
          </div>
        </div>
        
        <button className="w-full border border-gray-300 hover:bg-gray-100 px-4 py-2 rounded-md text-sm transition-colors">
          Voir détails
        </button>
      </div>
    </div>
  );
}

export default ProductCard;