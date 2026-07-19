import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import ToastProvider from './components/ui/ToastProvider';
import PageTransition from './components/ui/PageTransition';
import Layout from './components/layout/Layout';
import PrivateRoute from './components/auth/PrivateRoute';
import Home from './pages/Home/Home';
import Shop from './pages/Shop/Shop';
import Product from './pages/Product/Product';
import Profile from './pages/Profile/Profile';
import Cart from './pages/Cart/Cart';
import Checkout from './pages/Checkout/Checkout';
import CheckoutSuccess from './pages/Checkout/CheckoutSuccess';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';
import VerifyEmail from './pages/auth/VerifyEmail';

function AppRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageTransition><Home /></PageTransition>} />
        <Route path="/shop" element={<PageTransition><Shop /></PageTransition>} />
        <Route path="/product/:id" element={<PageTransition><Product /></PageTransition>} />
        <Route path="/login" element={<PageTransition><Login /></PageTransition>} />
        <Route path="/register" element={<PageTransition><Register /></PageTransition>} />
        <Route path="/forgot-password" element={<PageTransition><ForgotPassword /></PageTransition>} />
        <Route path="/reset-password" element={<PageTransition><ResetPassword /></PageTransition>} />
        <Route path="/verify-email" element={<PageTransition><VerifyEmail /></PageTransition>} />

        <Route
          path="/profile"
          element={(
            <PageTransition>
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            </PageTransition>
          )}
        />
        <Route path="/cart" element={<PageTransition><Cart /></PageTransition>} />
        <Route
          path="/checkout"
          element={(
            <PageTransition>
              <PrivateRoute>
                <Checkout />
              </PrivateRoute>
            </PageTransition>
          )}
        />
        <Route
          path="/checkout/success"
          element={(
            <PageTransition>
              <PrivateRoute>
                <CheckoutSuccess />
              </PrivateRoute>
            </PageTransition>
          )}
        />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <ToastProvider>
      <Layout>
        <AppRoutes />
      </Layout>
    </ToastProvider>
  );
}

export default App;
