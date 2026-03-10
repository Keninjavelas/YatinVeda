'use client'

import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

export type Locale = 'en' | 'hi'

type Dictionary = Record<string, string>

const dictionaries: Record<Locale, Dictionary> = {
  en: {
    nav_dashboard: 'Dashboard',
    nav_ai_assistant: 'AI Assistant',
    nav_community: 'Community',
    nav_book_session: 'Book Session',
    nav_prescriptions: 'Prescriptions',
    nav_profile: 'Profile',
    nav_practitioner_portal: 'Practitioner Portal',
    nav_admin_panel: 'Admin Panel',
    nav_video_consult: 'Video Consult',
    nav_sign_out: 'Sign Out',
    nav_profile_settings: 'Profile Settings',
    common_back: 'Back',
    common_loading: 'Loading...',
    common_retry: 'Retry',
    common_status: 'Status',
    common_payment: 'Payment',
    common_booking: 'Booking',
    common_session_type: 'Session Type',
    common_total: 'Total',
    admin_certificate_alerts: 'Certificate Alerts',
    admin_advanced_analytics: 'Advanced Analytics',
    admin_analytics_title: 'Advanced Analytics',
    admin_loading_analytics: 'Loading analytics...',
    admin_users: 'Users',
    admin_new_in_period: 'New In Period',
    admin_practitioners: 'Practitioners',
    admin_verified: 'Verified',
    admin_bookings: 'Bookings',
    admin_in_period: 'In Period',
    admin_completed_in_period: 'Completed In Period',
    admin_revenue: 'Revenue',
    admin_gross_inr: 'Gross (INR)',
    admin_refund_inr: 'Refunds (INR)',
    admin_net_inr: 'Net (INR)',
    admin_daily_trends: 'Daily Trends',
    admin_breakdowns: 'Breakdowns',
    admin_booking_status_breakdown: 'Booking Status Breakdown',
    admin_payment_status_breakdown: 'Payment Status Breakdown',
    admin_no_breakdown_data: 'No breakdown data available for this period.',
    period_last_7_days: 'Last 7 days',
    period_last_30_days: 'Last 30 days',
    period_last_90_days: 'Last 90 days',
    period_last_365_days: 'Last 365 days',
    practitioner_portal_title: 'Practitioner Portal',
    practitioner_portal_subtitle: 'Manage your sessions, earnings, and professional profile.',
    practitioner_availability_title: 'Availability Management',
    practitioner_booking_title: 'Booking Management',
    practitioner_earnings_title: 'Earnings',
    practitioner_reviews_title: 'Reviews',
    practitioner_loading_earnings: 'Loading earnings...',
    practitioner_loading_reviews: 'Loading reviews...',
    practitioner_completed_sessions: 'Completed Sessions',
    practitioner_avg_session_value: 'Average Session Value',
    practitioner_average_rating: 'Average Rating',
    practitioner_total_reviews: 'Total Reviews',
    practitioner_no_reviews: 'No reviews available yet.',
    booking_filter_all_statuses: 'All statuses',
    booking_filter_pending: 'Pending',
    booking_filter_confirmed: 'Confirmed',
    booking_filter_completed: 'Completed',
    booking_filter_cancelled: 'Cancelled',
    booking_filter_upcoming: 'Upcoming',
    booking_filter_past: 'Past',
    booking_filter_all: 'All',
    booking_card_accept: 'Accept',
    booking_card_decline: 'Decline',
    booking_card_at: 'at',
    availability_planner_title: 'Availability Planner',
    availability_add_slot: 'Add Slot',
    availability_save: 'Save Availability',
    earnings_snapshot: 'Earnings Snapshot',
    earnings_total: 'Total',
    earnings_this_month: 'This Month',
    earnings_this_year: 'This Year',
    earnings_pending: 'Pending',
    review_no_written_feedback: 'No written feedback.',
    video_consult_title: 'Video Consultation',
    video_consult_subtitle: 'Enter your booking ID to generate or retrieve the secure meeting link.',
    video_booking_id_placeholder: 'Booking ID',
    video_get_session_link: 'Get Session Link',
    video_join_session: 'Join Video Session',
    video_refresh_link: 'Refresh Session Link',
    video_load_failed: 'Failed to load video session',
    video_refresh_failed: 'Failed to refresh meeting link',
    video_link_refreshed: 'Meeting link refreshed',
    video_lifecycle_scheduled: 'Session not yet open. Join window starts 15 minutes before session time.',
    video_lifecycle_open: 'Join window is open. You can enter the session now.',
    video_lifecycle_expired: 'Join window has ended. You can refresh the link if your practitioner allows extension.',
  },
  hi: {
    nav_dashboard: 'डैशबोर्ड',
    nav_ai_assistant: 'एआई सहायक',
    nav_community: 'समुदाय',
    nav_book_session: 'सेशन बुक करें',
    nav_prescriptions: 'प्रिस्क्रिप्शन्स',
    nav_profile: 'प्रोफाइल',
    nav_practitioner_portal: 'प्रैक्टिशनर पोर्टल',
    nav_admin_panel: 'एडमिन पैनल',
    nav_video_consult: 'वीडियो परामर्श',
    nav_sign_out: 'साइन आउट',
    nav_profile_settings: 'प्रोफाइल सेटिंग्स',
    common_back: 'वापस',
    common_loading: 'लोड हो रहा है...',
    common_retry: 'फिर से प्रयास करें',
    common_status: 'स्थिति',
    common_payment: 'भुगतान',
    common_booking: 'बुकिंग',
    common_session_type: 'सेशन प्रकार',
    common_total: 'कुल',
    admin_certificate_alerts: 'सर्टिफिकेट अलर्ट्स',
    admin_advanced_analytics: 'उन्नत एनालिटिक्स',
    admin_analytics_title: 'उन्नत एनालिटिक्स',
    admin_loading_analytics: 'एनालिटिक्स लोड हो रहा है...',
    admin_users: 'उपयोगकर्ता',
    admin_new_in_period: 'अवधि में नए',
    admin_practitioners: 'प्रैक्टिशनर',
    admin_verified: 'सत्यापित',
    admin_bookings: 'बुकिंग्स',
    admin_in_period: 'अवधि में',
    admin_completed_in_period: 'अवधि में पूर्ण',
    admin_revenue: 'राजस्व',
    admin_gross_inr: 'सकल (INR)',
    admin_refund_inr: 'रिफंड (INR)',
    admin_net_inr: 'शुद्ध (INR)',
    admin_daily_trends: 'दैनिक रुझान',
    admin_breakdowns: 'विभाजन',
    admin_booking_status_breakdown: 'बुकिंग स्थिति विभाजन',
    admin_payment_status_breakdown: 'भुगतान स्थिति विभाजन',
    admin_no_breakdown_data: 'इस अवधि के लिए कोई विभाजन डेटा उपलब्ध नहीं है।',
    period_last_7_days: 'पिछले 7 दिन',
    period_last_30_days: 'पिछले 30 दिन',
    period_last_90_days: 'पिछले 90 दिन',
    period_last_365_days: 'पिछले 365 दिन',
    practitioner_portal_title: 'प्रैक्टिशनर पोर्टल',
    practitioner_portal_subtitle: 'अपने सेशन्स, कमाई और प्रोफेशनल प्रोफाइल को मैनेज करें।',
    practitioner_availability_title: 'उपलब्धता प्रबंधन',
    practitioner_booking_title: 'बुकिंग प्रबंधन',
    practitioner_earnings_title: 'कमाई',
    practitioner_reviews_title: 'समीक्षाएं',
    practitioner_loading_earnings: 'कमाई लोड हो रही है...',
    practitioner_loading_reviews: 'समीक्षाएं लोड हो रही हैं...',
    practitioner_completed_sessions: 'पूर्ण सेशन्स',
    practitioner_avg_session_value: 'औसत सेशन मूल्य',
    practitioner_average_rating: 'औसत रेटिंग',
    practitioner_total_reviews: 'कुल समीक्षाएं',
    practitioner_no_reviews: 'अभी तक कोई समीक्षा उपलब्ध नहीं है।',
    booking_filter_all_statuses: 'सभी स्थितियां',
    booking_filter_pending: 'लंबित',
    booking_filter_confirmed: 'पुष्ट',
    booking_filter_completed: 'पूर्ण',
    booking_filter_cancelled: 'रद्द',
    booking_filter_upcoming: 'आगामी',
    booking_filter_past: 'पिछला',
    booking_filter_all: 'सभी',
    booking_card_accept: 'स्वीकार करें',
    booking_card_decline: 'अस्वीकार करें',
    booking_card_at: 'पर',
    availability_planner_title: 'उपलब्धता योजनाकार',
    availability_add_slot: 'स्लॉट जोड़ें',
    availability_save: 'उपलब्धता सहेजें',
    earnings_snapshot: 'कमाई सारांश',
    earnings_total: 'कुल',
    earnings_this_month: 'इस माह',
    earnings_this_year: 'इस वर्ष',
    earnings_pending: 'लंबित',
    review_no_written_feedback: 'कोई लिखित प्रतिक्रिया नहीं।',
    video_consult_title: 'वीडियो परामर्श',
    video_consult_subtitle: 'सुरक्षित मीटिंग लिंक बनाने या प्राप्त करने के लिए अपनी बुकिंग आईडी दर्ज करें।',
    video_booking_id_placeholder: 'बुकिंग आईडी',
    video_get_session_link: 'सेशन लिंक प्राप्त करें',
    video_join_session: 'वीडियो सेशन जॉइन करें',
    video_refresh_link: 'सेशन लिंक रीफ्रेश करें',
    video_load_failed: 'वीडियो सेशन लोड नहीं हो सका',
    video_refresh_failed: 'मीटिंग लिंक रीफ्रेश नहीं हो सका',
    video_link_refreshed: 'मीटिंग लिंक रीफ्रेश हो गया',
    video_lifecycle_scheduled: 'सेशन अभी खुला नहीं है। जॉइन विंडो सेशन समय से 15 मिनट पहले शुरू होती है।',
    video_lifecycle_open: 'जॉइन विंडो खुली है। आप अभी सेशन में प्रवेश कर सकते हैं।',
    video_lifecycle_expired: 'जॉइन विंडो समाप्त हो गई है। यदि आपका प्रैक्टिशनर अनुमति देता है तो लिंक रीफ्रेश करें।',
  },
}

interface I18nContextType {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string, fallback?: string) => string
}

const I18nContext = createContext<I18nContextType | undefined>(undefined)

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en')

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('yv_locale') : null
    if (stored === 'en' || stored === 'hi') {
      setLocaleState(stored)
    }
  }, [])

  const setLocale = (next: Locale) => {
    setLocaleState(next)
    if (typeof window !== 'undefined') {
      localStorage.setItem('yv_locale', next)
    }
  }

  const value = useMemo<I18nContextType>(() => ({
    locale,
    setLocale,
    t: (key: string, fallback?: string) => dictionaries[locale][key] || fallback || key,
  }), [locale])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) {
    return {
      locale: 'en' as Locale,
      setLocale: () => {
        // no-op fallback for isolated renders (tests/storybook)
      },
      t: (key: string, fallback?: string) => dictionaries.en[key] || fallback || key,
    }
  }
  return ctx
}
