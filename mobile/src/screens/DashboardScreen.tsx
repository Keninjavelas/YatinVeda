import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { apiClient } from '../api/client';

interface Booking {
  id: string;
  practitioner_name: string;
  session_type: string;
  date: string;
  time: string;
  status: string;
}

export default function DashboardScreen() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchBookings = async () => {
    try {
      const data = await apiClient.get('/bookings/my');
      setBookings(Array.isArray(data) ? data : []);
    } catch {
      setBookings([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchBookings(); }, []);

  const onRefresh = () => { setRefreshing(true); fetchBookings(); };

  const statusColor = (s: string) => {
    switch (s) {
      case 'confirmed': return '#22c55e';
      case 'pending': return '#f59e0b';
      case 'cancelled': return '#ef4444';
      default: return '#64748b';
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#818cf8" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>My Bookings</Text>
      <FlatList
        data={bookings}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#818cf8" />}
        ListEmptyComponent={<Text style={styles.empty}>No bookings yet</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.practitioner}>{item.practitioner_name}</Text>
              <View style={[styles.badge, { backgroundColor: statusColor(item.status) + '20' }]}>
                <Text style={[styles.badgeText, { color: statusColor(item.status) }]}>
                  {item.status}
                </Text>
              </View>
            </View>
            <Text style={styles.type}>{item.session_type}</Text>
            <Text style={styles.date}>{item.date} at {item.time}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f172a' },
  header: { fontSize: 24, fontWeight: '700', color: '#e2e8f0', marginBottom: 16, marginTop: 48 },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 32, fontSize: 16 },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  practitioner: { fontSize: 16, fontWeight: '600', color: '#e2e8f0' },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  badgeText: { fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  type: { color: '#94a3b8', fontSize: 14, marginTop: 4 },
  date: { color: '#818cf8', fontSize: 13, marginTop: 4 },
});
