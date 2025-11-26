import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import axios from 'axios';
import { z } from 'zod';
import heroBanner from '../assets/hero-banner.jpg'; // Remplacez par votre image

// Schéma de validation
const formSchema = z.object({
  title: z.string().min(1, { message: "Le titre est requis" }),
  description: z.string().min(1, { message: "La description est requise" }),
  price: z.coerce.number().min(1, { message: "Le prix est requis" }),
  type: z.enum(["sale", "rent"], { required_error: "Le type est requis" }),
  condition: z.enum(["new", "used"], { required_error: "L'état est requis" }),
  location: z.string().min(1, { message: "La localisation est requise" }),
  category: z.string().min(1, { message: "La catégorie est requise" }),
  is_featured: z.boolean().optional(),
  images: z.any().refine((files) => files && files.length > 0, { 
    message: "Ajoutez au moins une image." 
  })
});

const AddListingForm = () => {
  const [selectedImages, setSelectedImages] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [categories, setCategories] = useState([]);
  const categoryIcons = {
  Electronique: '📱',
  Véhicules: '🚗',
  Immobilier: '🏠',
  Mode: '👗',
  'Sports & Loisirs': '⚽',
  Enfants: '👶',
  'Santé & Beauté': '💅',
  Emplois: '💼',
  Apprentissage: '🎓',
  Service: '🤝',
  Alimentation: '🍎',
  Animaux: '🐾',
};
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch
  } = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: "",
      description: "",
      price: 0,
      type: "sale",
      condition: "new",
      location: "",
      category: "",
      is_featured: false,
      images: [],
    },
  });
