import React from 'react';
import AddListingForm from '../components/AddListingForm';
import Header from '../components/Header';
import Footer from '../components/Footer';

const PublierAnnonce = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="py-8">
        <AddListingForm />
      </main>
      <Footer />
    </div>
  );
};

export default PublierAnnonce;