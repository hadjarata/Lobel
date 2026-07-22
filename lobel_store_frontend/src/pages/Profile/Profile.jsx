import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AnimatePresence, motion as Motion } from 'framer-motion';
import { panelVariants, springSnappy } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import { getOrders } from '../../api/orders';
import { getPayments } from '../../api/payments';
import { getCustomerProfile } from '../../api/profile';
import ProfileHeader from '../../components/profile/ProfileHeader';
import ProfileMobileNav from '../../components/profile/ProfileMobileNav';
import ProfileSidebar from '../../components/profile/ProfileSidebar';
import { VALID_PROFILE_TABS } from '../../components/profile/profileNavConfig';
import ProfileInfoPanel from '../../components/profile/ProfileInfoPanel';
import ProfileOrdersPanel from '../../components/profile/ProfileOrdersPanel';
import ProfilePaymentsPanel from '../../components/profile/ProfilePaymentsPanel';
import ProfileSettingsPanel from '../../components/profile/ProfileSettingsPanel';
import { logger } from '../../utils/logger';
import './Profile.css';

const Profile = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [customer, setCustomer] = useState(null);
  const [orders, setOrders] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [paymentsLoading, setPaymentsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  const activeTab = VALID_PROFILE_TABS.includes(searchParams.get('tab'))
    ? searchParams.get('tab')
    : 'profile';

  const setActiveTab = (tab) => {
    setSearchParams({ tab }, { replace: true });
  };

  const panelTransition = useMotionTransition(springSnappy);

  const loadProfile = useCallback(async () => {
    try {
      setError('');
      const profileData = await getCustomerProfile();
      setCustomer(profileData);
      return profileData;
    } catch (err) {
      logger.error('Error loading profile:', err);
      setError('Impossible de charger votre profil.');
      return null;
    }
  }, []);

  const loadOrders = useCallback(async () => {
    setOrdersLoading(true);
    try {
      const data = await getOrders();
      setOrders(
        data.results.filter(
          (order) => !(order.complete === false && order.status === 'pending'),
        ),
      );
    } catch (err) {
      logger.error('Error loading orders:', err);
      setOrders([]);
    } finally {
      setOrdersLoading(false);
    }
  }, []);

  const loadPayments = useCallback(async () => {
    setPaymentsLoading(true);
    try {
      const data = await getPayments();
      setPayments(data.results);
    } catch (err) {
      logger.error('Error loading payments:', err);
      setPayments([]);
    } finally {
      setPaymentsLoading(false);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    await Promise.all([loadProfile(), loadOrders(), loadPayments()]);
  }, [loadProfile, loadOrders, loadPayments]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await refreshAll();
      setLoading(false);
    };

    init();

  }, [refreshAll]);

  const stats = useMemo(
    () => ({
      ordersCount: orders.filter((order) => order.complete || order.status === 'paid').length,
    }),
    [orders],
  );

  const handleProfileUpdated = (updatedCustomer) => {
    setCustomer(updatedCustomer);
  };

  const handleViewOrderFromPayment = (orderId) => {
    setActiveTab('orders');
    // Order detail selection handled in orders panel via state - pass via URL?
    setSearchParams({ tab: 'orders', order: String(orderId) }, { replace: true });
  };

  const renderPanel = () => {
    switch (activeTab) {
      case 'orders':
        return (
          <ProfileOrdersPanel
            orders={orders}
            loading={ordersLoading}
            onRefresh={loadOrders}
            initialSelectedOrderId={
              searchParams.get('order') ? Number(searchParams.get('order')) : null
            }
          />
        );
      case 'payments':
        return (
          <ProfilePaymentsPanel
            payments={payments}
            loading={paymentsLoading}
            onRefresh={loadPayments}
            onViewOrder={handleViewOrderFromPayment}
          />
        );
      case 'settings':
        return <ProfileSettingsPanel />;
      case 'profile':
      default:
        return (
          <ProfileInfoPanel
            customer={customer}
            onUpdated={handleProfileUpdated}
            startEditing={isEditingProfile}
            onEditingChange={setIsEditingProfile}
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-loading">
          <div className="profile-spinner" />
          <p>Chargement de votre espace client...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-page">
        <div className="profile-error">
          <p>{error}</p>
          <button type="button" className="profile-btn profile-btn-primary" onClick={refreshAll}>
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <ProfileHeader
        customer={customer}
        compact={activeTab !== 'profile'}
        onEditProfile={() => {
          setActiveTab('profile');
          setIsEditingProfile(true);
        }}
      />

      <ProfileMobileNav activeTab={activeTab} onTabChange={setActiveTab} stats={stats} />

      <div className="profile-dashboard">
        <ProfileSidebar activeTab={activeTab} onTabChange={setActiveTab} stats={stats} />
        <AnimatePresence mode="wait">
          <Motion.div
            key={activeTab}
            className="profile-main"
            variants={panelVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={panelTransition}
          >
            {renderPanel()}
          </Motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Profile;