useEffect(() => {
  const fetchCategories = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/categories');
      console.log('Categories API response:', response.data);
      const cats = Array.isArray(response.data) ? response.data : response.data.results;
      setCategories(cats || []);
    } catch (error) {
      console.error("Erreur lors du chargement des catégories", error);
      setCategories([]);
    }
  };

  fetchCategories();
}, []);

  /*const categories = [
    { id: "1", name: "Villa", icon: "🏠" },
    { id: "2", name: "Appartement", icon: "🏢" },
    { id: "3", name: "Terrain", icon: "🌳" },
    { id: "4", name: "Immeuble", icon: "🏙️" },
    { id: "5", name: "Bureau", icon: "💼" },
    { id: "6", name: "Chambre", icon: "🛏️" },
  ];*/

  const suggestedCategories = [
    { name: "Électronique", icon: "📱" },
    { name: "Mobilier", icon: "🪑" },
    { name: "Vêtements", icon: "👕" },
    { name: "Livres", icon: "📚" },
    { name: "Sports", icon: "⚽" }
  ];

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (key === "images") {
          Array.from(value).forEach((file) => formData.append("images", file));
        } else {
          formData.append(key, String(value));
        }
      });

      const token = localStorage.getItem("access_token");
      await axios.post("http://localhost:8000/api/listings/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: token ? `Bearer ${token}` : undefined,
        },
        onUploadProgress: (event) => {
          const progress = Math.round((event.loaded * 100) / (event.total || 1));
          setUploadProgress(progress);
        },
      });

      alert("Annonce publiée avec succès !");
      reset();
      setSelectedImages([]);
    } catch (error) {
      alert(error.response?.data?.detail || "Impossible de publier l'annonce.");
    } finally {
      setIsSubmitting(false);
      setUploadProgress(0);
    }
  };

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files || []);
    setValue("images", files);
    setSelectedImages(files.map(file => URL.createObjectURL(file)));
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section with Background Image */}
      <section className="relative bg-gradient-to-r from-blue-600 to-blue-800 overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <img 
            src={heroBanner} 
            alt="Hero background" 
            className="w-full h-full object-cover"
          />
        </div>
        
        <div className="relative z-10">
          <header className="flex items-center justify-between px-10 py-4 bg-white bg-opacity-90 backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <div className="text-blue-600">
                <svg viewBox="0 0 48 48" className="w-6 h-6">
                  <path fill="currentColor" d="M24 0.757L47.243 24 24 47.243 0.757 24 24 0.757ZM21 35.757V12.243L9.243 24 21 35.757Z"/>
                </svg>
              </div>
              <h2 className="text-xl font-bold">Marché</h2>
            </div>
            
            <div className="flex items-center gap-8">
              <nav className="flex gap-6">
                <a href="/" className="text-sm font-medium hover:text-blue-600">Accueil</a>
                <a href="#" className="text-sm font-medium hover:text-blue-600">Catégories</a>
                <a href="#" className="text-sm font-medium hover:text-blue-600">Mes Annonces</a>
              </nav>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-full text-sm font-bold hover:bg-blue-700">
                Publier une annonce
              </button>
              <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
            </div>
          </header>
        </div>
      </section>

      {/* Main Form Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Left Column - Form */}
          <div className="flex-1 bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="p-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-6">Publier votre annonce</h1>
              
              {/* Step 1: Basic Information */}
              <div className="mb-8">
                <h3 className="text-lg font-bold mb-4">Étape 1 : Informations de base</h3>
                
                <div className="space-y-5">
                  {/* Title */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Titre *</label>
                    <input
                      {...register("title")}
                      placeholder="Entrez le titre de l'annonce"
                      className={`w-full px-4 py-3 rounded-xl border ${errors.title ? 'border-red-500' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                    />
                    {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                    <textarea
                      {...register("description")}
                      rows={4}
                      placeholder="Décrivez votre article en détail..."
                      className={`w-full px-4 py-3 rounded-xl border ${errors.description ? 'border-red-500' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                    />
                    {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>}
                  </div>

                  {/* Price and Location */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Prix (FCFA) *</label>
                      <input
                        type="number"
                        {...register("price")}
                        placeholder="1000000"
                        className={`w-full px-4 py-3 rounded-xl border ${errors.price ? 'border-red-500' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                      />
                      {errors.price && <p className="mt-1 text-sm text-red-600">{errors.price.message}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Localisation *</label>
                      <input
                        {...register("location")}
                        placeholder="Ex: Cocody, Abidjan"
                        className={`w-full px-4 py-3 rounded-xl border ${errors.location ? 'border-red-500' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                      />
                      {errors.location && <p className="mt-1 text-sm text-red-600">{errors.location.message}</p>}
                    </div>
                  </div>

                  {/* Type and Condition */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Type *</label>
                      <select
                        {...register("type")}
                        className={`w-full px-4 py-3 rounded-xl border ${errors.type ? 'border-red-500' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                      >
                        <option value="sale">À vendre</option>
                        <option value="rent">À louer</option>
                      </select>
                      {errors.type && <p className="mt-1 text-sm text-red-600">{errors.type.message}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">État *</label>
                      <select
                        {...register("condition")}
                        className={`w-full px-4 py-3 rounded-xl border ${errors.condition ? 'border-red-500' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                      >
                        <option value="new">Neuf</option>
                        <option value="used">Occasion</option>
                      </select>
                      {errors.condition && <p className="mt-1 text-sm text-red-600">{errors.condition.message}</p>}
                    </div>
                  </div>

                  {/* Category */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie *</label>
                    <select
                      {...register("category")}
                      className={`w-full px-4 py-3 rounded-xl border ${errors.category ? 'border-red-500' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                    >
                      <option value="">Sélectionnez une catégorie</option>
                      {categories.map(cat => (
                        cat.subcategories && cat.subcategories.length > 0 ? (
                          <optgroup key={cat.id} label={cat.name}>
                            {cat.subcategories.map(sub => (
                              <option key={sub.id} value={sub.id}>
                                {categoryIcons[cat.name] || ''} {sub.name}
                              </option>

                            ))}
                          </optgroup>
                        ) : (
                          <option key={cat.id} value={cat.id}>
                            {cat.name}
                          </option>
                        )
                      ))}
                    </select>

                    {errors.category && <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>}
                  </div>
                </div>
              </div>

              {/* Suggested Categories */}
              <div className="mb-8">
                <h3 className="text-lg font-bold mb-3">Catégories suggérées</h3>
                <div className="flex flex-wrap gap-2">
                  {suggestedCategories.map((cat, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => setValue("category", categories[index]?.id || "")}
                      className="flex items-center gap-2 px-3 py-1 bg-blue-50 rounded-full text-sm font-medium hover:bg-blue-100"
                    >
                      <span>{cat.icon}</span>
                      <span>{cat.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Featured Checkbox */}
              <div className="mb-8">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    {...register("is_featured")}
                    className="w-5 h-5 rounded border-2 border-blue-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium">Mettre cette annonce en avant</span>
                </label>
              </div>

              {/* Image Upload */}
              <div className="mb-8">
                <h3 className="text-lg font-bold mb-3">Images *</h3>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                    id="image-upload"
                  />
                  <label
                    htmlFor="image-upload"
                    className="cursor-pointer flex flex-col items-center justify-center gap-3"
                  >
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium">Glissez-déposez vos images ici</p>
                      <p className="text-sm text-gray-500">ou cliquez pour sélectionner</p>
                    </div>
                    <button
                      type="button"
                      className="px-4 py-2 bg-blue-50 text-blue-600 rounded-full text-sm font-medium hover:bg-blue-100"
                    >
                      Télécharger
                    </button>
                  </label>
                </div>
                {errors.images && <p className="mt-2 text-sm text-red-600 text-center">{errors.images.message}</p>}

                {/* Image Previews */}
                {selectedImages.length > 0 && (
                  <div className="mt-4 grid grid-cols-3 gap-3">
                    {selectedImages.map((src, index) => (
                      <div key={index} className="relative group">
                        <img
                          src={src}
                          alt={`Preview ${index}`}
                          className="w-full h-32 object-cover rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            const newImages = [...selectedImages];
                            newImages.splice(index, 1);
                            setSelectedImages(newImages);
                            setValue("images", newImages.map((_, i) => watch("images")[i]));
                          }}
                          className="absolute top-2 right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="flex justify-end">
                <button
                  type="submit"
                  onClick={handleSubmit(onSubmit)}
                  disabled={isSubmitting}
                  className="px-6 py-3 bg-blue-600 text-white rounded-full font-medium hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Publication...
                    </span>
                  ) : (
                    "Publier l'annonce"
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Preview */}
          <div className="w-full lg:w-96 bg-white rounded-xl shadow-lg overflow-hidden h-fit sticky top-8">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">Aperçu de l'annonce</h2>
              
              <div className="space-y-4">
                {/* Preview Image */}
                <div className="relative h-48 bg-gray-100 rounded-lg overflow-hidden">
                  {selectedImages.length > 0 ? (
                    <img
                      src={selectedImages[0]}
                      alt="Preview"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                      </svg>
                    </div>
                  )}
                </div>

                {/* Preview Content */}
                <div>
                  <h3 className="font-bold text-lg">
                    {watch("title") || "Titre de l'annonce"}
                  </h3>
                  <p className="text-gray-600 text-sm mt-1">
                    {watch("location") || "Localisation"}
                  </p>
                  <p className="text-gray-500 text-sm mt-2 line-clamp-2">
                    {watch("description") || "Description de l'annonce"}
                  </p>
                  <div className="mt-3 flex justify-between items-center">
                    <span className="font-bold text-blue-600">
                      {watch("price") ? `${watch("price").toLocaleString()} FCFA` : "Prix"}
                    </span>
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded-full text-gray-600">
                      {watch("type") === "rent" ? "À louer" : "À vendre"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddListingForm;