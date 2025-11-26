import { useState } from "react";

export default function SetupBoutique() {
  const steps = [
    { title: "Informations Sur Votre Boutique", status: "done" },
    { title: "Informations Sur La Société", status: "current" },
    { title: "Informations D’expédition", status: "pending" },
    { title: "Informations De Paiement", status: "pending" },
    { title: "Informations Complémentaires", status: "pending" },
  ];

  const [currentStep, setCurrentStep] = useState(0);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* 🔹 Titre principal */}
      <div>
        <h1 className="text-2xl font-bold">Votre boutique est maintenant en ligne !</h1>
        <p className="text-gray-600">
          Vous pouvez maintenant créer des produits et commencer à vendre
        </p>
      </div>

      {/* 🔹 Progress bar horizontale (en cartes) */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg border text-center cursor-pointer transition
              ${step.status === "done" ? "bg-green-50 border-green-400 text-green-600" : ""}
              ${step.status === "current" ? "bg-orange-50 border-orange-400 text-orange-600 font-semibold" : ""}
              ${step.status === "pending" ? "bg-gray-50 border-gray-300 text-gray-500" : ""}
            `}
            onClick={() => setCurrentStep(index)}
          >
            <div className="text-sm">{step.title}</div>
            {step.status === "done" && (
              <div className="text-xs mt-1 text-green-600 font-semibold">TERMINÉ</div>
            )}
            {step.status === "current" && (
              <div className="text-xs mt-1 text-orange-600 font-semibold">EN COURS</div>
            )}
            {step.status === "pending" && (
              <div className="text-xs mt-1 text-gray-400">EN COURS</div>
            )}
          </div>
        ))}
      </div>

      {/* 🔹 Formulaire (section par étape) */}
      <div className="bg-white rounded-xl border shadow-sm p-6 space-y-8">
        {currentStep === 0 && (
          <>
            {/* Détails du compte */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Détails du compte</h2>
              <p className="text-sm text-gray-500">
                Informations sur votre compte vendeur
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium">Adresse email</label>
                  <input
                    type="email"
                    value="confidencecuche314@gmail.com"
                    disabled
                    className="w-full border rounded-md px-3 py-2 bg-gray-100 text-gray-600"
                  />
                </div>
                <div className="flex gap-2">
                  <div>
                    <label className="block text-sm font-medium">Code pays</label>
                    <input
                      type="text"
                      value="+225"
                      disabled
                      className="w-20 border rounded-md px-3 py-2 bg-gray-100 text-gray-600"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium">Numéro de téléphone</label>
                    <input
                      type="text"
                      value="2720259000"
                      disabled
                      className="w-full border rounded-md px-3 py-2 bg-gray-100 text-gray-600"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium">Pays</label>
                  <input
                    type="text"
                    value="Côte d'Ivoire"
                    disabled
                    className="w-full border rounded-md px-3 py-2 bg-gray-100 text-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium">Type de compte</label>
                  <input
                    type="text"
                    value="Individuel"
                    disabled
                    className="w-full border rounded-md px-3 py-2 bg-gray-100 text-gray-600"
                  />
                </div>
              </div>
            </div>

            {/* Détails de la boutique */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Détails de la boutique</h2>
              <div>
                <label className="block text-sm font-medium">Nom de la boutique</label>
                <input
                  type="text"
                  placeholder="Nom de votre boutique"
                  className="w-full border rounded-md px-3 py-2"
                />
              </div>
            </div>
          </>
        )}

        {currentStep === 1 && (
          <div>
            <h2 className="text-lg font-semibold">Informations sur la société</h2>
            <p className="text-sm text-gray-500 mb-4">
              Veuillez fournir les détails du représentant légal
            </p>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Nom et prénom du représentant légal"
                className="w-full border rounded-md px-3 py-2"
              />
              <select className="w-full border rounded-md px-3 py-2">
                <option>Type de papier d’identité</option>
                <option>Carte d’identité</option>
                <option>Passeport</option>
              </select>
              <input
                type="text"
                placeholder="Numéro d’identification fiscale (TIN)"
                className="w-full border rounded-md px-3 py-2"
              />
            </div>
          </div>
        )}

        {/* Ajoute les autres étapes selon le besoin */}
      </div>

      {/* 🔹 Navigation */}
      <div className="flex justify-between">
        <button
          disabled={currentStep === 0}
          onClick={() => setCurrentStep((prev) => prev - 1)}
          className={`px-4 py-2 rounded-md ${
            currentStep === 0
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-gray-300 hover:bg-gray-400 text-black"
          }`}
        >
          Précédent
        </button>

        {currentStep < steps.length - 1 ? (
          <button
            onClick={() => setCurrentStep((prev) => prev + 1)}
            className="px-4 py-2 rounded-md bg-orange-500 text-white hover:bg-orange-600"
          >
            Suivant
          </button>
        ) : (
          <button className="px-4 py-2 rounded-md bg-green-500 text-white hover:bg-green-600">
            Sauvegarder
          </button>
        )}
      </div>
    </div>
  );
}
