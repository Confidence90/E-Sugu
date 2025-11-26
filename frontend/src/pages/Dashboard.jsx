import { Link } from "react-router-dom";

export default function Dashboard() {
  // Exemple de données mockées (plus tard tu pourras connecter à ton backend)
  const annonces = [
    { id: 1, titre: "Chaussures Nike Air", statut: "Publié" },
    { id: 2, titre: "T-shirt Adidas", statut: "Publié" },
  ];

  const performances = [
    { id: "7j", ca: "150 000 FCFA", ventes: 12, catalogues: 5 },
    { id: "30j", ca: "720 000 FCFA", ventes: 45, catalogues: 12 },
    { id: "90j", ca: "2 300 000 FCFA", ventes: 128, catalogues: 30 },
  ];

  const scoreVendeur = {
    expedition: "92%",
    retour: "3%",
    note: "4.6 / 5",
  };

  return (
    <div className="space-y-8">
      {/* 🔹 Bloc Actions requises */}
      <section className="bg-white rounded-xl shadow-sm p-6 border">
        <h2 className="text-lg font-semibold mb-4">Actions requises</h2>
        <Link
          to="/publier"
          className="inline-block bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition"
        >
          + Créer un produit / Publier annonce
        </Link>

        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-600 mb-2">
            Vos annonces publiées
          </h3>
          <ul className="space-y-2">
            {annonces.map((a) => (
              <li
                key={a.id}
                className="flex justify-between items-center p-3 bg-gray-50 rounded-md border"
              >
                <span>{a.titre}</span>
                <span className="text-green-600 text-sm">{a.statut}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* 🔹 Bloc Indicateurs de performances */}
      <section className="bg-white rounded-xl shadow-sm p-6 border">
        <h2 className="text-lg font-semibold mb-4">Indicateurs de performances</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {performances.map((p) => (
            <div
              key={p.id}
              className="p-4 border rounded-lg bg-gray-50 text-center"
            >
              <h3 className="font-semibold text-gray-700 mb-2">
                Sur {p.id}
              </h3>
              <p className="text-gray-800">
                <span className="font-bold">CA :</span> {p.ca}
              </p>
              <p className="text-gray-800">
                <span className="font-bold">Ventes :</span> {p.ventes}
              </p>
              <p className="text-gray-800">
                <span className="font-bold">Catalogues :</span> {p.catalogues}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 🔹 Bloc Score Vendeur */}
      <section className="bg-white rounded-xl shadow-sm p-6 border">
        <h2 className="text-lg font-semibold mb-4">Score Vendeur</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 border rounded-lg bg-gray-50 text-center">
            <h3 className="font-semibold text-gray-700">Vitesse d’expédition</h3>
            <p className="text-xl text-orange-500 font-bold">{scoreVendeur.expedition}</p>
          </div>
          <div className="p-4 border rounded-lg bg-gray-50 text-center">
            <h3 className="font-semibold text-gray-700">Taux de retour qualité</h3>
            <p className="text-xl text-orange-500 font-bold">{scoreVendeur.retour}</p>
          </div>
          <div className="p-4 border rounded-lg bg-gray-50 text-center">
            <h3 className="font-semibold text-gray-700">Note moyenne clients</h3>
            <p className="text-xl text-orange-500 font-bold">{scoreVendeur.note}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
