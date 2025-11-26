import Header from '../components/Header';
import HeroSection from '../components/HeroSection';
import CategoryGrid from '../components/CategoryGrid';
import ProductsSection from '../components/ProductsSection';
import Footer from '../components/Footer';
import { ToastContainer } from 'react-toastify';

function Index() {
  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899)' }}>
      <Header />
      <main>
        <HeroSection />
        <CategoryGrid />
        <ProductsSection />
      </main>
      <Footer />
    </div>
  );
}


export default Index;