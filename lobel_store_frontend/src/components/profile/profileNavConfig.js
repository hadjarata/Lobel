export const PROFILE_NAV_ITEMS = [
  { id: 'profile', label: 'Mon profil', shortLabel: 'Profil', icon: '👤' },
  { id: 'orders', label: 'Mes commandes', shortLabel: 'Commandes', icon: '📦' },
  { id: 'payments', label: 'Paiements', shortLabel: 'Paiements', icon: '💳' },
  { id: 'settings', label: 'Paramètres', shortLabel: 'Réglages', icon: '⚙️' },
];

export const VALID_PROFILE_TABS = PROFILE_NAV_ITEMS.map((item) => item.id);
